from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .adapters.everos import status as everos_status
from .adapters.mirofish import status as mirofish_status
from .adapters.trendradar import status as trendradar_status
from .config import Settings
from .db import database_status
from .license import load_license


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
    db_status = database_status(settings)
    license_status = load_license(settings.license_file, settings.license_secret)
    everos = everos_status(settings)
    trendradar = trendradar_status(settings)
    mirofish = mirofish_status(settings)
    caps = [
        Capability("health_api", "ready", "HTTP health endpoint is available"),
        Capability("readiness_api", "ready", "HTTP readiness endpoint is available"),
        Capability("version_api", "ready", "Runtime version endpoint is available"),
        Capability("jobs_api", "ready", "File-backed P0 job creation and listing is available"),
        Capability("audit_api", "ready", "File-backed P0 audit event listing is available"),
        Capability("obsidian_report_write", "ready", "Markdown report write endpoint is available"),
        Capability("model_gateway", "ready" if settings.has_model_gateway else "missing_config", "OpenAI-compatible model gateway" if settings.has_model_gateway else "BAIRUI_MODEL_* environment is incomplete"),
        Capability("license_validation", license_status.status, license_status.error or str(settings.license_file)),
        Capability("postgresql", db_status.status, db_status.detail),
        Capability("obsidian_vault", "partial" if settings.obsidian_vault_dir.exists() else "missing_config", str(settings.obsidian_vault_dir)),
        Capability(
            "everos_memory",
            everos.status,
            everos.detail,
            source=everos.source_path,
            license=everos.license,
        ),
        Capability(
            "trendradar_intelligence",
            trendradar.status,
            trendradar.detail,
            source=trendradar.source_path,
            license=trendradar.license,
        ),
        Capability(
            "mirofish_simulation",
            mirofish.status,
            mirofish.detail,
            source=mirofish.source_path,
            license=mirofish.license,
        ),
        Capability("searxng_search", "planned", "use Docker or Linux checkout because Windows checkout is incompatible", source="https://github.com/searxng/searxng", license="AGPLv3"),
    ]
    return [asdict(cap) for cap in caps]
