"""Frontend adapter contract for BaiLongma / Brain UI overlays."""

from __future__ import annotations

from typing import Any

from .routing import RouteType
from .server_time import utc_now


def frontend_contract(config: Any) -> dict[str, Any]:
    """Return a secret-safe, machine-readable contract for external frontends."""

    return {
        "status": "ok",
        "contract_version": "2026-06-phase-17",
        "source": "https://github.com/LUTAO581314/hermes-",
        "created_at": utc_now(),
        "runtime": {
            "base_url_env": "HERMES_RUNTIME_BASE_URL",
            "timeout_seconds_env": "HERMES_RUNTIME_TIMEOUT_SECONDS",
            "basic_auth_env": [
                "HERMES_RUNTIME_BASIC_USER",
                "HERMES_RUNTIME_BASIC_PASSWORD",
            ],
            "default_timeout_seconds": 5,
        },
        "endpoints": {
            "capabilities": {
                "method": "GET",
                "path": "/capabilities",
                "purpose": "Render health cards and missing-configuration hints.",
            },
            "performance": {
                "method": "GET",
                "path": "/performance",
                "purpose": "Render visible latency budgets and routing thresholds.",
            },
            "social_turn": {
                "method": "POST",
                "path": "/social/turn",
                "purpose": "Plan the first visible action for a channel message.",
                "request": {
                    "channel": "wechat|qq|feishu|web",
                    "target_id": "stable channel target id",
                    "message": "transient inbound text",
                },
                "response_keys": [
                    "first_action",
                    "ack",
                    "route",
                    "context_budget",
                    "job",
                    "active_job",
                    "outbound_media",
                ],
            },
            "jobs_event": {
                "method": "POST",
                "path": "/jobs/event",
                "purpose": "Report slow-task lifecycle without duplicating Hermes state.",
                "allowed_events": [
                    "ack_sent",
                    "worker_started",
                    "worker_completed",
                    "worker_failed",
                    "final_delivered",
                    "failure_delivered",
                ],
            },
            "media_plan_send": {
                "method": "POST",
                "path": "/media/plan-send",
                "purpose": "Ask the runtime whether a connector should send an image file, upload first, or send text fallback.",
                "request": {
                    "channel": "wechat|qq|feishu|web",
                    "target_id": "stable channel target id",
                    "outbound_media": "object returned by /social/turn",
                    "source_ref": "connector-local file path or runtime asset ref; never raw bytes",
                    "bridge_capabilities": {
                        "send_text": True,
                        "send_image_file": False,
                        "upload_then_send": False,
                    },
                },
                "response_keys": [
                    "action",
                    "message_type",
                    "text_fallback",
                    "source_ref",
                    "reason",
                    "bridge_requirements",
                    "report_event",
                    "safe_log",
                ],
            },
            "latency_turn": {
                "method": "POST",
                "path": "/latency/turn",
                "purpose": "Report external frontend or connector timing safely.",
            },
        },
        "frontend_states": {
            "direct_reply": {
                "bubble": "normal",
                "status_text": "",
                "send_ack_first": False,
            },
            "quick_ack": {
                "bubble": "progress",
                "status_text": "thinking",
                "send_ack_first": True,
            },
            "append_to_active_job": {
                "bubble": "progress",
                "status_text": "updating",
                "send_ack_first": True,
            },
            "approval_required": {
                "bubble": "confirmation",
                "status_text": "needs_owner_confirmation",
                "send_ack_first": True,
            },
        },
        "route_ui": _route_ui(config),
        "outbound_media": {
            "purpose": "Normalize image/sticker sending across web, WeChat, QQ, Feishu, and future connectors.",
            "keys": [
                "kind",
                "channel",
                "action",
                "send_strategy",
                "text_fallback",
                "upload_required",
                "review_required",
                "fallback_reason",
                "platform_payload",
                "metadata",
            ],
            "adapter_rule": "If send_strategy is text_fallback_until_upload_supported, send text_fallback immediately and log fallback_reason instead of dropping the media.",
            "wechat_rule": "Personal WeChat bridges may lack image upload; they must gracefully fall back to text until media_id or bridge-file sending is verified.",
            "feishu_rule": "Feishu image messages require runtime upload and image_key before send.",
        },
        "channel_planes": {
            "wechat": {
                "plane": "personal",
                "can_do_company_write": False,
                "can_do_money_or_legal_action": False,
                "badge": "个人陪伴",
            },
            "qq": {
                "plane": "personal",
                "can_do_company_write": False,
                "can_do_money_or_legal_action": False,
                "badge": "个人陪伴",
            },
            "web": {
                "plane": "personal",
                "can_do_company_write": False,
                "can_do_money_or_legal_action": False,
                "badge": "网页陪伴",
            },
            "feishu": {
                "plane": "company",
                "can_do_company_write": False,
                "can_do_money_or_legal_action": False,
                "badge": "公司管理",
                "write_policy": "owner_confirmation_required",
            },
        },
        "privacy": {
            "never_store_in_contract": [
                "api keys",
                "passwords",
                "raw message bodies",
                "media bytes",
                "screenshots",
                "platform user ids",
            ],
            "job_records_store": "route metadata, preview lengths, lifecycle status, and result pointers only",
        },
    }


def _route_ui(config: Any) -> dict[str, dict[str, Any]]:
    slow_budget = getattr(config, "slow_task_threshold_ms", 5000)
    fast_budget = getattr(config, "social_fast_reply_target_ms", 5000)
    return {
        RouteType.CASUAL_CHAT.value: {
            "label": "日常聊天",
            "status_text": "",
            "progress_kind": "none",
            "target_ms": fast_budget,
        },
        RouteType.QUICK_QUESTION.value: {
            "label": "快速回答",
            "status_text": "",
            "progress_kind": "none",
            "target_ms": fast_budget,
        },
        RouteType.IMAGE_READ.value: {
            "label": "图片识别",
            "status_text": "我在看图",
            "progress_kind": "vision",
            "target_ms": slow_budget,
        },
        RouteType.IMAGE_GENERATE.value: {
            "label": "图片生成",
            "status_text": "我在拍一下",
            "progress_kind": "image_generation",
            "target_ms": slow_budget,
        },
        RouteType.SEARCH.value: {
            "label": "搜索",
            "status_text": "我在查资料",
            "progress_kind": "search",
            "target_ms": slow_budget,
        },
        RouteType.PUBLIC_OPINION.value: {
            "label": "舆情",
            "status_text": "我在看热点",
            "progress_kind": "trend_search",
            "target_ms": slow_budget,
        },
        RouteType.COMPANY_TASK.value: {
            "label": "飞书公司任务",
            "status_text": "我在看飞书上下文",
            "progress_kind": "company_read",
            "target_ms": slow_budget,
        },
        RouteType.MEMORY_TASK.value: {
            "label": "记忆整理",
            "status_text": "我在整理记忆",
            "progress_kind": "memory_review",
            "target_ms": slow_budget,
        },
        RouteType.HIGH_RISK.value: {
            "label": "高风险确认",
            "status_text": "需要主人确认",
            "progress_kind": "approval_gate",
            "target_ms": fast_budget,
        },
    }
