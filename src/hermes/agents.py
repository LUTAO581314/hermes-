from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .model_gateway import ChatResult, complete_chat
from .storage import (
    create_audit_event,
    create_channel_approval_request,
    create_document_memory_candidate,
    create_job,
    create_report_record,
    utc_now,
)


@dataclass(frozen=True)
class AgentProfile:
    id: str
    display_name: str
    role: str
    model: str
    permission: str
    status: str
    disabled_reason: str
    avatar_initials: str
    tools: tuple[str, ...]


@dataclass(frozen=True)
class AgentSession:
    id: str
    title: str
    agent_ids: tuple[str, ...]
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AgentEvent:
    id: str
    session_id: str
    agent_id: str
    type: str
    status: str
    role: str
    model: str
    permission: str
    content: str
    error: str
    created_at: str


@dataclass(frozen=True)
class AgentPromotion:
    id: str
    event_id: str
    session_id: str
    agent_id: str
    target: str
    resource_type: str
    resource_id: str
    resource_status: str
    review_required: bool
    source: dict[str, Any]
    created_at: str


def as_payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return dict(value)


def list_agents(settings: Settings) -> tuple[AgentProfile, ...]:
    model_status = "ready" if settings.has_model_gateway else "missing_config"
    model_name = settings.model_name or "model-unconfigured"
    disabled_reason = "" if settings.has_model_gateway else "model_gateway_missing_config"
    return (
        AgentProfile("coordinator", "Coordinator", "coordinator", model_name, "draft", model_status, disabled_reason, "co", ("chat", "jobs")),
        AgentProfile("research", "Research", "research", model_name, "read_only", model_status, disabled_reason, "rs", ("search", "codegraph")),
        AgentProfile("document", "Document", "document", model_name, "draft", model_status, disabled_reason, "do", ("document_ingest", "reports")),
        AgentProfile("memory", "Memory", "memory", model_name, "approval_required", "approval_required", "", "me", ("memory_review",)),
        AgentProfile("channel", "Channel", "channel", model_name, "approval_required", "approval_required", "", "ch", ("channel_approval",)),
        AgentProfile("operator", "Operator", "operations", model_name, "read_only", "ready", "", "op", ("readiness", "audit", "events")),
    )


def get_agent(settings: Settings, agent_id: str) -> AgentProfile | None:
    return next((agent for agent in list_agents(settings) if agent.id == agent_id), None)


def create_agent_session(settings: Settings, title: str, agent_ids: tuple[str, ...]) -> AgentSession:
    valid_ids = {agent.id for agent in list_agents(settings)}
    selected = tuple(agent_id for agent_id in agent_ids if agent_id in valid_ids) or ("coordinator",)
    now = utc_now()
    session = AgentSession(
        id=str(uuid.uuid4()),
        title=title.strip() or "bairui command session",
        agent_ids=selected,
        status="active",
        created_at=now,
        updated_at=now,
    )
    _append_jsonl(_sessions_path(settings), asdict(session))
    create_audit_event(
        settings.data_dir,
        "agent.session_created",
        resource_type="agent_session",
        resource_ref=session.id,
        payload={"agent_ids": selected, "title": session.title},
    )
    return session


def list_agent_sessions(settings: Settings, limit: int = 50) -> list[dict[str, Any]]:
    return _read_jsonl(_sessions_path(settings), limit=limit)


def update_agent_session(settings: Settings, session_id: str, *, title: str) -> dict[str, Any]:
    title = title.strip()
    if not title:
        return {"status": "invalid_request", "detail": "title is required", "session": None}
    sessions = _read_jsonl(_sessions_path(settings), limit=10000)
    updated: dict[str, Any] | None = None
    now = utc_now()
    for session in sessions:
        if session.get("id") == session_id:
            session["title"] = title
            session["updated_at"] = now
            updated = session
            break
    if updated is None:
        return {"status": "not_found", "detail": f"agent session not found: {session_id}", "session": None}
    _write_jsonl(_sessions_path(settings), sessions)
    create_audit_event(
        settings.data_dir,
        "agent.session_updated",
        resource_type="agent_session",
        resource_ref=session_id,
        payload={"title": title},
    )
    return {"status": "completed", "detail": "agent session updated", "session": updated}


def add_agent_user_message(settings: Settings, session_id: str, content: str) -> dict[str, Any]:
    if not content.strip():
        return {"status": "invalid_request", "detail": "content is required", "event": None}
    if _find_session(settings, session_id) is None:
        return {"status": "not_found", "detail": f"agent session not found: {session_id}", "event": None}
    event = _create_event(
        settings,
        session_id=session_id,
        agent_id="owner",
        event_type="user_message",
        status="completed",
        role="owner",
        model="",
        permission="owner",
        content=content,
        error="",
    )
    return {"status": "completed", "detail": "user message recorded", "event": asdict(event)}


