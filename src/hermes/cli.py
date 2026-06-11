from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from . import __version__
from .avatar import (
    as_payload as avatar_payload,
    avatar_engine_status,
    build_avatar_manifest,
    set_avatar_state,
    validate_avatar_model,
)
from .adapters.everos import (
    add_memory,
    as_payload,
    build_add_payload,
    build_flush_payload,
    build_search_payload,
    flush_memory,
    search_memory,
    status as everos_status,
)
from .adapters.funasr import (
    as_payload as funasr_payload,
    build_docker_command as build_funasr_docker_command,
    build_server_command as build_funasr_server_command,
    build_transcription_payload as build_funasr_transcription_payload,
    status as funasr_status,
    transcribe as funasr_transcribe,
)
from .adapters.mineru import (
    as_payload as mineru_payload,
    build_install_command as build_mineru_install_command,
    build_parse_command as build_mineru_parse_command,
    status as mineru_status,
)
from .adapters.mirofish import (
    as_payload as mirofish_payload,
    build_backend_command,
    build_dev_command,
    build_frontend_command,
    build_setup_command,
    status as mirofish_status,
)
from .adapters.searxng import (
    as_payload as searxng_payload,
    build_docker_command as build_searxng_docker_command,
    build_search_payload as build_searxng_search_payload,
    search as searxng_search,
    status as searxng_status,
)
from .adapters.sonic import (
    as_payload as sonic_payload,
    build_docker_command as build_sonic_docker_command,
    build_push_payload as build_sonic_push_payload,
    build_query_payload as build_sonic_query_payload,
    ping as sonic_ping,
    push as sonic_push,
    query as sonic_query,
    status as sonic_status,
)
from .adapters.trendradar import (
    as_payload as trendradar_payload,
    build_doctor_command,
    build_mcp_command,
    build_schedule_command,
    status as trendradar_status,
)
from .capabilities import collect_capabilities
from .channels import (
    as_payload as channel_payload,
    channel_status,
    channel_targets,
    diagnose_channel_targets,
    list_channel_approvals,
    plan_channel_send,
    review_channel_approval,
)
from .codegraph import (
    as_payload as codegraph_payload,
    codegraph_impact,
    codegraph_overview,
    codegraph_status,
    list_codegraph_repos,
    query_codegraph,
    register_codegraph_repo,
    scan_codegraph_repo,
)
from .config import ensure_runtime_dirs, load_settings
from .db import database_status, run_migrations
from .demo import seed_demo_data
from .demo_flow import run_demo_flow
from .document_pipeline import (
    build_document_ingest_session_summary,
    build_document_workbench_state,
    create_document_ingest_report,
    create_document_source_refs,
    execute_document_workbench_next,
    generate_document_memory_candidates,
    index_document_artifacts,
    list_document_ingest_session_summaries,
    list_pending_document_memory_reviews,
    register_document_artifacts,
    review_document_memory_candidate,
    review_document_memory_candidates_batch,
    run_document_workbench_until_blocked,
    run_document_ingest,
)
from .events import list_frontend_events
from .frontend_contract import build_frontend_contract
from .license import load_license
from .model_gateway import complete_chat
from .platform import build_platform_heartbeat
from .runtime_readiness import collect_runtime_readiness
from .server import serve
from .storage import (
    create_document_ingest,
    create_job,
    list_audit_events,
    list_document_artifacts,
    list_document_index_runs,
    list_document_ingest_reports,
    list_document_ingest_runs,
    list_document_ingests,
    list_document_memory_candidates,
    list_document_memory_reviews,
    list_jobs,
    list_source_refs,
    write_obsidian_report,
)


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, tuple):
        return list(value)
    return value


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_normalize))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.hermes",
        description="bairui Agent OS runtime CLI",
    )
    subcommands = parser.add_subparsers(dest="command")

    subcommands.add_parser("serve", help="Start the bairui HTTP server")
    subcommands.add_parser("status", help="Print health, readiness, license, and database status")
    subcommands.add_parser("capabilities", help="List runtime and vendor capabilities")
    subcommands.add_parser("frontend-contract", help="Print the bairui frontend API contract")
    subcommands.add_parser("license", help="Inspect the configured license file")
    subcommands.add_parser("jobs", help="List recent file-backed jobs")
    subcommands.add_parser("document-ingests", help="List planned document ingestion records")
    subcommands.add_parser("document-ingest-runs", help="List document ingestion execution records")
    subcommands.add_parser("document-ingest-reports", help="List Obsidian document ingest report records")
    subcommands.add_parser("document-artifacts", help="List registered document parser artifacts")
    subcommands.add_parser("document-index-runs", help="List document artifact indexing execution records")
    subcommands.add_parser("document-memory-candidates", help="List pending document memory candidates")
    subcommands.add_parser("document-memory-reviews", help="List reviewed document memory candidates")
    subcommands.add_parser("source-refs", help="List structured source reference records")
    subcommands.add_parser("audit", help="List recent audit events")
    subcommands.add_parser("events", help="List frontend event stream snapshots")
    subcommands.add_parser("migrate", help="Run PostgreSQL schema migrations")
    subcommands.add_parser("heartbeat", help="Print the platform heartbeat payload")
    subcommands.add_parser("paths", help="Print runtime paths and key configuration")
    subcommands.add_parser("runtime-readiness", help="Print unified vendor runtime readiness")
    demo_parser = subcommands.add_parser("demo", help="Create demo data for local product walkthroughs")
    demo_subcommands = demo_parser.add_subparsers(dest="demo_command")
    demo_seed = demo_subcommands.add_parser("seed", help="Seed demo jobs, reports, memory candidates, and channel approvals")
    demo_seed.add_argument("--force", action="store_true", help="Create another demo set even if demo data already exists")
    demo_flow = demo_subcommands.add_parser("flow", help="Run the local product closure demo flow")
    demo_flow.add_argument("--workspace", default="", help="Optional local source workspace for CodeGraph demo")
    demo_flow.add_argument("--force-seed", action="store_true", help="Create another demo seed before running the flow")

    channels_parser = subcommands.add_parser("channels", help="Operate governed outbound channel plans")
    channels_subcommands = channels_parser.add_subparsers(dest="channels_command")
    channels_subcommands.add_parser("status", help="Inspect outbound channel configuration")
    channels_subcommands.add_parser("targets", help="List configured outbound channel targets")
    channels_subcommands.add_parser("diagnostics", help="Explain target readiness and blockers")
    channel_approvals = channels_subcommands.add_parser("approvals", help="List outbound send approval requests")
    channel_approvals.add_argument("--pending", action="store_true")
    channel_send = channels_subcommands.add_parser("plan-send", help="Create an owner-approved outbound send plan")
    channel_send.add_argument("--target-id", required=True)
    channel_send.add_argument("--text", default="")
    channel_send.add_argument("--media-kind", default="text")
    channel_send.add_argument("--attachment-path", default="")
    channel_review = channels_subcommands.add_parser("review-approval", help="Approve or reject one outbound send request")
    channel_review.add_argument("--request-id", required=True)
    channel_review.add_argument("--decision", choices=["approve", "reject"], required=True)
    channel_review.add_argument("--reviewer-ref", default="owner")
    channel_review.add_argument("--note", default="")

    memory_parser = subcommands.add_parser("memory", help="Operate the EverOS-backed memory adapter")
    memory_subcommands = memory_parser.add_subparsers(dest="memory_command")
    memory_subcommands.add_parser("status", help="Inspect EverOS source and API configuration")

    memory_ingest = memory_subcommands.add_parser("ingest", help="Send one text memory message to EverOS /add")
    memory_ingest.add_argument("--text", required=True)
    memory_ingest.add_argument("--user-id", default="owner")
    memory_ingest.add_argument("--session-id", default="cli-session")
    memory_ingest.add_argument("--app-id", default="default")
    memory_ingest.add_argument("--project-id", default="default")
    memory_ingest.add_argument("--sender-name", default="")

    memory_flush = memory_subcommands.add_parser("flush", help="Force EverOS extraction for a session")
    memory_flush.add_argument("--session-id", required=True)
    memory_flush.add_argument("--app-id", default="default")
    memory_flush.add_argument("--project-id", default="default")

    memory_search = memory_subcommands.add_parser("search", help="Search EverOS memory")
    memory_search.add_argument("--query", required=True)
    memory_search.add_argument("--user-id", default="owner")
    memory_search.add_argument("--agent-id", default="")
    memory_search.add_argument("--app-id", default="default")
    memory_search.add_argument("--project-id", default="default")
    memory_search.add_argument("--top-k", type=int, default=5)
    memory_search.add_argument("--method", default="hybrid")
    memory_search.add_argument("--include-profile", action="store_true")

    avatar_parser = subcommands.add_parser("avatar", help="Operate browser avatar runtime integration")
    avatar_subcommands = avatar_parser.add_subparsers(dest="avatar_command")
    avatar_subcommands.add_parser("status", help="Inspect browser avatar engine contract")
    avatar_manifest = avatar_subcommands.add_parser("manifest", help="Print frontend avatar manifest")
    avatar_manifest.add_argument("--avatar-id", default="default")
    avatar_manifest.add_argument("--model-path", default="")
    avatar_validate = avatar_subcommands.add_parser("validate", help="Validate one Live2D model manifest and assets")
    avatar_validate.add_argument("--model-path", required=True)
    avatar_state = avatar_subcommands.add_parser("state", help="Record an avatar state change for frontend consumers")
    avatar_state.add_argument("--avatar-id", default="default")
    avatar_state.add_argument("--state", required=True)
    avatar_state.add_argument("--motion", default="")
    avatar_state.add_argument("--expression", default="")
    avatar_state.add_argument("--text", default="")
    avatar_state.add_argument("--audio-url", default="")
    avatar_state.add_argument("--lip-sync", action="store_true")

    intel_parser = subcommands.add_parser("intel", help="Operate intelligence runtime adapters")
    intel_subcommands = intel_parser.add_subparsers(dest="intel_command")
    intel_subcommands.add_parser("status", help="Inspect TrendRadar source and MCP configuration")
    intel_subcommands.add_parser("doctor-command", help="Print the real TrendRadar doctor command")
    intel_subcommands.add_parser("schedule-command", help="Print the real TrendRadar schedule command")
    intel_mcp = intel_subcommands.add_parser("mcp-command", help="Print the real TrendRadar MCP server command")
    intel_mcp.add_argument("--transport", choices=["stdio", "http"], default="http")
    intel_mcp.add_argument("--host", default="127.0.0.1")
    intel_mcp.add_argument("--port", type=int, default=3333)

    simulation_parser = subcommands.add_parser("simulation", help="Operate simulation runtime adapters")
    simulation_subcommands = simulation_parser.add_subparsers(dest="simulation_command")
    simulation_subcommands.add_parser("status", help="Inspect MiroFish source and service configuration")
    simulation_subcommands.add_parser("setup-command", help="Print the real MiroFish dependency setup command")
    simulation_subcommands.add_parser("backend-command", help="Print the real MiroFish backend command")
    simulation_subcommands.add_parser("frontend-command", help="Print the real MiroFish frontend command")
    simulation_subcommands.add_parser("dev-command", help="Print the real MiroFish full dev command")

    search_parser = subcommands.add_parser("search", help="Operate self-hosted search runtime adapters")
    search_subcommands = search_parser.add_subparsers(dest="search_command")
    search_subcommands.add_parser("status", help="Inspect SearXNG service configuration")
    search_docker = search_subcommands.add_parser("docker-command", help="Print a SearXNG Docker service command")
    search_docker.add_argument("--host-port", type=int, default=8080)
    search_query = search_subcommands.add_parser("query", help="Run one SearXNG JSON search")
    search_query.add_argument("--query", required=True)
    search_query.add_argument("--categories", default="")
    search_query.add_argument("--engines", default="")
    search_query.add_argument("--language", default="")
    search_query.add_argument("--safesearch", default="")
    search_query.add_argument("--time-range", default="")
    search_query.add_argument("--page", type=int, default=1)

    index_parser = subcommands.add_parser("index", help="Operate Sonic local internal search index")
    index_subcommands = index_parser.add_subparsers(dest="index_command")
    index_subcommands.add_parser("status", help="Inspect Sonic local index service configuration")
    index_docker = index_subcommands.add_parser("docker-command", help="Print a Sonic Docker service command")
    index_docker.add_argument("--host-port", type=int, default=1491)
    index_subcommands.add_parser("ping", help="Ping Sonic control channel")
    index_push = index_subcommands.add_parser("push", help="Push one object into Sonic ingest channel")
    index_push.add_argument("--collection", required=True)
    index_push.add_argument("--bucket", required=True)
    index_push.add_argument("--object-id", required=True)
    index_push.add_argument("--text", required=True)
    index_push.add_argument("--lang", default="")
    index_query = index_subcommands.add_parser("query", help="Query Sonic search channel")
    index_query.add_argument("--collection", required=True)
    index_query.add_argument("--bucket", required=True)
    index_query.add_argument("--query", required=True)
    index_query.add_argument("--limit", type=int, default=10)
    index_query.add_argument("--offset", type=int, default=0)
    index_query.add_argument("--lang", default="")

    codegraph_parser = subcommands.add_parser("codegraph", help="Operate local source structure index")
    codegraph_subcommands = codegraph_parser.add_subparsers(dest="codegraph_command")
    codegraph_subcommands.add_parser("status", help="Inspect local code structure index status")
    codegraph_subcommands.add_parser("repos", help="List registered source repositories")
    codegraph_register = codegraph_subcommands.add_parser("register", help="Register a local source repository")
    codegraph_register.add_argument("--path", required=True)
    codegraph_register.add_argument("--name", default="")
    codegraph_scan = codegraph_subcommands.add_parser("scan", help="Scan a registered source repository")
    codegraph_scan.add_argument("--repo-id", default="")
    codegraph_overview_parser = codegraph_subcommands.add_parser("overview", help="Summarize the latest code graph scan")
    codegraph_overview_parser.add_argument("--repo-id", default="")
    codegraph_query_parser = codegraph_subcommands.add_parser("query", help="Search files and symbols in the latest code graph scan")
    codegraph_query_parser.add_argument("--query", required=True)
    codegraph_query_parser.add_argument("--repo-id", default="")
    codegraph_query_parser.add_argument("--limit", type=int, default=20)
    codegraph_impact_parser = codegraph_subcommands.add_parser("impact", help="Estimate file-level impact from imports and symbols")
    codegraph_impact_parser.add_argument("--path", required=True)
    codegraph_impact_parser.add_argument("--repo-id", default="")

    voice_parser = subcommands.add_parser("voice", help="Operate voice runtime adapters")
    voice_subcommands = voice_parser.add_subparsers(dest="voice_command")
    asr_parser = voice_subcommands.add_parser("asr", help="Operate FunASR speech-to-text runtime")
    asr_subcommands = asr_parser.add_subparsers(dest="asr_command")
    asr_subcommands.add_parser("status", help="Inspect FunASR ASR service configuration")
    asr_server = asr_subcommands.add_parser("server-command", help="Print the upstream FunASR server command")
    asr_server.add_argument("--device", default="cuda")
    asr_server.add_argument("--model", default="")
    asr_docker = asr_subcommands.add_parser("docker-command", help="Print a FunASR Docker service command plan")
    asr_docker.add_argument("--host-port", type=int, default=8899)
    asr_transcribe = asr_subcommands.add_parser("transcribe", help="Transcribe one local audio file through FunASR")
    asr_transcribe.add_argument("--audio-path", required=True)
    asr_transcribe.add_argument("--model", default="")
    asr_transcribe.add_argument("--language", default="")
    asr_transcribe.add_argument("--prompt", default="")
    asr_transcribe.add_argument("--response-format", default="json")

    document_parser = subcommands.add_parser("document", help="Operate document parsing runtime adapters")
    document_subcommands = document_parser.add_subparsers(dest="document_command")
    parse_parser = document_subcommands.add_parser("parse", help="Operate MinerU document parser runtime")
    parse_subcommands = parse_parser.add_subparsers(dest="parse_command")
    parse_subcommands.add_parser("status", help="Inspect MinerU parser configuration")
    parse_subcommands.add_parser("install-command", help="Print MinerU CLI install command")
    parse_command = parse_subcommands.add_parser("parse-command", help="Print a MinerU document parse command")
    parse_command.add_argument("--input-path", required=True)
    parse_command.add_argument("--output-dir", default="")
    parse_command.add_argument("--backend", default="")
    parse_command.add_argument("--language", default="")
    parse_command.add_argument("--source", default="")
    parse_command.add_argument("--device", default="")
    ingest_plan = parse_subcommands.add_parser("ingest-plan", help="Create a planned MinerU document ingestion record")
    ingest_plan.add_argument("--input-path", required=True)
    ingest_plan.add_argument("--title", default="")
    ingest_plan.add_argument("--output-dir", default="")
    ingest_plan.add_argument("--backend", default="")
    ingest_plan.add_argument("--language", default="")
    ingest_plan.add_argument("--source", default="")
    ingest_plan.add_argument("--device", default="")
    run_ingest = parse_subcommands.add_parser("run-ingest", help="Execute one planned MinerU document ingestion record")
    run_ingest.add_argument("--ingest-id", required=True)
    run_ingest.add_argument("--timeout-seconds", type=int, default=0)
    register_artifacts = parse_subcommands.add_parser("register-artifacts", help="Register files produced by one document ingestion")
    register_artifacts.add_argument("--ingest-id", required=True)
    index_artifacts = parse_subcommands.add_parser("index-artifacts", help="Index registered text document artifacts into Sonic")
    index_artifacts.add_argument("--ingest-id", required=True)
    index_artifacts.add_argument("--collection", default="bairui")
    index_artifacts.add_argument("--bucket", default="documents")
    index_artifacts.add_argument("--lang", default="")
    memory_candidates = parse_subcommands.add_parser("memory-candidates", help="Generate pending memory candidates from document artifacts")
    memory_candidates.add_argument("--ingest-id", required=True)
    memory_candidates.add_argument("--max-candidates", type=int, default=20)
    review_candidate = parse_subcommands.add_parser("review-memory-candidate", help="Approve or reject one pending document memory candidate")
    review_candidate.add_argument("--candidate-id", required=True)
    review_candidate.add_argument("--decision", choices=["approve", "reject"], required=True)
    review_candidate.add_argument("--reviewer-ref", default="owner")
    review_candidate.add_argument("--note", default="")
    review_candidate.add_argument("--user-id", default="owner")
    review_candidate.add_argument("--session-id", default="")
    review_candidate.add_argument("--app-id", default="default")
    review_candidate.add_argument("--project-id", default="default")
    review_pending = parse_subcommands.add_parser("memory-review-pending", help="List pending document memory candidates for review")
    review_pending.add_argument("--ingest-id", default="")
    review_batch = parse_subcommands.add_parser("memory-review-batch", help="Approve or reject multiple document memory candidates")
    review_batch.add_argument("--candidate-id", action="append", default=[])
    review_batch.add_argument("--decision", choices=["approve", "reject"], required=True)
    review_batch.add_argument("--reviewer-ref", default="owner")
    review_batch.add_argument("--note", default="")
    review_batch.add_argument("--user-id", default="owner")
    review_batch.add_argument("--session-id", default="")
    review_batch.add_argument("--app-id", default="default")
    review_batch.add_argument("--project-id", default="default")
    review_batch.add_argument("--resume-after-review", action="store_true")
    review_batch.add_argument("--timeout-seconds", type=int, default=0)
    review_batch.add_argument("--max-steps", type=int, default=10)
    source_refs = parse_subcommands.add_parser("source-refs", help="Create source reference records for one document ingestion")
    source_refs.add_argument("--ingest-id", required=True)
    ingest_report = parse_subcommands.add_parser("ingest-report", help="Write one Obsidian report for a document ingestion")
    ingest_report.add_argument("--ingest-id", required=True)
    workbench_state = parse_subcommands.add_parser("workbench-state", help="Summarize one document ingestion workflow for UI/workbench use")
    workbench_state.add_argument("--ingest-id", required=True)
    session_summary = parse_subcommands.add_parser("session-summary", help="Build a frontend-ready document ingestion session summary")
    session_summary.add_argument("--ingest-id", required=True)
    session_list = parse_subcommands.add_parser("session-list", help="List frontend-ready document ingestion sessions")
    session_list.add_argument("--limit", type=int, default=50)
    workbench_next = parse_subcommands.add_parser("workbench-next", help="Execute the next safe document ingestion workbench action")
    workbench_next.add_argument("--ingest-id", required=True)
    workbench_next.add_argument("--timeout-seconds", type=int, default=0)
    workbench_next.add_argument("--collection", default="bairui")
    workbench_next.add_argument("--bucket", default="documents")
    workbench_next.add_argument("--lang", default="")
    workbench_next.add_argument("--max-candidates", type=int, default=20)
    workbench_run = parse_subcommands.add_parser("workbench-run-until-blocked", help="Run safe document ingestion workbench actions until complete or blocked")
    workbench_run.add_argument("--ingest-id", required=True)
    workbench_run.add_argument("--timeout-seconds", type=int, default=0)
    workbench_run.add_argument("--collection", default="bairui")
    workbench_run.add_argument("--bucket", default="documents")
    workbench_run.add_argument("--lang", default="")
    workbench_run.add_argument("--max-candidates", type=int, default=20)
    workbench_run.add_argument("--max-steps", type=int, default=10)

    job_parser = subcommands.add_parser("job", help="Create a queued job")
    job_parser.add_argument("--title", default="CLI job")
    job_parser.add_argument("--prompt", required=True)
    job_parser.add_argument("--route", default="general")

    chat_parser = subcommands.add_parser("chat", help="Run one OpenAI-compatible model gateway chat")
    chat_parser.add_argument("--prompt", required=True)
    chat_parser.add_argument("--system", default="")

    report_parser = subcommands.add_parser("report", help="Write one markdown report into the Obsidian vault")
    report_parser.add_argument("--title", default="bairui CLI Report")
    report_parser.add_argument("--body", required=True)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "serve"

    settings = load_settings()
    ensure_runtime_dirs(settings)

    if command == "serve":
        serve(settings)
        return 0

    if command == "status":
        license_state = load_license(settings.license_file, settings.license_secret)
        db_state = database_status(settings)
        print_json(
            {
                "service": "bairui",
                "version": __version__,
                "product": settings.product_name,
                "brand_key": settings.brand_key,
                "env": settings.env,
                "host": settings.host,
                "port": settings.port,
                "license": license_state,
                "database": db_state,
                "platform": "configured" if settings.platform_base_url else "missing_config",
                "server_id": "configured" if settings.server_id else "missing_config",
            }
        )
        return 0

    if command == "capabilities":
        print_json({"service": "bairui", "capabilities": collect_capabilities(settings)})
        return 0

    if command == "frontend-contract":
        print_json({"service": "bairui", "frontend_contract": build_frontend_contract(settings, __version__)})
        return 0

    if command == "license":
        print_json({"service": "bairui", "license": load_license(settings.license_file, settings.license_secret)})
        return 0

    if command == "jobs":
        print_json({"service": "bairui", "jobs": list_jobs(settings.data_dir)})
        return 0

    if command == "document-ingests":
        print_json({"service": "bairui", "document_ingests": list_document_ingests(settings.data_dir)})
        return 0

    if command == "document-ingest-runs":
        print_json({"service": "bairui", "document_ingest_runs": list_document_ingest_runs(settings.data_dir)})
        return 0

    if command == "document-ingest-reports":
        print_json({"service": "bairui", "document_ingest_reports": list_document_ingest_reports(settings.data_dir)})
        return 0

    if command == "document-artifacts":
        print_json({"service": "bairui", "document_artifacts": list_document_artifacts(settings.data_dir)})
        return 0

    if command == "document-index-runs":
        print_json({"service": "bairui", "document_index_runs": list_document_index_runs(settings.data_dir)})
        return 0

    if command == "document-memory-candidates":
        print_json({"service": "bairui", "document_memory_candidates": list_document_memory_candidates(settings.data_dir)})
        return 0

    if command == "document-memory-reviews":
        print_json({"service": "bairui", "document_memory_reviews": list_document_memory_reviews(settings.data_dir)})
        return 0

    if command == "source-refs":
        print_json({"service": "bairui", "source_refs": list_source_refs(settings.data_dir)})
        return 0

    if command == "audit":
        print_json({"service": "bairui", "audit": list_audit_events(settings.data_dir)})
        return 0

    if command == "events":
        print_json({"service": "bairui", "events": list_frontend_events(settings.data_dir)})
        return 0

    if command == "migrate":
        result = run_migrations(settings)
        print_json({"service": "bairui", "database": result})
        return 0 if result.status == "ready" else 1

    if command == "heartbeat":
        print_json({"service": "bairui", "heartbeat": build_platform_heartbeat(settings)})
        return 0

    if command == "paths":
        print_json(
            {
                "service": "bairui",
                "data_dir": str(settings.data_dir),
                "log_dir": str(settings.log_dir),
                "obsidian_vault_dir": str(settings.obsidian_vault_dir),
                "license_file": str(settings.license_file),
                "vendor_dir": str(settings.vendor_dir),
                "everos_memory_root": str(settings.everos_memory_root),
            }
        )
        return 0

    if command == "runtime-readiness":
        print_json({"service": "bairui", "runtime_readiness": collect_runtime_readiness(settings)})
        return 0

    if command == "demo":
        demo_command = args.demo_command or "seed"
        if demo_command == "seed":
            print_json({"service": "bairui", "demo_seed": seed_demo_data(settings, force=args.force)})
            return 0
        if demo_command == "flow":
            result = run_demo_flow(settings, workspace=args.workspace, force_seed=args.force_seed)
            print_json({"service": "bairui", "demo_flow": result})
            return 0 if result["status"] == "completed" else 1
        parser.error(f"unknown demo command: {demo_command}")
        return 2

    if command == "codegraph":
        codegraph_command = args.codegraph_command or "status"
        if codegraph_command == "status":
            print_json({"service": "bairui", "codegraph": codegraph_payload(codegraph_status(settings))})
            return 0
        if codegraph_command == "repos":
            print_json({"service": "bairui", "codegraph_repos": list_codegraph_repos(settings)})
            return 0
        if codegraph_command == "register":
            try:
                repo = register_codegraph_repo(settings, args.path, name=args.name)
            except ValueError as exc:
                print_json({"service": "bairui", "error": "invalid_request", "message": str(exc)})
                return 1
            print_json({"service": "bairui", "codegraph_repo": codegraph_payload(repo)})
            return 0
        if codegraph_command == "scan":
            result = scan_codegraph_repo(settings, args.repo_id)
            print_json({"service": "bairui", "codegraph_scan": result})
            return 0 if result["status"] == "completed" else 1
        if codegraph_command == "overview":
            result = codegraph_overview(settings, repo_id=args.repo_id)
            print_json({"service": "bairui", "codegraph": result})
            return 0
        if codegraph_command == "query":
            result = query_codegraph(settings, args.query, repo_id=args.repo_id, limit=args.limit)
            print_json({"service": "bairui", "codegraph_query": result})
            return 0 if result["status"] in {"completed", "empty"} else 1
        if codegraph_command == "impact":
            result = codegraph_impact(settings, args.path, repo_id=args.repo_id)
            print_json({"service": "bairui", "codegraph_impact": result})
            return 0 if result["status"] != "not_found" else 1
        parser.error(f"unknown codegraph command: {codegraph_command}")
        return 2

    if command == "channels":
        channels_command = args.channels_command or "status"
        if channels_command == "status":
            print_json({"service": "bairui", "channels": channel_payload(channel_status(settings))})
            return 0
        if channels_command == "targets":
            print_json({"service": "bairui", "channel_targets": list(channel_targets(settings))})
            return 0
        if channels_command == "diagnostics":
            print_json({"service": "bairui", "channel_diagnostics": tuple(diagnose_channel_targets(settings))})
            return 0
        if channels_command == "approvals":
            print_json({"service": "bairui", "channel_approvals": list_channel_approvals(settings, only_pending=args.pending)})
            return 0
        if channels_command == "plan-send":
            result = plan_channel_send(
                settings,
                {
                    "target_id": args.target_id,
                    "text": args.text,
                    "media_kind": args.media_kind,
                    "attachment_path": args.attachment_path,
                },
            )
            print_json({"service": "bairui", "channel_send": channel_payload(result)})
            return 0 if result.status == "approval_required" else 1
        if channels_command == "review-approval":
            result = review_channel_approval(
                settings,
                {
                    "request_id": args.request_id,
                    "decision": args.decision,
                    "reviewer_ref": args.reviewer_ref,
                    "note": args.note,
                },
            )
            print_json({"service": "bairui", "channel_approval_review": channel_payload(result)})
            return 0 if result.status == "reviewed" else 1
        parser.error(f"unknown channels command: {channels_command}")
        return 2

    if command == "memory":
        memory_command = args.memory_command or "status"
        if memory_command == "status":
            print_json({"service": "bairui", "memory": as_payload(everos_status(settings))})
            return 0
        if memory_command == "ingest":
            payload = build_add_payload(
                user_id=args.user_id,
                session_id=args.session_id,
                text=args.text,
                app_id=args.app_id,
                project_id=args.project_id,
                sender_name=args.sender_name or None,
            )
            result = add_memory(settings, payload)
            print_json({"service": "bairui", "memory": as_payload(result)})
            return 0 if result.status == "completed" else 1
        if memory_command == "flush":
            payload = build_flush_payload(session_id=args.session_id, app_id=args.app_id, project_id=args.project_id)
            result = flush_memory(settings, payload)
            print_json({"service": "bairui", "memory": as_payload(result)})
            return 0 if result.status == "completed" else 1
        if memory_command == "search":
            payload = build_search_payload(
                query=args.query,
                user_id=args.user_id,
                agent_id=args.agent_id,
                app_id=args.app_id,
                project_id=args.project_id,
                top_k=args.top_k,
                method=args.method,
                include_profile=args.include_profile,
            )
            result = search_memory(settings, payload)
            print_json({"service": "bairui", "memory": as_payload(result)})
            return 0 if result.status == "completed" else 1
        parser.error(f"unknown memory command: {memory_command}")
        return 2

    if command == "avatar":
        avatar_command = args.avatar_command or "status"
        if avatar_command == "status":
            print_json({"service": "bairui", "avatar": avatar_payload(avatar_engine_status(settings))})
            return 0
        if avatar_command == "manifest":
            print_json(
                {
                    "service": "bairui",
                    "avatar_manifest": build_avatar_manifest(settings, avatar_id=args.avatar_id, model_path=args.model_path),
                }
            )
            return 0
        if avatar_command == "validate":
            result = validate_avatar_model(settings, args.model_path)
            print_json({"service": "bairui", "avatar_validation": avatar_payload(result)})
            return 0 if result.status == "valid" else 1
        if avatar_command == "state":
            result = set_avatar_state(
                settings,
                {
                    "avatar_id": args.avatar_id,
                    "state": args.state,
                    "motion": args.motion,
                    "expression": args.expression,
                    "text": args.text,
                    "audio_url": args.audio_url,
                    "lip_sync": args.lip_sync,
                },
            )
            print_json({"service": "bairui", "avatar_state": result})
            return 0 if result["status"] == "accepted" else 1
        parser.error(f"unknown avatar command: {avatar_command}")
        return 2

    if command == "intel":
        intel_command = args.intel_command or "status"
        if intel_command == "status":
            print_json({"service": "bairui", "intelligence": trendradar_payload(trendradar_status(settings))})
            return 0
        if intel_command == "doctor-command":
            print_json({"service": "bairui", "intelligence": trendradar_payload(build_doctor_command(settings))})
            return 0
        if intel_command == "schedule-command":
            print_json({"service": "bairui", "intelligence": trendradar_payload(build_schedule_command(settings))})
            return 0
        if intel_command == "mcp-command":
            print_json(
                {
                    "service": "bairui",
                    "intelligence": trendradar_payload(
                        build_mcp_command(settings, transport=args.transport, host=args.host, port=args.port)
                    ),
                }
            )
            return 0
        parser.error(f"unknown intel command: {intel_command}")
        return 2

    if command == "simulation":
        simulation_command = args.simulation_command or "status"
        if simulation_command == "status":
            print_json({"service": "bairui", "simulation": mirofish_payload(mirofish_status(settings))})
            return 0
        if simulation_command == "setup-command":
            print_json({"service": "bairui", "simulation": mirofish_payload(build_setup_command(settings))})
            return 0
        if simulation_command == "backend-command":
            print_json({"service": "bairui", "simulation": mirofish_payload(build_backend_command(settings))})
            return 0
        if simulation_command == "frontend-command":
            print_json({"service": "bairui", "simulation": mirofish_payload(build_frontend_command(settings))})
            return 0
        if simulation_command == "dev-command":
            print_json({"service": "bairui", "simulation": mirofish_payload(build_dev_command(settings))})
            return 0
        parser.error(f"unknown simulation command: {simulation_command}")
        return 2

    if command == "search":
        search_command = args.search_command or "status"
        if search_command == "status":
            print_json({"service": "bairui", "search": searxng_payload(searxng_status(settings))})
            return 0
        if search_command == "docker-command":
            print_json({"service": "bairui", "search": searxng_payload(build_searxng_docker_command(settings, host_port=args.host_port))})
            return 0
        if search_command == "query":
            payload = build_searxng_search_payload(
                query=args.query,
                categories=args.categories,
                engines=args.engines,
                language=args.language,
                safesearch=args.safesearch,
                time_range=args.time_range,
                page=args.page,
            )
            result = searxng_search(settings, payload)
            print_json({"service": "bairui", "search": searxng_payload(result)})
            return 0 if result.status == "completed" else 1
        parser.error(f"unknown search command: {search_command}")
        return 2

    if command == "index":
        index_command = args.index_command or "status"
        if index_command == "status":
            print_json({"service": "bairui", "index": sonic_payload(sonic_status(settings))})
            return 0
        if index_command == "docker-command":
            print_json({"service": "bairui", "index": sonic_payload(build_sonic_docker_command(settings, host_port=args.host_port))})
            return 0
        if index_command == "ping":
            result = sonic_ping(settings)
            print_json({"service": "bairui", "index": sonic_payload(result)})
            return 0 if result.status == "completed" else 1
        if index_command == "push":
            payload = build_sonic_push_payload(
                collection=args.collection,
                bucket=args.bucket,
                object_id=args.object_id,
                text=args.text,
                lang=args.lang,
            )
            result = sonic_push(settings, payload)
            print_json({"service": "bairui", "index": sonic_payload(result)})
            return 0 if result.status == "completed" else 1
        if index_command == "query":
            payload = build_sonic_query_payload(
                collection=args.collection,
                bucket=args.bucket,
                query=args.query,
                limit=args.limit,
                offset=args.offset,
                lang=args.lang,
            )
            result = sonic_query(settings, payload)
            print_json({"service": "bairui", "index": sonic_payload(result)})
            return 0 if result.status == "completed" else 1
        parser.error(f"unknown index command: {index_command}")
        return 2

    if command == "voice":
        voice_command = args.voice_command or "asr"
        if voice_command != "asr":
            parser.error(f"unknown voice command: {voice_command}")
            return 2
        asr_command = args.asr_command or "status"
        if asr_command == "status":
            print_json({"service": "bairui", "voice_asr": funasr_payload(funasr_status(settings))})
            return 0
        if asr_command == "server-command":
            print_json({"service": "bairui", "voice_asr": funasr_payload(build_funasr_server_command(settings, device=args.device, model=args.model))})
            return 0
        if asr_command == "docker-command":
            print_json({"service": "bairui", "voice_asr": funasr_payload(build_funasr_docker_command(settings, host_port=args.host_port))})
            return 0
        if asr_command == "transcribe":
            payload = build_funasr_transcription_payload(
                audio_path=args.audio_path,
                model=args.model,
                language=args.language,
                prompt=args.prompt,
                response_format=args.response_format,
            )
            result = funasr_transcribe(settings, payload)
            print_json({"service": "bairui", "voice_asr": funasr_payload(result)})
            return 0 if result.status == "completed" else 1
        parser.error(f"unknown voice asr command: {asr_command}")
        return 2

    if command == "document":
        document_command = args.document_command or "parse"
        if document_command != "parse":
            parser.error(f"unknown document command: {document_command}")
            return 2
        parse_command = args.parse_command or "status"
        if parse_command == "status":
            print_json({"service": "bairui", "document_parse": mineru_payload(mineru_status(settings))})
            return 0
        if parse_command == "install-command":
            print_json({"service": "bairui", "document_parse": mineru_payload(build_mineru_install_command(settings))})
            return 0
        if parse_command == "parse-command":
            plan = build_mineru_parse_command(
                settings,
                input_path=args.input_path,
                output_dir=args.output_dir,
                backend=args.backend,
                language=args.language,
                source=args.source,
                device=args.device,
            )
            print_json({"service": "bairui", "document_parse": mineru_payload(plan)})
            return 0
        if parse_command == "ingest-plan":
            plan = build_mineru_parse_command(
                settings,
                input_path=args.input_path,
                output_dir=args.output_dir,
                backend=args.backend,
                language=args.language,
                source=args.source,
                device=args.device,
            )
            output_dir = plan.command[plan.command.index("-o") + 1]
            ingest = create_document_ingest(
                settings.data_dir,
                title=args.title,
                input_path=args.input_path,
                output_dir=output_dir,
                parser_command=plan.command,
            )
            print_json({"service": "bairui", "document_ingest": ingest, "document_parse": mineru_payload(plan)})
            return 0
        if parse_command == "run-ingest":
            result = run_document_ingest(
                settings.data_dir,
                args.ingest_id,
                timeout_seconds=args.timeout_seconds or settings.mineru_timeout_seconds,
            )
            print_json({"service": "bairui", "document_pipeline": result})
            return 0 if result.status == "completed" else 1
        if parse_command == "register-artifacts":
            result = register_document_artifacts(settings.data_dir, args.ingest_id)
            print_json({"service": "bairui", "document_artifact_registration": result})
            return 0 if result.status == "completed" else 1
        if parse_command == "index-artifacts":
            result = index_document_artifacts(
                settings,
                args.ingest_id,
                collection=args.collection,
                bucket=args.bucket,
                lang=args.lang,
            )
            print_json({"service": "bairui", "document_index": result})
            return 0 if result.status in {"completed", "skipped"} else 1
        if parse_command == "memory-candidates":
            result = generate_document_memory_candidates(
                settings.data_dir,
                args.ingest_id,
                max_candidates=args.max_candidates,
            )
            print_json({"service": "bairui", "document_memory_candidate_generation": result})
            return 0 if result.status in {"completed", "skipped"} else 1
        if parse_command == "review-memory-candidate":
            result = review_document_memory_candidate(
                settings,
                args.candidate_id,
                decision=args.decision,
                reviewer_ref=args.reviewer_ref,
                note=args.note,
                user_id=args.user_id,
                session_id=args.session_id,
                app_id=args.app_id,
                project_id=args.project_id,
            )
            print_json({"service": "bairui", "document_memory_review": result})
            return 0 if result.status in {"approved", "rejected"} else 1
        if parse_command == "memory-review-pending":
            result = list_pending_document_memory_reviews(settings, ingest_id=args.ingest_id)
            print_json({"service": "bairui", "document_memory_review_queue": result})
            return 0 if result.status != "not_found" else 1
        if parse_command == "memory-review-batch":
            result = review_document_memory_candidates_batch(
                settings,
                tuple(args.candidate_id),
                decision=args.decision,
                reviewer_ref=args.reviewer_ref,
                note=args.note,
                user_id=args.user_id,
                session_id=args.session_id,
                app_id=args.app_id,
                project_id=args.project_id,
                resume_after_review=args.resume_after_review,
                timeout_seconds=args.timeout_seconds or settings.mineru_timeout_seconds,
                max_steps=args.max_steps,
            )
            print_json({"service": "bairui", "document_memory_review_batch": result})
            return 0 if result.status in {"completed", "partial", "empty"} else 1
        if parse_command == "source-refs":
            result = create_document_source_refs(settings, args.ingest_id)
            print_json({"service": "bairui", "document_source_refs": result})
            return 0 if result.status in {"completed", "skipped"} else 1
        if parse_command == "ingest-report":
            result = create_document_ingest_report(settings, args.ingest_id)
            print_json({"service": "bairui", "document_ingest_report": result})
            return 0 if result.status == "completed" else 1
        if parse_command == "workbench-state":
            state = build_document_workbench_state(settings, args.ingest_id)
            print_json({"service": "bairui", "document_workbench": state})
            return 0 if state.status != "not_found" else 1
        if parse_command == "session-summary":
            summary = build_document_ingest_session_summary(settings, args.ingest_id)
            print_json({"service": "bairui", "document_ingest_session": summary})
            return 0 if summary.status != "not_found" else 1
        if parse_command == "session-list":
            session_list = list_document_ingest_session_summaries(settings, limit=args.limit)
            print_json({"service": "bairui", "document_ingest_sessions": session_list})
            return 0
        if parse_command == "workbench-next":
            result = execute_document_workbench_next(
                settings,
                args.ingest_id,
                timeout_seconds=args.timeout_seconds or settings.mineru_timeout_seconds,
                collection=args.collection,
                bucket=args.bucket,
                lang=args.lang,
                max_candidates=args.max_candidates,
            )
            print_json({"service": "bairui", "document_workbench_step": result})
            return 0 if result.status in {"completed", "needs_review"} else 1
        if parse_command == "workbench-run-until-blocked":
            result = run_document_workbench_until_blocked(
                settings,
                args.ingest_id,
                timeout_seconds=args.timeout_seconds or settings.mineru_timeout_seconds,
                collection=args.collection,
                bucket=args.bucket,
                lang=args.lang,
                max_candidates=args.max_candidates,
                max_steps=args.max_steps,
            )
            print_json({"service": "bairui", "document_workbench_run": result})
            return 0 if result.status in {"completed", "needs_review", "step_limit_reached"} else 1
        parser.error(f"unknown document parse command: {parse_command}")
        return 2

    if command == "job":
        job = create_job(settings.data_dir, title=args.title, prompt=args.prompt, route=args.route)
        print_json({"service": "bairui", "job": job})
        return 0

    if command == "chat":
        result = complete_chat(settings, args.prompt, system=args.system)
        print_json({"service": "bairui", "chat": result})
        return 0 if result.status == "completed" else 1

    if command == "report":
        report = write_obsidian_report(settings.obsidian_vault_dir, settings.data_dir, title=args.title, body=args.body)
        print_json({"service": "bairui", "report": report})
        return 0

    parser.error(f"unknown command: {command}")
    return 2


def main() -> None:
    raise SystemExit(run())
