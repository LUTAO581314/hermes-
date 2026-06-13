from __future__ import annotations

import hmac
import json
import mimetypes
from dataclasses import asdict
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from . import __version__
from .agents import (
    add_agent_user_message,
    as_payload as agent_payload,
    create_agent_session,
    get_agent,
    list_agent_events,
    list_agent_events_page,
    list_agent_sessions,
    list_agent_promotions,
    list_agents,
    promote_agent_event,
    retry_agent_event,
    run_agent_round,
    update_agent_session,
)
from .admin_session import as_payload as admin_session_payload, build_admin_session_status
from .backup import backup_payload, build_backup_plan
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
from .avatar import as_payload as avatar_payload, avatar_engine_status, build_avatar_manifest, set_avatar_state, validate_avatar_model
from .channels import (
    as_payload as channel_payload,
    channel_status,
    channel_targets,
    diagnose_channel_targets,
    list_channel_approvals,
    list_channel_approval_reviews,
    plan_channel_send,
    review_channel_approval,
)
from .codegraph import (
    as_payload as codegraph_payload,
    codegraph_impact,
    codegraph_overview,
    codegraph_status,
    list_codegraph_repos,
    query_codegraph,
    register_codegraph_repo,
    scan_codegraph_repo,
)
from .config import ensure_runtime_dirs, load_settings
from .config_apply import apply_local_config
from .config_status import build_config_status
from .db import database_status, run_migrations
from .demo import seed_demo_data
from .demo_flow import run_demo_flow
from .diagnostics import build_diagnostic_bundle
from .document_pipeline import (
    build_document_ingest_session_summary,
    build_document_workbench_state,
    create_document_ingest_report,
    create_document_source_refs,
    execute_document_workbench_next,
    generate_document_memory_candidates,
    index_document_artifacts,
    list_document_ingest_session_summaries,
    list_pending_document_memory_reviews,
    register_document_artifacts,
    review_document_memory_candidate,
    review_document_memory_candidates_batch,
    run_document_workbench_until_blocked,
    run_document_ingest,
)
from .events import build_sse_frame, list_frontend_events
from .frontend_contract import build_frontend_contract
from .license import load_license
from .model_gateway import complete_chat
from .observability import build_metrics_summary, list_error_logs, record_error_log
from .platform import build_platform_heartbeat
from .runtime_readiness import collect_runtime_readiness
from .storage import (
    create_audit_event,
    create_document_ingest,
    create_job,
    list_audit_events,
    list_document_artifacts,
    list_document_index_runs,
    list_document_ingest_reports,
    list_document_ingest_runs,
    list_document_ingests,
    list_document_memory_candidates,
    list_document_memory_reviews,
    list_jobs,
    list_reports,
    list_source_refs,
    write_obsidian_report,
)


PUBLIC_SERVICE = "bairui"


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


