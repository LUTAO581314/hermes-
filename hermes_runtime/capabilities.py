"""Capability matrix for frontend and connector diagnostics."""

from __future__ import annotations

from typing import Any

from .config import RuntimeConfig
from .server_time import utc_now


def _status(
    state: str,
    label: str,
    *,
    configured: bool = False,
    detail: str = "",
    next_action: str = "",
    plane: str = "runtime",
) -> dict[str, Any]:
    return {
        "state": state,
        "label": label,
        "configured": configured,
        "plane": plane,
        "detail": detail,
        "next_action": next_action,
    }


def _ready(label: str, *, detail: str = "", plane: str = "runtime") -> dict[str, Any]:
    return _status("ready", label, configured=True, detail=detail, plane=plane)


def _partial(
    label: str,
    *,
    detail: str,
    next_action: str,
    plane: str = "runtime",
) -> dict[str, Any]:
    return _status(
        "partial",
        label,
        configured=True,
        detail=detail,
        next_action=next_action,
        plane=plane,
    )


def _missing(
    label: str,
    *,
    detail: str,
    next_action: str,
    plane: str = "runtime",
) -> dict[str, Any]:
    return _status(
        "missing_config",
        label,
        detail=detail,
        next_action=next_action,
        plane=plane,
    )


def _disabled(
    label: str,
    *,
    detail: str = "Disabled by configuration.",
    next_action: str = "",
    plane: str = "runtime",
) -> dict[str, Any]:
    return _status(
        "disabled",
        label,
        detail=detail,
        next_action=next_action,
        plane=plane,
    )


def _planned(label: str, *, detail: str, next_action: str) -> dict[str, Any]:
    return _status("planned", label, detail=detail, next_action=next_action)


def _all_configured(*flags: bool) -> bool:
    return all(flags)


