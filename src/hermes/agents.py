from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .model_gateway import ChatResult, complete_chat
from .storage import create_audit_event, utc_now


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


def promote_agent_event(settings: Settings, event_id: str, target: str) -> dict[str, Any]:
    event = next((item for item in list_agent_events(settings, limit=1000) if item.get("id") == event_id), None)
    if event is None:
        return {"status": "not_found", "detail": f"agent event not found: {event_id}"}
    if target not in {"job", "report", "memory_review", "channel_draft"}:
        return {"status": "invalid_target", "detail": "target must be job, report, memory_review, or channel_draft"}
    create_audit_event(
        settings.data_dir,
        "agent.event_promotion_planned",
        resource_type="agent_event",
        resource_ref=event_id,
        risk_level="medium" if target in {"memory_review", "channel_draft"} else "low",
        payload={"target": target, "will_execute_external_action": False},
    )
    return {"status": "planned", "detail": f"promotion to {target} recorded for owner review", "target": target, "will_execute_external_action": False}


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


def _sessions_path(settings: Settings) -> Path:
    return settings.data_dir / "agents" / "sessions.jsonl"


def _events_path(settings: Settings) -> Path:
    return settings.data_dir / "agents" / "events.jsonl"


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _read_jsonl(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows[-limit:]
