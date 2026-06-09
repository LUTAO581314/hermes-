from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _read_jsonl(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows[-limit:]


@dataclass(frozen=True)
class AuditEvent:
    id: str
    action: str
    actor_type: str
    actor_ref: str
    resource_type: str
    resource_ref: str
    risk_level: str
    payload: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class Job:
    id: str
    title: str
    route: str
    status: str
    input: str
    owner_confirmation_required: bool
    result_pointer: str
    created_at: str
    updated_at: str


def create_audit_event(
    data_dir: Path,
    action: str,
    *,
    actor_type: str = "system",
    actor_ref: str = "hermes",
    resource_type: str = "runtime",
    resource_ref: str = "local",
    risk_level: str = "low",
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        id=str(uuid.uuid4()),
        action=action,
        actor_type=actor_type,
        actor_ref=actor_ref,
        resource_type=resource_type,
        resource_ref=resource_ref,
        risk_level=risk_level,
        payload=payload or {},
        created_at=utc_now(),
    )
    _append_jsonl(data_dir / "audit.jsonl", asdict(event))
    return event


def list_audit_events(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "audit.jsonl", limit=limit)


def create_job(data_dir: Path, title: str, prompt: str, route: str = "general") -> Job:
    now = utc_now()
    job = Job(
        id=str(uuid.uuid4()),
        title=title.strip() or "Untitled job",
        route=route.strip() or "general",
        status="queued",
        input=prompt.strip(),
        owner_confirmation_required=False,
        result_pointer="",
        created_at=now,
        updated_at=now,
    )
    _append_jsonl(data_dir / "jobs.jsonl", asdict(job))
    create_audit_event(
        data_dir,
        "job.created",
        resource_type="job",
        resource_ref=job.id,
        payload={"title": job.title, "route": job.route},
    )
    return job


def list_jobs(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "jobs.jsonl", limit=limit)


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_-]+", "-", value.strip()).strip("-")
    return normalized[:80] or "report"


def write_obsidian_report(vault_dir: Path, data_dir: Path, title: str, body: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    folder = vault_dir / "05_Reports"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{now.strftime('%Y%m%d-%H%M%S')}-{_slug(title)}.md"
    path = folder / filename
    content = "\n".join(
        [
            "---",
            f"title: {title}",
            f"created_at: {now.isoformat()}",
            "source: hermes",
            "---",
            "",
            f"# {title}",
            "",
            body.strip(),
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")
    create_audit_event(
        data_dir,
        "obsidian.report_written",
        resource_type="obsidian_report",
        resource_ref=str(path),
        payload={"title": title},
    )
    return {"path": str(path), "title": title, "created_at": now.isoformat()}