def run_agent_round(settings: Settings, session_id: str, prompt: str) -> dict[str, Any]:
    session = _find_session(settings, session_id)
    if session is None:
        return {"status": "not_found", "detail": f"agent session not found: {session_id}", "events": ()}
    if not prompt.strip():
        return {"status": "invalid_request", "detail": "prompt is required", "events": ()}

    events: list[AgentEvent] = []
    for agent_id in tuple(session.get("agent_ids", ("coordinator",))):
        agent = get_agent(settings, str(agent_id))
        if agent is None:
            continue
        if agent.permission == "approval_required":
            events.append(
                _create_event(
                    settings,
                    session_id=session_id,
                    agent_id=agent.id,
                    event_type="agent_notice",
                    status="approval_required",
                    role=agent.role,
                    model=agent.model,
                    permission=agent.permission,
                    content=f"{agent.display_name} can draft review items, but execution must happen in the dedicated approval screen.",
                    error="",
                )
            )
            continue
        if not settings.has_model_gateway and agent.role not in {"operations"}:
            events.append(
                _create_event(
                    settings,
                    session_id=session_id,
                    agent_id=agent.id,
                    event_type="agent_message",
                    status="missing_config",
                    role=agent.role,
                    model=agent.model,
                    permission=agent.permission,
                    content="",
                    error="model_gateway_missing_config",
                )
            )
            continue
        result = _agent_reply(settings, agent, prompt)
        events.append(
            _create_event(
                settings,
                session_id=session_id,
                agent_id=agent.id,
                event_type="agent_message",
                status=result.status,
                role=agent.role,
                model=agent.model,
                permission=agent.permission,
                content=result.content,
                error=result.error,
            )
        )
    status = "completed" if any(event.status == "completed" for event in events) else "partial"
    create_audit_event(
        settings.data_dir,
        "agent.round_completed",
        resource_type="agent_session",
        resource_ref=session_id,
        payload={"event_count": len(events), "status": status},
    )
    return {"status": status, "detail": f"{len(events)} agent events recorded", "events": tuple(asdict(event) for event in events)}


def list_agent_events(settings: Settings, session_id: str = "", limit: int = 100) -> list[dict[str, Any]]:
    events = _read_jsonl(_events_path(settings), limit=1000)
    if session_id:
        events = [event for event in events if event.get("session_id") == session_id]
    return events[-limit:]


def list_agent_events_page(settings: Settings, session_id: str = "", *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    events = _read_jsonl(_events_path(settings), limit=10000)
    if session_id:
        events = [event for event in events if event.get("session_id") == session_id]
    total = len(events)
    page = events[offset : offset + limit]
    return {
        "status": "completed",
        "events": page,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "next_offset": offset + limit if offset + limit < total else None,
            "previous_offset": max(0, offset - limit) if offset > 0 else None,
        },
    }


def retry_agent_event(settings: Settings, event_id: str) -> dict[str, Any]:
    event = next((item for item in list_agent_events(settings, limit=1000) if item.get("id") == event_id), None)
    if event is None:
        return {"status": "not_found", "detail": f"agent event not found: {event_id}", "event": None}
    retryable = {"failed", "missing_config", "blocked"}
    if event.get("status") not in retryable:
        return {"status": "not_retryable", "detail": "only failed, missing_config, or blocked agent events can be retried", "event": None}
    session = _find_session(settings, str(event.get("session_id", "")))
    if session is None:
        return {"status": "not_found", "detail": f"agent session not found: {event.get('session_id', '')}", "event": None}
    agent = get_agent(settings, str(event.get("agent_id", "")))
    if agent is None or agent.id == "owner":
        return {"status": "not_retryable", "detail": "event has no retryable agent", "event": None}

    prompt = _latest_owner_prompt(settings, str(event.get("session_id", ""))) or _event_text(event) or "Retry the previous agent task."
    if agent.permission == "approval_required":
        retried = _create_event(
            settings,
            session_id=str(event.get("session_id", "")),
            agent_id=agent.id,
            event_type="agent_retry",
            status="approval_required",
            role=agent.role,
            model=agent.model,
            permission=agent.permission,
            content=f"{agent.display_name} retry still requires owner approval in the dedicated review screen.",
            error="",
        )
    elif not settings.has_model_gateway and agent.role not in {"operations"}:
        retried = _create_event(
            settings,
            session_id=str(event.get("session_id", "")),
            agent_id=agent.id,
            event_type="agent_retry",
            status="missing_config",
            role=agent.role,
            model=agent.model,
            permission=agent.permission,
            content="",
            error="model_gateway_missing_config",
        )
    else:
        result = _agent_reply(settings, agent, prompt)
        retried = _create_event(
            settings,
            session_id=str(event.get("session_id", "")),
            agent_id=agent.id,
            event_type="agent_retry",
            status=result.status,
            role=agent.role,
            model=agent.model,
            permission=agent.permission,
            content=result.content,
            error=result.error,
        )
    create_audit_event(
        settings.data_dir,
        "agent.event_retried",
        resource_type="agent_event",
        resource_ref=event_id,
        payload={"new_event_id": retried.id, "status": retried.status, "will_execute_external_action": False},
    )
    return {
        "status": "completed" if retried.status == "completed" else "partial",
        "detail": "agent retry recorded",
        "event": asdict(retried),
        "will_execute_external_action": False,
    }


