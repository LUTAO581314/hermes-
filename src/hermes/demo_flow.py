from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agents import create_agent_session, list_agent_events, promote_agent_event, run_agent_round
from .channels import list_channel_approvals, plan_channel_send, review_channel_approval
from .codegraph import codegraph_impact, codegraph_overview, query_codegraph, register_codegraph_repo, scan_codegraph_repo
from .config import Settings
from .demo import seed_demo_data
from .document_pipeline import review_document_memory_candidate
from .storage import (
    create_audit_event,
    list_channel_approval_reviews,
    list_document_memory_candidates,
    list_document_memory_reviews,
    list_reports,
)


def run_demo_flow(settings: Settings, *, workspace: str = "", force_seed: bool = False) -> dict[str, Any]:
    """Run a local product walkthrough using real product contracts.

    The flow intentionally keeps risky operations as records only:
    no external channel send and no automatic long-term memory write.
    """

    seed = seed_demo_data(settings, force=force_seed)
    session = create_agent_session(settings, "Demo product closure", ("operator", "channel", "memory"))
    round_result = run_agent_round(settings, session.id, "Prepare a safe customer onboarding walkthrough.")
    events = list_agent_events(settings, session_id=session.id)
    operator_event = next((event for event in reversed(events) if event.get("agent_id") == "operator"), None)
    channel_notice = next((event for event in reversed(events) if event.get("agent_id") == "channel"), None)
    memory_notice = next((event for event in reversed(events) if event.get("agent_id") == "memory"), None)

    report_promotion = promote_agent_event(settings, str(operator_event.get("id", "")), "report") if operator_event else {"status": "not_found"}
    memory_promotion = promote_agent_event(settings, str(memory_notice.get("id", "")), "memory_review") if memory_notice else {"status": "not_found"}
    channel_promotion = promote_agent_event(settings, str(channel_notice.get("id", "")), "channel_draft") if channel_notice else {"status": "not_found"}

    channel_plan = plan_channel_send(
        settings,
        {
            "target_id": "owner_review",
            "media_kind": "text",
            "text": "Demo draft: confirm customer onboarding scope after owner review.",
        },
    )
    channel_review = (
        review_channel_approval(
            settings,
            {
                "request_id": channel_plan.approval_request_id,
                "decision": "reject",
                "reviewer_ref": "owner",
                "note": "Demo flow records review only; no external send.",
            },
        )
        if channel_plan.approval_request_id
        else None
    )

    memory_candidates = list_document_memory_candidates(settings.data_dir, limit=200)
    pending_candidate = next((item for item in reversed(memory_candidates) if item.get("status") == "pending_review"), None)
    memory_review = (
        review_document_memory_candidate(
            settings,
            str(pending_candidate.get("id", "")),
            decision="reject",
            reviewer_ref="owner",
            note="Demo flow rejects memory candidate; no long-term memory write.",
        )
        if pending_candidate
        else None
    )

    codegraph = _run_codegraph_demo(settings, workspace)
    reports = list_reports(settings.data_dir, limit=100)
    approvals = list_channel_approvals(settings)
    reviews = list_channel_approval_reviews(settings.data_dir, limit=100)
    memory_reviews = list_document_memory_reviews(settings.data_dir, limit=100)
    marker = create_audit_event(
        settings.data_dir,
        "demo.flow_completed",
        resource_type="demo_flow",
        resource_ref=session.id,
        payload={
            "will_send": False,
            "will_write_long_term_memory": False,
            "session_id": session.id,
            "report_promotion_status": report_promotion.get("status"),
            "channel_plan_status": channel_plan.status,
            "codegraph_status": codegraph.get("scan", {}).get("status", codegraph.get("status")),
        },
    )

    checkpoints = {
        "command_session": round_result.get("status") in {"completed", "partial"},
        "report_created": report_promotion.get("status") in {"planned", "duplicate"} and bool(reports),
        "channel_review_recorded": channel_review is not None and channel_review.status == "reviewed" and not channel_review.will_send,
        "memory_review_recorded": memory_review is not None and memory_review.status in {"rejected", "already_reviewed"},
        "codegraph_query_ready": codegraph.get("query", {}).get("status") == "completed",
        "no_external_send": channel_plan.will_send is False and (channel_review is None or channel_review.will_send is False),
        "no_auto_memory_write": True,
    }
    status = "completed" if all(checkpoints.values()) else "partial"
    return {
        "status": status,
        "checkpoints": checkpoints,
        "session": asdict(session),
        "agent_round": round_result,
        "promotions": {
            "report": report_promotion,
            "memory_review": memory_promotion,
            "channel_draft": channel_promotion,
        },
        "channel": {
            "plan": asdict(channel_plan),
            "review": asdict(channel_review) if channel_review else None,
            "approval_count": len(approvals),
            "review_count": len(reviews),
        },
        "memory": {
            "candidate_id": pending_candidate.get("id", "") if pending_candidate else "",
            "review": _memory_review_payload(memory_review),
            "review_count": len(memory_reviews),
            "will_write_long_term_memory": False,
        },
        "reports": {"count": len(reports), "latest": reports[-1] if reports else None},
        "codegraph": codegraph,
        "audit_marker": asdict(marker),
        "seed": seed,
    }


def _run_codegraph_demo(settings: Settings, workspace: str) -> dict[str, Any]:
    root = Path(workspace).expanduser().resolve() if workspace else settings.data_dir / "demo-flow-code"
    root.mkdir(parents=True, exist_ok=True)
    sample = root / "demo_agent.py"
    if not sample.exists():
        sample.write_text(
            "\n".join(
                [
                    "class DemoAgent:",
                    "    def plan(self):",
                    "        return 'owner reviewed workflow'",
                    "",
                    "def demo_flow_entry():",
                    "    return DemoAgent().plan()",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    repo = register_codegraph_repo(settings, str(root), name="bairui-demo-flow")
    scan = scan_codegraph_repo(settings, repo.id)
    overview = codegraph_overview(settings, repo_id=repo.id)
    query = query_codegraph(settings, "demo_flow_entry", repo_id=repo.id)
    impact = codegraph_impact(settings, "demo_agent.py", repo_id=repo.id)
    return {
        "status": "completed" if scan.get("status") == "completed" and query.get("status") == "completed" else "partial",
        "repo": asdict(repo),
        "scan": scan,
        "overview": overview,
        "query": query,
        "impact": impact,
        "memory_boundary": "CodeGraph indexes source structure only and does not write long-term memory.",
    }


def _memory_review_payload(result: Any) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "status": result.status,
        "detail": result.detail,
        "candidate": result.candidate,
        "review": asdict(result.review) if result.review else None,
        "obsidian_note": str(result.obsidian_note) if result.obsidian_note else "",
    }
