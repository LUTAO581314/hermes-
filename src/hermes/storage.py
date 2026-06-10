from __future__ import annotations

import json
import mimetypes
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
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


@dataclass(frozen=True)
class DocumentIngest:
    id: str
    title: str
    status: str
    input_path: str
    output_dir: str
    parser: str
    parser_command: tuple[str, ...]
    pipeline: dict[str, str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DocumentIngestRun:
    id: str
    ingest_id: str
    status: str
    command: tuple[str, ...]
    cwd: str
    exit_code: int | None
    stdout: str
    stderr: str
    error: str
    started_at: str
    finished_at: str


@dataclass(frozen=True)
class DocumentArtifact:
    id: str
    ingest_id: str
    path: str
    relative_path: str
    artifact_type: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: str


@dataclass(frozen=True)
class DocumentIndexRun:
    id: str
    ingest_id: str
    status: str
    provider: str
    collection: str
    bucket: str
    indexed_count: int
    skipped_count: int
    failed_count: int
    results: tuple[dict[str, Any], ...]
    error: str
    created_at: str


@dataclass(frozen=True)
class DocumentMemoryCandidate:
    id: str
    ingest_id: str
    artifact_id: str
    source_path: str
    status: str
    candidate_type: str
    text: str
    confidence: float
    reason: str
    created_at: str


@dataclass(frozen=True)
class DocumentMemoryReview:
    id: str
    candidate_id: str
    decision: str
    status: str
    reviewer_ref: str
    note: str
    everos_status: str
    everos_endpoint: str
    everos_error: str
    created_at: str


@dataclass(frozen=True)
class SourceRef:
    id: str
    source_type: str
    source_ref: str
    provider: str
    title: str
    url: str
    confidence: str
    metadata: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class DocumentIngestReport:
    id: str
    ingest_id: str
    title: str
    path: str
    status: str
    artifact_count: int
    index_run_count: int
    candidate_count: int
    review_count: int
    source_ref_count: int
    created_at: str


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


def create_document_ingest(
    data_dir: Path,
    *,
    title: str,
    input_path: str,
    output_dir: str,
    parser_command: tuple[str, ...],
) -> DocumentIngest:
    now = utc_now()
    ingest = DocumentIngest(
        id=str(uuid.uuid4()),
        title=title.strip() or Path(input_path).name or "Document ingest",
        status="planned",
        input_path=input_path,
        output_dir=output_dir,
        parser="mineru",
        parser_command=parser_command,
        pipeline={
            "parse": "planned",
            "artifact_registration": "pending",
            "sonic_index": "pending",
            "everos_memory_candidate": "pending",
            "postgresql_source_ref": "pending",
            "obsidian_report": "pending",
        },
        created_at=now,
        updated_at=now,
    )
    _append_jsonl(data_dir / "document_ingests.jsonl", asdict(ingest))
    create_audit_event(
        data_dir,
        "document.ingest_planned",
        resource_type="document_ingest",
        resource_ref=ingest.id,
        payload={"title": ingest.title, "input_path": input_path, "parser": ingest.parser},
    )
    return ingest


def list_document_ingests(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "document_ingests.jsonl", limit=limit)


def create_document_ingest_run(
    data_dir: Path,
    *,
    ingest_id: str,
    status: str,
    command: tuple[str, ...],
    cwd: str,
    exit_code: int | None,
    stdout: str = "",
    stderr: str = "",
    error: str = "",
    started_at: str = "",
    finished_at: str = "",
) -> DocumentIngestRun:
    started = started_at or utc_now()
    finished = finished_at or utc_now()
    run = DocumentIngestRun(
        id=str(uuid.uuid4()),
        ingest_id=ingest_id,
        status=status,
        command=command,
        cwd=cwd,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        error=error,
        started_at=started,
        finished_at=finished,
    )
    _append_jsonl(data_dir / "document_ingest_runs.jsonl", asdict(run))
    create_audit_event(
        data_dir,
        "document.ingest_run_finished",
        resource_type="document_ingest",
        resource_ref=ingest_id,
        risk_level="medium" if status != "completed" else "low",
        payload={"status": status, "exit_code": exit_code, "run_id": run.id},
    )
    return run


def list_document_ingest_runs(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "document_ingest_runs.jsonl", limit=limit)


def create_document_artifact(
    data_dir: Path,
    *,
    ingest_id: str,
    path: Path,
    output_dir: Path,
) -> DocumentArtifact:
    resolved_path = path.resolve()
    resolved_output_dir = output_dir.resolve()
    try:
        relative_path = str(resolved_path.relative_to(resolved_output_dir))
    except ValueError:
        relative_path = resolved_path.name
    artifact = DocumentArtifact(
        id=str(uuid.uuid4()),
        ingest_id=ingest_id,
        path=str(resolved_path),
        relative_path=relative_path,
        artifact_type=_classify_artifact(resolved_path),
        mime_type=mimetypes.guess_type(resolved_path.name)[0] or "application/octet-stream",
        size_bytes=resolved_path.stat().st_size,
        sha256=_file_sha256(resolved_path),
        created_at=utc_now(),
    )
    _append_jsonl(data_dir / "document_artifacts.jsonl", asdict(artifact))
    return artifact


def list_document_artifacts(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "document_artifacts.jsonl", limit=limit)


def create_document_index_run(
    data_dir: Path,
    *,
    ingest_id: str,
    status: str,
    provider: str,
    collection: str,
    bucket: str,
    indexed_count: int,
    skipped_count: int,
    failed_count: int,
    results: tuple[dict[str, Any], ...] = (),
    error: str = "",
) -> DocumentIndexRun:
    run = DocumentIndexRun(
        id=str(uuid.uuid4()),
        ingest_id=ingest_id,
        status=status,
        provider=provider,
        collection=collection,
        bucket=bucket,
        indexed_count=indexed_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        results=results,
        error=error,
        created_at=utc_now(),
    )
    _append_jsonl(data_dir / "document_index_runs.jsonl", asdict(run))
    create_audit_event(
        data_dir,
        "document.sonic_index_finished",
        resource_type="document_ingest",
        resource_ref=ingest_id,
        risk_level="medium" if status not in {"completed", "skipped"} else "low",
        payload={
            "status": status,
            "provider": provider,
            "collection": collection,
            "bucket": bucket,
            "indexed_count": indexed_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "run_id": run.id,
        },
    )
    return run


def list_document_index_runs(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "document_index_runs.jsonl", limit=limit)


def create_document_memory_candidate(
    data_dir: Path,
    *,
    ingest_id: str,
    artifact_id: str,
    source_path: str,
    candidate_type: str,
    text: str,
    confidence: float,
    reason: str,
) -> DocumentMemoryCandidate:
    candidate = DocumentMemoryCandidate(
        id=str(uuid.uuid4()),
        ingest_id=ingest_id,
        artifact_id=artifact_id,
        source_path=source_path,
        status="pending_review",
        candidate_type=candidate_type,
        text=text,
        confidence=confidence,
        reason=reason,
        created_at=utc_now(),
    )
    _append_jsonl(data_dir / "document_memory_candidates.jsonl", asdict(candidate))
    return candidate


def list_document_memory_candidates(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "document_memory_candidates.jsonl", limit=limit)


def create_document_memory_review(
    data_dir: Path,
    *,
    candidate_id: str,
    decision: str,
    status: str,
    reviewer_ref: str,
    note: str = "",
    everos_status: str = "",
    everos_endpoint: str = "",
    everos_error: str = "",
) -> DocumentMemoryReview:
    review = DocumentMemoryReview(
        id=str(uuid.uuid4()),
        candidate_id=candidate_id,
        decision=decision,
        status=status,
        reviewer_ref=reviewer_ref,
        note=note,
        everos_status=everos_status,
        everos_endpoint=everos_endpoint,
        everos_error=everos_error,
        created_at=utc_now(),
    )
    _append_jsonl(data_dir / "document_memory_reviews.jsonl", asdict(review))
    create_audit_event(
        data_dir,
        "document.memory_candidate_reviewed",
        resource_type="document_memory_candidate",
        resource_ref=candidate_id,
        risk_level="medium" if status == "promotion_failed" else "low",
        payload={
            "decision": decision,
            "status": status,
            "reviewer_ref": reviewer_ref,
            "everos_status": everos_status,
            "review_id": review.id,
        },
    )
    return review


def list_document_memory_reviews(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "document_memory_reviews.jsonl", limit=limit)


def create_source_ref(
    data_dir: Path,
    *,
    source_type: str,
    source_ref: str,
    provider: str,
    title: str,
    url: str = "",
    confidence: str = "medium",
    metadata: dict[str, Any] | None = None,
) -> SourceRef:
    ref = SourceRef(
        id=str(uuid.uuid4()),
        source_type=source_type,
        source_ref=source_ref,
        provider=provider,
        title=title.strip() or source_ref,
        url=url,
        confidence=confidence,
        metadata=metadata or {},
        created_at=utc_now(),
    )
    _append_jsonl(data_dir / "source_refs.jsonl", asdict(ref))
    create_audit_event(
        data_dir,
        "source_ref.created",
        resource_type="source_ref",
        resource_ref=ref.id,
        payload={
            "source_type": ref.source_type,
            "source_ref": ref.source_ref,
            "provider": ref.provider,
            "title": ref.title,
        },
    )
    return ref


def list_source_refs(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "source_refs.jsonl", limit=limit)


def create_document_ingest_report_record(
    data_dir: Path,
    *,
    ingest_id: str,
    title: str,
    path: Path,
    status: str,
    artifact_count: int,
    index_run_count: int,
    candidate_count: int,
    review_count: int,
    source_ref_count: int,
    created_at: str,
) -> DocumentIngestReport:
    report = DocumentIngestReport(
        id=str(uuid.uuid4()),
        ingest_id=ingest_id,
        title=title,
        path=str(path),
        status=status,
        artifact_count=artifact_count,
        index_run_count=index_run_count,
        candidate_count=candidate_count,
        review_count=review_count,
        source_ref_count=source_ref_count,
        created_at=created_at,
    )
    _append_jsonl(data_dir / "document_ingest_reports.jsonl", asdict(report))
    create_audit_event(
        data_dir,
        "document.ingest_report_written",
        resource_type="document_ingest",
        resource_ref=ingest_id,
        payload={
            "report_id": report.id,
            "path": report.path,
            "status": status,
            "artifact_count": artifact_count,
            "index_run_count": index_run_count,
            "candidate_count": candidate_count,
            "review_count": review_count,
            "source_ref_count": source_ref_count,
        },
    )
    return report


def list_document_ingest_reports(data_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(data_dir / "document_ingest_reports.jsonl", limit=limit)


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _classify_artifact(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".json", ".jsonl"}:
        return "json"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff"}:
        return "image"
    if suffix in {".csv", ".tsv", ".xlsx", ".xls"}:
        return "table"
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix in {".txt", ".text"}:
        return "text"
    return "other"


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


def write_obsidian_memory_review_note(
    vault_dir: Path,
    data_dir: Path,
    *,
    candidate: dict[str, Any],
    review: DocumentMemoryReview,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    folder = vault_dir / "00-Inbox" / "everos-candidates"
    folder.mkdir(parents=True, exist_ok=True)
    _ensure_memory_candidate_moc(folder)
    title = f"Document Memory Review {review.id[:8]}"
    filename = f"{now.strftime('%Y%m%d-%H%M%S')}-{_slug(title)}.md"
    path = folder / filename
    ingest_link = f"Document Ingest {str(candidate.get('ingest_id', 'unknown'))[:8]}"
    source_path = str(candidate.get("source_path", ""))
    content = "\n".join(
        [
            "---",
            f"title: {title}",
            "type: document_memory_review",
            f"status: {review.status}",
            f"decision: {review.decision}",
            f"candidate_id: {review.candidate_id}",
            f"review_id: {review.id}",
            f"created_at: {now.isoformat()}",
            "source: hermes",
            "tags:",
            "  - bairui/memory",
            "  - bairui/document",
            "  - hermes/review",
            "---",
            "",
            f"# {title}",
            "",
            "Links: [[Document Memory Candidates]] [[Bairui]] [[Hermes]] [[EverOS]] "
            f"[[{ingest_link}]]",
            "",
            "## Review",
            "",
            f"- Decision: {review.decision}",
            f"- Status: {review.status}",
            f"- Reviewer: {review.reviewer_ref}",
            f"- EverOS status: {review.everos_status or 'not_called'}",
            f"- Source path: `{source_path}`",
            "",
            "## Candidate",
            "",
            str(candidate.get("text", "")).strip(),
            "",
            "## Note",
            "",
            review.note.strip(),
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")
    create_audit_event(
        data_dir,
        "obsidian.memory_review_note_written",
        resource_type="obsidian_memory_review",
        resource_ref=str(path),
        payload={"candidate_id": review.candidate_id, "review_id": review.id, "status": review.status},
    )
    return {"path": str(path), "title": title, "created_at": now.isoformat()}


def write_obsidian_document_ingest_report(
    vault_dir: Path,
    data_dir: Path,
    *,
    ingest: dict[str, Any],
    artifacts: list[dict[str, Any]],
    index_runs: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    source_refs: list[dict[str, Any]],
    audit_events: list[dict[str, Any]],
) -> DocumentIngestReport:
    now = datetime.now(timezone.utc)
    folder = vault_dir / "05_Reports" / "document-ingests"
    folder.mkdir(parents=True, exist_ok=True)
    _ensure_document_ingest_report_moc(folder)

    ingest_id = str(ingest.get("id", "unknown"))
    title = f"Document Ingest {ingest_id[:8]} Report"
    filename = f"{now.strftime('%Y%m%d-%H%M%S')}-{_slug(title)}.md"
    path = folder / filename
    review_note_paths = _memory_review_note_paths(audit_events)
    reviews_by_candidate = {str(review.get("candidate_id", "")): review for review in reviews}

    content = "\n".join(
        [
            "---",
            f"title: {title}",
            "type: document_ingest_report",
            f"ingest_id: {ingest_id}",
            f"created_at: {now.isoformat()}",
            "source: hermes",
            "tags:",
            "  - bairui/document",
            "  - hermes/report",
            "  - hermes/ingest",
            "---",
            "",
            f"# {title}",
            "",
            "Links: [[Document Ingest Reports]] [[Document Memory Candidates]] [[Bairui]] [[Hermes]] "
            "[[MinerU]] [[Sonic]] [[EverOS]] [[Obsidian]]",
            "",
            "## Summary",
            "",
            f"- Input: `{ingest.get('input_path', '')}`",
            f"- Output dir: `{ingest.get('output_dir', '')}`",
            f"- Parser: {ingest.get('parser', '')}",
            f"- Status: {ingest.get('status', '')}",
            f"- Artifacts: {len(artifacts)}",
            f"- Index runs: {len(index_runs)}",
            f"- Memory candidates: {len(candidates)}",
            f"- Memory reviews: {len(reviews)}",
            f"- Source refs: {len(source_refs)}",
            "",
            "## Artifacts",
            "",
            *_artifact_lines(artifacts),
            "",
            "## Index Runs",
            "",
            *_index_run_lines(index_runs),
            "",
            "## Memory Candidates And Reviews",
            "",
            *_candidate_lines(candidates, reviews_by_candidate, review_note_paths),
            "",
            "## Source References",
            "",
            *_source_ref_lines(source_refs),
            "",
            "## Next Actions",
            "",
            *_next_action_lines(candidates, reviews_by_candidate, index_runs, source_refs),
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")
    return create_document_ingest_report_record(
        data_dir,
        ingest_id=ingest_id,
        title=title,
        path=path,
        status="completed",
        artifact_count=len(artifacts),
        index_run_count=len(index_runs),
        candidate_count=len(candidates),
        review_count=len(reviews),
        source_ref_count=len(source_refs),
        created_at=now.isoformat(),
    )


def _ensure_memory_candidate_moc(folder: Path) -> None:
    moc = folder / "Document Memory Candidates.md"
    if moc.exists():
        return
    moc.write_text(
        "\n".join(
            [
                "---",
                "title: Document Memory Candidates",
                "type: moc",
                "source: hermes",
                "tags:",
                "  - bairui/memory",
                "  - hermes/moc",
                "---",
                "",
                "# Document Memory Candidates",
                "",
                "Graph links: [[Bairui]] [[Hermes]] [[EverOS]] [[Obsidian]]",
                "",
                "This note collects reviewed document memory candidates generated by Hermes.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _ensure_document_ingest_report_moc(folder: Path) -> None:
    moc = folder / "Document Ingest Reports.md"
    if moc.exists():
        return
    moc.write_text(
        "\n".join(
            [
                "---",
                "title: Document Ingest Reports",
                "type: moc",
                "source: hermes",
                "tags:",
                "  - bairui/document",
                "  - hermes/moc",
                "---",
                "",
                "# Document Ingest Reports",
                "",
                "Graph links: [[Bairui]] [[Hermes]] [[MinerU]] [[Sonic]] [[EverOS]] [[Obsidian]]",
                "",
                "This note collects Hermes document ingestion reports.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _artifact_lines(artifacts: list[dict[str, Any]]) -> list[str]:
    if not artifacts:
        return ["No registered artifacts yet."]
    lines = ["| Type | Path | Size | SHA256 |", "| --- | --- | ---: | --- |"]
    for artifact in artifacts:
        lines.append(
            "| "
            f"{artifact.get('artifact_type', '')} | "
            f"`{artifact.get('relative_path') or artifact.get('path') or ''}` | "
            f"{artifact.get('size_bytes', 0)} | "
            f"`{str(artifact.get('sha256', ''))[:12]}` |"
        )
    return lines


def _index_run_lines(index_runs: list[dict[str, Any]]) -> list[str]:
    if not index_runs:
        return ["No Sonic index runs recorded yet."]
    lines = ["| Provider | Status | Indexed | Skipped | Failed |", "| --- | --- | ---: | ---: | ---: |"]
    for run in index_runs:
        lines.append(
            "| "
            f"{run.get('provider', '')} | "
            f"{run.get('status', '')} | "
            f"{run.get('indexed_count', 0)} | "
            f"{run.get('skipped_count', 0)} | "
            f"{run.get('failed_count', 0)} |"
        )
    return lines


def _candidate_lines(
    candidates: list[dict[str, Any]],
    reviews_by_candidate: dict[str, dict[str, Any]],
    review_note_paths: dict[str, str],
) -> list[str]:
    if not candidates:
        return ["No memory candidates generated yet."]
    lines: list[str] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("id", ""))
        review = reviews_by_candidate.get(candidate_id, {})
        review_id = str(review.get("id", ""))
        note_path = review_note_paths.get(review_id, "")
        lines.extend(
            [
                f"### Candidate `{candidate_id[:8]}`",
                "",
                f"- Source: `{candidate.get('source_path', '')}`",
                f"- Review status: {review.get('status', 'pending_review')}",
                f"- EverOS status: {review.get('everos_status', 'not_called') or 'not_called'}",
                f"- Review note path: `{note_path}`" if note_path else "- Review note path: not written",
                "",
                str(candidate.get("text", "")).strip()[:600],
                "",
            ]
        )
    return lines


def _source_ref_lines(source_refs: list[dict[str, Any]]) -> list[str]:
    if not source_refs:
        return ["No source references generated yet."]
    lines = ["| Type | Provider | Confidence | Title |", "| --- | --- | --- | --- |"]
    for ref in source_refs:
        lines.append(
            "| "
            f"{ref.get('source_type', '')} | "
            f"{ref.get('provider', '')} | "
            f"{ref.get('confidence', '')} | "
            f"{ref.get('title', '')} |"
        )
    return lines


def _next_action_lines(
    candidates: list[dict[str, Any]],
    reviews_by_candidate: dict[str, dict[str, Any]],
    index_runs: list[dict[str, Any]],
    source_refs: list[dict[str, Any]],
) -> list[str]:
    actions: list[str] = []
    pending = [candidate for candidate in candidates if str(candidate.get("id", "")) not in reviews_by_candidate]
    if pending:
        actions.append(f"- Review {len(pending)} pending memory candidates.")
    if any(run.get("status") not in {"completed", "skipped"} for run in index_runs):
        actions.append("- Inspect failed or partial Sonic index runs.")
    if not source_refs:
        actions.append("- Run `document parse source-refs` for provenance tracking.")
    if not actions:
        actions.append("- No immediate blockers recorded for this ingest.")
    return actions


def _memory_review_note_paths(audit_events: list[dict[str, Any]]) -> dict[str, str]:
    paths: dict[str, str] = {}
    for event in audit_events:
        if event.get("action") != "obsidian.memory_review_note_written":
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        review_id = str(payload.get("review_id", ""))
        if review_id:
            paths[review_id] = str(event.get("resource_ref", ""))
    return paths
