"""Small client helpers for external WeChat/Feishu connectors."""

from __future__ import annotations

import json
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

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.timeout_seconds = timeout_seconds

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

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            urljoin(self.base_url, path.lstrip("/")),
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
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


def _normalize_base_url(base_url: str) -> str:
    text = str(base_url or "").strip()
    if not text:
        raise ValueError("base_url is required")
    if not text.endswith("/"):
        text += "/"
    return text
