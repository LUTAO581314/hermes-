from __future__ import annotations

from .config import Settings


def build_frontend_contract(settings: Settings, version: str) -> dict[str, object]:
    return {
        "contract_version": "2026-06-11.1",
        "service": "hermes",
        "product": {
            "name": settings.product_name,
            "brand_key": settings.brand_key,
            "trademark": settings.trademark_name,
            "logo_text": settings.logo_text,
            "version": version,
            "env": settings.env,
        },
        "principles": (
            "Frontend reads stable Hermes product APIs instead of joining raw storage files.",
            "Frontend must show missing_config, partial, blocked, and needs_review states honestly.",
            "Runtime secrets must never be returned to or bundled into frontend JavaScript.",
        ),
        "status_sources": (
            {"id": "health", "method": "GET", "path": "/health", "purpose": "basic service liveness"},
            {"id": "ready", "method": "GET", "path": "/ready", "purpose": "deployment readiness"},
            {"id": "capabilities", "method": "GET", "path": "/capabilities", "purpose": "runtime capability list"},
            {"id": "runtime_readiness", "method": "GET", "path": "/runtime/readiness", "purpose": "vendor runtime blockers and warnings"},
            {"id": "platform_heartbeat", "method": "GET", "path": "/platform/heartbeat", "purpose": "control-plane heartbeat payload"},
        ),
        "screens": (
            {
                "id": "dashboard",
                "title": "Operations Dashboard",
                "read": ("/health", "/ready", "/runtime/readiness", "/capabilities", "/platform/heartbeat"),
                "actions": (),
            },
            {
                "id": "chat",
                "title": "Chat Command Surface",
                "read": ("/capabilities", "/memory/status"),
                "actions": ({"id": "send_chat", "method": "POST", "path": "/chat"},),
            },
            {
                "id": "document_ingest_sessions",
                "title": "Document Knowledge Ingestion",
                "read": ("/document/parse/session-list", "/document/parse/session-summary"),
                "actions": (
                    {"id": "create_ingest_plan", "method": "POST", "path": "/document/parse/ingest-plan"},
                    {"id": "advance_next_step", "method": "POST", "path": "/document/parse/workbench-next"},
                    {"id": "advance_until_blocked", "method": "POST", "path": "/document/parse/workbench-run-until-blocked"},
                    {"id": "review_memory_candidate", "method": "POST", "path": "/document/parse/review-memory-candidate"},
                    {"id": "batch_review_memory_candidates", "method": "POST", "path": "/document/parse/memory-review-batch"},
                ),
            },
            {
                "id": "memory_review",
                "title": "Memory Review Inbox",
                "read": ("/document/parse/memory-review-pending", "/document/memory-candidates", "/document/memory-reviews"),
                "actions": (
                    {"id": "review_memory_candidate", "method": "POST", "path": "/document/parse/review-memory-candidate"},
                    {"id": "batch_review_memory_candidates", "method": "POST", "path": "/document/parse/memory-review-batch"},
                ),
            },
            {
                "id": "reports",
                "title": "Source-backed Reports",
                "read": ("/document/ingest-reports", "/source-refs"),
                "actions": ({"id": "write_obsidian_report", "method": "POST", "path": "/obsidian/reports"},),
            },
            {
                "id": "runtime_settings",
                "title": "Runtime Settings",
                "read": (
                    "/memory/status",
                    "/voice/asr/status",
                    "/document/parse/status",
                    "/intel/status",
                    "/simulation/status",
                    "/search/status",
                    "/index/status",
                ),
                "actions": (),
            },
        ),
        "api_groups": (
            {
                "id": "document_workbench",
                "stability": "stable",
                "endpoints": (
                    {"method": "POST", "path": "/document/parse/session-list"},
                    {"method": "POST", "path": "/document/parse/session-summary"},
                    {"method": "POST", "path": "/document/parse/workbench-state"},
                    {"method": "POST", "path": "/document/parse/workbench-next"},
                    {"method": "POST", "path": "/document/parse/workbench-run-until-blocked"},
                ),
            },
            {
                "id": "document_review",
                "stability": "stable",
                "endpoints": (
                    {"method": "POST", "path": "/document/parse/memory-review-pending"},
                    {"method": "POST", "path": "/document/parse/review-memory-candidate"},
                    {"method": "POST", "path": "/document/parse/memory-review-batch"},
                ),
            },
            {
                "id": "runtime_status",
                "stability": "stable",
                "endpoints": (
                    {"method": "GET", "path": "/capabilities"},
                    {"method": "GET", "path": "/runtime/readiness"},
                    {"method": "GET", "path": "/memory/status"},
                    {"method": "GET", "path": "/document/parse/status"},
                    {"method": "GET", "path": "/index/status"},
                    {"method": "GET", "path": "/search/status"},
                    {"method": "GET", "path": "/voice/asr/status"},
                ),
            },
        ),
        "state_values": (
            "ready",
            "partial",
            "blocked",
            "missing_config",
            "not_found",
            "completed",
            "failed",
            "needs_review",
            "step_limit_reached",
        ),
    }
