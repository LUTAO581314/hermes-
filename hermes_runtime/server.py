"""Minimal HTTP runtime for Hermes."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import signal
from typing import Any

from .config import RuntimeConfig, load_config
from .logging_utils import configure_logging


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
        if self.path == "/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "service": self.server.config.app_name,
                    "env": self.server.config.env,
                    "safe_mode": self.server.config.safe_mode,
                    "created_at": utc_now(),
                },
            )
            return

        if self.path == "/ready":
            payload = readiness(self.server.config)
            status = HTTPStatus.OK if payload["status"] == "ready" else HTTPStatus.SERVICE_UNAVAILABLE
            self._send_json(status, payload)
            return

        if self.path == "/version":
            self._send_json(
                HTTPStatus.OK,
                {
                    "service": self.server.config.app_name,
                    "version": "0.1.0",
                    "created_at": utc_now(),
                },
            )
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})

    def log_message(self, format: str, *args: Any) -> None:
        self.server.logger.info("%s %s", self.address_string(), format % args)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class HermesServer(ThreadingHTTPServer):
    config: RuntimeConfig
    logger: logging.Logger


def build_server(config: RuntimeConfig, logger: logging.Logger) -> HermesServer:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.log_dir.mkdir(parents=True, exist_ok=True)
    config.obsidian_vault_dir.mkdir(parents=True, exist_ok=True)

    server = HermesServer((config.host, config.port), HermesHandler)
    server.config = config
    server.logger = logger
    return server


def run() -> None:
    config = load_config()
    logger = configure_logging(config.log_dir)
    server = build_server(config, logger)
    logger.info("starting hermes runtime on %s:%s", config.host, config.port)
    logger.info("runtime config: %s", asdict(config))

    def handle_stop(signum: int, _frame: object) -> None:
        logger.info("received signal %s; stopping hermes runtime", signum)
        server.shutdown()

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    server.serve_forever(poll_interval=0.5)


if __name__ == "__main__":
    run()
