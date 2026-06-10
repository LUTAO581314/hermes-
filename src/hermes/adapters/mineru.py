from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..config import Settings


MINERU_LICENSE = "MinerU Open Source License"
MINERU_SOURCE_URL = "https://github.com/opendatalab/MinerU"


@dataclass(frozen=True)
class MinerUStatus:
    status: str
    detail: str
    source: str
    license: str
    project_root: str
    output_dir: str
    backend: str
    device: str
    cli_contract: tuple[str, ...]
    output_contract: tuple[str, ...]
    commercial_boundary: str


@dataclass(frozen=True)
class MinerUCommandPlan:
    status: str
    command: tuple[str, ...]
    cwd: str
    detail: str


def project_root(settings: Settings) -> Path:
    return settings.mineru_project_root or (settings.vendor_dir / "mineru")


def status(settings: Settings) -> MinerUStatus:
    root = project_root(settings)
    cli_contract = (
        "pip install mineru[pipeline]",
        "mineru -p <input_path> -o <output_path>",
        "mineru -p <input_path> -o <output_path> -b pipeline",
        "mineru -p <input_path> -o <output_path> -b hybrid-http-client -u http://127.0.0.1:30000",
    )
    output_contract = (
        "Markdown output for LLM-ready reading",
        "JSON output for structured ingestion",
        "extracted images/tables/formulas where supported by the selected backend",
    )

    if root.exists():
        state = "source_ready"
        detail = "MinerU project root exists; install dependencies and run parse-command on target documents"
    else:
        state = "missing_config"
        detail = "Set MINERU_PROJECT_ROOT or install MinerU CLI to enable document parsing commands"

    return MinerUStatus(
        status=state,
        detail=detail,
        source=MINERU_SOURCE_URL,
        license=MINERU_LICENSE,
        project_root=str(root),
        output_dir=str(settings.mineru_output_dir),
        backend=settings.mineru_backend,
        device=settings.mineru_device,
        cli_contract=cli_contract,
        output_contract=output_contract,
        commercial_boundary=(
            "MinerU uses a project-specific open-source license based on Apache-2.0 with additional terms; "
            "review before customer distribution or hosted parsing service use."
        ),
    )


def build_install_command(settings: Settings) -> MinerUCommandPlan:
    return MinerUCommandPlan(
        status="ready",
        command=("pip", "install", "mineru[pipeline]"),
        cwd=str(project_root(settings)),
        detail="Install the local MinerU parsing CLI in an isolated runtime environment before processing customer files.",
    )


def build_parse_command(
    settings: Settings,
    *,
    input_path: str,
    output_dir: str = "",
    backend: str = "",
    language: str = "",
    source: str = "",
    device: str = "",
) -> MinerUCommandPlan:
    out_dir = output_dir or str(settings.mineru_output_dir)
    command = ("mineru", "-p", input_path, "-o", out_dir)
    selected_backend = backend or settings.mineru_backend
    if selected_backend:
        command += ("-b", selected_backend)
    if language:
        command += ("-l", language)
    if source:
        command += ("--source", source)
    selected_device = device or settings.mineru_device
    if selected_device and selected_device != "cpu":
        command += ("-d", selected_device)
    return MinerUCommandPlan(
        status="ready",
        command=command,
        cwd=str(project_root(settings)),
        detail="Run MinerU locally so private customer documents are parsed inside the controlled runtime boundary.",
    )


def as_payload(value: MinerUStatus | MinerUCommandPlan) -> dict[str, object]:
    return asdict(value)
