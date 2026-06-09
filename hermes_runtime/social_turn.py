"""Connector-ready social turn planning."""

from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from .async_jobs import AsyncJob, AsyncJobStore
from .context_budget import budget_for_policy
from .routing import RoutePolicy, RouteType, classify_route
from .sticker_bridge import build_media_envelope, select_sticker


ACK_TEXT: dict[RouteType, str] = {
    RouteType.IMAGE_READ: "\u6211\u770b\u4e00\u4e0b\u8fd9\u5f20\u56fe\uff0c\u7b49\u6211\u4e00\u4e0b\u54e6\uff5e",
    RouteType.IMAGE_GENERATE: "\u7b49\u6211\u62cd\u4e00\u4e0b\uff0c\u9a6c\u4e0a\u7ed9\u4f60\uff5e",
    RouteType.SEARCH: "\u6211\u67e5\u4e00\u4e0b\uff0c\u522b\u6025\uff5e",
    RouteType.PUBLIC_OPINION: "\u6211\u53bb\u770b\u770b\u6700\u65b0\u52a8\u5411\uff0c\u7b49\u6211\u4e00\u4e0b\uff5e",
    RouteType.COMPANY_TASK: "\u6211\u5148\u770b\u4e00\u4e0b\u98de\u4e66\u91cc\u7684\u4e0a\u4e0b\u6587\uff0c\u9a6c\u4e0a\u56de\u4f60\uff5e",
    RouteType.MEMORY_TASK: "\u6211\u5148\u6574\u7406\u4e00\u4e0b\u8bb0\u5fc6\u7ebf\u7d22\uff0c\u7b49\u6211\u4e00\u4e0b\uff5e",
    RouteType.HIGH_RISK: "\u8fd9\u4ef6\u4e8b\u8981\u8ba4\u771f\u786e\u8ba4\u4e00\u4e0b\uff0c\u6211\u5148\u505c\u5728\u786e\u8ba4\u8fb9\u754c\u54e6\u3002",
}

FOLLOW_UP_ACK = "\u521a\u624d\u90a3\u4ef6\u4e8b\u6ca1\u4e22\uff0c\u6211\u628a\u8fd9\u53e5\u4e00\u8d77\u7b97\u8fdb\u53bb\uff5e"
CANCEL_RE = re.compile(r"\b(cancel|stop|abort|never mind)\b|(\u53d6\u6d88|\u522b\u505a|\u505c\u4e0b)", re.I)


def plan_social_turn(
    *,
    message: str,
    channel: str,
    target_id: str,
    config: Any,
    jobs: AsyncJobStore | None = None,
) -> dict[str, Any]:
    """Plan the first visible action for a social-channel message.

    The returned payload is safe for connector logs. It contains route metadata,
    context budget, optional acknowledgement text, and optional job metadata,
    but never stores or returns the message body.
    """

    clean_channel = _clean_label(channel, "unknown")
    clean_target_id = _clean_label(target_id, "unknown")
    active_job = jobs.active_for_target(clean_channel, clean_target_id) if jobs else None

    if active_job is not None and not _is_cancel_request(message):
        return _follow_up_payload(
            message=message,
            channel=clean_channel,
            target_id=clean_target_id,
            active_job=active_job,
        )

    policy = classify_route(message, config)
    budget = budget_for_policy(policy)
    ack_text = _ack_text(policy)
    action = "quick_ack" if policy.quick_ack else "direct_reply"
    job = None

    if policy.async_required and jobs is not None:
        job = jobs.create(
            route=policy.route.value,
            channel=clean_channel,
            target_id=clean_target_id,
            input_text=message,
            tool_name=policy.tool_group,
            owner_confirmation_required=policy.approval_required,
        )

    return {
        "status": "ok",
        "channel": clean_channel,
        "target_id": clean_target_id,
        "first_action": action,
        "ack": {
            "should_send": bool(policy.quick_ack),
            "text": ack_text,
            "counts_as_final": False,
            "next_job_status_after_send": "acknowledged" if job else "",
        },
        "route": asdict(policy),
        "context_budget": asdict(budget),
        "job": asdict(job) if job is not None else None,
        "active_job": None,
        "outbound_media": _outbound_media(policy, clean_channel, config),
        "message_preview_chars": min(len(str(message or "")), 160),
        "privacy": "message body is not stored in the plan payload",
    }


def _follow_up_payload(
    *,
    message: str,
    channel: str,
    target_id: str,
    active_job: AsyncJob,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "channel": channel,
        "target_id": target_id,
        "first_action": "append_to_active_job",
        "ack": {
            "should_send": True,
            "text": FOLLOW_UP_ACK,
            "counts_as_final": False,
            "next_job_status_after_send": "",
        },
        "route": {
            "route": active_job.route,
            "model_slot": "",
            "memory_depth": "follow_up_delta",
            "tool_group": active_job.tool_name,
            "quick_ack": True,
            "async_required": True,
            "approval_required": active_job.owner_confirmation_required,
            "latency_budget_ms": 0,
        },
        "context_budget": {
            "route": active_job.route,
            "memory_depth": "follow_up_delta",
            "max_recent_messages": 2,
            "allow_long_term_memory": False,
            "allow_obsidian_lookup": False,
            "tool_schema_group": active_job.tool_name,
            "max_tool_schemas": 0,
            "notes": ("active_job_follow_up",),
        },
        "job": None,
        "active_job": asdict(active_job),
        "outbound_media": None,
        "message_preview_chars": min(len(str(message or "")), 160),
        "privacy": "message body is not stored in the plan payload",
    }


def _ack_text(policy: RoutePolicy) -> str:
    if not policy.quick_ack:
        return ""
    return ACK_TEXT.get(
        policy.route,
        "\u6211\u60f3\u60f3\u54e6\uff0c\u9a6c\u4e0a\u56de\u4f60\uff5e",
    )


def _is_cancel_request(message: str) -> bool:
    return bool(CANCEL_RE.search(str(message or "")))


def _outbound_media(
    policy: RoutePolicy,
    channel: str,
    config: Any,
) -> dict[str, Any] | None:
    if policy.route != RouteType.IMAGE_GENERATE:
        return None

    provider = getattr(config, "sticker_default_provider", "metadata_only")
    if policy.tool_group == "image_generation" and getattr(
        config, "sticker_image_generation_enabled", False
    ):
        provider = "image_generation"

    candidate = select_sticker(
        "cute_greeting",
        provider=provider,
        style=getattr(config, "sticker_default_style", "kawaii_anime"),
    )
    bridge_supports_upload = channel in {"feishu", "web"} and provider != "metadata_only"
    payload = build_media_envelope(
        candidate,
        channel if channel in {"web", "feishu", "wechat", "wecom", "line"} else "generic",
        kind="sticker",
        bridge_supports_upload=bridge_supports_upload,
        review_required=getattr(config, "sticker_generation_review_required", True),
    )
    return payload.to_dict()


def _clean_label(value: str, default: str) -> str:
    text = str(value or "").strip()
    if not text:
        return default
    return "".join(ch for ch in text[:80] if ch.isalnum() or ch in {"_", "-", ".", ":"})
