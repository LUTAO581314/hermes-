from __future__ import annotations

import hmac
from dataclasses import dataclass, asdict
from typing import Mapping

from .config import Settings


@dataclass(frozen=True)
class AdminSessionStatus:
    status: str
    identity: str
    auth_method: str
    write_api_protected: bool
    authenticated: bool
    token_configured: bool
    secret_policy: str
    next_step: str


def build_admin_session_status(settings: Settings, headers: Mapping[str, str] | None = None) -> AdminSessionStatus:
    expected = str(settings.owner_token or "").strip()
    provided = _provided_token(headers or {})
    token_configured = bool(expected)
    authenticated = bool(expected and provided and hmac.compare_digest(provided, expected))

    if not token_configured:
        status = "missing_config"
        next_step = "Set BAIRUI_OWNER_TOKEN before exposing the console beyond trusted local development."
    elif authenticated:
        status = "authenticated"
        next_step = "Owner token accepted for this request. Write APIs can be used from this browser."
    else:
        status = "locked"
        next_step = "Save the owner token locally in Settings or send X-Bairui-Owner-Token / Authorization: Bearer."

    return AdminSessionStatus(
        status=status,
        identity="local_owner",
        auth_method="owner_token_header",
        write_api_protected=token_configured,
        authenticated=authenticated,
        token_configured=token_configured,
        secret_policy="owner token is accepted by header only and is never returned",
        next_step=next_step,
    )


def as_payload(status: AdminSessionStatus) -> dict[str, object]:
    return asdict(status)


def _provided_token(headers: Mapping[str, str]) -> str:
    provided = str(headers.get("X-Bairui-Owner-Token", "") or headers.get("x-bairui-owner-token", "")).strip()
    authorization = str(headers.get("Authorization", "") or headers.get("authorization", "")).strip()
    if not provided and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    return provided
