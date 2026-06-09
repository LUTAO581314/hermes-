"""Small client helpers for external WeChat/Feishu connectors."""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class ConnectorClientError(RuntimeError):
    """Raised when the runtime cannot be reached or returns invalid JSON."""


class HermesConnectorClient:
    """HTTP client for the connector-facing runtime contract.

    This helper intentionally sends only transient inbound text to the runtime
    planning endpoint. The runtime returns preview lengths and metadata; callers
    must keep raw messages, media, screenshots, credentials, and API responses
    out of durable job records.
    """

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 5.0,
        *,
        basic_username: str = "",
        basic_password: str = "",
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.timeout_seconds = timeout_seconds
        self.basic_username = str(basic_username or "")
        self.basic_password = str(basic_password or "")

    @classmethod
    def from_env(cls) -> "HermesConnectorClient":
        return cls(
            os.getenv("HERMES_RUNTIME_BASE_URL", "http://127.0.0.1:8787"),
            timeout_seconds=float(os.getenv("HERMES_RUNTIME_TIMEOUT_SECONDS", "5")),
            basic_username=os.getenv("HERMES_RUNTIME_BASIC_USER", ""),
            basic_password=os.getenv("HERMES_RUNTIME_BASIC_PASSWORD", ""),
        )

    def plan_social_turn(
        self,
        *,
        channel: str,
        target_id: str,
        message: str,
    ) -> dict[str, Any]:
        return self._post_json(
            "/social/turn",
            {
                "channel": channel,
                "target_id": target_id,
                "message": message,
            },
        )

    def report_job_event(
        self,
        *,
        job_id: str,
        event: str,
        result_pointer: str = "",
        error_message: str = "",
    ) -> dict[str, Any]:
        body = {
            "job_id": job_id,
            "event": event,
            "result_pointer": result_pointer,
            "error_message": error_message,
        }
        return self._post_json("/jobs/event", body)

    def plan_media_send(
        self,
        *,
        channel: str,
        target_id: str,
        outbound_media: dict[str, Any],
        source_ref: str = "",
        text_fallback: str = "",
        bridge_capabilities: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post_json(
            "/media/plan-send",
            {
                "channel": channel,
                "target_id": target_id,
                "outbound_media": outbound_media,
                "source_ref": source_ref,
                "text_fallback": text_fallback,
                "bridge_capabilities": bridge_capabilities or {},
            },
        )

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            urljoin(self.base_url, path.lstrip("/")),
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers=self._headers(),
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise ConnectorClientError("runtime request failed") from error
        if not isinstance(payload, dict):
            raise ConnectorClientError("runtime returned non-object json")
        if payload.get("status") != "ok":
            raise ConnectorClientError(str(payload.get("error", "runtime error")))
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.basic_username or self.basic_password:
            token = f"{self.basic_username}:{self.basic_password}".encode("utf-8")
            headers["Authorization"] = (
                "Basic " + base64.b64encode(token).decode("ascii")
            )
        return headers


def _normalize_base_url(base_url: str) -> str:
    text = str(base_url or "").strip()
    if not text:
        raise ValueError("base_url is required")
    if not text.endswith("/"):
        text += "/"
    return text
