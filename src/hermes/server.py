from __future__ import annotations

import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import __version__
from .adapters.everos import (
    add_memory,
    as_payload,
    build_add_payload,
    build_flush_payload,
    build_search_payload,
    flush_memory,
    search_memory,
    status as everos_status,
)
from .adapters.funasr import (
    as_payload as funasr_payload,
    build_transcription_payload as build_funasr_transcription_payload,
    status as funasr_status,
    transcribe as funasr_transcribe,
)
from .adapters.mineru import as_payload as mineru_payload, build_parse_command as build_mineru_parse_command, status as mineru_status
from .adapters.mirofish import as_payload as mirofish_payload, status as mirofish_status
from .adapters.searxng import (
    as_payload as searxng_payload,
    build_search_payload as build_searxng_search_payload,
    search as searxng_search,
    status as searxng_status,
)
from .adapters.sonic import (
    as_payload as sonic_payload,
    build_push_payload as build_sonic_push_payload,
    build_query_payload as build_sonic_query_payload,
    ping as sonic_ping,
    push as sonic_push,
    query as sonic_query,
    status as sonic_status,
)
from .adapters.trendradar import as_payload as trendradar_payload, status as trendradar_status
from .capabilities import collect_capabilities
from .config import ensure_runtime_dirs, load_settings
from .db import database_status, run_migrations
from .document_pipeline import (
    generate_document_memory_candidates,
    index_document_artifacts,
    register_document_artifacts,
    run_document_ingest,
)
from .license import load_license
from .model_gateway import complete_chat
from .platform import build_platform_heartbeat
from .runtime_readiness import collect_runtime_readiness
from .storage import (
    create_audit_event,
    create_document_ingest,
    create_job,
    list_audit_events,
    list_document_artifacts,
    list_document_index_runs,
    list_document_ingest_runs,
    list_document_ingests,
    list_document_memory_candidates,
    list_jobs,
    write_obsidian_report,
)


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
            license_state = load_license(settings.license_file, settings.license_secret)
            db_state = database_status(settings)
            self._send(
                {
                    "status": "partial",
                    "service": "hermes",
                    "database": db_state.__dict__,
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
        if self.path == "/runtime/readiness":
            self._send({"service": "hermes", "runtime_readiness": collect_runtime_readiness(settings)})
            return
        if self.path == "/platform/heartbeat":
            self._send({"service": "hermes", "heartbeat": build_platform_heartbeat(settings)})
            return
        if self.path == "/license":
            self._send({"service": "hermes", "license": load_license(settings.license_file, settings.license_secret).__dict__})
            return
        if self.path == "/jobs":
            self._send({"service": "hermes", "jobs": list_jobs(settings.data_dir)})
            return
        if self.path == "/document/ingests":
            self._send({"service": "hermes", "document_ingests": list_document_ingests(settings.data_dir)})
            return
        if self.path == "/document/ingest-runs":
            self._send({"service": "hermes", "document_ingest_runs": list_document_ingest_runs(settings.data_dir)})
            return
        if self.path == "/document/artifacts":
            self._send({"service": "hermes", "document_artifacts": list_document_artifacts(settings.data_dir)})
            return
        if self.path == "/document/index-runs":
            self._send({"service": "hermes", "document_index_runs": list_document_index_runs(settings.data_dir)})
            return
        if self.path == "/document/memory-candidates":
            self._send({"service": "hermes", "document_memory_candidates": list_document_memory_candidates(settings.data_dir)})
            return
        if self.path == "/audit":
            self._send({"service": "hermes", "audit": list_audit_events(settings.data_dir)})
            return
        if self.path == "/memory/status":
            self._send({"service": "hermes", "memory": as_payload(everos_status(settings))})
            return
        if self.path == "/voice/asr/status":
            self._send({"service": "hermes", "voice_asr": funasr_payload(funasr_status(settings))})
            return
        if self.path == "/document/parse/status":
            self._send({"service": "hermes", "document_parse": mineru_payload(mineru_status(settings))})
            return
        if self.path == "/intel/status":
            self._send({"service": "hermes", "intelligence": trendradar_payload(trendradar_status(settings))})
            return
        if self.path == "/simulation/status":
            self._send({"service": "hermes", "simulation": mirofish_payload(mirofish_status(settings))})
            return
        if self.path == "/search/status":
            self._send({"service": "hermes", "search": searxng_payload(searxng_status(settings))})
            return
        if self.path == "/index/status":
            self._send({"service": "hermes", "index": sonic_payload(sonic_status(settings))})
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

        if self.path == "/chat":
            prompt = str(payload.get("prompt", ""))
            system = str(payload.get("system", ""))
            if not prompt.strip():
                self._send({"error": "invalid_request", "message": "prompt is required"}, status=400)
                return
            result = complete_chat(settings, prompt, system=system)
            create_audit_event(
                settings.data_dir,
                "chat.completed" if result.status == "completed" else "chat.not_completed",
                resource_type="model_gateway",
                resource_ref=result.model or "missing_model",
                risk_level="low",
                payload={"status": result.status, "provider": result.provider, "error": result.error},
            )
            status = 200 if result.status == "completed" else 503
            self._send({"service": "hermes", "chat": result.__dict__}, status=status)
            return

        if self.path == "/memory/ingest":
            text = str(payload.get("text", ""))
            if not text.strip():
                self._send({"error": "invalid_request", "message": "text is required"}, status=400)
                return
            result = add_memory(
                settings,
                build_add_payload(
                    user_id=str(payload.get("user_id", "owner")),
                    session_id=str(payload.get("session_id", "api-session")),
                    text=text,
                    app_id=str(payload.get("app_id", "default")),
                    project_id=str(payload.get("project_id", "default")),
                    sender_name=str(payload.get("sender_name") or "") or None,
                ),
            )
            self._send({"service": "hermes", "memory": as_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/memory/flush":
            session_id = str(payload.get("session_id", ""))
            if not session_id.strip():
                self._send({"error": "invalid_request", "message": "session_id is required"}, status=400)
                return
            result = flush_memory(
                settings,
                build_flush_payload(
                    session_id=session_id,
                    app_id=str(payload.get("app_id", "default")),
                    project_id=str(payload.get("project_id", "default")),
                ),
            )
            self._send({"service": "hermes", "memory": as_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/memory/search":
            query = str(payload.get("query", ""))
            if not query.strip():
                self._send({"error": "invalid_request", "message": "query is required"}, status=400)
                return
            result = search_memory(
                settings,
                build_search_payload(
                    query=query,
                    user_id=str(payload.get("user_id", "owner")),
                    agent_id=str(payload.get("agent_id", "")),
                    app_id=str(payload.get("app_id", "default")),
                    project_id=str(payload.get("project_id", "default")),
                    top_k=int(payload.get("top_k", 5)),
                    method=str(payload.get("method", "hybrid")),
                    include_profile=bool(payload.get("include_profile", False)),
                ),
            )
            self._send({"service": "hermes", "memory": as_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/search/query":
            query = str(payload.get("query", ""))
            if not query.strip():
                self._send({"error": "invalid_request", "message": "query is required"}, status=400)
                return
            result = searxng_search(
                settings,
                build_searxng_search_payload(
                    query=query,
                    categories=str(payload.get("categories", "")),
                    engines=str(payload.get("engines", "")),
                    language=str(payload.get("language", "")),
                    safesearch=str(payload.get("safesearch", "")),
                    time_range=str(payload.get("time_range", "")),
                    page=int(payload.get("page", 1)),
                ),
            )
            self._send({"service": "hermes", "search": searxng_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/index/ping":
            result = sonic_ping(settings)
            self._send({"service": "hermes", "index": sonic_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/index/push":
            required = ("collection", "bucket", "object_id", "text")
            if any(not str(payload.get(name, "")).strip() for name in required):
                self._send({"error": "invalid_request", "message": "collection, bucket, object_id, and text are required"}, status=400)
                return
            result = sonic_push(
                settings,
                build_sonic_push_payload(
                    collection=str(payload["collection"]),
                    bucket=str(payload["bucket"]),
                    object_id=str(payload["object_id"]),
                    text=str(payload["text"]),
                    lang=str(payload.get("lang", "")),
                ),
            )
            self._send({"service": "hermes", "index": sonic_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/index/query":
            required = ("collection", "bucket", "query")
            if any(not str(payload.get(name, "")).strip() for name in required):
                self._send({"error": "invalid_request", "message": "collection, bucket, and query are required"}, status=400)
                return
            result = sonic_query(
                settings,
                build_sonic_query_payload(
                    collection=str(payload["collection"]),
                    bucket=str(payload["bucket"]),
                    query=str(payload["query"]),
                    limit=int(payload.get("limit", 10)),
                    offset=int(payload.get("offset", 0)),
                    lang=str(payload.get("lang", "")),
                ),
            )
            self._send({"service": "hermes", "index": sonic_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/voice/asr/transcribe":
            audio_path = str(payload.get("audio_path", ""))
            if not audio_path.strip():
                self._send({"error": "invalid_request", "message": "audio_path is required"}, status=400)
                return
            result = funasr_transcribe(
                settings,
                build_funasr_transcription_payload(
                    audio_path=audio_path,
                    model=str(payload.get("model", "")),
                    language=str(payload.get("language", "")),
                    prompt=str(payload.get("prompt", "")),
                    response_format=str(payload.get("response_format", "json")),
                ),
            )
            self._send({"service": "hermes", "voice_asr": funasr_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/document/parse/ingest-plan":
            input_path = str(payload.get("input_path", ""))
            if not input_path.strip():
                self._send({"error": "invalid_request", "message": "input_path is required"}, status=400)
                return
            plan = build_mineru_parse_command(
                settings,
                input_path=input_path,
                output_dir=str(payload.get("output_dir", "")),
                backend=str(payload.get("backend", "")),
                language=str(payload.get("language", "")),
                source=str(payload.get("source", "")),
                device=str(payload.get("device", "")),
            )
            output_dir = plan.command[plan.command.index("-o") + 1]
            ingest = create_document_ingest(
                settings.data_dir,
                title=str(payload.get("title", "")),
                input_path=input_path,
                output_dir=output_dir,
                parser_command=plan.command,
            )
            self._send({"service": "hermes", "document_ingest": ingest.__dict__, "document_parse": mineru_payload(plan)}, status=201)
            return

        if self.path == "/document/parse/run-ingest":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            result = run_document_ingest(
                settings.data_dir,
                ingest_id,
                timeout_seconds=int(payload.get("timeout_seconds") or settings.mineru_timeout_seconds),
            )
            status = 200 if result.status == "completed" else 503
            if result.status == "not_found":
                status = 404
            self._send({"service": "hermes", "document_pipeline": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/register-artifacts":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            result = register_document_artifacts(settings.data_dir, ingest_id)
            status = 200 if result.status == "completed" else 503
            if result.status == "not_found":
                status = 404
            self._send({"service": "hermes", "document_artifact_registration": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/index-artifacts":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            result = index_document_artifacts(
                settings,
                ingest_id,
                collection=str(payload.get("collection", "bairui")),
                bucket=str(payload.get("bucket", "documents")),
                lang=str(payload.get("lang", "")),
            )
            status = 200 if result.status in {"completed", "skipped"} else 503
            if result.status == "not_found":
                status = 404
            self._send({"service": "hermes", "document_index": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/memory-candidates":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            result = generate_document_memory_candidates(
                settings.data_dir,
                ingest_id,
                max_candidates=int(payload.get("max_candidates", 20)),
            )
            status = 200 if result.status in {"completed", "skipped"} else 503
            if result.status == "not_found":
                status = 404
            self._send({"service": "hermes", "document_memory_candidate_generation": asdict(result)}, status=status)
            return

        if self.path == "/admin/migrate":
            result = run_migrations(settings)
            create_audit_event(
                settings.data_dir,
                "database.migration",
                resource_type="database",
                resource_ref="postgresql",
                risk_level="medium",
                payload=result.__dict__,
            )
            status = 200 if result.status == "ready" else 503
            self._send({"service": "hermes", "database": result.__dict__}, status=status)
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


def serve(settings: Any | None = None) -> None:
    settings = settings or load_settings()
    ensure_runtime_dirs(settings)
    server = ThreadingHTTPServer((settings.host, settings.port), HermesHandler)
    print(f"Hermes listening on http://{settings.host}:{settings.port}", flush=True)
    server.serve_forever()


def main() -> None:
    serve()
