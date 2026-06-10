from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..config import Settings


MIROFISH_LICENSE = "AGPLv3"


@dataclass(frozen=True)
class MiroFishStatus:
    status: str
    detail: str
    source_path: str
    license: str
    project_root: str
    backend_base_url: str
    frontend_base_url: str
    npm_contract: tuple[str, ...]
    api_contract: tuple[str, ...]
    simulation_scripts: tuple[str, ...]
    commercial_boundary: str


@dataclass(frozen=True)
class MiroFishCommandPlan:
    status: str
    command: tuple[str, ...]
    cwd: str
    detail: str


def source_path(settings: Settings) -> Path:
    return settings.vendor_dir / "mirofish"


def project_root(settings: Settings) -> Path:
    return settings.mirofish_project_root or source_path(settings)


def status(settings: Settings) -> MiroFishStatus:
    src = source_path(settings)
    npm_contract = (
        "npm run setup:all",
        "npm run backend",
        "npm run frontend",
        "npm run dev",
        "npm run build",
    )
    api_contract = (
        "GET /health",
        "POST /api/graph/build",
        "POST /api/simulation/create",
        "POST /api/simulation/prepare",
        "POST /api/simulation/start",
        "GET /api/simulation/<simulation_id>/run-status",
        "POST /api/report/generate",
    )
    simulation_scripts = (
        "backend/scripts/run_twitter_simulation.py",
        "backend/scripts/run_reddit_simulation.py",
        "backend/scripts/run_parallel_simulation.py",
    )

    if not src.exists():
        state = "missing_source"
        detail = "MiroFish source is not present under vendor/runtimes/mirofish"
    elif not (src / "LICENSE").exists():
        state = "invalid_source"
        detail = "MiroFish source is present but LICENSE is missing"
    elif not (src / "package.json").exists():
        state = "invalid_source"
        detail = "MiroFish root npm package.json is missing"
    elif not (src / "backend" / "run.py").exists():
        state = "invalid_source"
        detail = "MiroFish Flask backend entrypoint is missing"
    elif not (src / "frontend" / "package.json").exists():
        state = "invalid_source"
        detail = "MiroFish Vite frontend package.json is missing"
    elif not settings.mirofish_backend_base_url:
        state = "source_ready"
        detail = "MiroFish source is present; set MIROFISH_BACKEND_BASE_URL to enable live simulation API calls"
    else:
        state = "configured"
        detail = "MiroFish source and backend URL are configured"

    return MiroFishStatus(
        status=state,
        detail=detail,
        source_path=str(src),
        license=MIROFISH_LICENSE,
        project_root=str(project_root(settings)),
        backend_base_url=settings.mirofish_backend_base_url,
        frontend_base_url=settings.mirofish_frontend_base_url,
        npm_contract=npm_contract,
        api_contract=api_contract,
        simulation_scripts=simulation_scripts,
        commercial_boundary="AGPLv3 runtime needs hosted-service source-delivery review before customer use.",
    )


def build_setup_command(settings: Settings) -> MiroFishCommandPlan:
    return _npm_plan(settings, ("npm", "run", "setup:all"), "Install MiroFish frontend and backend dependencies.")


def build_backend_command(settings: Settings) -> MiroFishCommandPlan:
    return _npm_plan(settings, ("npm", "run", "backend"), "Start the upstream MiroFish Flask backend.")


def build_frontend_command(settings: Settings) -> MiroFishCommandPlan:
    return _npm_plan(settings, ("npm", "run", "frontend"), "Start the upstream MiroFish Vite frontend.")


def build_dev_command(settings: Settings) -> MiroFishCommandPlan:
    return _npm_plan(settings, ("npm", "run", "dev"), "Start MiroFish backend and frontend through the upstream npm dev script.")


def _npm_plan(settings: Settings, command: tuple[str, ...], detail: str) -> MiroFishCommandPlan:
    root = project_root(settings)
    current = status(settings)
    if current.status not in {"source_ready", "configured"}:
        return MiroFishCommandPlan(status="unavailable", command=(), cwd=str(root), detail=current.detail)
    return MiroFishCommandPlan(status="ready", command=command, cwd=str(root), detail=detail)


def as_payload(value: MiroFishStatus | MiroFishCommandPlan) -> dict[str, object]:
    return asdict(value)