class HermesHandler(BaseHTTPRequestHandler):
    server_version = "bairuiHTTP/0.1"

    def do_GET(self) -> None:
        settings = load_settings()
        ensure_runtime_dirs(settings)

        if self.path == "/health":
            self._send(
                {
                    "status": "ok",
                    "service": PUBLIC_SERVICE,
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
                    "service": PUBLIC_SERVICE,
                    "database": db_state.__dict__,
                    "license": license_state.status,
                    "platform": "configured" if settings.platform_base_url else "missing_config",
                    "server_id": "configured" if settings.server_id else "missing_config",
                }
            )
            return
        if self.path == "/version":
            self._send({"service": PUBLIC_SERVICE, "version": __version__})
            return
        if self.path in {"/console", "/console/"}:
            self._send_console_asset("index.html")
            return
        if self.path.startswith("/console/"):
            self._send_console_asset(self.path.removeprefix("/console/"))
            return
        if self.path == "/capabilities":
            self._send({"service": PUBLIC_SERVICE, "capabilities": collect_capabilities(settings)})
            return
        if self.path == "/frontend/contract":
            self._send({"service": "bairui", "frontend_contract": build_frontend_contract(settings, __version__)})
            return
        if self.path == "/config/status":
            self._send({"service": PUBLIC_SERVICE, "config_status": build_config_status(settings)})
            return
        if self.path == "/backup/status":
            self._send({"service": PUBLIC_SERVICE, "backup": backup_payload(settings)})
            return
        if self.path == "/backup/plan":
            self._send({"service": PUBLIC_SERVICE, "backup_plan": build_backup_plan(settings)})
            return
        if self.path == "/admin/session":
            self._send({"service": PUBLIC_SERVICE, "admin_session": admin_session_payload(build_admin_session_status(settings, self.headers))})
            return
        if self.path == "/runtime/readiness":
            self._send({"service": PUBLIC_SERVICE, "runtime_readiness": collect_runtime_readiness(settings)})
            return
        if self.path == "/diagnostics/bundle":
            self._send({"service": PUBLIC_SERVICE, "diagnostic_bundle": build_diagnostic_bundle(settings)})
            return
        if self.path == "/metrics":
            self._send({"service": PUBLIC_SERVICE, "metrics": build_metrics_summary(settings)})
            return
        if self.path == "/errors":
            self._send({"service": PUBLIC_SERVICE, "errors": list_error_logs(settings)})
            return
        if self.path == "/avatar/status":
            self._send({"service": PUBLIC_SERVICE, "avatar": avatar_payload(avatar_engine_status(settings))})
            return
        if self.path == "/avatar/manifest":
            self._send({"service": PUBLIC_SERVICE, "avatar_manifest": build_avatar_manifest(settings)})
            return
        if self.path.startswith("/avatars/assets/"):
            self._send_avatar_asset(settings, self.path.removeprefix("/avatars/assets/"))
            return
        if self.path == "/platform/heartbeat":
            self._send({"service": PUBLIC_SERVICE, "heartbeat": build_platform_heartbeat(settings)})
            return
        if self.path == "/license":
            self._send({"service": PUBLIC_SERVICE, "license": load_license(settings.license_file, settings.license_secret).__dict__})
            return
        if self.path == "/jobs":
            self._send({"service": PUBLIC_SERVICE, "jobs": list_jobs(settings.data_dir)})
            return
        if self.path == "/agents":
            self._send({"service": PUBLIC_SERVICE, "agents": [agent_payload(agent) for agent in list_agents(settings)]})
            return
        if self.path.startswith("/agents/session/") and self.path.endswith("/events"):
            session_id = self.path.removeprefix("/agents/session/").removesuffix("/events").strip("/")
            self._send({"service": PUBLIC_SERVICE, "agent_events": list_agent_events(settings, session_id=session_id)})
            return
        if self.path.startswith("/agents/session/") and self.path.endswith("/promotions"):
            session_id = self.path.removeprefix("/agents/session/").removesuffix("/promotions").strip("/")
            self._send({"service": PUBLIC_SERVICE, "agent_promotions": list_agent_promotions(settings, session_id=session_id)})
            return
        if self.path.startswith("/agents/") and not self.path.startswith("/agents/session"):
            agent_id = self.path.removeprefix("/agents/").strip("/")
            agent = get_agent(settings, agent_id)
            if agent is None:
                self._send({"error": "not_found", "path": self.path}, status=404)
                return
            self._send({"service": PUBLIC_SERVICE, "agent": agent_payload(agent)})
            return
        if self.path == "/agents/sessions":
            self._send({"service": PUBLIC_SERVICE, "agent_sessions": list_agent_sessions(settings)})
            return
        if self.path == "/agents/events":
            self._send({"service": PUBLIC_SERVICE, "agent_events": list_agent_events(settings)})
            return
        if self.path == "/document/ingests":
            self._send({"service": PUBLIC_SERVICE, "document_ingests": list_document_ingests(settings.data_dir)})
            return
        if self.path == "/document/ingest-runs":
            self._send({"service": PUBLIC_SERVICE, "document_ingest_runs": list_document_ingest_runs(settings.data_dir)})
            return
        if self.path == "/document/ingest-reports":
            self._send({"service": PUBLIC_SERVICE, "document_ingest_reports": list_document_ingest_reports(settings.data_dir)})
            return
        if self.path == "/reports":
            self._send({"service": PUBLIC_SERVICE, "reports": list_reports(settings.data_dir)})
            return
        if self.path == "/document/artifacts":
            self._send({"service": PUBLIC_SERVICE, "document_artifacts": list_document_artifacts(settings.data_dir)})
            return
        if self.path == "/document/index-runs":
            self._send({"service": PUBLIC_SERVICE, "document_index_runs": list_document_index_runs(settings.data_dir)})
            return
        if self.path == "/document/memory-candidates":
            self._send({"service": PUBLIC_SERVICE, "document_memory_candidates": list_document_memory_candidates(settings.data_dir)})
            return
        if self.path == "/document/memory-reviews":
            self._send({"service": PUBLIC_SERVICE, "document_memory_reviews": list_document_memory_reviews(settings.data_dir)})
            return
        if self.path == "/source-refs":
            self._send({"service": PUBLIC_SERVICE, "source_refs": list_source_refs(settings.data_dir)})
            return
        if self.path == "/audit":
            self._send({"service": PUBLIC_SERVICE, "audit": list_audit_events(settings.data_dir)})
            return
        if self.path == "/events":
            self._send_sse(list_frontend_events(settings.data_dir))
            return
        if self.path == "/channels/status":
            self._send({"service": PUBLIC_SERVICE, "channels": channel_payload(channel_status(settings))})
            return
        if self.path == "/channels/targets":
            self._send({"service": PUBLIC_SERVICE, "channel_targets": list(channel_targets(settings))})
            return
        if self.path == "/channels/diagnostics":
            self._send({"service": PUBLIC_SERVICE, "channel_diagnostics": [channel_payload(item) for item in diagnose_channel_targets(settings)]})
            return
        if self.path == "/channels/approvals":
            self._send({"service": PUBLIC_SERVICE, "channel_approvals": list(list_channel_approvals(settings))})
            return
        if self.path == "/channels/approvals/reviews":
            self._send({"service": PUBLIC_SERVICE, "channel_approval_reviews": list_channel_approval_reviews(settings.data_dir)})
            return
        if self.path == "/memory/status":
            self._send({"service": PUBLIC_SERVICE, "memory": as_payload(everos_status(settings))})
            return
        if self.path == "/voice/asr/status":
            self._send({"service": PUBLIC_SERVICE, "voice_asr": funasr_payload(funasr_status(settings))})
            return
        if self.path == "/document/parse/status":
            self._send({"service": PUBLIC_SERVICE, "document_parse": mineru_payload(mineru_status(settings))})
            return
        if self.path == "/intel/status":
            self._send({"service": PUBLIC_SERVICE, "intelligence": trendradar_payload(trendradar_status(settings))})
            return
        if self.path == "/simulation/status":
            self._send({"service": PUBLIC_SERVICE, "simulation": mirofish_payload(mirofish_status(settings))})
            return
        if self.path == "/search/status":
            self._send({"service": PUBLIC_SERVICE, "search": searxng_payload(searxng_status(settings))})
            return
        if self.path == "/index/status":
            self._send({"service": PUBLIC_SERVICE, "index": sonic_payload(sonic_status(settings))})
            return
        if self.path == "/codegraph/status":
            self._send({"service": PUBLIC_SERVICE, "codegraph": codegraph_payload(codegraph_status(settings))})
            return
        if self.path == "/codegraph/repos":
            self._send({"service": PUBLIC_SERVICE, "codegraph_repos": list_codegraph_repos(settings)})
            return
        if self.path == "/codegraph/overview" or self.path.startswith("/codegraph/overview?"):
            query = parse_qs(urlparse(self.path).query)
            repo_id = str((query.get("repo_id") or [""])[0])
            self._send({"service": PUBLIC_SERVICE, "codegraph": codegraph_overview(settings, repo_id=repo_id)})
            return

        self._send({"error": "not_found", "path": self.path}, status=404)

    def do_POST(self) -> None:
        settings = load_settings()
        ensure_runtime_dirs(settings)
        payload = self._read_json()

        if not self._require_owner(settings, permission="write_api"):
            return

        if self.path == "/config/apply":
            result = apply_local_config(settings, payload)
            next_settings = load_settings()
            create_audit_event(
                settings.data_dir,
                "config.apply.confirmation_required" if result["status"] == "confirmation_required" else "config.apply",
                actor_type="owner",
                actor_ref="local_console",
                resource_type="configuration",
                resource_ref="local-config",
                risk_level="high" if result.get("dangerous_fields") else "medium",
                payload={
                    "status": result.get("status"),
                    "applied": result.get("applied", {}),
                    "dangerous_fields": result.get("dangerous_fields", []),
                    "restart_required": result.get("restart_required", False),
                    "secret_echo": False,
                },
            )
            status = 200 if result["status"] in {"saved", "no_changes"} else 409 if result["status"] == "confirmation_required" else 400
            self._send({"service": PUBLIC_SERVICE, "config_apply": result, "config_status": build_config_status(next_settings)}, status=status)
            return

        if self.path == "/jobs":
            title = str(payload.get("title", "Untitled job"))
            prompt = str(payload.get("prompt", ""))
            route = str(payload.get("route", "general"))
            if not prompt.strip():
                self._send({"error": "invalid_request", "message": "prompt is required"}, status=400)
                return
            job = create_job(settings.data_dir, title=title, prompt=prompt, route=route)
            self._send({"service": PUBLIC_SERVICE, "job": job.__dict__}, status=201)
            return

        if self.path == "/demo/seed":
            result = seed_demo_data(settings, force=bool(payload.get("force", False)))
            status = 201 if result["status"] == "completed" else 200
            self._send({"service": PUBLIC_SERVICE, "demo_seed": result}, status=status)
            return

        if self.path == "/demo/flow":
            result = run_demo_flow(
                settings,
                workspace=str(payload.get("workspace", "")),
                force_seed=bool(payload.get("force_seed", False)),
            )
            self._send({"service": PUBLIC_SERVICE, "demo_flow": result}, status=200 if result["status"] == "completed" else 207)
            return

        if self.path == "/obsidian/reports":
            title = str(payload.get("title", "bairui Report"))
            body = str(payload.get("body", ""))
            if not body.strip():
                self._send({"error": "invalid_request", "message": "body is required"}, status=400)
                return
            report = write_obsidian_report(settings.obsidian_vault_dir, settings.data_dir, title=title, body=body)
            self._send({"service": PUBLIC_SERVICE, "report": report}, status=201)
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
            self._send({"service": PUBLIC_SERVICE, "chat": result.__dict__}, status=status)
            return

        if self.path == "/agents/session":
            agent_ids = payload.get("agent_ids", ())
            if not isinstance(agent_ids, list):
                self._send({"error": "invalid_request", "message": "agent_ids must be a list"}, status=400)
                return
            session = create_agent_session(settings, str(payload.get("title", "")), tuple(str(agent_id) for agent_id in agent_ids))
            self._send({"service": PUBLIC_SERVICE, "agent_session": agent_payload(session)}, status=201)
            return

        if self.path.startswith("/agents/session/") and self.path.endswith("/message"):
            session_id = self.path.removeprefix("/agents/session/").removesuffix("/message").strip("/")
            result = add_agent_user_message(settings, session_id, str(payload.get("content", "")))
            status = 200 if result["status"] == "completed" else 400
            if result["status"] == "not_found":
                status = 404
            self._send({"service": PUBLIC_SERVICE, "agent_message": result}, status=status)
            return

        if self.path.startswith("/agents/session/") and self.path.endswith("/round"):
            session_id = self.path.removeprefix("/agents/session/").removesuffix("/round").strip("/")
            result = run_agent_round(settings, session_id, str(payload.get("prompt", "")))
            status = 200 if result["status"] in {"completed", "partial"} else 400
            if result["status"] == "not_found":
                status = 404
            self._send({"service": PUBLIC_SERVICE, "agent_round": result}, status=status)
            return

        if self.path.startswith("/agents/session/") and self.path.endswith("/events"):
            session_id = self.path.removeprefix("/agents/session/").removesuffix("/events").strip("/")
            result = list_agent_events_page(
                settings,
                session_id=session_id,
                limit=int(payload.get("limit", 50)),
                offset=int(payload.get("offset", 0)),
            )
            self._send({"service": PUBLIC_SERVICE, "agent_events": result["events"], "agent_events_page": result})
            return

        if self.path.startswith("/agents/session/") and self.path.endswith("/title"):
            session_id = self.path.removeprefix("/agents/session/").removesuffix("/title").strip("/")
            result = update_agent_session(settings, session_id, title=str(payload.get("title", "")))
            status = 200 if result["status"] == "completed" else 400
            if result["status"] == "not_found":
                status = 404
            self._send({"service": PUBLIC_SERVICE, "agent_session_update": result}, status=status)
            return

        if self.path.startswith("/agents/session/") and self.path.endswith("/promote"):
            result = promote_agent_event(settings, str(payload.get("event_id", "")), str(payload.get("target", "")))
            status = 200 if result["status"] in {"planned", "duplicate"} else 400
            if result["status"] == "not_found":
                status = 404
            self._send({"service": PUBLIC_SERVICE, "agent_promotion": result}, status=status)
            return

        if self.path.startswith("/agents/session/") and self.path.endswith("/retry"):
            result = retry_agent_event(settings, str(payload.get("event_id", "")))
            status = 200 if result["status"] in {"completed", "partial"} else 400
            if result["status"] == "not_found":
                status = 404
            if result["status"] == "not_retryable":
                status = 409
            self._send({"service": PUBLIC_SERVICE, "agent_retry": result}, status=status)
            return

        if self.path == "/channels/send":
            target_id = str(payload.get("target_id", ""))
            media_kind = str(payload.get("media_kind", "text"))
            text = str(payload.get("text", ""))
            attachment_path = str(payload.get("attachment_path", ""))
            if not target_id.strip():
                self._send({"error": "invalid_request", "message": "target_id is required"}, status=400)
                return
            if not media_kind.strip():
                self._send({"error": "invalid_request", "message": "media_kind is required"}, status=400)
                return
            if not text.strip() and not attachment_path.strip():
                self._send({"error": "invalid_request", "message": "text or attachment_path is required"}, status=400)
                return
            result = plan_channel_send(settings, payload)
            status = 202 if result.status == "approval_required" else 503
            if result.status in {"invalid_request", "unsupported_media"}:
                status = 400
            if result.status == "not_found":
                status = 404
            self._send({"service": PUBLIC_SERVICE, "channel_send": channel_payload(result)}, status=status)
            return

        if self.path == "/avatar/validate":
            model_path = str(payload.get("model_path", ""))
            if not model_path.strip():
                self._send({"error": "invalid_request", "message": "model_path is required"}, status=400)
                return
            result = validate_avatar_model(settings, model_path)
            status = 200 if result.status == "valid" else 422
            if result.status == "not_found":
                status = 404
            self._send({"service": PUBLIC_SERVICE, "avatar_validation": avatar_payload(result)}, status=status)
            return

        if self.path == "/avatar/state":
            result = set_avatar_state(settings, payload)
            self._send({"service": PUBLIC_SERVICE, "avatar_state": result}, status=202 if result["status"] == "accepted" else 400)
            return

        if self.path == "/channels/approvals/review":
            request_id = str(payload.get("request_id", ""))
            decision = str(payload.get("decision", ""))
            if not request_id.strip():
                self._send({"error": "invalid_request", "message": "request_id is required"}, status=400)
                return
            if not decision.strip():
                self._send({"error": "invalid_request", "message": "decision is required"}, status=400)
                return
            result = review_channel_approval(settings, payload)
            status = 200 if result.status == "reviewed" else 503
            if result.status == "invalid_decision":
                status = 400
            if result.status == "not_found":
                status = 404
            if result.status == "already_reviewed":
                status = 409
            self._send({"service": PUBLIC_SERVICE, "channel_approval_review": channel_payload(result)}, status=status)
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
            self._send({"service": PUBLIC_SERVICE, "memory": as_payload(result)}, status=200 if result.status == "completed" else 503)
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
            self._send({"service": PUBLIC_SERVICE, "memory": as_payload(result)}, status=200 if result.status == "completed" else 503)
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
            self._send({"service": PUBLIC_SERVICE, "memory": as_payload(result)}, status=200 if result.status == "completed" else 503)
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
            self._send({"service": PUBLIC_SERVICE, "search": searxng_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/index/ping":
            result = sonic_ping(settings)
            self._send({"service": PUBLIC_SERVICE, "index": sonic_payload(result)}, status=200 if result.status == "completed" else 503)
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
            self._send({"service": PUBLIC_SERVICE, "index": sonic_payload(result)}, status=200 if result.status == "completed" else 503)
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
            self._send({"service": PUBLIC_SERVICE, "index": sonic_payload(result)}, status=200 if result.status == "completed" else 503)
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
            self._send({"service": PUBLIC_SERVICE, "voice_asr": funasr_payload(result)}, status=200 if result.status == "completed" else 503)
            return

        if self.path == "/codegraph/repos/register":
            repo_path = str(payload.get("path", ""))
            if not repo_path.strip():
                self._send({"error": "invalid_request", "message": "path is required"}, status=400)
                return
            try:
                repo = register_codegraph_repo(settings, repo_path, name=str(payload.get("name", "")))
            except ValueError as exc:
                self._send({"error": "invalid_request", "message": str(exc)}, status=400)
                return
            self._send({"service": PUBLIC_SERVICE, "codegraph_repo": codegraph_payload(repo)}, status=201)
            return

        if self.path == "/codegraph/repos/scan":
            repo_id = str(payload.get("repo_id", ""))
            result = scan_codegraph_repo(settings, repo_id)
            status = 200 if result["status"] == "completed" else 404
            if result["status"] == "missing_source":
                status = 503
            self._send({"service": PUBLIC_SERVICE, "codegraph_scan": result}, status=status)
            return

        if self.path == "/codegraph/query":
            result = query_codegraph(settings, str(payload.get("query", "")), repo_id=str(payload.get("repo_id", "")), limit=int(payload.get("limit", 20)))
            status = 200 if result["status"] in {"completed", "empty"} else 400
            self._send({"service": PUBLIC_SERVICE, "codegraph_query": result}, status=status)
            return

        if self.path == "/codegraph/impact":
            target_path = str(payload.get("path", ""))
            if not target_path.strip():
                self._send({"error": "invalid_request", "message": "path is required"}, status=400)
                return
            result = codegraph_impact(settings, target_path, repo_id=str(payload.get("repo_id", "")))
            self._send({"service": PUBLIC_SERVICE, "codegraph_impact": result}, status=200 if result["status"] != "not_found" else 404)
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
            self._send({"service": PUBLIC_SERVICE, "document_ingest": ingest.__dict__, "document_parse": mineru_payload(plan)}, status=201)
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
            self._send({"service": PUBLIC_SERVICE, "document_pipeline": asdict(result)}, status=status)
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
            self._send({"service": PUBLIC_SERVICE, "document_artifact_registration": asdict(result)}, status=status)
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
            self._send({"service": PUBLIC_SERVICE, "document_index": asdict(result)}, status=status)
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
            self._send({"service": PUBLIC_SERVICE, "document_memory_candidate_generation": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/review-memory-candidate":
            candidate_id = str(payload.get("candidate_id", ""))
            decision = str(payload.get("decision", ""))
            if not candidate_id.strip():
                self._send({"error": "invalid_request", "message": "candidate_id is required"}, status=400)
                return
            if not decision.strip():
                self._send({"error": "invalid_request", "message": "decision is required"}, status=400)
                return
            result = review_document_memory_candidate(
                settings,
                candidate_id,
                decision=decision,
                reviewer_ref=str(payload.get("reviewer_ref", "owner")),
                note=str(payload.get("note", "")),
                user_id=str(payload.get("user_id", "owner")),
                session_id=str(payload.get("session_id", "")),
                app_id=str(payload.get("app_id", "default")),
                project_id=str(payload.get("project_id", "default")),
            )
            status = 200 if result.status in {"approved", "rejected"} else 503
            if result.status == "not_found":
                status = 404
            if result.status == "invalid_decision":
                status = 400
            if result.status == "already_reviewed":
                status = 409
            self._send({"service": PUBLIC_SERVICE, "document_memory_review": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/memory-review-pending":
            result = list_pending_document_memory_reviews(settings, ingest_id=str(payload.get("ingest_id", "")))
            status = 200 if result.status != "not_found" else 404
            self._send({"service": PUBLIC_SERVICE, "document_memory_review_queue": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/memory-review-batch":
            candidate_ids = payload.get("candidate_ids", ())
            if not isinstance(candidate_ids, list):
                self._send({"error": "invalid_request", "message": "candidate_ids must be a list"}, status=400)
                return
            decision = str(payload.get("decision", ""))
            if not decision.strip():
                self._send({"error": "invalid_request", "message": "decision is required"}, status=400)
                return
            result = review_document_memory_candidates_batch(
                settings,
                tuple(str(candidate_id) for candidate_id in candidate_ids),
                decision=decision,
                reviewer_ref=str(payload.get("reviewer_ref", "owner")),
                note=str(payload.get("note", "")),
                user_id=str(payload.get("user_id", "owner")),
                session_id=str(payload.get("session_id", "")),
                app_id=str(payload.get("app_id", "default")),
                project_id=str(payload.get("project_id", "default")),
                resume_after_review=bool(payload.get("resume_after_review", False)),
                timeout_seconds=int(payload.get("timeout_seconds") or settings.mineru_timeout_seconds),
                max_steps=int(payload.get("max_steps", 10)),
            )
            status = 200 if result.status in {"completed", "partial", "empty"} else 503
            if result.status == "invalid_decision":
                status = 400
            self._send({"service": PUBLIC_SERVICE, "document_memory_review_batch": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/source-refs":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            result = create_document_source_refs(settings, ingest_id)
            status = 200 if result.status in {"completed", "skipped"} else 503
            if result.status == "not_found":
                status = 404
            self._send({"service": PUBLIC_SERVICE, "document_source_refs": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/ingest-report":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            result = create_document_ingest_report(settings, ingest_id)
            status = 200 if result.status == "completed" else 503
            if result.status == "not_found":
                status = 404
            self._send({"service": PUBLIC_SERVICE, "document_ingest_report": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/workbench-state":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            state = build_document_workbench_state(settings, ingest_id)
            status = 200 if state.status != "not_found" else 404
            self._send({"service": PUBLIC_SERVICE, "document_workbench": asdict(state)}, status=status)
            return

        if self.path == "/document/parse/session-summary":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            summary = build_document_ingest_session_summary(settings, ingest_id)
            status = 200 if summary.status != "not_found" else 404
            self._send({"service": PUBLIC_SERVICE, "document_ingest_session": asdict(summary)}, status=status)
            return

        if self.path == "/document/parse/session-list":
            result = list_document_ingest_session_summaries(settings, limit=int(payload.get("limit", 50)))
            self._send({"service": PUBLIC_SERVICE, "document_ingest_sessions": asdict(result)})
            return

        if self.path == "/document/parse/workbench-next":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            result = execute_document_workbench_next(
                settings,
                ingest_id,
                timeout_seconds=int(payload.get("timeout_seconds") or settings.mineru_timeout_seconds),
                collection=str(payload.get("collection", "bairui")),
                bucket=str(payload.get("bucket", "documents")),
                lang=str(payload.get("lang", "")),
                max_candidates=int(payload.get("max_candidates", 20)),
            )
            status = 200 if result.status in {"completed", "needs_review"} else 503
            if result.status == "not_found":
                status = 404
            if result.status == "unsupported_action":
                status = 409
            self._send({"service": PUBLIC_SERVICE, "document_workbench_step": asdict(result)}, status=status)
            return

        if self.path == "/document/parse/workbench-run-until-blocked":
            ingest_id = str(payload.get("ingest_id", ""))
            if not ingest_id.strip():
                self._send({"error": "invalid_request", "message": "ingest_id is required"}, status=400)
                return
            result = run_document_workbench_until_blocked(
                settings,
                ingest_id,
                timeout_seconds=int(payload.get("timeout_seconds") or settings.mineru_timeout_seconds),
                collection=str(payload.get("collection", "bairui")),
                bucket=str(payload.get("bucket", "documents")),
                lang=str(payload.get("lang", "")),
                max_candidates=int(payload.get("max_candidates", 20)),
                max_steps=int(payload.get("max_steps", 10)),
            )
            status = 200 if result.status in {"completed", "needs_review", "step_limit_reached"} else 503
            if result.status == "not_found":
                status = 404
            if result.status == "unsupported_action":
                status = 409
            self._send({"service": PUBLIC_SERVICE, "document_workbench_run": asdict(result)}, status=status)
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
            self._send({"service": PUBLIC_SERVICE, "database": result.__dict__}, status=status)
            return

        self._send({"error": "not_found", "path": self.path}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, payload: dict[str, Any], status: int = 200) -> None:
        if status >= 400:
            try:
                record_error_log(load_settings(), method=self.command, path=self.path, status=status, payload=payload)
            except OSError:
                pass
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self, events: list[dict[str, Any]]) -> None:
        body = b"".join(build_sse_frame(event) for event in events)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_avatar_asset(self, settings: Any, asset_ref: str) -> None:
        root = settings.avatar_assets_dir.resolve()
        path = (root / unquote(asset_ref)).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            self._send({"error": "forbidden", "path": asset_ref}, status=403)
            return
        if not path.exists() or not path.is_file():
            self._send({"error": "not_found", "path": asset_ref}, status=404)
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_console_asset(self, asset_ref: str) -> None:
        root = Path(__file__).resolve().parents[2] / "web" / "bairui-console"
        path = (root / unquote(asset_ref)).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            self._send({"error": "forbidden", "path": asset_ref}, status=403)
            return
        if not path.exists() or not path.is_file():
            self._send({"error": "not_found", "path": asset_ref}, status=404)
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if path.suffix == ".js":
            content_type = "text/javascript; charset=utf-8"
        if path.suffix in {".html", ".css"}:
            content_type = f"{content_type}; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
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

    def _require_owner(self, settings: Any, *, permission: str = "owner") -> bool:
        expected = str(getattr(settings, "owner_token", "") or "").strip()
        if not expected:
            return True
        provided = self.headers.get("X-Bairui-Owner-Token", "").strip()
        authorization = self.headers.get("Authorization", "").strip()
        if not provided and authorization.lower().startswith("bearer "):
            provided = authorization[7:].strip()
        if hmac.compare_digest(provided, expected):
            return True
        create_audit_event(
            settings.data_dir,
            "auth.owner_token_denied",
            actor_type="anonymous",
            actor_ref=self.client_address[0] if self.client_address else "unknown",
            resource_type="api",
            resource_ref=self.path,
            risk_level="high",
            payload={"permission": permission, "method": self.command, "path": self.path, "secret_echo": False},
        )
        self._send(
            {
                "service": PUBLIC_SERVICE,
                "error": "owner_token_required",
                "message": "Owner token required for write API access.",
                "permission": permission,
                "secret_policy": "owner token is accepted by header only and is never returned",
            },
            status=401,
        )
        return False


def serve(settings: Any | None = None) -> None:
    settings = settings or load_settings()
    ensure_runtime_dirs(settings)
    server = ThreadingHTTPServer((settings.host, settings.port), HermesHandler)
    print(f"bairui listening on http://{settings.host}:{settings.port}", flush=True)
    server.serve_forever()


def main() -> None:
    serve()
