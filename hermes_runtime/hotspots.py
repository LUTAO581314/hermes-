"""Hermes-native hotspot panel data."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from .config import RuntimeConfig
from .server_time import utc_now


def hotspots_payload(config: RuntimeConfig, *, limit: int = 24) -> dict[str, Any]:
    """Return the Brain UI hotspot shape from Hermes-owned data sources."""

    output_dir = config.trendradar_output_dir
    feed = _load_trendradar_feed(output_dir, limit=limit)
    return {
        "status": "ok",
        "source": "hermes",
        "provider": "trendradar",
        "created_at": utc_now(),
        "output_dir_configured": str(output_dir),
        "output_dir_exists": output_dir.exists(),
        "items": feed,
        "feed": feed,
        "platforms": [
            {
                "id": "trendradar",
                "label": "TrendRadar",
                "state": "ready" if feed else "empty",
                "count": len(feed),
            }
        ],
        "migration": {
            "from": "BaiLongma src/hotspots.js data shape",
            "rule": "Keep the visual panel and normalized data shape; do not keep BaiLongma as a backend authority.",
        },
    }


def _load_trendradar_feed(output_dir: Path, *, limit: int) -> list[dict[str, Any]]:
    if not output_dir.exists() or not output_dir.is_dir():
        return []

    items: list[dict[str, Any]] = []
    for path in sorted(output_dir.rglob("*.json"), key=_mtime, reverse=True)[:20]:
        for raw in _extract_items(_read_json(path)):
            normalized = _normalize_item(raw, path)
            if normalized:
                items.append(normalized)
            if len(items) >= limit:
                return items
    return items


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _extract_items(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("items", "feed", "results", "articles", "entries", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = _extract_items(value)
            if nested:
                return nested
    return [payload] if _looks_like_item(payload) else []


def _looks_like_item(value: dict[str, Any]) -> bool:
    return any(key in value for key in ("title", "url", "link", "summary", "content"))


def _normalize_item(raw: Any, path: Path) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    title = _first_text(raw, "title", "name", "headline", "topic")
    summary = _first_text(raw, "summary", "description", "content", "text")
    url = _first_text(raw, "url", "link", "source_url")
    if not title and not summary:
        return None
    return {
        "id": _first_text(raw, "id", "guid")
        or f"{path.name}:{abs(hash((title, url))) % 1000000}",
        "title": title or summary[:80],
        "summary": summary,
        "url": url,
        "source": _first_text(raw, "source", "provider", "site") or "trendradar",
        "platform": _first_text(raw, "platform", "category") or "trendradar",
        "created_at": _first_text(raw, "created_at", "published_at", "time", "date"),
        "source_file": path.name,
    }


def _first_text(raw: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return ""


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0
