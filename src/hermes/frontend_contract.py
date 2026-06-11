from __future__ import annotations

from .config import Settings


def build_frontend_contract(settings: Settings, version: str) -> dict[str, object]:
    brand = {
        "name": "bairui",
        "brand_key": "bairui",
        "trademark": "bairui",
        "logo_text": "bairui",
        "version": version,
        "env": settings.env,
    }
    return {
        "contract_version": "2026-06-11.4",
        "service": "bairui",
        "brand": brand,
        "product": brand,
        "visibility_policy": {
            "public_brand": "bairui",
            "forbidden_public_brands": (),
            "rule": "Customer-facing UI, setup copy, reports, and activation screens must expose only the bairui brand.",
        },
        "ui_base": {
            "source": "open-source-ui-base",
            "strategy": "source-based customization",
            "rule": "Keep the preferred component density and interaction patterns, then replace all public copy, route labels, and brand fields with bairui.",
        },
        "design_system": {
            "direction": "premium sci-fi operations console",
            "layout": "dense control-room shell with left navigation, top command bar, split workbench panes, and detail drawers",
            "palette": {
                "canvas": "#070A0F",
                "surface": "#0E141D",
                "panel": "#121B24",
                "line": "#253241",
                "text": "#EAF2F8",
                "muted": "#8FA3B5",
                "accent": "#35E6C7",
                "accent_secondary": "#67A8FF",
                "danger": "#FF5C7A",
                "warning": "#F6C85F",
                "success": "#5EF0A4",
            },
            "typography": {
                "body": "compact enterprise sans",
                "data": "tabular mono for ids, status, and timestamps",
                "rule": "No oversized marketing typography inside workbench panels.",
            },
            "motion": {
                "default": "short, precise state transitions",
                "reduced_motion": "preserve information with fades disabled and progress shown numerically",
            },
            "components": (
                "status badge",
                "readiness checklist",
                "stepper",
                "segmented control",
                "command button",
                "data table",
                "detail drawer",
                "review queue",
                "log panel",
                "avatar dock",
                "empty state",
            ),
        },
        "principles": (
            "Read stable bairui product APIs instead of joining raw storage files.",
            "Show missing_config, partial, blocked, and needs_review states honestly.",
            "Never expose runtime secrets in frontend JavaScript, reports, or setup screens.",
            "Activation must be a complete guided flow, not a single optimistic button.",
            "Keep code structure indexing separate from long-term memory; CodeGraph reads source structure and never auto-promotes memory.",
        ),
        "activation_flow": (
            {
                "id": "brand_lock",
                "title": "Brand Lock",
                "read": ("/frontend/contract", "/version"),
                "complete_when": "contract brand.name is bairui and no public legacy brand labels are rendered",
                "blocking": True,
            },
            {
                "id": "runtime_health",
                "title": "Runtime Health",
                "read": ("/health", "/ready", "/runtime/readiness"),
                "complete_when": "service responds and required blockers are visible",
                "blocking": True,
            },
            {
                "id": "license_and_platform",
                "title": "License And Platform",
                "read": ("/license", "/platform/heartbeat", "/audit"),
                "complete_when": "license, server id, database, platform status, and audit visibility are shown",
                "blocking": False,
            },
            {
                "id": "model_gateway",
                "title": "Model Gateway",
                "read": ("/capabilities",),
                "action": {"id": "send_chat_probe", "method": "POST", "path": "/chat"},
                "complete_when": "chat action succeeds or shows missing_config with exact environment requirements",
                "blocking": True,
            },
            {
                "id": "document_runtime",
                "title": "Document Runtime",
                "read": ("/document/parse/status",),
                "action": {"id": "create_ingest_plan", "method": "POST", "path": "/document/parse/ingest-plan"},
                "complete_when": "document parser status and ingest-plan form are usable",
                "blocking": False,
            },
            {
                "id": "memory_review",
                "title": "Memory Review",
                "read": ("/document/parse/memory-review-pending",),
                "action": {"id": "batch_review_memory_candidates", "method": "POST", "path": "/document/parse/memory-review-batch"},
                "complete_when": "pending review queue renders and decisions require explicit owner action",
                "blocking": False,
            },
            {
                "id": "reports_and_sources",
                "title": "Reports And Sources",
                "read": ("/reports", "/document/ingest-reports", "/source-refs"),
                "complete_when": "reports and source references are visible or empty states explain next steps",
                "blocking": False,
            },
            {
                "id": "channels",
                "title": "Channels",
                "read": ("/channels/status", "/channels/targets", "/channels/approvals"),
                "action": {"id": "plan_channel_send", "method": "POST", "path": "/channels/send"},
                "complete_when": "channel targets and approval queue render; outbound sends remain owner-reviewed",
                "blocking": False,
            },
            {
                "id": "avatar",
                "title": "Avatar",
                "read": ("/avatar/status", "/avatar/manifest"),
                "action": {"id": "set_avatar_state", "method": "POST", "path": "/avatar/state"},
                "complete_when": "avatar state endpoint accepts idle, thinking, speaking, approval_required, and error states",
                "blocking": False,
            },
            {
                "id": "codegraph",
                "title": "CodeGraph",
                "read": ("/codegraph/status", "/codegraph/repos", "/codegraph/overview"),
                "action": {"id": "register_code_repo", "method": "POST", "path": "/codegraph/repos/register"},
                "complete_when": "source index status is visible and remains separate from long-term memory",
                "blocking": False,
            },
        ),
        "status_sources": (
            {"id": "health", "method": "GET", "path": "/health", "purpose": "service liveness"},
            {"id": "ready", "method": "GET", "path": "/ready", "purpose": "deployment readiness"},
            {"id": "capabilities", "method": "GET", "path": "/capabilities", "purpose": "capability list"},
            {"id": "runtime_readiness", "method": "GET", "path": "/runtime/readiness", "purpose": "runtime blockers and warnings"},
            {"id": "platform_heartbeat", "method": "GET", "path": "/platform/heartbeat", "purpose": "platform heartbeat payload"},
        ),
        "screens": (
            {
                "id": "activation",
                "title": "Activation",
                "read": ("/frontend/contract", "/health", "/ready", "/runtime/readiness", "/license", "/platform/heartbeat"),
                "actions": ({"id": "send_chat_probe", "method": "POST", "path": "/chat"},),
                "uses": ("activation_flow",),
            },
            {
                "id": "dashboard",
                "title": "Dashboard",
                "read": ("/health", "/ready", "/runtime/readiness", "/capabilities", "/platform/heartbeat", "/jobs", "/audit", "/events"),
                "actions": (
                    {"id": "create_job", "method": "POST", "path": "/jobs", "schema": "job_create"},
                    {"id": "seed_demo_data", "method": "POST", "path": "/demo/seed", "schema": "demo_seed"},
                ),
            },
            {
                "id": "chat",
                "title": "Command",
                "read": ("/agents", "/agents/sessions", "/agents/events", "/capabilities", "/memory/status"),
                "actions": (
                    {"id": "create_agent_session", "method": "POST", "path": "/agents/session", "schema": "agent_session_create"},
                    {"id": "update_agent_session_title", "method": "POST", "path": "/agents/session/{session_id}/title", "schema": "agent_session_title"},
                    {"id": "append_agent_message", "method": "POST", "path": "/agents/session/{session_id}/message", "schema": "agent_message_append"},
                    {"id": "run_agent_round", "method": "POST", "path": "/agents/session/{session_id}/round", "schema": "agent_round"},
                    {"id": "promote_agent_event", "method": "POST", "path": "/agents/session/{session_id}/promote", "schema": "agent_promotion"},
                    {"id": "retry_agent_event", "method": "POST", "path": "/agents/session/{session_id}/retry", "schema": "agent_retry"},
                    {"id": "send_chat", "method": "POST", "path": "/chat", "schema": "chat_message"},
                ),
            },
            {
                "id": "document_ingest",
                "title": "Documents",
                "read": ("/document/parse/session-list", "/document/parse/session-summary"),
                "actions": (
                    {"id": "create_ingest_plan", "method": "POST", "path": "/document/parse/ingest-plan", "schema": "document_ingest_plan"},
                    {"id": "advance_next_step", "method": "POST", "path": "/document/parse/workbench-next", "schema": "document_workbench_step"},
                    {"id": "advance_until_blocked", "method": "POST", "path": "/document/parse/workbench-run-until-blocked", "schema": "document_workbench_run"},
                    {"id": "create_source_refs", "method": "POST", "path": "/document/parse/source-refs", "schema": "document_workbench_step"},
                    {"id": "create_ingest_report", "method": "POST", "path": "/document/parse/ingest-report", "schema": "document_workbench_step"},
                ),
            },
            {
                "id": "memory_review",
                "title": "Memory Review",
                "read": ("/document/parse/memory-review-pending", "/document/memory-candidates", "/document/memory-reviews"),
                "actions": (
                    {"id": "review_memory_candidate", "method": "POST", "path": "/document/parse/review-memory-candidate", "schema": "memory_review_decision"},
                    {"id": "batch_review_memory_candidates", "method": "POST", "path": "/document/parse/memory-review-batch", "schema": "memory_review_batch"},
                ),
            },
            {
                "id": "reports",
                "title": "Reports",
                "read": ("/reports", "/document/ingest-reports", "/source-refs"),
                "actions": ({"id": "write_report", "method": "POST", "path": "/obsidian/reports", "schema": "report_write"},),
            },
            {
                "id": "channels",
                "title": "Channels",
                "read": ("/channels/status", "/channels/targets", "/channels/diagnostics", "/channels/approvals", "/events"),
                "actions": (
                    {"id": "plan_channel_send", "method": "POST", "path": "/channels/send", "schema": "channel_send"},
                    {
                        "id": "review_channel_approval",
                        "method": "POST",
                        "path": "/channels/approvals/review",
                        "schema": "channel_approval_review",
                    },
                ),
            },
            {
                "id": "avatar",
                "title": "Avatar",
                "read": ("/avatar/status", "/avatar/manifest"),
                "actions": (
                    {"id": "validate_avatar_model", "method": "POST", "path": "/avatar/validate", "schema": "avatar_validate"},
                    {"id": "set_avatar_state", "method": "POST", "path": "/avatar/state", "schema": "avatar_state"},
                ),
            },
            {
                "id": "runtime_settings",
                "title": "Settings",
                "read": (
                    "/memory/status",
                    "/voice/asr/status",
                    "/document/parse/status",
                    "/intel/status",
                    "/simulation/status",
                    "/search/status",
                    "/index/status",
                    "/avatar/status",
                    "/codegraph/status",
                ),
                "actions": (),
            },
            {
                "id": "codegraph",
                "title": "CodeGraph",
                "read": ("/codegraph/status", "/codegraph/repos", "/codegraph/overview"),
                "actions": (
                    {"id": "register_code_repo", "method": "POST", "path": "/codegraph/repos/register", "schema": "codegraph_repo_register"},
                    {"id": "scan_code_repo", "method": "POST", "path": "/codegraph/repos/scan", "schema": "codegraph_repo_scan"},
                    {"id": "query_codegraph", "method": "POST", "path": "/codegraph/query", "schema": "codegraph_query"},
                    {"id": "impact_codegraph", "method": "POST", "path": "/codegraph/impact", "schema": "codegraph_impact"},
                ),
            },
        ),
        "forms": {
            "chat_message": {
                "fields": (
                    {"name": "prompt", "type": "textarea", "required": True, "label": "Message"},
                    {"name": "system", "type": "textarea", "required": False, "label": "Instruction"},
                )
            },
            "job_create": {
                "fields": (
                    {"name": "title", "type": "text", "required": False, "label": "Title"},
                    {"name": "prompt", "type": "textarea", "required": True, "label": "Task"},
                    {"name": "route", "type": "select", "required": False, "label": "Route", "options": ("general", "research", "document", "operations")},
                )
            },
            "demo_seed": {
                "safety": {
                    "will_send": False,
                    "will_write_long_term_memory": False,
                    "idempotent": True,
                },
                "fields": (
                    {"name": "force", "type": "toggle", "required": False, "label": "Create Another Demo Set"},
                ),
            },
            "agent_session_create": {
                "fields": (
                    {"name": "title", "type": "text", "required": False, "label": "Title"},
                    {"name": "agent_ids", "type": "id_list", "required": False, "label": "Agent IDs"},
                )
            },
            "agent_session_title": {
                "fields": (
                    {"name": "title", "type": "text", "required": True, "label": "Title"},
                )
            },
            "agent_message_append": {
                "fields": (
                    {"name": "content", "type": "textarea", "required": True, "label": "Message"},
                )
            },
            "agent_round": {
                "fields": (
                    {"name": "prompt", "type": "textarea", "required": True, "label": "Prompt"},
                )
            },
            "agent_promotion": {
                "safety": {
                    "will_execute_external_action": False,
                    "idempotency_key": "event_id + target",
                    "source_chain": "created_resource.source links back to agent_event, session, agent, role, and target",
                },
                "fields": (
                    {"name": "event_id", "type": "id", "required": True, "label": "Event ID"},
                    {"name": "target", "type": "select", "required": True, "label": "Target", "options": ("job", "report", "memory_review", "channel_draft")},
                )
            },
            "agent_retry": {
                "safety": {
                    "will_execute_external_action": False,
                    "retryable_statuses": ("failed", "missing_config", "blocked"),
                },
                "fields": (
                    {"name": "event_id", "type": "id", "required": True, "label": "Event ID"},
                ),
            },
            "document_ingest_plan": {
                "fields": (
                    {"name": "input_path", "type": "file_path", "required": True, "label": "Document"},
                    {"name": "title", "type": "text", "required": False, "label": "Title"},
                    {"name": "output_dir", "type": "directory_path", "required": False, "label": "Output Directory"},
                    {"name": "backend", "type": "select", "required": False, "label": "Parse Backend", "options": ("", "pipeline", "vlm-transformers", "hybrid-http-client")},
                    {"name": "language", "type": "text", "required": False, "label": "Language"},
                    {"name": "device", "type": "select", "required": False, "label": "Device", "options": ("cpu", "cuda")},
                )
            },
            "document_workbench_step": {
                "fields": (
                    {"name": "ingest_id", "type": "id", "required": True, "label": "Ingest ID"},
                    {"name": "timeout_seconds", "type": "number", "required": False, "label": "Timeout"},
                )
            },
            "document_workbench_run": {
                "fields": (
                    {"name": "ingest_id", "type": "id", "required": True, "label": "Ingest ID"},
                    {"name": "timeout_seconds", "type": "number", "required": False, "label": "Timeout"},
                    {"name": "max_steps", "type": "number", "required": False, "label": "Max Steps"},
                )
            },
            "memory_review_decision": {
                "fields": (
                    {"name": "candidate_id", "type": "id", "required": True, "label": "Candidate ID"},
                    {"name": "decision", "type": "segmented", "required": True, "label": "Decision", "options": ("approve", "reject")},
                    {"name": "note", "type": "textarea", "required": False, "label": "Note"},
                )
            },
            "memory_review_batch": {
                "fields": (
                    {"name": "candidate_ids", "type": "id_list", "required": True, "label": "Candidate IDs"},
                    {"name": "decision", "type": "segmented", "required": True, "label": "Decision", "options": ("approve", "reject")},
                    {"name": "resume_after_review", "type": "toggle", "required": False, "label": "Continue Workflow"},
                )
            },
            "report_write": {
                "fields": (
                    {"name": "title", "type": "text", "required": False, "label": "Title"},
                    {"name": "body", "type": "textarea", "required": True, "label": "Body"},
                )
            },
            "channel_send": {
                "fields": (
                    {"name": "target_id", "type": "select", "required": True, "label": "Target", "source": "/channels/targets"},
                    {"name": "media_kind", "type": "segmented", "required": True, "label": "Media", "options": ("text", "image", "video", "file")},
                    {"name": "text", "type": "textarea", "required": False, "label": "Message"},
                    {"name": "attachment_path", "type": "file_path", "required": False, "label": "Attachment"},
                    {"name": "owner_confirmation", "type": "toggle", "required": True, "label": "Owner Confirmation"},
                )
            },
            "channel_approval_review": {
                "fields": (
                    {"name": "request_id", "type": "id", "required": True, "label": "Request ID"},
                    {"name": "decision", "type": "segmented", "required": True, "label": "Decision", "options": ("approve", "reject")},
                    {"name": "note", "type": "textarea", "required": False, "label": "Note"},
                )
            },
            "avatar_validate": {
                "fields": (
                    {"name": "model_path", "type": "file_path", "required": True, "label": "Model Manifest"},
                )
            },
            "avatar_state": {
                "fields": (
                    {"name": "avatar_id", "type": "id", "required": False, "label": "Avatar ID"},
                    {
                        "name": "state",
                        "type": "segmented",
                        "required": True,
                        "label": "State",
                        "options": ("idle", "thinking", "speaking", "approval_required", "error", "done", "hidden"),
                    },
                    {"name": "text", "type": "textarea", "required": False, "label": "Speech Text"},
                    {"name": "audio_url", "type": "text", "required": False, "label": "Audio URL"},
                    {"name": "lip_sync", "type": "toggle", "required": False, "label": "Lip Sync"},
                )
            },
            "codegraph_repo_register": {
                "fields": (
                    {"name": "path", "type": "directory_path", "required": True, "label": "Repository Path"},
                    {"name": "name", "type": "text", "required": False, "label": "Display Name"},
                )
            },
            "codegraph_repo_scan": {
                "fields": (
                    {"name": "repo_id", "type": "id", "required": False, "label": "Repo ID"},
                )
            },
            "codegraph_query": {
                "fields": (
                    {"name": "query", "type": "text", "required": True, "label": "Query"},
                    {"name": "repo_id", "type": "id", "required": False, "label": "Repo ID"},
                    {"name": "limit", "type": "number", "required": False, "label": "Limit"},
                )
            },
            "codegraph_impact": {
                "fields": (
                    {"name": "path", "type": "file_path", "required": True, "label": "File Path"},
                    {"name": "repo_id", "type": "id", "required": False, "label": "Repo ID"},
                )
            },
        },
        "api_groups": (
            {
                "id": "operations",
                "stability": "stable",
                "endpoints": (
                    {"method": "GET", "path": "/jobs"},
                    {"method": "POST", "path": "/jobs"},
                    {"method": "POST", "path": "/demo/seed"},
                    {"method": "GET", "path": "/audit"},
                    {"method": "GET", "path": "/events", "content_type": "text/event-stream"},
                    {"method": "GET", "path": "/platform/heartbeat"},
                ),
            },
            {
                "id": "agents",
                "stability": "experimental",
                "endpoints": (
                    {"method": "GET", "path": "/agents"},
                    {"method": "GET", "path": "/agents/{id}"},
                    {"method": "GET", "path": "/agents/sessions"},
                    {"method": "GET", "path": "/agents/events"},
                    {"method": "POST", "path": "/agents/session"},
                    {"method": "POST", "path": "/agents/session/{session_id}/message"},
                    {"method": "POST", "path": "/agents/session/{session_id}/title"},
                    {"method": "POST", "path": "/agents/session/{session_id}/round"},
                    {"method": "POST", "path": "/agents/session/{session_id}/events"},
                    {"method": "POST", "path": "/agents/session/{session_id}/promote"},
                    {"method": "POST", "path": "/agents/session/{session_id}/retry"},
                ),
            },
            {
                "id": "document_workbench",
                "stability": "stable",
                "endpoints": (
                    {"method": "POST", "path": "/document/parse/session-list"},
                    {"method": "POST", "path": "/document/parse/session-summary"},
                    {"method": "POST", "path": "/document/parse/workbench-state"},
                    {"method": "POST", "path": "/document/parse/workbench-next"},
                    {"method": "POST", "path": "/document/parse/workbench-run-until-blocked"},
                    {"method": "POST", "path": "/document/parse/source-refs"},
                    {"method": "POST", "path": "/document/parse/ingest-report"},
                ),
            },
            {
                "id": "memory_review",
                "stability": "stable",
                "endpoints": (
                    {"method": "POST", "path": "/document/parse/memory-review-pending"},
                    {"method": "POST", "path": "/document/parse/review-memory-candidate"},
                    {"method": "POST", "path": "/document/parse/memory-review-batch"},
                ),
            },
            {
                "id": "channels",
                "stability": "stable",
                "endpoints": (
                    {"method": "GET", "path": "/channels/status"},
                    {"method": "GET", "path": "/channels/targets"},
                    {"method": "GET", "path": "/channels/diagnostics"},
                    {"method": "GET", "path": "/channels/approvals"},
                    {"method": "POST", "path": "/channels/send"},
                    {"method": "POST", "path": "/channels/approvals/review"},
                ),
            },
            {
                "id": "reports",
                "stability": "stable",
                "endpoints": (
                    {"method": "GET", "path": "/reports"},
                    {"method": "GET", "path": "/document/ingest-reports"},
                    {"method": "POST", "path": "/obsidian/reports"},
                ),
            },
            {
                "id": "avatar",
                "stability": "experimental",
                "endpoints": (
                    {"method": "GET", "path": "/avatar/status"},
                    {"method": "GET", "path": "/avatar/manifest"},
                    {"method": "POST", "path": "/avatar/validate"},
                    {"method": "POST", "path": "/avatar/state"},
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
                    {"method": "GET", "path": "/avatar/status"},
                    {"method": "GET", "path": "/codegraph/status"},
                ),
            },
            {
                "id": "codegraph",
                "stability": "experimental",
                "memory_boundary": "separate_source_structure_index",
                "endpoints": (
                    {"method": "GET", "path": "/codegraph/status"},
                    {"method": "GET", "path": "/codegraph/repos"},
                    {"method": "GET", "path": "/codegraph/overview"},
                    {"method": "POST", "path": "/codegraph/repos/register"},
                    {"method": "POST", "path": "/codegraph/repos/scan"},
                    {"method": "POST", "path": "/codegraph/query"},
                    {"method": "POST", "path": "/codegraph/impact"},
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
            "approval_required",
            "unsupported_media",
            "pending_review",
            "reviewed",
            "already_reviewed",
            "source_ready",
            "speaking",
            "thinking",
            "hidden",
            "invalid_state",
        ),
    }
