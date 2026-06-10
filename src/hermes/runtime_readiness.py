from __future__ import annotations

from dataclasses import asdict, dataclass

from .adapters.everos import status as everos_status
from .adapters.mirofish import status as mirofish_status
from .adapters.searxng import status as searxng_status
from .adapters.sonic import status as sonic_status
from .adapters.trendradar import status as trendradar_status
from .config import Settings


READY_STATES = {"configured"}
SOURCE_READY_STATES = {"source_ready"}
BLOCKING_STATES = {"missing_config", "missing_source", "invalid_source", "error", "http_error"}


@dataclass(frozen=True)
class RuntimeReadinessItem:
    name: str
    status: str
    required_for_usable: bool
    detail: str
    source: str
    license: str


@dataclass(frozen=True)
class RuntimeReadiness:
    status: str
    summary: str
    items: tuple[RuntimeReadinessItem, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def collect_runtime_readiness(settings: Settings) -> dict[str, object]:
    everos = everos_status(settings)
    trendradar = trendradar_status(settings)
    mirofish = mirofish_status(settings)
    searxng = searxng_status(settings)
    sonic = sonic_status(settings)

    items = (
        RuntimeReadinessItem("everos_memory", everos.status, True, everos.detail, everos.source_path, everos.license),
        RuntimeReadinessItem("trendradar_intelligence", trendradar.status, False, trendradar.detail, trendradar.source_path, trendradar.license),
        RuntimeReadinessItem("mirofish_simulation", mirofish.status, False, mirofish.detail, mirofish.source_path, mirofish.license),
        RuntimeReadinessItem("searxng_metasearch", searxng.status, False, searxng.detail, searxng.source, searxng.license),
        RuntimeReadinessItem("sonic_local_index", sonic.status, False, sonic.detail, sonic.source, sonic.license),
    )

    blockers = tuple(f"{item.name}: {item.detail}" for item in items if item.required_for_usable and item.status in BLOCKING_STATES)
    warnings = tuple(f"{item.name}: {item.detail}" for item in items if not item.required_for_usable and item.status in BLOCKING_STATES)

    if blockers:
        status = "blocked"
        summary = "Required runtime configuration is incomplete"
    elif any(item.status in SOURCE_READY_STATES for item in items):
        status = "partial"
        summary = "Required runtime source is present; optional runtimes may still need live service configuration"
    else:
        status = "ready"
        summary = "Runtime adapter configuration is complete"

    readiness = RuntimeReadiness(status=status, summary=summary, items=items, blockers=blockers, warnings=warnings)
    return asdict(readiness)
