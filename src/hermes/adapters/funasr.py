from __future__ import annotations

import json
import mimetypes
import uuid
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..config import Settings
from ..storage import create_audit_event


FUNASR_LICENSE = "MIT"
FUNASR_SOURCE_URL = "https://github.com/modelscope/FunASR"
FUNASR_OPENAI_TRANSCRIPTION_PATH = "/v1/audio/transcriptions"


@dataclass(frozen=True)
class FunASRStatus:
    status: str
    detail: str
    source: str
    license: str
    project_root: str
    base_url: str
    public_base_url: str
    model: str
    api_contract: tuple[str, ...]
    cli_contract: tuple[str, ...]
    commercial_boundary: str


@dataclass(frozen=True)
class FunASRCommandPlan:
    status: str
    command: tuple[str, ...]
    cwd: str
    detail: str


@dataclass(frozen=True)
class FunASRResult:
    status: str
    endpoint: str
    payload: dict[str, Any]
    response: dict[str, Any] | None = None
    error: str = ""


def project_root(settings: Settings) -> Path:
    return settings.funasr_project_root or (settings.vendor_dir / "funasr")


def status(settings: Settings) -> FunASRStatus:
    root = project_root(settings)
    api_contract = (
        "GET /health",
        "POST /v1/audio/transcriptions",
        "multipart form field: file",
        "multipart form field: model",
    )
    cli_contract = (
        "pip install torch torchaudio funasr vllm fastapi uvicorn python-multipart",
        "funasr-server --device cuda",
        "funasr-server --model <model> --device <cpu|cuda>",
    )
    if not settings.funasr_base_url:
        state = "missing_config"
        detail = "Set FUNASR_BASE_URL to enable OpenAI-compatible ASR transcription calls"
    else:
        state = "configured"
        detail = "FunASR OpenAI-compatible transcription endpoint is configured"

    return FunASRStatus(
        status=state,
        detail=detail,
        source=FUNASR_SOURCE_URL,
        license=FUNASR_LICENSE,
        project_root=str(root),
        base_url=settings.funasr_base_url,
        public_base_url=settings.funasr_public_base_url,
        model=settings.funasr_model,
        api_contract=api_contract,
        cli_contract=cli_contract,
        commercial_boundary="MIT runtime is suitable for productized ASR integration while preserving license notices.",
    )


def build_server_command(settings: Settings, *, device: str = "cuda", model: str = "") -> FunASRCommandPlan:
    command = ("funasr-server", "--device", device)
    if model:
        command = ("funasr-server", "--model", model, "--device", device)
    return FunASRCommandPlan(
        status="ready",
        command=command,
        cwd=str(project_root(settings)),
        detail="Start the upstream FunASR OpenAI-compatible server after installing FunASR server dependencies.",
    )


def build_docker_command(settings: Settings, *, host_port: int = 8899) -> FunASRCommandPlan:
    base_url = settings.funasr_public_base_url or f"http://127.0.0.1:{host_port}"
    return FunASRCommandPlan(
        status="ready",
        command=(
            "docker",
            "run",
            "-d",
            "--name",
            "bairui-funasr",
            "-p",
            f"127.0.0.1:{host_port}:8000",
            "-e",
            f"FUNASR_PUBLIC_BASE_URL={base_url}",
            "modelscope/funasr:latest",
        ),
        cwd=str(project_root(settings)),
        detail="Planned Docker command for a FunASR service; verify the chosen image/tag on the target server before production.",
    )


def build_transcription_payload(
    *,
    audio_path: str,
    model: str = "",
    language: str = "",
    prompt: str = "",
    response_format: str = "json",
) -> dict[str, str]:
    payload = {
        "audio_path": audio_path,
        "model": model,
        "response_format": response_format,
    }
    if language:
        payload["language"] = language
    if prompt:
        payload["prompt"] = prompt
    return payload


def transcribe(settings: Settings, payload: dict[str, str]) -> FunASRResult:
    if not settings.funasr_base_url:
        return FunASRResult(
            status="missing_config",
            endpoint=FUNASR_OPENAI_TRANSCRIPTION_PATH,
            payload=payload,
            error="FUNASR_BASE_URL is not configured",
        )

    audio_path = Path(payload["audio_path"])
    if not audio_path.exists() or not audio_path.is_file():
        return FunASRResult(
            status="invalid_request",
            endpoint=FUNASR_OPENAI_TRANSCRIPTION_PATH,
            payload=payload,
            error=f"audio file does not exist: {audio_path}",
        )

    model = payload.get("model") or settings.funasr_model
    fields = {
        "model": model,
        "response_format": payload.get("response_format", "json"),
    }
    for name in ("language", "prompt"):
        if payload.get(name):
            fields[name] = payload[name]
    files = {"file": audio_path}
    body, content_type = _multipart_body(fields, files)
    url = settings.funasr_base_url.rstrip("/") + FUNASR_OPENAI_TRANSCRIPTION_PATH
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type, "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.funasr_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        error = exc.read().decode("utf-8", errors="replace")
        return FunASRResult(status="http_error", endpoint=FUNASR_OPENAI_TRANSCRIPTION_PATH, payload=payload, error=f"{exc.code}: {error}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return FunASRResult(status="error", endpoint=FUNASR_OPENAI_TRANSCRIPTION_PATH, payload=payload, error=str(exc))

    create_audit_event(
        settings.data_dir,
        "funasr.transcription",
        resource_type="funasr",
        resource_ref=FUNASR_OPENAI_TRANSCRIPTION_PATH,
        risk_level="low",
        payload={"status": "completed", "audio_file": audio_path.name, "model": model},
    )
    return FunASRResult(status="completed", endpoint=FUNASR_OPENAI_TRANSCRIPTION_PATH, payload=payload, response=data)


def _multipart_body(fields: dict[str, str], files: dict[str, Path]) -> tuple[bytes, str]:
    boundary = "bairui-" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    for name, path in files.items():
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode("utf-8"),
                f"Content-Type: {mime}\r\n\r\n".encode("utf-8"),
                path.read_bytes(),
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def as_payload(value: FunASRStatus | FunASRCommandPlan | FunASRResult) -> dict[str, object]:
    return asdict(value)
