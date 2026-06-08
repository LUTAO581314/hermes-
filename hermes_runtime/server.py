"""Minimal HTTP runtime for Hermes."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import signal
import threading
from typing import Any
from urllib.parse import parse_qs, urlparse

from .async_jobs import AsyncJobStore, jobs_payload
from .config import RuntimeConfig, load_config
from .context_budget import context_payload
from .latency import LatencyRecorder, latency_payload
from .logging_utils import configure_logging
from .performance import performance_payload
from .routing import route_payload
from .social_turn import plan_social_turn


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def readiness(config: RuntimeConfig) -> dict[str, Any]:
    checks = {
        "data_dir": config.data_dir.exists(),
        "log_dir": config.log_dir.exists(),
        "obsidian_vault_dir": config.obsidian_vault_dir.exists(),
        "safe_mode": config.safe_mode,
    }
    return {
        "status": "ready" if all(checks.values()) else "degraded",
        "checks": checks,
        "created_at": utc_now(),
    }


class HermesHandler(BaseHTTPRequestHandler):
    server_version = "HermesRuntime/0.1"

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == "/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "service": self.server.config.app_name,
                    "env": self.server.config.env,
                    "safe_mode": self.server.config.safe_mode,
                    "search": {
                        "mode": self.server.config.search_mode,
                        "project": self.server.config.search_project,
                    },
                    "ai": {
                        "provider": self.server.config.ai_provider,
                        "base_url_configured": bool(self.server.config.ai_base_url),
                        "api_key_configured": self.server.config.ai_api_key_configured,
                        "default_model": self.server.config.ai_default_model,
                        "fast_model": self.server.config.ai_fast_model,
                        "summary_model": self.server.config.ai_summary_model,
                        "reasoning_model": self.server.config.ai_reasoning_model,
                        "vision_model": self.server.config.ai_vision_model,
                    },
                    "wechat": {
                        "mode": self.server.config.wechat_mode,
                        "channel": self.server.config.wechat_channel,
                        "persona_mode": self.server.config.wechat_persona_mode,
                        "proactive_chat": self.server.config.wechat_proactive_chat,
                        "max_daily_proactive_messages": (
                            self.server.config.wechat_max_daily_proactive_messages
                        ),
                        "personal_bridge_enabled": (
                            self.server.config.wechat_personal_bridge_enabled
                        ),
                        "official_account": {
                            "app_id_configured": (
                                self.server.config.wechat_official_app_id_configured
                            ),
                            "app_secret_configured": (
                                self.server.config.wechat_official_app_secret_configured
                            ),
                            "token_configured": (
                                self.server.config.wechat_official_token_configured
                            ),
                            "aes_key_configured": (
                                self.server.config.wechat_official_aes_key_configured
                            ),
                        },
                        "wecom": {
                            "corp_id_configured": self.server.config.wecom_corp_id_configured,
                            "agent_id_configured": (
                                self.server.config.wecom_agent_id_configured
                            ),
                            "secret_configured": self.server.config.wecom_secret_configured,
                            "customer_service_token_configured": (
                                self.server.config.wecom_customer_service_token_configured
                            ),
                        },
                    },
                    "stickers": {
                        "bridge_enabled": self.server.config.sticker_bridge_enabled,
                        "default_provider": self.server.config.sticker_default_provider,
                        "default_style": self.server.config.sticker_default_style,
                        "api_key_configured": (
                            self.server.config.sticker_api_key_configured
                        ),
                        "image_generation_enabled": (
                            self.server.config.sticker_image_generation_enabled
                        ),
                        "image_generation_base_url_configured": bool(
                            self.server.config.sticker_image_generation_base_url
                        ),
                        "image_generation_model": (
                            self.server.config.sticker_image_generation_model
                        ),
                        "generation_review_required": (
                            self.server.config.sticker_generation_review_required
                        ),
                        "runtime_cache_enabled": (
                            self.server.config.sticker_runtime_cache_enabled
                        ),
                    },
                    "performance": performance_payload(self.server.config)["profile"],
                    "created_at": utc_now(),
                },
            )
            return

        if path == "/ready":
            payload = readiness(self.server.config)
            status = HTTPStatus.OK if payload["status"] == "ready" else HTTPStatus.SERVICE_UNAVAILABLE
            self._send_json(status, payload)
            return

        if path == "/version":
            self._send_json(
                HTTPStatus.OK,
                {
                    "service": self.server.config.app_name,
                    "version": "0.1.0",
                    "created_at": utc_now(),
                },
            )
            return

        if path == "/performance":
            self._send_json(HTTPStatus.OK, performance_payload(self.server.config))
            return

        if path == "/context":
            message = query.get("message", [""])[0]
            trace = self.server.latency.trace(route="context_budget")
            trace.mark("intake_ms")
            payload = context_payload(message, self.server.config)
            trace.route = payload["route"]["route"]
            trace.mark("context_ms")
            self._send_json(HTTPStatus.OK, payload)
            trace.mark("final_send_ms")
            trace.finish()
            return

        if path == "/latency":
            limit = int(query.get("limit", ["50"])[0] or "50")
            self._send_json(HTTPStatus.OK, latency_payload(self.server.latency, limit))
            return

        if path == "/jobs":
            limit = int(query.get("limit", ["50"])[0] or "50")
            self._send_json(HTTPStatus.OK, jobs_payload(self.server.jobs, limit))
            return

        if path == "/route":
            message = query.get("message", [""])[0]
            trace = self.server.latency.trace(route="route_diagnostic")
            trace.mark("intake_ms")
            payload = route_payload(message, self.server.config)
            trace.route = payload["route"]["route"]
            trace.mark("context_ms")
            self._send_json(HTTPStatus.OK, payload)
            trace.mark("final_send_ms")
            trace.finish()
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/latency/turn":
            self._handle_latency_turn()
            return

        if parsed_url.path == "/jobs":
            self._handle_create_job()
            return

        if parsed_url.path == "/jobs/transition":
            self._handle_transition_job()
            return

        if parsed_url.path == "/social/turn":
            self._handle_social_turn()
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": parsed_url.path})

    def _handle_latency_turn(self) -> None:
        try:
            payload = self._read_json_body()
            record = self.server.latency.add_external(
                route=payload.get("route", "unknown"),
                status=payload.get("status", "ok"),
                stages=payload.get("stages", {}),
                turn_id=payload.get("turn_id"),
            )
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        self._send_json(HTTPStatus.OK, {"status": "ok", "record": record.__dict__})

    def _handle_create_job(self) -> None:
        try:
            payload = self._read_json_body()
            job = self.server.jobs.create(
                route=payload.get("route", "unknown"),
                channel=payload.get("channel", "unknown"),
                target_id=payload.get("target_id", "unknown"),
                input_text=payload.get("input", ""),
                tool_name=payload.get("tool_name", "unknown"),
                owner_confirmation_required=payload.get(
                    "owner_confirmation_required", False
                ),
            )
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        self._send_json(HTTPStatus.OK, {"status": "ok", "job": job.__dict__})

    def _handle_transition_job(self) -> None:
        try:
            payload = self._read_json_body()
            job = self.server.jobs.transition(
                job_id=payload.get("job_id", ""),
                status=payload.get("status", ""),
                result_pointer=payload.get("result_pointer", ""),
                error_message=payload.get("error_message", ""),
            )
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        self._send_json(HTTPStatus.OK, {"status": "ok", "job": job.__dict__})

    def _handle_social_turn(self) -> None:
        try:
            payload = self._read_json_body()
            trace = self.server.latency.trace(route="social_turn")
            trace.mark("intake_ms")
            plan = plan_social_turn(
                message=payload.get("message", ""),
                channel=payload.get("channel", "unknown"),
                target_id=payload.get("target_id", "unknown"),
                config=self.server.config,
                jobs=self.server.jobs,
            )
            trace.route = plan["route"]["route"]
            trace.mark("context_ms")
            self._send_json(HTTPStatus.OK, plan)
            trace.mark("final_send_ms")
            trace.finish()
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

    def log_message(self, format: str, *args: Any) -> None:
        self.server.logger.info("%s %s", self.address_string(), format % args)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        if length > 64 * 1024:
            raise ValueError("request body too large")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as error:
            raise ValueError("invalid json") from error
        if not isinstance(payload, dict):
            raise ValueError("json body must be an object")
        return payload


class HermesServer(ThreadingHTTPServer):
    config: RuntimeConfig
    logger: logging.Logger
    latency: LatencyRecorder
    jobs: AsyncJobStore


def build_server(config: RuntimeConfig, logger: logging.Logger) -> HermesServer:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.log_dir.mkdir(parents=True, exist_ok=True)
    config.obsidian_vault_dir.mkdir(parents=True, exist_ok=True)

    server = HermesServer((config.host, config.port), HermesHandler)
    server.config = config
    server.logger = logger
    server.latency = LatencyRecorder()
    server.jobs = AsyncJobStore()
    return server


def run() -> None:
    config = load_config()
    logger = configure_logging(config.log_dir)
    server = build_server(config, logger)
    logger.info("starting hermes runtime on %s:%s", config.host, config.port)
    logger.info("runtime config: %s", asdict(config))
    stop_requested = False

    def handle_stop(signum: int, _frame: object) -> None:
        nonlocal stop_requested
        if stop_requested:
            return
        stop_requested = True
        logger.info("received signal %s; stopping hermes runtime", signum)
        threading.Thread(target=server.shutdown, name="hermes-shutdown", daemon=True).start()

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        server.server_close()
        logger.info("hermes runtime stopped")


if __name__ == "__main__":
    run()