def capability_matrix(config: RuntimeConfig) -> dict[str, Any]:
    """Return a secret-safe capability matrix for UI dashboards.

    This is intentionally conservative: it reports whether required knobs are
    present, not whether a third-party service is reachable.
    """

    ai_ready = bool(config.ai_base_url and config.ai_api_key_configured)
    search_ready = bool(
        config.trendradar_base_url
        or config.trendradar_mcp_command
        or config.searxng_base_url
        or config.trendradar_output_dir.exists()
    )
    wechat_ready = (
        config.wechat_personal_bridge_enabled
        or _all_configured(
            config.wechat_official_app_id_configured,
            config.wechat_official_app_secret_configured,
            config.wechat_official_token_configured,
        )
        or _all_configured(
            config.wecom_corp_id_configured,
            config.wecom_agent_id_configured,
            config.wecom_secret_configured,
        )
    )
    qq_ready = _all_configured(
        config.qq_bot_app_id_configured,
        config.qq_bot_token_configured,
        config.qq_bot_secret_configured,
        config.qq_webhook_token_configured,
    )
    sticker_image_ready = _all_configured(
        config.sticker_image_generation_enabled,
        config.sticker_api_key_configured,
        bool(config.sticker_image_generation_base_url),
        bool(config.sticker_image_generation_model),
    )

    capabilities: dict[str, dict[str, Any]] = {
        "runtime": _ready(
            "Hermes runtime contract",
            detail="/health, /ready, /social/turn, /jobs/event are available.",
        ),
        "model_gateway": (
            _ready(
                "Model gateway",
                detail=f"{config.ai_provider} base URL and API key are configured.",
            )
            if ai_ready
            else _missing(
                "Model gateway",
                detail="Model base URL or API key is missing.",
                next_action="Set HERMES_AI_BASE_URL and HERMES_AI_API_KEY on the server.",
            )
        ),
        "text_chat": (
            _ready("Text chat", detail="Uses the configured model gateway.")
            if ai_ready
            else _missing(
                "Text chat",
                detail="Text replies need a configured model gateway.",
                next_action="Configure the model gateway first.",
            )
        ),
        "image_understanding": (
            _ready(
                "Image understanding",
                detail=f"Vision slot: {config.ai_vision_model or 'default model'}.",
            )
            if ai_ready
            else _missing(
                "Image understanding",
                detail="Image reading needs a vision-capable model gateway.",
                next_action="Configure HERMES_AI_API_KEY and an optional vision model slot.",
            )
        ),
        "search_intelligence": (
            _ready(
                "Search and trend intelligence",
                detail=f"Search project: {config.search_project}.",
            )
            if search_ready
            else _missing(
                "Search and trend intelligence",
                detail="No external search runtime URL or command is configured.",
                next_action="Configure TrendRadar or SearXNG runtime settings.",
            )
        ),
        "hotspots": (
            _ready(
                "Hotspot panel",
                detail="Hermes /hotspots can read TrendRadar output for Brain UI.",
            )
            if config.trendradar_output_dir.exists()
            else _missing(
                "Hotspot panel",
                detail="TrendRadar output directory is missing or empty from this runtime view.",
                next_action="Set HERMES_TRENDRADAR_OUTPUT_DIR or run TrendRadar before opening the hotspot panel.",
            )
        ),
        "memory_governance": (
            _ready(
                "Governed memory",
                detail="Obsidian vault path exists and durable writes are review-gated.",
            )
            if config.obsidian_vault_dir.exists()
            else _missing(
                "Governed memory",
                detail="Obsidian vault path does not exist.",
                next_action="Create the vault path or update HERMES_OBSIDIAN_VAULT_DIR.",
            )
        ),
        "wechat": (
            _disabled(
                "WeChat channel",
                next_action="Set HERMES_WECHAT_MODE when the bridge is ready.",
                plane="personal",
            )
            if config.wechat_mode == "disabled"
            else (
                _ready(
                    "WeChat channel",
                    detail=f"Mode: {config.wechat_mode}, channel: {config.wechat_channel}.",
                    plane="personal",
                )
                if wechat_ready
                else _missing(
                    "WeChat channel",
                    detail="WeChat mode is enabled or planned, but credentials are incomplete.",
                    next_action="Finish official account, WeCom, or personal bridge credentials.",
                    plane="personal",
                )
            )
        ),
        "feishu_company": (
            _partial(
                "Feishu company surface",
                detail="Feishu smoke mode is enabled; production identity mapping still needs runtime verification.",
                next_action="Verify group mentions, sender mapping, idempotency, and read-only docs/tables.",
                plane="company",
            )
            if config.enable_feishu_smoke
            else _planned(
                "Feishu company surface",
                detail="Company plane is planned but not exposed as a complete runtime capability here.",
                next_action="Expose Feishu app credentials and company data readiness as secret-safe flags.",
            )
        ),
        "qq": (
            _disabled(
                "QQ channel",
                next_action="Set HERMES_QQ_MODE and official bot credentials.",
                plane="personal",
            )
            if config.qq_mode == "disabled"
            else (
                _ready(
                    "QQ official bot",
                    detail="Official bot credentials are configured.",
                    plane="personal",
                )
                if qq_ready
                else _missing(
                    "QQ official bot",
                    detail="QQ mode is enabled or planned, but official bot credentials are incomplete.",
                    next_action="Set app id, token, secret, and webhook token.",
                    plane="personal",
                )
            )
        ),
        "voice_input": _partial(
            "Voice input",
            detail="Local or provider ASR is handled by the upstream interaction runtime.",
            next_action="Expose ASR provider health from the BaiLongma/Hermes frontend adapter.",
            plane="personal",
        ),
        "voice_output": _partial(
            "Voice output",
            detail="Browser TTS fallback is acceptable for web chat; cloud TTS is provider-gated.",
            next_action="Add provider health when cloud TTS is selected.",
            plane="personal",
        ),
        "stickers": (
            _ready(
                "Sticker bridge",
                detail=f"Provider: {config.sticker_default_provider}; style: {config.sticker_default_style}.",
                plane="personal",
            )
            if config.sticker_bridge_enabled
            else _disabled(
                "Sticker bridge",
                next_action="Enable HERMES_STICKER_BRIDGE_ENABLED when channel upload is ready.",
                plane="personal",
            )
        ),
        "image_generation": (
            _ready(
                "Reviewed image generation",
                detail=f"Model: {config.sticker_image_generation_model}. Review required: {config.sticker_generation_review_required}.",
                plane="personal",
            )
            if sticker_image_ready
            else _planned(
                "Reviewed image generation",
                detail="Image generation is not fully configured or is disabled.",
                next_action="Configure image generation base URL, key, model, and review workflow.",
            )
        ),
    }

    counts = {"ready": 0, "partial": 0, "missing_config": 0, "disabled": 0, "planned": 0}
    for capability in capabilities.values():
        state = str(capability["state"])
        counts[state] = counts.get(state, 0) + 1

    return {
        "status": "ok",
        "service": config.app_name,
        "created_at": utc_now(),
        "summary": counts,
        "capabilities": capabilities,
        "frontend_contract": {
            "recommended_poll_seconds": 30,
            "status_order": ["missing_config", "partial", "planned", "disabled", "ready"],
            "secret_policy": "Only configured booleans and next actions are returned; raw secrets are never exposed.",
        },
    }
