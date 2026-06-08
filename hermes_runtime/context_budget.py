"""Context slimming policy for route-aware Hermes turns."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .routing import RoutePolicy, classify_route


@dataclass(frozen=True)
class ContextBudget:
    route: str
    memory_depth: str
    max_recent_messages: int
    allow_long_term_memory: bool
    allow_obsidian_lookup: bool
    tool_schema_group: str
    max_tool_schemas: int
    notes: tuple[str, ...]


CONTEXT_BUDGETS: dict[str, ContextBudget] = {
    "casual_chat": ContextBudget(
        route="casual_chat",
        memory_depth="identity_recent",
        max_recent_messages=8,
        allow_long_term_memory=False,
        allow_obsidian_lookup=False,
        tool_schema_group="send_only",
        max_tool_schemas=1,
        notes=("identity", "recent_chat"),
    ),
    "quick_question": ContextBudget(
        route="quick_question",
        memory_depth="critical_recent",
        max_recent_messages=12,
        allow_long_term_memory=True,
        allow_obsidian_lookup=False,
        tool_schema_group="minimal",
        max_tool_schemas=3,
        notes=("critical_memory", "recent_chat"),
    ),
    "image_read": ContextBudget(
        route="image_read",
        memory_depth="recent_only",
        max_recent_messages=6,
        allow_long_term_memory=False,
        allow_obsidian_lookup=False,
        tool_schema_group="vision",
        max_tool_schemas=2,
        notes=("image_context", "recent_chat"),
    ),
    "image_generate": ContextBudget(
        route="image_generate",
        memory_depth="recent_only",
        max_recent_messages=4,
        allow_long_term_memory=False,
        allow_obsidian_lookup=False,
        tool_schema_group="image_generation",
        max_tool_schemas=2,
        notes=("style_policy", "review_policy"),
    ),
    "search": ContextBudget(
        route="search",
        memory_depth="source_policy",
        max_recent_messages=6,
        allow_long_term_memory=False,
        allow_obsidian_lookup=False,
        tool_schema_group="search",
        max_tool_schemas=3,
        notes=("source_policy", "freshness_policy"),
    ),
    "public_opinion": ContextBudget(
        route="public_opinion",
        memory_depth="source_policy",
        max_recent_messages=6,
        allow_long_term_memory=False,
        allow_obsidian_lookup=False,
        tool_schema_group="trend_search",
        max_tool_schemas=4,
        notes=("trendradar", "source_policy", "summary_style"),
    ),
    "company_task": ContextBudget(
        route="company_task",
        memory_depth="company_policy",
        max_recent_messages=10,
        allow_long_term_memory=True,
        allow_obsidian_lookup=False,
        tool_schema_group="company_read",
        max_tool_schemas=5,
        notes=("feishu_identity", "department_policy", "approval_policy"),
    ),
    "memory_task": ContextBudget(
        route="memory_task",
        memory_depth="memory_governance",
        max_recent_messages=10,
        allow_long_term_memory=True,
        allow_obsidian_lookup=True,
        tool_schema_group="memory_review",
        max_tool_schemas=4,
        notes=("memory_rules", "dream_cleanup", "obsidian_links"),
    ),
    "high_risk": ContextBudget(
        route="high_risk",
        memory_depth="policy_only",
        max_recent_messages=4,
        allow_long_term_memory=False,
        allow_obsidian_lookup=False,
        tool_schema_group="approval_gate",
        max_tool_schemas=1,
        notes=("risk_policy", "owner_confirmation"),
    ),
}


def budget_for_policy(policy: RoutePolicy) -> ContextBudget:
    return CONTEXT_BUDGETS[policy.route.value]


def context_payload(message: str, config: Any) -> dict[str, Any]:
    policy = classify_route(message, config)
    budget = budget_for_policy(policy)
    return {
        "status": "ok",
        "route": asdict(policy),
        "context_budget": asdict(budget),
        "message_preview_chars": min(len(str(message or "")), 160),
    }
