from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .config import Settings


@dataclass(frozen=True)
class Capability:
    name: str
    status: str
    detail: str
    source: str = "hermes"
    license: str = ""


def _vendor_capability(name: str, path: Path, purpose: str, license_name: str) -> Capability:
    if path.exists():
        return Capability(name=name, status="partial", detail=f"source integrated for {purpose}", source=str(path), license=license_name)
    return Capability(name=name, status="missing_config", detail=f"vendor source missing for {purpose}", source=str(path), license=license_name)


def collect_capabilities(settings: Settings) -> list[dict[str, str]]:
    vendor = settings.vendor_dir
    caps = [
        Capability("health_api", "ready", "HTTP health endpoint is available"),
        Capability("readiness_api", "ready", "HTTP readiness endpoint is available"),
        Capability("version_api", "ready", "Runtime version endpoint is available"),
        Capability("jobs_api", "ready", "File-backed P0 job creation and listing is available"),
        Capability("audit_api", "ready", "File-backed P0 audit event listing is available"),
        Capability("obsidian_report_write", "ready", "Markdown report write endpoint is available"),
        Capability("postgresql", "partial" if settings.has_database else "missing_config", "database URL configured" if settings.has_database else "HERMES_DATABASE_URL is empty"),
        Capability("obsidian_vault", "partial" if settings.obsidian_vault_dir.exists() else "missing_config", str(settings.obsidian_vault_dir)),
        _vendor_capability("everos_memory", vendor / "everos", "memory extraction and retrieval", "Apache-2.0"),
        _vendor_capability("trendradar_intelligence", vendor / "trendradar", "trend and public-opinion intelligence", "GPLv3"),
        _vendor_capability("mirofish_simulation", vendor / "mirofish", "scenario simulation", "AGPLv3"),
        Capability("searxng_search", "planned", "use Docker or Linux checkout because Windows checkout is incompatible", source="https://github.com/searxng/searxng", license="AGPLv3"),
    ]
    return [asdict(cap) for cap in caps]
