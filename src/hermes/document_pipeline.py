from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .adapters.everos import add_memory as everos_add_memory, build_add_payload as build_everos_add_payload
from .adapters.sonic import SonicResult, build_push_payload as build_sonic_push_payload, push as sonic_push
from .config import Settings
from .storage import (
    DocumentArtifact,
    DocumentIndexRun,
    DocumentIngestRun,
    DocumentMemoryCandidate,
    DocumentMemoryReview,
    SourceRef,
    create_audit_event,
    create_document_artifact,
    create_document_index_run,
    create_document_ingest_run,
    create_document_memory_candidate,
    create_document_memory_review,
    create_source_ref,
    list_document_artifacts,
    list_document_ingests,
    list_document_memory_candidates,
    list_document_memory_reviews,
    list_document_index_runs,
    utc_now,
    write_obsidian_memory_review_note,
)


@dataclass(frozen=True)
class DocumentPipelineResult:
    status: str
    detail: str
    ingest: dict[str, object] | None
    run: DocumentIngestRun | None


@dataclass(frozen=True)
class DocumentArtifactRegistrationResult:
    status: str
    detail: str
    ingest: dict[str, object] | None
    artifacts: tuple[DocumentArtifact, ...]


@dataclass(frozen=True)
class DocumentIndexResult:
    status: str
    detail: str
    ingest: dict[str, object] | None
    run: DocumentIndexRun | None


@dataclass(frozen=True)
class DocumentMemoryCandidateResult:
    status: str
    detail: str
    ingest: dict[str, object] | None
    candidates: tuple[DocumentMemoryCandidate, ...]
    skipped_count: int


@dataclass(frozen=True)
class DocumentMemoryReviewResult:
    status: str
    detail: str
    candidate: dict[str, object] | None
    review: DocumentMemoryReview | None
    obsidian_note: dict[str, object] | None


@dataclass(frozen=True)
class DocumentSourceRefResult:
    status: str
    detail: str
    ingest: dict[str, object] | None
    source_refs: tuple[SourceRef, ...]
    skipped_count: int


