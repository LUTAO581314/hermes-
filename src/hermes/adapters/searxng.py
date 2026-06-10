from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

from ..config import Settings
from ..storage import create_audit_event


SEARXNG_LICENSE = "AGPLv3"
SEARXNG_SOURCE_URL = "https://github.com/searxng/searxng"


@dataclass(frozen=True)
class SearXNGStatus:
    status: str
    detail: str
    source: str
    license: str
    base_url: str
    api_contract: tuple[str, ...]
    docker_contract: tuple[str, ...]
    commercial_boundary: str


@dataclass(frozen=True)
class SearXNGCommandPlan:
    status: str
    command: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class SearXNGResult:
    status: str
    endpoint: str
    payload: dict[str, Any]
    response: dict[str, Any] | None = None
    error: str = ""


def status(settings: Settings) -> SearXNGStatus:
    api_contract = (
        "GET /search?q=<query>&format=json",
        "POST /search with q=<query>&format=json",
        "settings.yml search.formats must include json",
    )
    docker_contract = (
        "docker.io/searxng/searxng:latest",
        "container port 8080",
        "mount settings.yml with json output enabled",
    )
    if not settings.searxng_base_url:
        state = "missing_config"
        detail = "Set SEARXNG_BASE_URL to enable self-hosted metasearch calls"
    else:
        state = "configured"
        detail = "SearXNG base URL is configured; JSON output must be enabled in settings.yml"

    return SearXNGStatus(
        status=state,
        detail=detail,
        source=SEARXNG_SOURCE_URL,
        license=SEARXNG_LICENSE,
        base_url=settings.searxng_base_url,
        api_contract=api_contract,
        docker_contract=docker_contract,
        commercial_boundary="AGPLv3 service needs hosted-use source-delivery review before customer use.",
    )


def build_docker_command(settings: Settings, *, host_port: int = 8080) -> SearXNGCommandPlan:
    base_url = settings.searxng_public_base_url or f"http://127.0.0.1:{host_port}"
    return SearXNGCommandPlan(
        status="ready",
        command=(
            "docker",
            "run",
            "-d",
            "--name",
            "bairui-searxng",
            "-p",
            f"{host_port}:8080",
            "-e",
            f"SEARXNG_BASE_URL={base_url}",
            "docker.io/searxng/searxng:latest",
        ),
        detail="Start SearXNG as an external Docker service; enable json in settings.yml for API use.",
    )


def build_search_payload(
    *,
    query: str,
    categories: str = "",
    engines: str = "",
    language: str = "",
    safesearch: str = "",
    time_range: str = "",
    page: int = 1,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"q": query, "format": "json", "pageno": page}
    if categories:
        payload["categories"] = categories
    if engines:
        payload["engines"] = engines
    if language:
        payload["language"] = language
    if safesearch:
        payload["safesearch"] = safesearch
    if time_range:
        payload["time_range"] = time_range
    return payload


def search(settings: Settings, payload: dict[str, Any]) -> SearXNGResult:
    if not settings.searxng_base_url:
        return SearXNGResult(
            status="missing_config",
            endpoint="/search",
            payload=payload,
            error="SEARXNG_BASE_URL is not configured",
        )

    query = urllib.parse.urlencode(payload)
    url = settings.searxng_base_url.rstrip("/") + "/search?" + query
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=settings.searxng_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        error = exc.read().decode("utf-8", errors="replace")
        return SearXNGResult(status="http_error", endpoint="/search", payload=payload, error=f"{exc.code}: {error}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return SearXNGResult(status="error", endpoint="/search", payload=payload, error=str(exc))

    create_audit_event(
        settings.data_dir,
        "searxng.search",
        resource_type="searxng",
        resource_ref="/search",
        risk_level="low",
        payload={"status": "completed", "query": payload.get("q", "")},
    )
    return SearXNGResult(status="completed", endpoint="/search", payload=payload, response=data)


def as_payload(value: SearXNGStatus | SearXNGCommandPlan | SearXNGResult) -> dict[str, object]:
    return asdict(value)
