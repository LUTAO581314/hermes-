"""Connector-ready social turn planning."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .async_jobs import AsyncJobStore
from .context_budget import budget_for_policy
from .routing import RoutePolicy, RouteType, classify_route


ACK_TEXT: dict[RouteType, str] = {
    RouteType.IMAGE_READ: "我看一下这张图，等我一下哦～",
    RouteType.IMAGE_GENERATE: "等我拍一下，马上给你～",
    RouteType.SEARCH: "我查一下，别急～",
    RouteType.PUBLIC_OPINION: "我去看看最新动向，等我一下～",
    RouteType.COMPANY_TASK: "我先看一下飞书里的上下文，马上回你～",
    RouteType.MEMORY_TASK: "我先整理一下记忆线索，等我一下～",
    RouteType.HIGH_RISK: "这件事要认真确认一下，我先停在确认边界哦。",
}


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

    policy = classify_route(message, config)
    budget = budget_for_policy(policy)
    ack_text = _ack_text(policy)
    action = "quick_ack" if policy.quick_ack else "direct_reply"
    job = None

    if policy.async_required and jobs is not None:
        job = jobs.create(
            route=policy.route.value,
            channel=channel,
            target_id=target_id,
            input_text=message,
            tool_name=policy.tool_group,
            owner_confirmation_required=policy.approval_required,
        )

    return {
        "status": "ok",
        "channel": _clean_label(channel, "unknown"),
        "target_id": _clean_label(target_id, "unknown"),
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
        "message_preview_chars": min(len(str(message or "")), 160),
        "privacy": "message body is not stored in the plan payload",
    }


def _ack_text(policy: RoutePolicy) -> str:
    if not policy.quick_ack:
        return ""
    return ACK_TEXT.get(policy.route, "我想想哦，马上回你～")


def _clean_label(value: str, default: str) -> str:
    text = str(value or "").strip()
    if not text:
        return default
    return "".join(ch for ch in text[:80] if ch.isalnum() or ch in {"_", "-", ".", ":"})
