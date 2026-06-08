"""In-memory async job state for slow social-agent work."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import threading
import uuid
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStatus(str, Enum):
    QUEUED = "queued"
    ACKNOWLEDGED = "acknowledged"
    RUNNING = "running"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    FAILED = "failed"
    FAILURE_DELIVERED = "failure_delivered"
    CANCELLED = "cancelled"


ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.QUEUED: {JobStatus.ACKNOWLEDGED, JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.ACKNOWLEDGED: {JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.RUNNING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.COMPLETED: {JobStatus.DELIVERED},
    JobStatus.FAILED: {JobStatus.FAILURE_DELIVERED},
    JobStatus.DELIVERED: set(),
    JobStatus.FAILURE_DELIVERED: set(),
    JobStatus.CANCELLED: set(),
}


@dataclass
class AsyncJob:
    job_id: str
    route: str
    channel: str
    target_id: str
    input_preview_chars: int
    tool_name: str
    status: str = JobStatus.QUEUED.value
    owner_confirmation_required: bool = False
    result_pointer: str = ""
    error_message: str = ""
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    started_at: str = ""
    completed_at: str = ""


class AsyncJobStore:
    """Small process-local job store used by connectors and diagnostics.

    It intentionally stores only previews and result pointers. Message bodies,
    tool outputs, screenshots, API responses, and credentials must stay outside
    this store.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, AsyncJob] = {}

    def create(
        self,
        *,
        route: str,
        channel: str,
        target_id: str,
        input_text: str,
        tool_name: str,
        owner_confirmation_required: bool = False,
    ) -> AsyncJob:
        job = AsyncJob(
            job_id=uuid.uuid4().hex,
            route=_clean_token(route, "unknown"),
            channel=_clean_token(channel, "unknown"),
            target_id=_clean_token(target_id, "unknown"),
            input_preview_chars=min(len(str(input_text or "")), 160),
            tool_name=_clean_token(tool_name, "unknown"),
            owner_confirmation_required=bool(owner_confirmation_required),
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def transition(
        self,
        job_id: str,
        status: str,
        *,
        result_pointer: str = "",
        error_message: str = "",
    ) -> AsyncJob:
        try:
            next_status = JobStatus(status)
        except ValueError as error:
            raise ValueError("invalid job status") from error

        with self._lock:
            job = self._jobs.get(str(job_id or ""))
            if job is None:
                raise ValueError("job not found")
            current = JobStatus(job.status)
            if next_status not in ALLOWED_TRANSITIONS[current]:
                raise ValueError(f"invalid transition: {current.value}->{next_status.value}")

            now = utc_now()
            job.status = next_status.value
            job.updated_at = now
            if next_status == JobStatus.RUNNING and not job.started_at:
                job.started_at = now
            if next_status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
                job.completed_at = now
            if result_pointer:
                job.result_pointer = _clean_pointer(result_pointer)
            if error_message:
                job.error_message = _clean_error(error_message)
            return job

    def list(self, limit: int = 50) -> list[AsyncJob]:
        safe_limit = max(1, min(int(limit or 50), 200))
        with self._lock:
            return list(self._jobs.values())[-safe_limit:]

    def get(self, job_id: str) -> AsyncJob | None:
        with self._lock:
            return self._jobs.get(str(job_id or ""))


def jobs_payload(store: AsyncJobStore, limit: int = 50) -> dict[str, Any]:
    return {
        "status": "ok",
        "jobs": [asdict(job) for job in store.list(limit)],
        "allowed_statuses": [status.value for status in JobStatus],
        "privacy": "stores metadata, previews, and result pointers only",
    }


def _clean_token(value: str, default: str) -> str:
    text = str(value or "").strip()
    if not text:
        return default
    return "".join(ch for ch in text[:80] if ch.isalnum() or ch in {"_", "-", ".", ":"})


def _clean_pointer(value: str) -> str:
    return str(value or "").strip()[:240]


def _clean_error(value: str) -> str:
    return str(value or "").strip()[:240]
