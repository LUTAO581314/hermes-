from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import Settings, local_config_path


FIELD_TO_ENV = {
    "model_base_url": "BAIRUI_MODEL_BASE_URL",
    "model_api_key": "BAIRUI_MODEL_API_KEY",
    "model_name": "BAIRUI_MODEL_NAME",
    "document_output_dir": "MINERU_OUTPUT_DIR",
    "memory_vault_dir": "HERMES_OBSIDIAN_VAULT_DIR",
    "channel_targets_json": "BAIRUI_CHANNEL_TARGETS_JSON",
    "avatar_assets_dir": "BAIRUI_AVATAR_ASSETS_DIR",
    "avatar_default_model": "BAIRUI_AVATAR_DEFAULT_MODEL",
    "codegraph_root": "BAIRUI_CODEGRAPH_ROOT",
    "database_url": "HERMES_DATABASE_URL",
    "owner_token": "BAIRUI_OWNER_TOKEN",
}

SECRET_FIELDS = {"model_api_key", "database_url", "owner_token"}
PATH_FIELDS = {"document_output_dir", "memory_vault_dir", "avatar_assets_dir", "codegraph_root"}
HIGH_RISK_FIELDS = {"database_url", "owner_token", "memory_vault_dir", "channel_targets_json", "codegraph_root"}
DANGEROUS_CONFIRMATION_PHRASE = "APPLY BAIRUI CONFIG"


def apply_local_config(settings: Settings, payload: dict[str, Any]) -> dict[str, Any]:
    """Persist owner-provided configuration without returning secret values."""

    values = payload.get("values", payload)
    if not isinstance(values, dict):
        return {"status": "invalid_request", "message": "values must be an object"}

    create_dirs = bool(payload.get("create_dirs", True))
    danger_confirmation = str(payload.get("danger_confirmation", "")).strip()
    existing = _read_existing(settings)
    applied: dict[str, str] = {}
    pending: dict[str, str] = {}
    errors: list[dict[str, str]] = []

    for field, env_key in FIELD_TO_ENV.items():
        if field not in values:
            continue
        raw_value = values.get(field)
        if raw_value is None:
            continue
        value = str(raw_value).strip()
        if not value and field in SECRET_FIELDS:
            continue
        if field == "channel_targets_json" and value:
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                errors.append({"field": field, "message": "channel_targets_json must be valid JSON"})
                continue
            if not isinstance(parsed, list):
                errors.append({"field": field, "message": "channel_targets_json must be a JSON array"})
                continue
        pending[env_key] = value
        applied[field] = "configured" if field in SECRET_FIELDS and value else value

    if errors:
        return {"status": "invalid_request", "errors": errors, "applied": _safe_applied(applied)}
    if not applied:
        return {"status": "no_changes", "applied": {}}
    dangerous_fields = sorted(field for field in applied if field in HIGH_RISK_FIELDS)
    if dangerous_fields and danger_confirmation != DANGEROUS_CONFIRMATION_PHRASE:
        return {
            "status": "confirmation_required",
            "message": "High-risk configuration changes require typed confirmation before they are saved.",
            "dangerous_fields": dangerous_fields,
            "confirmation_phrase": DANGEROUS_CONFIRMATION_PHRASE,
            "applied": _safe_applied(applied),
            "restart_required": True,
            "secret_policy": "secret values were not saved and are not returned",
        }

    for field, value in ((field, str(values.get(field, "")).strip()) for field in applied if field in PATH_FIELDS):
        if value and create_dirs:
            try:
                Path(value).expanduser().mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return {"status": "invalid_request", "errors": [{"field": field, "message": f"could not create directory: {exc}"}], "applied": _safe_applied(applied)}

    existing.update(pending)

    path = local_config_path(settings.data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"values": existing}, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "status": "saved",
        "path": str(path.expanduser().resolve()),
        "applied": _safe_applied(applied),
        "dangerous_fields": dangerous_fields,
        "restart_required": bool(dangerous_fields),
        "secret_policy": "secret values were saved locally but are not returned",
    }


def _read_existing(settings: Settings) -> dict[str, str]:
    path = local_config_path(settings.data_dir)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    values = payload.get("values", {}) if isinstance(payload, dict) else {}
    if not isinstance(values, dict):
        return {}
    return {str(key): str(value) for key, value in values.items()}


def _safe_applied(applied: dict[str, str]) -> dict[str, str]:
    return {field: ("configured" if field in SECRET_FIELDS else value) for field, value in applied.items()}
