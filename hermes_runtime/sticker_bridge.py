"""Metadata-only sticker bridge for chat surfaces.

The bridge intentionally stores provider hints and outbound instructions only.
It does not download or persist sticker image files into the repository.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


Channel = Literal["web", "feishu", "wechat", "wecom", "line", "generic"]
ProviderKind = Literal[
    "metadata_only",
    "stipop",
    "giphy",
    "openmoji",
    "noto_emoji",
    "line_official",
    "image_generation",
]


@dataclass(frozen=True)
class StickerCandidate:
    intent: str
    provider: ProviderKind
    style: str
    title: str
    tags: tuple[str, ...]
    query: str
    license_note: str
    provider_ref: str = ""
    preview_url: str = ""
    attribution_required: bool = False
    runtime_upload_required: bool = True
    text_fallback: str = ""


@dataclass(frozen=True)
class StickerIntentProfile:
    intent: str
    description: str
    default_text: str
    tags: tuple[str, ...]
    safety_note: str = ""


@dataclass(frozen=True)
class OutboundStickerPayload:
    channel: Channel
    action: str
    intent: str
    provider: ProviderKind
    style: str
    text_fallback: str
    instructions: tuple[str, ...]
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OutboundMediaPayload:
    """Connector-neutral media envelope for chat surfaces.

    Channel adapters can send a real image when their bridge supports upload.
    If not, they must send ``text_fallback`` and log ``fallback_reason`` instead
    of silently dropping the media turn.
    """

    kind: Literal["sticker", "image"]
    channel: Channel
    action: str
    send_strategy: str
    text_fallback: str
    upload_required: bool
    review_required: bool
    fallback_reason: str
    platform_payload: dict[str, object] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


INTENT_REGISTRY: dict[str, StickerIntentProfile] = {
    "cute_greeting": StickerIntentProfile(
        intent="cute_greeting",
        description="A soft hello or wake-up greeting.",
        default_text="嘿嘿，来啦～",
        tags=("kawaii", "anime girl", "hello", "wave", "cute"),
    ),
    "happy_praise": StickerIntentProfile(
        intent="happy_praise",
        description="Excited praise for good news or progress.",
        default_text="啊啊啊太棒啦！",
        tags=("kawaii", "anime girl", "cheer", "sparkle", "praise"),
    ),
    "soft_comfort": StickerIntentProfile(
        intent="soft_comfort",
        description="Gentle comfort when the user is tired or sad.",
        default_text="抱抱你，我在呢。",
        tags=("kawaii", "anime girl", "hug", "comfort", "soft"),
        safety_note="Do not use this as a substitute for crisis support.",
    ),
    "shy_like": StickerIntentProfile(
        intent="shy_like",
        description="Light shy affection without being too intense.",
        default_text="哼，才没有很想你呢。",
        tags=("kawaii", "anime girl", "shy", "blush", "heart"),
    ),
    "working_hard": StickerIntentProfile(
        intent="working_hard",
        description="Encouragement during work or study.",
        default_text="继续冲呀，我陪你。",
        tags=("kawaii", "anime girl", "work", "study", "encourage"),
    ),
    "sleepy_goodnight": StickerIntentProfile(
        intent="sleepy_goodnight",
        description="Good night and sleepy companion tone.",
        default_text="晚安安，记得好好睡呀。",
        tags=("kawaii", "anime girl", "sleepy", "good night", "moon"),
    ),
    "thank_you": StickerIntentProfile(
        intent="thank_you",
        description="Cute thanks and appreciation.",
        default_text="谢谢主人～",
        tags=("kawaii", "anime girl", "thank you", "bow", "smile"),
    ),
}


PROVIDER_LICENSE_NOTES: dict[ProviderKind, str] = {
    "metadata_only": "No remote asset selected yet; keep only intent and search metadata.",
    "stipop": "Use Stipop API results at runtime; do not copy or bundle sticker assets.",
    "giphy": "Use GIPHY API results at runtime and preserve required attribution.",
    "openmoji": "OpenMoji assets are licensed under CC BY-SA 4.0; attribution/share-alike rules apply.",
    "noto_emoji": "Noto Emoji assets are open source under Apache-2.0, but style is emoji rather than anime.",
    "line_official": "LINE sticker messages use packageId/stickerId only on LINE-supported channels.",
    "image_generation": "Generate original stickers through the configured image API at runtime; review before sending.",
}


def select_sticker(
    intent: str,
    *,
    provider: ProviderKind = "metadata_only",
    style: str = "kawaii_anime",
) -> StickerCandidate:
    """Select sticker metadata for an intent without fetching image bytes."""
    profile = INTENT_REGISTRY.get(intent, INTENT_REGISTRY["cute_greeting"])
    normalized_provider = provider if provider in PROVIDER_LICENSE_NOTES else "metadata_only"
    query_tags = ("cute girl", "anime", "kawaii", *profile.tags)
    if normalized_provider == "image_generation":
        query = (
            "original kawaii anime chat sticker, soft pastel girl, expressive, "
            f"{', '.join(profile.tags)}, transparent background, no text"
        )
    else:
        query = " ".join(dict.fromkeys(query_tags))

    return StickerCandidate(
        intent=profile.intent,
        provider=normalized_provider,
        style=style,
        title=profile.description,
        tags=profile.tags,
        query=query,
        license_note=PROVIDER_LICENSE_NOTES[normalized_provider],
        attribution_required=normalized_provider in {"giphy", "openmoji"},
        runtime_upload_required=normalized_provider not in {"line_official"},
        text_fallback=profile.default_text,
    )


def build_outbound_payload(
    candidate: StickerCandidate,
    channel: Channel = "generic",
) -> OutboundStickerPayload:
    """Build a channel-specific send instruction from sticker metadata."""
    normalized_channel: Channel = channel if channel in {
        "web",
        "feishu",
        "wechat",
        "wecom",
        "line",
        "generic",
    } else "generic"

    instructions_by_channel: dict[Channel, tuple[str, ...]] = {
        "web": (
            "Resolve provider metadata through the approved API.",
            "Render remote preview only when provider terms allow embedding.",
            "Fall back to text if no compliant preview URL is available.",
        ),
        "feishu": (
            "Resolve or generate the sticker at runtime.",
            "Upload the runtime image to Feishu and send by image_key.",
            "Never commit Feishu image_key, temporary image files, or provider secrets.",
        ),
        "wechat": (
            "Resolve or generate the sticker at runtime.",
            "Upload through the active WeChat bridge or official media API and send by media id.",
            "Use text fallback when media upload fails or platform policy blocks the image.",
        ),
        "wecom": (
            "Resolve or generate the sticker at runtime.",
            "Upload through WeCom media APIs or customer-service media flow before sending.",
            "Keep company channels approval-gated for non-companion messages.",
        ),
        "line": (
            "Use packageId and stickerId directly when provider is line_official.",
            "Use runtime image upload only for non-LINE providers if the channel supports it.",
        ),
        "generic": (
            "Return metadata to the channel adapter.",
            "Let the adapter decide upload, embed, or text fallback based on platform policy.",
        ),
    }

    action = "send_text_fallback"
    if candidate.provider == "line_official" and normalized_channel == "line":
        action = "send_platform_sticker_id"
    elif candidate.provider == "image_generation":
        action = "generate_review_upload_send"
    elif candidate.provider != "metadata_only":
        action = "resolve_runtime_upload_send"

    return OutboundStickerPayload(
        channel=normalized_channel,
        action=action,
        intent=candidate.intent,
        provider=candidate.provider,
        style=candidate.style,
        text_fallback=candidate.text_fallback,
        instructions=instructions_by_channel[normalized_channel],
        metadata={
            "query": candidate.query,
            "tags": candidate.tags,
            "provider_ref": candidate.provider_ref,
            "preview_url": candidate.preview_url,
            "license_note": candidate.license_note,
            "attribution_required": candidate.attribution_required,
            "runtime_upload_required": candidate.runtime_upload_required,
        },
    )


def build_media_envelope(
    candidate: StickerCandidate,
    channel: Channel = "generic",
    *,
    kind: Literal["sticker", "image"] = "sticker",
    bridge_supports_upload: bool = False,
    review_required: bool = True,
) -> OutboundMediaPayload:
    """Build a normalized outbound media payload for social connectors."""

    sticker_payload = build_outbound_payload(candidate, channel)
    normalized_channel = sticker_payload.channel
    upload_required = candidate.runtime_upload_required

    platform_payloads: dict[Channel, dict[str, object]] = {
        "feishu": {
            "message_type": "image",
            "requires": "image_key",
            "upload_then_send": True,
        },
        "wechat": {
            "message_type": "image",
            "requires": "media_id_or_bridge_file",
            "upload_then_send": True,
            "compatible_text_fallback": True,
        },
        "wecom": {
            "message_type": "image",
            "requires": "media_id",
            "upload_then_send": True,
        },
        "web": {
            "message_type": "image_preview_or_text",
            "requires": "preview_url_or_runtime_blob",
        },
        "line": {
            "message_type": "sticker" if candidate.provider == "line_official" else "image",
            "requires": "packageId/stickerId or image upload",
        },
        "generic": {
            "message_type": "image_or_text",
            "requires": "adapter_capability_check",
        },
    }

    if bridge_supports_upload and upload_required:
        send_strategy = "upload_then_send"
        fallback_reason = ""
    elif sticker_payload.action == "send_platform_sticker_id":
        send_strategy = "send_platform_sticker_id"
        fallback_reason = ""
    elif upload_required:
        send_strategy = "text_fallback_until_upload_supported"
        fallback_reason = "channel media upload is not confirmed for this bridge"
    else:
        send_strategy = "send_text_fallback"
        fallback_reason = "metadata-only provider has no resolved image asset"

    return OutboundMediaPayload(
        kind=kind,
        channel=normalized_channel,
        action=sticker_payload.action,
        send_strategy=send_strategy,
        text_fallback=sticker_payload.text_fallback,
        upload_required=upload_required,
        review_required=review_required and candidate.provider == "image_generation",
        fallback_reason=fallback_reason,
        platform_payload=platform_payloads[normalized_channel],
        metadata={
            "intent": candidate.intent,
            "provider": candidate.provider,
            "style": candidate.style,
            "query": candidate.query,
            "license_note": candidate.license_note,
            "attribution_required": candidate.attribution_required,
            "instructions": sticker_payload.instructions,
        },
    )


def list_intents() -> list[dict[str, object]]:
    """Return owner-reviewable sticker intents."""
    return [asdict(profile) for profile in INTENT_REGISTRY.values()]