def run_document_ingest(data_dir: Path, ingest_id: str, *, timeout_seconds: int) -> DocumentPipelineResult:
    ingest = _find_ingest(data_dir, ingest_id)
    if ingest is None:
        return DocumentPipelineResult(status="not_found", detail=f"document ingest not found: {ingest_id}", ingest=None, run=None)

    command = tuple(str(part) for part in ingest.get("parser_command", ()))
    if not command:
        run = create_document_ingest_run(
            data_dir,
            ingest_id=ingest_id,
            status="failed",
            command=(),
            cwd="",
            exit_code=None,
            error="parser_command is empty",
        )
        return DocumentPipelineResult(status="failed", detail="parser_command is empty", ingest=ingest, run=run)

    cwd = str(Path.cwd())
    started_at = utc_now()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        status = "completed" if completed.returncode == 0 else "failed"
        run = create_document_ingest_run(
            data_dir,
            ingest_id=ingest_id,
            status=status,
            command=command,
            cwd=cwd,
            exit_code=completed.returncode,
            stdout=completed.stdout[-8000:],
            stderr=completed.stderr[-8000:],
            started_at=started_at,
            finished_at=utc_now(),
        )
        return DocumentPipelineResult(status=status, detail=f"command exited with {completed.returncode}", ingest=ingest, run=run)
    except FileNotFoundError as exc:
        error = f"executable not found: {command[0]} ({exc})"
        run = create_document_ingest_run(
            data_dir,
            ingest_id=ingest_id,
            status="failed",
            command=command,
            cwd=cwd,
            exit_code=None,
            error=error,
            started_at=started_at,
            finished_at=utc_now(),
        )
        return DocumentPipelineResult(status="failed", detail="parser executable was not found", ingest=ingest, run=run)
    except subprocess.TimeoutExpired as exc:
        run = create_document_ingest_run(
            data_dir,
            ingest_id=ingest_id,
            status="timeout",
            command=command,
            cwd=cwd,
            exit_code=None,
            stdout=(exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "",
            error=f"command timed out after {timeout_seconds}s",
            started_at=started_at,
            finished_at=utc_now(),
        )
        return DocumentPipelineResult(status="timeout", detail=f"command timed out after {timeout_seconds}s", ingest=ingest, run=run)


def register_document_artifacts(data_dir: Path, ingest_id: str) -> DocumentArtifactRegistrationResult:
    ingest = _find_ingest(data_dir, ingest_id)
    if ingest is None:
        return DocumentArtifactRegistrationResult(
            status="not_found",
            detail=f"document ingest not found: {ingest_id}",
            ingest=None,
            artifacts=(),
        )

    output_dir = Path(str(ingest.get("output_dir", "")))
    if not output_dir.exists():
        create_audit_event(
            data_dir,
            "document.artifact_registration_failed",
            resource_type="document_ingest",
            resource_ref=ingest_id,
            risk_level="medium",
            payload={"reason": "output_dir_not_found", "output_dir": str(output_dir)},
        )
        return DocumentArtifactRegistrationResult(
            status="missing_output",
            detail=f"output_dir does not exist: {output_dir}",
            ingest=ingest,
            artifacts=(),
        )
    if not output_dir.is_dir():
        create_audit_event(
            data_dir,
            "document.artifact_registration_failed",
            resource_type="document_ingest",
            resource_ref=ingest_id,
            risk_level="medium",
            payload={"reason": "output_dir_is_not_directory", "output_dir": str(output_dir)},
        )
        return DocumentArtifactRegistrationResult(
            status="invalid_output",
            detail=f"output_dir is not a directory: {output_dir}",
            ingest=ingest,
            artifacts=(),
        )

    artifacts = tuple(
        create_document_artifact(data_dir, ingest_id=ingest_id, path=path, output_dir=output_dir)
        for path in sorted(output_dir.rglob("*"))
        if path.is_file()
    )
    create_audit_event(
        data_dir,
        "document.artifacts_registered",
        resource_type="document_ingest",
        resource_ref=ingest_id,
        payload={"artifact_count": len(artifacts), "output_dir": str(output_dir)},
    )
    return DocumentArtifactRegistrationResult(
        status="completed",
        detail=f"registered {len(artifacts)} document artifacts",
        ingest=ingest,
        artifacts=artifacts,
    )


def index_document_artifacts(
    settings: Settings,
    ingest_id: str,
    *,
    collection: str = "bairui",
    bucket: str = "documents",
    lang: str = "",
) -> DocumentIndexResult:
    ingest = _find_ingest(settings.data_dir, ingest_id)
    if ingest is None:
        return DocumentIndexResult(status="not_found", detail=f"document ingest not found: {ingest_id}", ingest=None, run=None)

    artifacts = [artifact for artifact in list_document_artifacts(settings.data_dir, limit=1000) if artifact.get("ingest_id") == ingest_id]
    text_artifacts = [artifact for artifact in artifacts if artifact.get("artifact_type") in {"markdown", "text", "json", "html"}]
    skipped_count = len(artifacts) - len(text_artifacts)
    if not text_artifacts:
        run = create_document_index_run(
            settings.data_dir,
            ingest_id=ingest_id,
            status="skipped",
            provider="sonic",
            collection=collection,
            bucket=bucket,
            indexed_count=0,
            skipped_count=skipped_count,
            failed_count=0,
            error="no text artifacts registered for this ingest",
        )
        return DocumentIndexResult(status="skipped", detail="no text artifacts registered for this ingest", ingest=ingest, run=run)

    results: list[dict[str, object]] = []
    indexed_count = 0
    failed_count = 0
    missing_count = 0
    for artifact in text_artifacts:
        path = Path(str(artifact.get("path", "")))
        if not path.exists():
            missing_count += 1
            failed_count += 1
            results.append(
                {
                    "artifact_id": artifact.get("id", ""),
                    "object_id": _artifact_object_id(ingest_id, artifact),
                    "status": "missing_file",
                    "path": str(path),
                }
            )
            continue
        text = _read_indexable_text(path, str(artifact.get("artifact_type", "")))
        result = sonic_push(
            settings,
            build_sonic_push_payload(
                collection=collection,
                bucket=bucket,
                object_id=_artifact_object_id(ingest_id, artifact),
                text=text,
                lang=lang,
            ),
        )
        results.append(_sonic_result_summary(artifact, result))
        if result.status == "completed":
            indexed_count += 1
        else:
            failed_count += 1

    status = "completed" if failed_count == 0 else "failed"
    if indexed_count > 0 and failed_count > 0:
        status = "partial"
    detail = f"indexed {indexed_count} document artifacts into Sonic"
    if failed_count:
        detail += f"; {failed_count} failed"
    run = create_document_index_run(
        settings.data_dir,
        ingest_id=ingest_id,
        status=status,
        provider="sonic",
        collection=collection,
        bucket=bucket,
        indexed_count=indexed_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        results=tuple(results),
        error=f"{missing_count} registered files were missing" if missing_count else "",
    )
    return DocumentIndexResult(status=status, detail=detail, ingest=ingest, run=run)


def generate_document_memory_candidates(
    data_dir: Path,
    ingest_id: str,
    *,
    max_candidates: int = 20,
) -> DocumentMemoryCandidateResult:
    ingest = _find_ingest(data_dir, ingest_id)
    if ingest is None:
        return DocumentMemoryCandidateResult(
            status="not_found",
            detail=f"document ingest not found: {ingest_id}",
            ingest=None,
            candidates=(),
            skipped_count=0,
        )

    artifacts = [artifact for artifact in list_document_artifacts(data_dir, limit=1000) if artifact.get("ingest_id") == ingest_id]
    text_artifacts = [artifact for artifact in artifacts if artifact.get("artifact_type") in {"markdown", "text", "json", "html"}]
    skipped_count = len(artifacts) - len(text_artifacts)
    candidates: list[DocumentMemoryCandidate] = []
    for artifact in text_artifacts:
        if len(candidates) >= max_candidates:
            break
        path = Path(str(artifact.get("path", "")))
        if not path.exists():
            skipped_count += 1
            continue
        for text, reason in _extract_candidate_texts(path, str(artifact.get("artifact_type", ""))):
            if len(candidates) >= max_candidates:
                break
            candidates.append(
                create_document_memory_candidate(
                    data_dir,
                    ingest_id=ingest_id,
                    artifact_id=str(artifact.get("id", "")),
                    source_path=str(artifact.get("relative_path") or artifact.get("path") or ""),
                    candidate_type="document_fact",
                    text=text,
                    confidence=0.55,
                    reason=reason,
                )
            )

    status = "completed" if candidates else "skipped"
    detail = f"generated {len(candidates)} pending memory candidates"
    if not candidates:
        detail = "no suitable document text found for memory candidates"
    create_audit_event(
        data_dir,
        "document.memory_candidates_generated",
        resource_type="document_ingest",
        resource_ref=ingest_id,
        payload={"candidate_count": len(candidates), "skipped_count": skipped_count, "status": status},
    )
    return DocumentMemoryCandidateResult(
        status=status,
        detail=detail,
        ingest=ingest,
        candidates=tuple(candidates),
        skipped_count=skipped_count,
    )


def review_document_memory_candidate(
    settings: Settings,
    candidate_id: str,
    *,
    decision: str,
    reviewer_ref: str = "owner",
    note: str = "",
    user_id: str = "owner",
    session_id: str = "",
    app_id: str = "default",
    project_id: str = "default",
) -> DocumentMemoryReviewResult:
    candidate = _find_memory_candidate(settings.data_dir, candidate_id)
    if candidate is None:
        return DocumentMemoryReviewResult(
            status="not_found",
            detail=f"document memory candidate not found: {candidate_id}",
            candidate=None,
            review=None,
            obsidian_note=None,
        )
    if _latest_memory_review(settings.data_dir, candidate_id) is not None:
        return DocumentMemoryReviewResult(
            status="already_reviewed",
            detail=f"document memory candidate already reviewed: {candidate_id}",
            candidate=candidate,
            review=None,
            obsidian_note=None,
        )

    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"approve", "reject"}:
        return DocumentMemoryReviewResult(
            status="invalid_decision",
            detail="decision must be approve or reject",
            candidate=candidate,
            review=None,
            obsidian_note=None,
        )

    if normalized_decision == "reject":
        review = create_document_memory_review(
            settings.data_dir,
            candidate_id=candidate_id,
            decision="reject",
            status="rejected",
            reviewer_ref=reviewer_ref,
            note=note,
        )
        obsidian_note = write_obsidian_memory_review_note(
            settings.obsidian_vault_dir,
            settings.data_dir,
            candidate=candidate,
            review=review,
        )
        return DocumentMemoryReviewResult(
            status="rejected",
            detail="document memory candidate rejected",
            candidate=candidate,
            review=review,
            obsidian_note=obsidian_note,
        )

    everos_result = everos_add_memory(
        settings,
        build_everos_add_payload(
            user_id=user_id,
            session_id=session_id or f"document-memory-{candidate_id}",
            text=str(candidate.get("text", "")),
            app_id=app_id,
            project_id=project_id,
            sender_name="Hermes Document Memory Review",
        ),
    )
    status = "approved" if everos_result.status == "completed" else "promotion_failed"
    review = create_document_memory_review(
        settings.data_dir,
        candidate_id=candidate_id,
        decision="approve",
        status=status,
        reviewer_ref=reviewer_ref,
        note=note,
        everos_status=everos_result.status,
        everos_endpoint=everos_result.endpoint,
        everos_error=everos_result.error,
    )
    detail = "document memory candidate approved and sent to EverOS"
    if status == "promotion_failed":
        detail = "document memory candidate approval could not be promoted to EverOS"
    obsidian_note = write_obsidian_memory_review_note(
        settings.obsidian_vault_dir,
        settings.data_dir,
        candidate=candidate,
        review=review,
    )
    return DocumentMemoryReviewResult(status=status, detail=detail, candidate=candidate, review=review, obsidian_note=obsidian_note)