def promote_agent_event(settings: Settings, event_id: str, target: str) -> dict[str, Any]:
    event = next((item for item in list_agent_events(settings, limit=1000) if item.get("id") == event_id), None)
    if event is None:
        return {"status": "not_found", "detail": f"agent event not found: {event_id}"}
    if target not in {"job", "report", "memory_review", "channel_draft"}:
        return {"status": "invalid_target", "detail": "target must be job, report, memory_review, or channel_draft"}
    if not _event_text(event).strip():
        return {"status": "invalid_request", "detail": "agent event has no promotable content"}

    existing = _find_promotion(settings, event_id, target)
    if existing is not None:
        created = _resource_from_promotion(existing)
        create_audit_event(
            settings.data_dir,
            "agent.event_promotion_reused",
            resource_type=created["type"],
            resource_ref=str(created["id"]),
            risk_level="medium" if target in {"memory_review", "channel_draft"} else "low",
            payload={
                "target": target,
                "event_id": event_id,
                "promotion_id": existing.get("id", ""),
                "will_execute_external_action": False,
                "duplicate": True,
            },
        )
        return {
            "status": "duplicate",
            "detail": f"promotion to {target} already exists",
            "target": target,
            "promotion_id": existing.get("id", ""),
            "created_resource": created,
            "will_execute_external_action": False,
            "duplicate": True,
        }

    created = _create_promotion_resource(settings, event, target)
    promotion = _record_promotion(settings, event, target, created)
    create_audit_event(
        settings.data_dir,
        "agent.event_promoted",
        resource_type=created["type"],
        resource_ref=str(created["id"]),
        risk_level="medium" if target in {"memory_review", "channel_draft"} else "low",
        payload={
            "target": target,
            "event_id": event_id,
            "promotion_id": promotion.id,
            "source": created.get("source", {}),
            "will_execute_external_action": False,
            "duplicate": False,
        },
    )
    return {
        "status": "planned",
        "detail": f"promotion to {target} recorded for owner review",
        "target": target,
        "promotion_id": promotion.id,
        "created_resource": created,
        "will_execute_external_action": False,
        "duplicate": False,
    }


def _agent_reply(settings: Settings, agent: AgentProfile, prompt: str) -> ChatResult:
    if agent.role == "operations":
        return ChatResult(
            status="completed",
            content="Runtime operations can inspect readiness, audit, events, and blocked states. No external action was executed.",
            model=agent.model,
            provider="local",
        )
    system = f"You are the bairui {agent.role} agent. Permission: {agent.permission}. Do not claim external actions were executed."
    return complete_chat(settings, prompt, system=system)


