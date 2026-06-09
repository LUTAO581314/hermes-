from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import __version__
from .capabilities import collect_capabilities
from .config import ensure_runtime_dirs, load_settings
from .license import load_license
from .storage import create_job, list_audit_events, list_jobs, write_obsidian_report


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


class HermesHandler(BaseHTTPRequestHandler):
    server_version = "HermesHTTP/0.1"

    def do_GET(self) -> None:
        settings = load_settings()
        ensure_runtime_dirs(settings)

        if self.path == "/health":
            self._send(
                {
                    "status": "ok",
                    "service": "hermes",
                    "product": settings.product_name,
                    "brand": {
                        "key": settings.brand_key,
                        "trademark": settings.trademark_name,
                        "logo_text": settings.logo_text,
                    },
                    "env": settings.env,
                    "version": __version__,
                }
            )
            return
        if self.path == "/ready":
            license_state = load_license(settings.license_file)
            self._send(
                {
                    "status": "partial",
                    "service": "hermes",
                    "database": "configured" if settings.has_database else "missing_config",
                    "license": license_state.status,
                    "platform": "configured" if settings.platform_base_url else "missing_config",
                    "server_id": "configured" if settings.server_id else "missing_config",
                }
            )
            return
        if self.path == "/version":
            self._send({"service": "hermes", "version": __version__})
            return
        if self.path == "/capabilities":
            self._send({"service": "hermes", "capabilities": collect_capabilities(settings)})
            return
        if self.path == "/license":
            self._send({"service": "hermes", "license": load_license(settings.license_file).__dict__})
            return
        if self.path == "/jobs":
            self._send({"service": "hermes", "jobs": list_jobs(settings.data_dir)})
            return
        if self.path == "/audit":
            self._send({"service": "hermes", "audit": list_audit_events(settings.data_dir)})
            return

        self._send({"error": "not_found", "path": self.path}, status=404)

    def do_POST(self) -> None:
        settings = load_settings()
        ensure_runtime_dirs(settings)
        payload = self._read_json()

        if self.path == "/jobs":
            title = str(payload.get("title", "Untitled job"))
            prompt = str(payload.get("prompt", ""))
            route = str(payload.get("route", "general"))
            if not prompt.strip():
                self._send({"error": "invalid_request", "message": "prompt is required"}, status=400)
                return
            job = create_job(settings.data_dir, title=title, prompt=prompt, route=route)
            self._send({"service": "hermes", "job": job.__dict__}, status=201)
            return

        if self.path == "/obsidian/reports":
            title = str(payload.get("title", "Hermes Report"))
            body = str(payload.get("body", ""))
            if not body.strip():
                self._send({"error": "invalid_request", "message": "body is required"}, status=400)
                return
            report = write_obsidian_report(settings.obsidian_vault_dir, settings.data_dir, title=title, body=body)
            self._send({"service": "hermes", "report": report}, status=201)
            return

        self._send({"error": "not_found", "path": self.path}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, payload: dict[str, Any], status: int = 200) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        if isinstance(payload, dict):
            return payload
        return {}


def main() -> None:
    settings = load_settings()
    ensure_runtime_dirs(settings)
    server = ThreadingHTTPServer((settings.host, settings.port), HermesHandler)
    print(f"Hermes listening on http://{settings.host}:{settings.port}", flush=True)
    server.serve_forever()
