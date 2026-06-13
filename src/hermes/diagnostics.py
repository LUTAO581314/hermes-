from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from . import __version__
from .config import Settings
from .config_status import build_config_status
from .db import database_status
from .events import list_frontend_events
from .license import load_license
from .observability import build_metrics_summary, list_error_logs
from .platform import build_platform_heartbeat
from .runtime_readiness import collect_runtime_readiness
from .storage import (
    list_audit_events,
    list_document_ingest_reports,
    list_document_ingests,
    list_document_memory_candidates,
    list_document_memory_reviews,
    list_jobs,
    list_reports,
)


def build_diagnostic_bundle(settings: Settings, *, audit_limit: int = 100) -> dict[str, Any]:
    """Build an operator-safe diagnostic bundle without secret values."""

    config_status = build_config_status(settings)
    readiness = collect_runtime_readiness(settings)
    audit = list_audit_events(settings.data_dir, limit=audit_limit)
    frontend_events = list_frontend_events(settings.data_dir, limit=audit_limit)
    jobs = list_jobs(settings.data_dir)
    reports = list_reports(settings.data_dir)
    document_ingests = list_document_ingests(settings.data_dir)
    ingest_reports = list_document_ingest_reports(settings.data_dir)
    memory_candidates = list_document_memory_candidates(settings.data_dir)
    memory_reviews = list_document_memory_reviews(settings.data_dir)
    license_state = load_license(settings.license_file, settings.license_secret)
    db_state = database_status(settings)
    errors = list_error_logs(settings, limit=100)
    metrics = build_metrics_summary(settings)
    counts = _counts(
        audit=audit,
        errors=errors,
        frontend_events=frontend_events,
        jobs=jobs,
        reports=reports,
        document_ingests=document_ingests,
        ingest_reports=ingest_reports,
        memory_candidates=memory_candidates,
        memory_reviews=memory_reviews,
    )
    return {
        "service": "bairui",
        "bundle_type": "diagnostic",
        "schema_version": 1,
        "version": __version__,
        "secret_policy": "secrets are redacted; API keys, owner tokens, license secrets, and database URLs are never included",
        "external_send_performed": False,
        "long_term_memory_auto_write": False,
        "health": {
            "status": "ok",
            "product": settings.product_name,
            "brand": {"key": settings.brand_key, "trademark": settings.trademark_name, "logo_text": settings.logo_text},
            "env": settings.env,
            "version": __version__,
        },
        "ready": {
            "status": "partial",
            "database": db_state.__dict__,
            "license": license_state.status,
            "platform": "configured" if settings.platform_base_url else "missing_config",
            "server_id": "configured" if settings.server_id else "missing_config",
        },
        "platform": build_platform_heartbeat(settings),
        "config_status": config_status,
        "runtime_readiness": readiness,
        "counts": counts,
        "metrics": metrics,
        "audit_summary": _audit_summary(audit),
        "error_summary": _error_summary(errors),
        "recent_errors": errors[-50:],
        "recent_audit": _safe_recent_audit(audit),
        "frontend_events": frontend_events[-25:],
        "file_inventory": _file_inventory(settings),
        "support_next_steps": _support_next_steps(config_status, readiness, counts),
    }


def _counts(**groups: list[Any]) -> dict[str, int]:
    return {name: len(items) for name, items in groups.items()}


def _audit_summary(audit: list[dict[str, Any]]) -> dict[str, Any]:
    actions = Counter(str(item.get("action", "")) for item in audit)
    risk_levels = Counter(str(item.get("risk_level", "")) for item in audit)
    blocked = [item for item in audit if _is_blocked_event(item)]
    return {
        "total": len(audit),
        "actions": dict(actions.most_common(20)),
        "risk_levels": dict(risk_levels),
        "blocked_count": len(blocked),
        "latest_created_at": str(audit[-1].get("created_at", "")) if audit else "",
    }


def _error_summary(errors: list[dict[str, Any]]) -> dict[str, Any]:
    codes = Counter(str(item.get("status", "")) for item in errors)
    paths = Counter(str(item.get("path", "")) for item in errors)
    names = Counter(str(item.get("error", "")) for item in errors)
    return {
        "total": len(errors),
        "status_codes": dict(codes),
        "top_paths": dict(paths.most_common(10)),
        "top_errors": dict(names.most_common(10)),
        "latest_created_at": str(errors[-1].get("created_at", "")) if errors else "",
    }


def _safe_recent_audit(audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe: list[dict[str, Any]] = []
    for event in audit[-50:]:
        payload = event.get("payload", {})
        safe.append(
            {
                "id": str(event.get("id", "")),
                "action": str(event.get("action", "")),
                "resource_type": str(event.get("resource_type", "")),
                "resource_ref": str(event.get("resource_ref", "")),
                "risk_level": str(event.get("risk_level", "")),
                "created_at": str(event.get("created_at", "")),
                "payload": _redact(payload if isinstance(payload, dict) else {}),
            }
        )
    return safe


def _file_inventory(settings: Settings) -> dict[str, Any]:
    roots = {
        "data_dir": settings.data_dir,
        "log_dir": settings.log_dir,
        "obsidian_vault_dir": settings.obsidian_vault_dir,
        "document_output_dir": settings.mineru_output_dir,
        "avatar_assets_dir": settings.avatar_assets_dir,
        "codegraph_root": settings.codegraph_root,
    }
    return {name: _path_inventory(path) for name, path in roots.items()}


def _path_inventory(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve(strict=False)
    exists = resolved.exists()
    files = 0
    dirs = 0
    if exists and resolved.is_dir():
        try:
            for item in resolved.rglob("*"):
                if item.is_dir():
                    dirs += 1
                elif item.is_file():
                    files += 1
        except OSError:
            return {"path": str(resolved), "exists": exists, "status": "unreadable", "files": files, "dirs": dirs}
    return {"path": str(resolved), "exists": exists, "status": "ready" if exists else "missing", "files": files, "dirs": dirs}


def _support_next_steps(config_status: dict[str, Any], readiness: Any, counts: dict[str, int]) -> list[str]:
    steps: list[str] = []
    for blocker in config_status.get("blockers", []):
        steps.append(f"Resolve config blocker: {blocker}")
    for blocker in getattr(readiness, "blockers", []):
        steps.append(f"Resolve runtime blocker: {blocker}")
    if counts.get("audit", 0) == 0:
        steps.append("Run Demo Flow or create a job to generate baseline audit evidence.")
    if not steps:
        steps.append("No immediate blockers detected; continue customer scenario validation.")
    return steps[:12]


def _is_blocked_event(event: dict[str, Any]) -> bool:
    text = " ".join(str(event.get(key, "")) for key in ("action", "risk_level", "resource_type"))
    payload = event.get("payload", {})
    if isinstance(payload, dict):
        text += " " + " ".join(str(value) for value in payload.values())
    return any(marker in text.lower() for marker in ("blocked", "missing_config", "not_completed", "denied", "error"))


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("redacted" if _is_secret_key(key) else _redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in ("secret", "token", "api_key", "password", "database_url", "authorization"))
