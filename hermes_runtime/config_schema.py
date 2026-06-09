"""Secret-safe writable configuration schema for Hermes runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any

from .config import RuntimeConfig
from .server_time import utc_now


class ConfigValidationError(ValueError):
    """Raised when a configuration update fails whitelist validation."""


@dataclass(frozen=True)
class ConfigField:
    key: str
    group: str
    label: str
    kind: str
    config_attr: str | None = None
    default: str | int | bool | None = None
    options: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None
    secret: bool = False
    writable: bool = True
    restart_required: bool = False
    help: str = ""


CONFIG_FIELDS: tuple[ConfigField, ...] = (
    ConfigField(
        "HERMES_AI_PROVIDER",
        "model",
        "AI Provider",
        "text",
        "ai_provider",
        "supermoxi",
        help="Model gateway provider name shown in health and settings.",
    ),
    ConfigField(
        "HERMES_AI_BASE_URL",
        "model",
        "AI Base URL",
        "url",
        "ai_base_url",
        "",
        help="OpenAI-compatible model gateway base URL.",
    ),
    ConfigField(
        "HERMES_AI_API_KEY",
        "model",
        "AI API Key",
        "secret",
        "ai_api_key_configured",
        "",
        secret=True,
        help="Write-only API key. Empty updates keep the current value.",
    ),
    ConfigField(
        "HERMES_AI_DEFAULT_MODEL",
        "model",
        "Default Model",
        "text",
        "ai_default_model",
        "",
    ),
    ConfigField(
        "HERMES_AI_FAST_MODEL",
        "model",
        "Fast Model",
        "text",
        "ai_fast_model",
        "",
    ),
    ConfigField(
        "HERMES_AI_SUMMARY_MODEL",
        "model",
        "Summary Model",
        "text",
        "ai_summary_model",
        "",
    ),
    ConfigField(
        "HERMES_AI_REASONING_MODEL",
        "model",
        "Reasoning Model",
        "text",
        "ai_reasoning_model",
        "",
    ),
    ConfigField(
        "HERMES_AI_VISION_MODEL",
        "model",
        "Vision Model",
        "text",
        "ai_vision_model",
        "",
    ),
    ConfigField(
        "HERMES_AI_TIMEOUT_SECONDS",
        "model",
        "AI Timeout Seconds",
        "int",
        "ai_timeout_seconds",
        60,
        minimum=1,
        maximum=600,
    ),
    ConfigField(
        "HERMES_SEARCH_MODE",
        "search",
        "Search Mode",
        "select",
        "search_mode",
        "external_project",
        options=("disabled", "external_project", "searxng"),
    ),
    ConfigField(
        "HERMES_SEARCH_PROJECT",
        "search",
        "Search Project",
        "select",
        "search_project",
        "trendradar",
        options=("trendradar", "searxng", "custom"),
    ),
    ConfigField(
        "HERMES_TRENDRADAR_BASE_URL",
        "search",
        "TrendRadar Base URL",
        "url",
        "trendradar_base_url",
        "",
    ),
    ConfigField(
        "HERMES_TRENDRADAR_OUTPUT_DIR",
        "search",
        "TrendRadar Output Directory",
        "text",
        "trendradar_output_dir",
        "/home/hermes/external/TrendRadar/output",
        help="Directory scanned by Hermes /hotspots for source-backed TrendRadar JSON output.",
    ),
    ConfigField(
        "HERMES_SEARXNG_BASE_URL",
        "search",
        "SearXNG Base URL",
        "url",
        "searxng_base_url",
        "",
    ),
    ConfigField(
        "HERMES_STICKER_BRIDGE_ENABLED",
        "media",
        "Sticker Bridge Enabled",
        "bool",
        "sticker_bridge_enabled",
        False,
    ),
    ConfigField(
        "HERMES_STICKER_DEFAULT_PROVIDER",
        "media",
        "Sticker Provider",
        "select",
        "sticker_default_provider",
        "metadata_only",
        options=("metadata_only", "stipop", "custom"),
    ),
    ConfigField(
        "HERMES_STICKER_DEFAULT_STYLE",
        "media",
        "Sticker Style",
        "text",
        "sticker_default_style",
        "kawaii_anime",
    ),
    ConfigField(
        "HERMES_STICKER_API_KEY",
        "media",
        "Sticker API Key",
        "secret",
        "sticker_api_key_configured",
        "",
        secret=True,
        help="Write-only provider key. Empty updates keep the current value.",
    ),
    ConfigField(
        "HERMES_STICKER_IMAGE_GENERATION_ENABLED",
        "media",
        "Image Generation Enabled",
        "bool",
        "sticker_image_generation_enabled",
        False,
    ),
    ConfigField(
        "HERMES_STICKER_IMAGE_GENERATION_BASE_URL",
        "media",
        "Image Generation Base URL",
        "url",
        "sticker_image_generation_base_url",
        "",
    ),
    ConfigField(
        "HERMES_STICKER_IMAGE_GENERATION_MODEL",
        "media",
        "Image Generation Model",
        "text",
        "sticker_image_generation_model",
        "",
    ),
    ConfigField(
        "HERMES_STICKER_GENERATION_REVIEW_REQUIRED",
        "media",
        "Generation Review Required",
        "bool",
        "sticker_generation_review_required",
        True,
    ),
    ConfigField(
        "HERMES_STICKER_RUNTIME_CACHE_ENABLED",
        "media",
        "Runtime Cache Enabled",
        "bool",
        "sticker_runtime_cache_enabled",
        False,
    ),
    ConfigField(
        "HERMES_SOCIAL_QUICK_ACK_DELAY_MS",
        "performance",
        "Quick ACK Delay",
        "int",
        "social_quick_ack_delay_ms",
        1200,
        minimum=0,
        maximum=10000,
    ),
    ConfigField(
        "HERMES_SOCIAL_FAST_REPLY_TARGET_MS",
        "performance",
        "Fast Reply Target",
        "int",
        "social_fast_reply_target_ms",
        5000,
        minimum=500,
        maximum=30000,
    ),
    ConfigField(
        "HERMES_SLOW_TASK_THRESHOLD_MS",
        "performance",
        "Slow Task Threshold",
        "int",
        "slow_task_threshold_ms",
        5000,
        minimum=500,
        maximum=120000,
    ),
    ConfigField(
        "HERMES_ASYNC_TASK_TIMEOUT_SECONDS",
        "performance",
        "Async Task Timeout",
        "int",
        "async_task_timeout_seconds",
        180,
        minimum=5,
        maximum=3600,
    ),
    ConfigField(
        "HERMES_LATENCY_TELEMETRY_ENABLED",
        "performance",
        "Latency Telemetry Enabled",
        "bool",
        "latency_telemetry_enabled",
        True,
    ),
)

FIELD_BY_KEY = {field.key: field for field in CONFIG_FIELDS}
GROUP_LABELS = {
    "model": "Model Gateway",
    "search": "Search Intelligence",
    "media": "Media And Stickers",
    "performance": "Social Performance",
}
ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def config_env_path() -> Path:
    return Path(os.getenv("HERMES_CONFIG_ENV_PATH", ".env.hermes-runtime")).expanduser()


def config_schema_payload(config: RuntimeConfig) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    for field in CONFIG_FIELDS:
        group = groups.setdefault(
            field.group,
            {"id": field.group, "label": GROUP_LABELS[field.group], "fields": []},
        )
        group["fields"].append(_field_payload(field, config))

    return {
        "status": "ok",
        "schema_version": 1,
        "mode": "safe_whitelist",
        "env_path_configured": bool(os.getenv("HERMES_CONFIG_ENV_PATH", "")),
        "groups": list(groups.values()),
        "guardrails": {
            "secret_values_returned": False,
            "unknown_keys_allowed": False,
            "empty_secret_update": "keep_existing",
            "high_risk_runtime_keys": "read_only_or_excluded",
        },
        "created_at": utc_now(),
    }


def apply_config_updates(
    payload: dict[str, Any], env_path: Path | None = None
) -> dict[str, Any]:
    updates = payload.get("updates", payload)
    if not isinstance(updates, dict):
        raise ConfigValidationError("updates must be an object")

    validated: dict[str, str] = {}
    skipped: list[str] = []
    for key, raw_value in updates.items():
        if not isinstance(key, str) or not ENV_KEY_RE.match(key):
            raise ConfigValidationError(f"invalid config key: {key}")
        field = FIELD_BY_KEY.get(key)
        if field is None or not field.writable:
            raise ConfigValidationError(f"config key is not writable: {key}")
        value = _normalize_value(field, raw_value)
        if field.secret and value == "":
            skipped.append(key)
            continue
        validated[key] = value

    target = env_path or config_env_path()
    if validated:
        _write_env_values(target, validated)
        os.environ.update(validated)

    return {
        "status": "ok",
        "env_path": str(target),
        "changed_keys": sorted(validated.keys()),
        "skipped_empty_secret_keys": sorted(skipped),
        "created_at": utc_now(),
    }


def _field_payload(field: ConfigField, config: RuntimeConfig) -> dict[str, Any]:
    item: dict[str, Any] = {
        "key": field.key,
        "label": field.label,
        "type": field.kind,
        "writable": field.writable,
        "secret": field.secret,
        "restart_required": field.restart_required,
        "help": field.help,
    }
    if field.options:
        item["options"] = list(field.options)
    if field.minimum is not None:
        item["min"] = field.minimum
    if field.maximum is not None:
        item["max"] = field.maximum

    if field.secret:
        item["configured"] = bool(getattr(config, field.config_attr or "", False))
    else:
        item["value"] = _json_safe_value(
            getattr(config, field.config_attr or "", field.default)
        )
    return item


def _json_safe_value(value: Any) -> str | int | bool | None:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


def _normalize_value(field: ConfigField, raw_value: Any) -> str:
    if raw_value is None:
        value = ""
    elif isinstance(raw_value, bool):
        value = "true" if raw_value else "false"
    else:
        value = str(raw_value).strip()

    if field.kind == "bool":
        lowered = value.lower()
        if lowered in {"1", "true", "yes", "on"}:
            return "true"
        if lowered in {"0", "false", "no", "off"}:
            return "false"
        raise ConfigValidationError(f"{field.key} must be a boolean")

    if field.kind == "int":
        try:
            number = int(value)
        except ValueError as error:
            raise ConfigValidationError(f"{field.key} must be an integer") from error
        if field.minimum is not None and number < field.minimum:
            raise ConfigValidationError(f"{field.key} must be >= {field.minimum}")
        if field.maximum is not None and number > field.maximum:
            raise ConfigValidationError(f"{field.key} must be <= {field.maximum}")
        return str(number)

    if field.options and value not in field.options:
        allowed = ", ".join(field.options)
        raise ConfigValidationError(f"{field.key} must be one of: {allowed}")

    if "\x00" in value or "\n" in value or "\r" in value:
        raise ConfigValidationError(f"{field.key} contains unsupported characters")

    return value


def _write_env_values(path: Path, updates: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    remaining = dict(updates)
    output: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in remaining:
            output.append(f"{key}={_quote_env_value(remaining.pop(key))}")
        else:
            output.append(line)

    if remaining and output and output[-1] != "":
        output.append("")
    for key in sorted(remaining):
        output.append(f"{key}={_quote_env_value(remaining[key])}")

    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def _quote_env_value(value: str) -> str:
    if value == "":
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_./:@+\-]+", value):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
