"""Connector-facing media delivery planning.

This module does not upload images itself. It tells thin channel adapters what
to try next based on their currently verified media capability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


MediaSendAction = Literal[
    "send_image_file",
    "upload_then_send",
    "send_text_fallback",
    "reject_unsafe_request",
]


@dataclass(frozen=True)
class MediaDeliveryPlan:
    status: str
    channel: str
    target_id: str
    action: MediaSendAction
    message_type: str
    text_fallback: str
    source_ref: str
    reason: str
    bridge_requirements: tuple[str, ...]
    report_event: str
    safe_log: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def plan_media_delivery(payload: dict[str, Any]) -> dict[str, object]:
    """Return a safe send plan for connector-owned media delivery."""

    channel = _clean_label(payload.get("channel"), "generic")
    target_id = _clean_label(payload.get("target_id"), "unknown")
    text_fallback = _clean_text(payload.get("text_fallback"), "我先把文字发给你，图片稍后再补～")
    source_ref = _clean_source_ref(payload.get("source_ref"))
    media = payload.get("outbound_media") if isinstance(payload.get("outbound_media"), dict) else {}
    capabilities = (
        payload.get("bridge_capabilities")
        if isinstance(payload.get("bridge_capabilities"), dict)
        else {}
    )

    supports_file = bool(capabilities.get("send_image_file"))
    supports_upload = bool(capabilities.get("upload_then_send"))
    supports_text = capabilities.get("send_text") is not False
    upload_required = bool(media.get("upload_required", True))
    message_type = _clean_label(
        (media.get("platform_payload") or {}).get("message_type")
        if isinstance(media.get("platform_payload"), dict)
        else media.get("kind"),
        "image",
    )

    if not source_ref and upload_required:
        return MediaDeliveryPlan(
            status="ok",
            channel=channel,
            target_id=target_id,
            action="send_text_fallback" if supports_text else "reject_unsafe_request",
            message_type=message_type,
            text_fallback=text_fallback,
            source_ref="",
            reason="missing source_ref for media upload",
            bridge_requirements=("source_ref", "send_text fallback"),
            report_event="failure_delivered" if supports_text else "worker_failed",
            safe_log=_safe_log(channel, target_id, message_type, source_ref),
        ).to_dict()

    if supports_file and source_ref:
        action: MediaSendAction = "send_image_file"
        reason = "bridge supports direct image file delivery"
        report_event = "final_delivered"
    elif supports_upload and source_ref:
        action = "upload_then_send"
        reason = "bridge supports platform upload before send"
        report_event = "final_delivered"
    elif supports_text:
        action = "send_text_fallback"
        reason = "bridge media upload is not verified"
        report_event = "failure_delivered"
    else:
        action = "reject_unsafe_request"
        reason = "bridge exposes neither media send nor text fallback"
        report_event = "worker_failed"

    return MediaDeliveryPlan(
        status="ok",
        channel=channel,
        target_id=target_id,
        action=action,
        message_type=message_type,
        text_fallback=text_fallback,
        source_ref=source_ref if action in {"send_image_file", "upload_then_send"} else "",
        reason=reason,
        bridge_requirements=_requirements_for(action),
        report_event=report_event,
        safe_log=_safe_log(channel, target_id, message_type, source_ref),
    ).to_dict()


def _requirements_for(action: MediaSendAction) -> tuple[str, ...]:
    if action == "send_image_file":
        return ("connector verifies source_ref exists inside its own sandbox", "send file/image through bridge")
    if action == "upload_then_send":
        return ("upload runtime image through platform API", "send by platform media token")
    if action == "send_text_fallback":
        return ("send text_fallback", "log reason once")
    return ("do not send media", "surface operator-visible error")


def _safe_log(channel: str, target_id: str, message_type: str, source_ref: str) -> dict[str, object]:
    return {
        "channel": channel,
        "target_id_preview_chars": min(len(target_id), 80),
        "message_type": message_type,
        "source_ref_present": bool(source_ref),
    }


def _clean_label(value: object, default: str) -> str:
    text = str(value or "").strip()
    if not text:
        return default
    return "".join(ch for ch in text[:100] if ch.isalnum() or ch in {"_", "-", ".", ":", "/"})


def _clean_text(value: object, default: str) -> str:
    text = str(value or "").strip() or default
    return text[:500]


def _clean_source_ref(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith(("file://", "http://", "https://")):
        return ""
    return text[:240]