def create_document_source_refs(settings: Settings, ingest_id: str) -> DocumentSourceRefResult:
    ingest = _find_ingest(settings.data_dir, ingest_id)
    if ingest is None:
        return DocumentSourceRefResult(
            status="not_found",
            detail=f"document ingest not found: {ingest_id}",
            ingest=None,
            source_refs=(),
            skipped_count=0,
        )

    artifacts = [artifact for artifact in list_document_artifacts(settings.data_dir, limit=1000) if artifact.get("ingest_id") == ingest_id]
    index_runs = [run for run in list_document_index_runs(settings.data_dir, limit=1000) if run.get("ingest_id") == ingest_id]
    candidates = [candidate for candidate in list_document_memory_candidates(settings.data_dir, limit=1000) if candidate.get("ingest_id") == ingest_id]
    reviews = list_document_memory_reviews(settings.data_dir, limit=1000)
    reviews_by_candidate = {str(review.get("candidate_id", "")): review for review in reviews}

    refs: list[SourceRef] = []
    for artifact in artifacts:
        refs.append(
            create_source_ref(
                settings.data_dir,
                source_type="document_artifact",
                source_ref=str(artifact.get("id", "")),
                provider="mineru",
                title=str(artifact.get("relative_path") or artifact.get("path") or "Document artifact"),
                url=str(artifact.get("path", "")),
                confidence="high",
                metadata={
                    "ingest_id": ingest_id,
                    "artifact_type": artifact.get("artifact_type", ""),
                    "mime_type": artifact.get("mime_type", ""),
                    "sha256": artifact.get("sha256", ""),
                    "size_bytes": artifact.get("size_bytes", 0),
                },
            )
        )

    for run in index_runs:
        refs.append(
            create_source_ref(
                settings.data_dir,
                source_type="document_index_run",
                source_ref=str(run.get("id", "")),
                provider=str(run.get("provider", "sonic")),
                title=f"Sonic index run for {ingest_id[:8]}",
                confidence="medium" if run.get("status") not in {"completed", "skipped"} else "high",
                metadata={
                    "ingest_id": ingest_id,
                    "status": run.get("status", ""),
                    "collection": run.get("collection", ""),
                    "bucket": run.get("bucket", ""),
                    "indexed_count": run.get("indexed_count", 0),
                    "skipped_count": run.get("skipped_count", 0),
                    "failed_count": run.get("failed_count", 0),
                },
            )
        )

    for candidate in candidates:
        review = reviews_by_candidate.get(str(candidate.get("id", "")))
        refs.append(
            create_source_ref(
                settings.data_dir,
                source_type="document_memory_candidate",
                source_ref=str(candidate.get("id", "")),
                provider="hermes",
                title=f"Memory candidate from {candidate.get('source_path', 'document')}",
                confidence="medium",
                metadata={
                    "ingest_id": ingest_id,
                    "artifact_id": candidate.get("artifact_id", ""),
                    "candidate_status": candidate.get("status", ""),
                    "review_status": review.get("status", "pending_review") if review else "pending_review",
                    "review_id": review.get("id", "") if review else "",
                    "everos_status": review.get("everos_status", "") if review else "",
                },
            )
        )

    status = "completed" if refs else "skipped"
    detail = f"created {len(refs)} source references"
    if not refs:
        detail = "no document artifacts, index runs, or memory candidates found for source refs"
    create_audit_event(
        settings.data_dir,
        "document.source_refs_created",
        resource_type="document_ingest",
        resource_ref=ingest_id,
        payload={"source_ref_count": len(refs), "status": status},
    )
    return DocumentSourceRefResult(status=status, detail=detail, ingest=ingest, source_refs=tuple(refs), skipped_count=0)


