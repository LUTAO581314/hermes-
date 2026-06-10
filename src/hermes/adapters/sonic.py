from __future__ import annotations

import socket
from dataclasses import asdict, dataclass
from typing import Any

from ..config import Settings
from ..storage import create_audit_event


SONIC_LICENSE = "MPL-2.0"
SONIC_SOURCE_URL = "https://github.com/valeriansaliou/sonic"
SONIC_IMAGE = "valeriansaliou/sonic:latest"


@dataclass(frozen=True)
class SonicStatus:
    status: str
    detail: str
    source: str
    license: str
    host: str
    port: int
    auth: str
    protocol_contract: tuple[str, ...]
    docker_contract: tuple[str, ...]
    commercial_boundary: str


@dataclass(frozen=True)
class SonicCommandPlan:
    status: str
    command: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class SonicResult:
    status: str
    channel: str
    command: str
    response: tuple[str, ...] = ()
    payload: dict[str, Any] | None = None
    error: str = ""


def status(settings: Settings) -> SonicStatus:
    protocol_contract = (
        "TCP channel protocol on port 1491",
        "START search|ingest|control <password>",
        'QUERY <collection> <bucket> "<terms>" LIMIT(<n>)',
        'PUSH <collection> <bucket> <object> "<text>"',
        "PING",
    )
    docker_contract = (
        SONIC_IMAGE,
        "container port 1491",
        "SONIC_CHANNEL__AUTH_PASSWORD must be set for production",
    )
    if not settings.sonic_host:
        state = "missing_config"
        detail = "Set SONIC_HOST and SONIC_PASSWORD to enable local internal search indexing"
    elif not settings.sonic_password:
        state = "missing_config"
        detail = "SONIC_HOST is configured but SONIC_PASSWORD is missing"
    else:
        state = "configured"
        detail = "Sonic TCP endpoint and password are configured"

    return SonicStatus(
        status=state,
        detail=detail,
        source=SONIC_SOURCE_URL,
        license=SONIC_LICENSE,
        host=settings.sonic_host,
        port=settings.sonic_port,
        auth="configured" if settings.sonic_password else "missing_config",
        protocol_contract=protocol_contract,
        docker_contract=docker_contract,
        commercial_boundary="MPL-2.0 runtime can be used as an external service while preserving license notices.",
    )


def build_docker_command(settings: Settings, *, host_port: int = 1491) -> SonicCommandPlan:
    password = settings.sonic_password or "change-me-long-random-sonic-password"
    return SonicCommandPlan(
        status="ready",
        command=(
            "docker",
            "run",
            "-d",
            "--name",
            "bairui-sonic",
            "-p",
            f"127.0.0.1:{host_port}:1491",
            "-v",
            "$(pwd)/infra/sonic/config.cfg:/etc/sonic.cfg",
            "-v",
            "$(pwd)/data/sonic:/var/lib/sonic/store",
            "-e",
            f"SONIC_CHANNEL__AUTH_PASSWORD={password}",
            SONIC_IMAGE,
        ),
        detail="Start Sonic with a mounted sonic.cfg; the password is interpolated from SONIC_CHANNEL__AUTH_PASSWORD.",
    )


def build_push_payload(
    *,
    collection: str,
    bucket: str,
    object_id: str,
    text: str,
    lang: str = "",
) -> dict[str, str]:
    payload = {"collection": collection, "bucket": bucket, "object_id": object_id, "text": text}
    if lang:
        payload["lang"] = lang
    return payload


def build_query_payload(
    *,
    collection: str,
    bucket: str,
    query: str,
    limit: int = 10,
    offset: int = 0,
    lang: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {"collection": collection, "bucket": bucket, "query": query, "limit": limit}
    if offset:
        payload["offset"] = offset
    if lang:
        payload["lang"] = lang
    return payload


def ping(settings: Settings) -> SonicResult:
    return _run(settings, "control", "PING", audit_action="sonic.ping")


def push(settings: Settings, payload: dict[str, str]) -> SonicResult:
    command = (
        f"PUSH {payload['collection']} {payload['bucket']} {payload['object_id']} "
        f'"{_quote(payload["text"])}"{_lang(payload.get("lang", ""))}'
    )
    return _run(settings, "ingest", command, payload=payload, audit_action="sonic.push")


def query(settings: Settings, payload: dict[str, Any]) -> SonicResult:
    command = (
        f"QUERY {payload['collection']} {payload['bucket']} "
        f'"{_quote(str(payload["query"]))}" LIMIT({int(payload.get("limit", 10))})'
    )
    if payload.get("offset"):
        command += f" OFFSET({int(payload['offset'])})"
    if payload.get("lang"):
        command += _lang(str(payload["lang"]))
    return _run(settings, "search", command, payload=payload, audit_action="sonic.query")


def _run(
    settings: Settings,
    channel: str,
    command: str,
    *,
    payload: dict[str, Any] | None = None,
    audit_action: str,
) -> SonicResult:
    if not settings.sonic_host or not settings.sonic_password:
        return SonicResult(
            status="missing_config",
            channel=channel,
            command=command,
            payload=payload,
            error="SONIC_HOST and SONIC_PASSWORD must be configured",
        )
    try:
        responses = _exchange(settings, channel, command)
    except (OSError, TimeoutError) as exc:
        return SonicResult(status="error", channel=channel, command=command, payload=payload, error=str(exc))

    if any(line.startswith(("ERR ", "ENDED ")) and "quit" not in line for line in responses):
        return SonicResult(status="error", channel=channel, command=command, response=tuple(responses), payload=payload)

    create_audit_event(
        settings.data_dir,
        audit_action,
        resource_type="sonic",
        resource_ref=channel,
        risk_level="low",
        payload={"status": "completed", "command": command.split(" ", 1)[0]},
    )
    return SonicResult(status="completed", channel=channel, command=command, response=tuple(responses), payload=payload)


def _exchange(settings: Settings, channel: str, command: str) -> list[str]:
    lines: list[str] = []
    with socket.create_connection((settings.sonic_host, settings.sonic_port), timeout=settings.sonic_timeout_seconds) as sock:
        sock.settimeout(settings.sonic_timeout_seconds)
        reader = sock.makefile("r", encoding="utf-8", newline="\n")
        writer = sock.makefile("w", encoding="utf-8", newline="\n")
        lines.append(reader.readline().strip())
        writer.write(f"START {channel} {settings.sonic_password}\n")
        writer.flush()
        lines.append(reader.readline().strip())
        writer.write(command + "\n")
        writer.flush()
        lines.append(reader.readline().strip())
        if lines[-1].startswith("PENDING "):
            lines.append(reader.readline().strip())
        writer.write("QUIT\n")
        writer.flush()
        final = reader.readline().strip()
        if final:
            lines.append(final)
    return lines


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _lang(value: str) -> str:
    return f" LANG({value})" if value else ""


def as_payload(value: SonicStatus | SonicCommandPlan | SonicResult) -> dict[str, object]:
    return asdict(value)
