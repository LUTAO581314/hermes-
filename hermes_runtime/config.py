"""Configuration loading for the minimal Hermes runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class RuntimeConfig:
    app_name: str
    env: str
    host: str
    port: int
    log_dir: Path
    data_dir: Path
    obsidian_vault_dir: Path
    safe_mode: bool
    enable_feishu_smoke: bool
    search_mode: str
    search_project: str
    trendradar_base_url: str
    trendradar_mcp_command: str
    searxng_base_url: str
    ai_provider: str
    ai_base_url: str
    ai_api_key_configured: bool
    ai_default_model: str
    ai_fast_model: str
    ai_reasoning_model: str
    ai_vision_model: str
    ai_timeout_seconds: int
    wechat_mode: str
    wechat_channel: str
    wechat_persona_mode: str
    wechat_proactive_chat: bool
    wechat_max_daily_proactive_messages: int
    wechat_personal_bridge_enabled: bool
    wechat_official_app_id_configured: bool
    wechat_official_app_secret_configured: bool
    wechat_official_token_configured: bool
    wechat_official_aes_key_configured: bool
    wecom_corp_id_configured: bool
    wecom_agent_id_configured: bool
    wecom_secret_configured: bool
    wecom_customer_service_token_configured: bool


def load_config() -> RuntimeConfig:
    data_dir = Path(os.getenv("HERMES_DATA_DIR", "./data")).resolve()
    log_dir = Path(os.getenv("HERMES_LOG_DIR", "./logs")).resolve()
    obsidian_vault_dir = Path(
        os.getenv("HERMES_OBSIDIAN_VAULT_DIR", "./obsidian-vault")
    ).resolve()

    return RuntimeConfig(
        app_name=os.getenv("HERMES_APP_NAME", "hermes-runtime"),
        env=os.getenv("HERMES_ENV", "development"),
        host=os.getenv("HERMES_HOST", "127.0.0.1"),
        port=_as_int(os.getenv("HERMES_PORT"), 8787),
        log_dir=log_dir,
        data_dir=data_dir,
        obsidian_vault_dir=obsidian_vault_dir,
        safe_mode=_as_bool(os.getenv("HERMES_SAFE_MODE"), True),
        enable_feishu_smoke=_as_bool(os.getenv("HERMES_ENABLE_FEISHU_SMOKE"), False),
        search_mode=os.getenv("HERMES_SEARCH_MODE", "external_project"),
        search_project=os.getenv("HERMES_SEARCH_PROJECT", "trendradar"),
        trendradar_base_url=os.getenv("HERMES_TRENDRADAR_BASE_URL", ""),
        trendradar_mcp_command=os.getenv("HERMES_TRENDRADAR_MCP_COMMAND", ""),
        searxng_base_url=os.getenv("HERMES_SEARXNG_BASE_URL", ""),
        ai_provider=os.getenv("HERMES_AI_PROVIDER", "supermoxi"),
        ai_base_url=os.getenv("HERMES_AI_BASE_URL", ""),
        ai_api_key_configured=bool(os.getenv("HERMES_AI_API_KEY", "")),
        ai_default_model=os.getenv("HERMES_AI_DEFAULT_MODEL", ""),
        ai_fast_model=os.getenv("HERMES_AI_FAST_MODEL", ""),
        ai_reasoning_model=os.getenv("HERMES_AI_REASONING_MODEL", ""),
        ai_vision_model=os.getenv("HERMES_AI_VISION_MODEL", ""),
        ai_timeout_seconds=_as_int(os.getenv("HERMES_AI_TIMEOUT_SECONDS"), 60),
        wechat_mode=os.getenv("HERMES_WECHAT_MODE", "disabled"),
        wechat_channel=os.getenv("HERMES_WECHAT_CHANNEL", "official_account"),
        wechat_persona_mode=os.getenv("HERMES_WECHAT_PERSONA_MODE", "companion"),
        wechat_proactive_chat=_as_bool(os.getenv("HERMES_WECHAT_PROACTIVE_CHAT"), False),
        wechat_max_daily_proactive_messages=_as_int(
            os.getenv("HERMES_WECHAT_MAX_DAILY_PROACTIVE_MESSAGES"), 3
        ),
        wechat_personal_bridge_enabled=_as_bool(
            os.getenv("HERMES_WECHAT_PERSONAL_BRIDGE_ENABLED"), False
        ),
        wechat_official_app_id_configured=bool(
            os.getenv("HERMES_WECHAT_OFFICIAL_APP_ID", "")
        ),
        wechat_official_app_secret_configured=bool(
            os.getenv("HERMES_WECHAT_OFFICIAL_APP_SECRET", "")
        ),
        wechat_official_token_configured=bool(
            os.getenv("HERMES_WECHAT_OFFICIAL_TOKEN", "")
        ),
        wechat_official_aes_key_configured=bool(
            os.getenv("HERMES_WECHAT_OFFICIAL_AES_KEY", "")
        ),
        wecom_corp_id_configured=bool(os.getenv("HERMES_WECOM_CORP_ID", "")),
        wecom_agent_id_configured=bool(os.getenv("HERMES_WECOM_AGENT_ID", "")),
        wecom_secret_configured=bool(os.getenv("HERMES_WECOM_SECRET", "")),
        wecom_customer_service_token_configured=bool(
            os.getenv("HERMES_WECOM_CUSTOMER_SERVICE_TOKEN", "")
        ),
    )