def _find_ingest(data_dir: Path, ingest_id: str) -> dict[str, object] | None:
    for ingest in reversed(list_document_ingests(data_dir, limit=1000)):
        if ingest.get("id") == ingest_id:
            return ingest
    return None


def _artifact_object_id(ingest_id: str, artifact: dict[str, object]) -> str:
    artifact_id = str(artifact.get("id", "artifact"))
    return f"document:{ingest_id}:{artifact_id}"


def _read_indexable_text(path: Path, artifact_type: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if artifact_type == "json":
        return " ".join(text.split())
    return text


def _sonic_result_summary(artifact: dict[str, object], result: SonicResult) -> dict[str, object]:
    return {
        "artifact_id": artifact.get("id", ""),
        "relative_path": artifact.get("relative_path", ""),
        "artifact_type": artifact.get("artifact_type", ""),
        "object_id": _artifact_object_id(str(artifact.get("ingest_id", "")), artifact),
        "status": result.status,
        "error": result.error,
    }


def _extract_candidate_texts(path: Path, artifact_type: str) -> list[tuple[str, str]]:
    text = _read_indexable_text(path, artifact_type)
    chunks: list[tuple[str, str]] = []
    for paragraph in _split_candidate_paragraphs(text):
        normalized = " ".join(paragraph.split())
        if _looks_like_memory_candidate(normalized):
            chunks.append((normalized[:1200], "document paragraph contains durable factual context"))
        if len(chunks) >= 5:
            break
    return chunks


def _split_candidate_paragraphs(text: str) -> list[str]:
    paragraphs = re.split(r"\n\s*\n|(?<=[。！？.!?])\s+", text)
    return [paragraph.strip(" \t\r\n#-*`>") for paragraph in paragraphs if paragraph.strip()]


def _looks_like_memory_candidate(text: str) -> bool:
    if len(text) < 20:
        return False
    if len(text) > 4000:
        return False
    lowered = text.lower()
    durable_markers = (
        "owner",
        "用户",
        "主人",
        "偏好",
        "要求",
        "规则",
        "配置",
        "项目",
        "bairui",
        "hermes",
        "moxi",
        "everos",
        "postgresql",
        "sonic",
        "mineru",
    )
    return any(marker in lowered or marker in text for marker in durable_markers)


def _find_memory_candidate(data_dir: Path, candidate_id: str) -> dict[str, object] | None:
    for candidate in reversed(list_document_memory_candidates(data_dir, limit=1000)):
        if candidate.get("id") == candidate_id:
            return candidate
    return None


def _latest_memory_review(data_dir: Path, candidate_id: str) -> dict[str, object] | None:
    for review in reversed(list_document_memory_reviews(data_dir, limit=1000)):
        if review.get("candidate_id") == candidate_id:
            return review
    return None