def _create_promotion_resource(settings: Settings, event: dict[str, Any], target: str) -> dict[str, Any]:
    content = _event_text(event)
    event_id = str(event.get("id", ""))
    agent_id = str(event.get("agent_id", "agent"))
    role = str(event.get("role", agent_id))
    title = f"Agent {role} {target.replace('_', ' ')}"
    source = _promotion_source(event, target)
    if target == "job":
        job = create_job(settings.data_dir, title=title, prompt=_promotion_body(event), route=role or "general")
        return {"type": "job", "id": job.id, "status": job.status, "path": "", "review_required": False, "source": source}
    if target == "report":
        report = create_report_record(
            settings.data_dir,
            title=title,
            body=_promotion_body(event),
            source_type="agent_event",
            source_ref=event_id,
            status="draft",
        )
        return {"type": "report", "id": report.id, "status": report.status, "path": report.path, "review_required": False, "source": source}
    if target == "memory_review":
        candidate = create_document_memory_candidate(
            settings.data_dir,
            ingest_id=f"agent-session-{str(event.get('session_id', 'unknown'))[:8]}",
            artifact_id=event_id,
            source_path=f"agent_event:{event_id}",
            candidate_type="agent_event",
            text=content,
            confidence=0.5,
            reason="agent_event_promotion_requires_owner_review",
        )
        return {"type": "document_memory_candidate", "id": candidate.id, "status": candidate.status, "path": "", "review_required": True, "source": source}
    approval = create_channel_approval_request(
        settings.data_dir,
        target_id="owner_review",
        channel_type="personal_chat",
        media_kind="text",
        message_preview=content[:160],
        reason="agent_event_channel_draft_requires_owner_review",
    )
    return {"type": "channel_approval_request", "id": approval.id, "status": approval.status, "path": "", "review_required": True, "source": source}


def _promotion_source(event: dict[str, Any], target: str) -> dict[str, Any]:
    return {
        "source_type": "agent_event",
        "source_ref": str(event.get("id", "")),
        "session_id": str(event.get("session_id", "")),
        "agent_id": str(event.get("agent_id", "")),
        "role": str(event.get("role", "")),
        "target": target,
        "status": str(event.get("status", "")),
    }


def _record_promotion(settings: Settings, event: dict[str, Any], target: str, created: dict[str, Any]) -> AgentPromotion:
    promotion = AgentPromotion(
        id=str(uuid.uuid4()),
        event_id=str(event.get("id", "")),
        session_id=str(event.get("session_id", "")),
        agent_id=str(event.get("agent_id", "")),
        target=target,
        resource_type=str(created.get("type", "")),
        resource_id=str(created.get("id", "")),
        resource_status=str(created.get("status", "")),
        review_required=bool(created.get("review_required", False)),
        source=dict(created.get("source", {})),
        created_at=utc_now(),
    )
    _append_jsonl(_promotions_path(settings), asdict(promotion))
    return promotion


def _find_promotion(settings: Settings, event_id: str, target: str) -> dict[str, Any] | None:
    return next(
        (
            promotion
            for promotion in _read_jsonl(_promotions_path(settings), limit=10000)
            if promotion.get("event_id") == event_id and promotion.get("target") == target
        ),
        None,
    )


def _resource_from_promotion(promotion: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": promotion.get("resource_type", ""),
        "id": promotion.get("resource_id", ""),
        "status": promotion.get("resource_status", ""),
        "path": "",
        "review_required": bool(promotion.get("review_required", False)),
        "source": promotion.get("source", {}),
    }


def _event_text(event: dict[str, Any]) -> str:
    return str(event.get("content") or event.get("error") or "").strip()


def _promotion_body(event: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Source event: {event.get('id', '')}",
            f"Session: {event.get('session_id', '')}",
            f"Agent: {event.get('agent_id', '')}",
            f"Role: {event.get('role', '')}",
            f"Status: {event.get('status', '')}",
            "",
            _event_text(event),
        ]
    )


def _create_event(
    settings: Settings,
    *,
    session_id: str,
    agent_id: str,
    event_type: str,
    status: str,
    role: str,
    model: str,
    permission: str,
    content: str,
    error: str,
) -> AgentEvent:
    event = AgentEvent(
        id=str(uuid.uuid4()),
        session_id=session_id,
        agent_id=agent_id,
        type=event_type,
        status=status,
        role=role,
        model=model,
        permission=permission,
        content=content,
        error=error,
        created_at=utc_now(),
    )
    _append_jsonl(_events_path(settings), asdict(event))
    return event


def _find_session(settings: Settings, session_id: str) -> dict[str, Any] | None:
    return next((session for session in list_agent_sessions(settings, limit=1000) if session.get("id") == session_id), None)


def _latest_owner_prompt(settings: Settings, session_id: str) -> str:
    events = list_agent_events(settings, session_id=session_id, limit=1000)
    for event in reversed(events):
        if event.get("agent_id") == "owner" and event.get("content"):
            return str(event.get("content", ""))
    return ""


def _sessions_path(settings: Settings) -> Path:
    return settings.data_dir / "agents" / "sessions.jsonl"


def _events_path(settings: Settings) -> Path:
    return settings.data_dir / "agents" / "events.jsonl"


def _promotions_path(settings: Settings) -> Path:
    return settings.data_dir / "agents" / "promotions.jsonl"


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _read_jsonl(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows[-limit:]
