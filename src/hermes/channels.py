from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .storage import create_audit_event


SUPPORTED_MEDIA_KINDS = ("text", "image", "video", "file")
DEFAULT_TARGETS = (
    {
        "id": "owner_review",
        "label": "Owner Review",
        "channel_type": "personal_chat",
        "status": "approval_required",
        "supports": SUPPORTED_MEDIA_KINDS,
        "requires_owner_confirmation": True,
    },
)


@dataclass(frozen=True)
class ChannelStatus:
    status: str
    enabled: bool
    configured_target_count: int
    supported_media_kinds: tuple[str, ...]
    requires_owner_confirmation: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ChannelSendPlan:
    status: str
    target_id: str
    channel_type: str
    media_kind: str
    message_preview: str
    attachment_path: str
    requires_owner_confirmation: bool
    will_send: bool
    reason: str
    audit_event_id: str


def channel_status(settings: Settings) -> ChannelStatus:
    targets = channel_targets(settings)
    enabled = _channels_enabled()
    blockers: list[str] = []
    warnings: list[str] = []
    if not enabled:
        blockers.append("channels_disabled")
    if not targets:
        blockers.append("missing_targets")
    if targets and not enabled:
        warnings.append("targets_configured_but_channels_disabled")
    status = "ready" if enabled and targets else "missing_config"
    return ChannelStatus(
        status=status,
        enabled=enabled,
        configured_target_count=len(targets),
        supported_media_kinds=SUPPORTED_MEDIA_KINDS,
        requires_owner_confirmation=True,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def channel_targets(settings: Settings) -> tuple[dict[str, Any], ...]:
    configured = _load_configured_targets()
    if configured:
        return tuple(configured)
    return DEFAULT_TARGETS


def plan_channel_send(settings: Settings, payload: dict[str, Any]) -> ChannelSendPlan:
    targets = {str(target.get("id", "")): target for target in channel_targets(settings)}
    target_id = str(payload.get("target_id", "")).strip()
    media_kind = str(payload.get("media_kind", "text")).strip() or "text"
    message = str(payload.get("text", "")).strip()
    attachment_path = str(payload.get("attachment_path", "")).strip()

    status = "approval_required"
    reason = "owner_confirmation_required"
    target = targets.get(target_id)
    if not _channels_enabled():
        status = "blocked"
        reason = "channels_disabled"
    elif not target:
        status = "not_found"
        reason = "target_not_found"
    elif media_kind not in SUPPORTED_MEDIA_KINDS:
        status = "unsupported_media"
        reason = "unsupported_media_kind"
    elif media_kind == "text" and not message:
        status = "invalid_request"
        reason = "text_required"
    elif media_kind != "text" and not attachment_path:
        status = "invalid_request"
        reason = "attachment_path_required"
    elif media_kind != "text" and not Path(attachment_path).exists():
        status = "blocked"
        reason = "attachment_not_found"

    audit = create_audit_event(
        settings.data_dir,
        "channel.send_planned" if status == "approval_required" else "channel.send_blocked",
        resource_type="channel_target",
        resource_ref=target_id or "missing_target",
        risk_level="high",
        payload={
            "status": status,
            "target_id": target_id,
            "channel_type": str((target or {}).get("channel_type", "")),
            "media_kind": media_kind,
            "reason": reason,
            "will_send": False,
        },
    )
    return ChannelSendPlan(
        status=status,
        target_id=target_id,
        channel_type=str((target or {}).get("channel_type", "")),
        media_kind=media_kind,
        message_preview=message[:160],
        attachment_path=attachment_path,
        requires_owner_confirmation=True,
        will_send=False,
        reason=reason,
        audit_event_id=audit.id,
    )


def as_payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, dict):
        return value
    return dict(value)


def _channels_enabled() -> bool:
    value = os.getenv("BAIRUI_CHANNELS_ENABLED", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_configured_targets() -> list[dict[str, Any]]:
    raw = os.getenv("BAIRUI_CHANNEL_TARGETS_JSON", "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    targets: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        target_id = str(item.get("id", "")).strip()
        if not target_id:
            continue
        supports = item.get("supports", SUPPORTED_MEDIA_KINDS)
        if not isinstance(supports, list):
            supports = list(SUPPORTED_MEDIA_KINDS)
        targets.append(
            {
                "id": target_id,
                "label": str(item.get("label", target_id)).strip() or target_id,
                "channel_type": str(item.get("channel_type", "team_webhook")).strip() or "team_webhook",
                "status": str(item.get("status", "approval_required")).strip() or "approval_required",
                "supports": tuple(str(value) for value in supports if str(value) in SUPPORTED_MEDIA_KINDS),
                "requires_owner_confirmation": bool(item.get("requires_owner_confirmation", True)),
            }
        )
    return targets
