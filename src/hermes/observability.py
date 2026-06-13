from __future__ import annotations

import json
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .storage import list_audit_events, utc_now


@dataclass(frozen=True)
class ErrorLogRecord:
    id: str
    created_at: str
    method: str
    path: str
    status: int
    error: str
    message: str
    risk_level: str
    payload: dict[str, Any]


def record_error_log(settings: Settings, *, method: str, path: str, status: int, payload: dict[str, Any]) -> ErrorLogRecord | None:
    if status < 400:
        return None
    record = ErrorLogRecord(
        id=str(uuid.uuid4()),
        created_at=utc_now(),
        method=method,
        path=path,
        status=status,
        error=str(payload.get("error") or payload.get("status") or payload.get("code") or "http_error"),
        message=str(payload.get("message") or payload.get("detail") or ""),
        risk_level=_risk_for_status(status),
        payload=_safe_error_payload(payload),
    )
    path_obj = _error_log_path(settings)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with path_obj.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")
    return record


def list_error_logs(settings: Settings, limit: int = 100) -> list[dict[str, Any]]:
    return _read_jsonl(_error_log_path(settings), limit=limit)


def build_metrics_summary(settings: Settings) -> dict[str, Any]:
    audit = list_audit_events(settings.data_dir, limit=1000)
    errors = list_error_logs(settings, limit=1000)
    actions = Counter(str(item.get("action", "")) for item in audit)
    resources = Counter(str(item.get("resource_type", "")) for item in audit)
    status_codes = Counter(str(item.get("status", "")) for item in errors)
    error_paths = Counter(str(item.get("path", "")) for item in errors)
    risk_levels = Counter(str(item.get("risk_level", "")) for item in audit + errors)
    return {
        "status": "ready",
        "audit_count": len(audit),
        "error_count": len(errors),
        "high_risk_count": risk_levels.get("high", 0),
        "blocked_or_denied_count": _blocked_or_denied_count(audit, errors),
        "top_actions": dict(actions.most_common(10)),
        "top_resources": dict(resources.most_common(10)),
        "status_codes": dict(status_codes),
        "top_error_paths": dict(error_paths.most_common(10)),
        "risk_levels": dict(risk_levels),
        "latest_error_at": str(errors[-1].get("created_at", "")) if errors else "",
        "secret_policy": "metrics are aggregated from redacted audit and error logs; secret values are not included",
    }


def _error_log_path(settings: Settings) -> Path:
    return settings.log_dir / "errors.jsonl"


def _risk_for_status(status: int) -> str:
    if status in {401, 403}:
        return "high"
    if status >= 500:
        return "medium"
    return "low"


def _safe_error_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"service", "error", "message", "detail", "status", "permission", "secret_policy"}
    return {key: _redact(value) for key, value in payload.items() if key in allowed}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("redacted" if _is_secret_key(key) else _redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in ("secret", "token", "api_key", "password", "database_url", "authorization"))


def _blocked_or_denied_count(audit: list[dict[str, Any]], errors: list[dict[str, Any]]) -> int:
    count = 0
    for item in audit:
        text = f"{item.get('action', '')} {item.get('resource_type', '')} {item.get('risk_level', '')}".lower()
        if any(marker in text for marker in ("blocked", "denied", "not_completed", "missing_config")):
            count += 1
    for item in errors:
        if int(item.get("status", 0) or 0) >= 400:
            count += 1
    return count


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows[-limit:]
