from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from . import __version__
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
from .config import ensure_runtime_dirs, load_settings
from .db import database_status, run_migrations
from .license import load_license
from .model_gateway import complete_chat
from .platform import build_platform_heartbeat
from .runtime_readiness import collect_runtime_readiness
from .server import serve
from .storage import create_document_ingest, create_job, list_audit_events, list_document_ingests, list_jobs, write_obsidian_report


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
        description="bairui Agent OS Hermes runtime CLI",
    )
    subcommands = parser.add_subparsers(dest="command")

    subcommands.add_parser("serve", help="Start the Hermes HTTP server")
    subcommands.add_parser("status", help="Print health, readiness, license, and database status")
    subcommands.add_parser("capabilities", help="List runtime and vendor capabilities")
    subcommands.add_parser("license", help="Inspect the configured license file")
    subcommands.add_parser("jobs", help="List recent file-backed jobs")
    subcommands.add_parser("document-ingests", help="List planned document ingestion records")
    subcommands.add_parser("audit", help="List recent audit events")
    subcommands.add_parser("migrate", help="Run PostgreSQL schema migrations")
    subcommands.add_parser("heartbeat", help="Print the platform heartbeat payload")
    subcommands.add_parser("paths", help="Print runtime paths and key configuration")
    subcommands.add_parser("runtime-readiness", help="Print unified vendor runtime readiness")

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

    job_parser = subcommands.add_parser("job", help="Create a queued job")
    job_parser.add_argument("--title", default="CLI job")
    job_parser.add_argument("--prompt", required=True)
    job_parser.add_argument("--route", default="general")

    chat_parser = subcommands.add_parser("chat", help="Run one OpenAI-compatible model gateway chat")
    chat_parser.add_argument("--prompt", required=True)
    chat_parser.add_argument("--system", default="")

    report_parser = subcommands.add_parser("report", help="Write one markdown report into the Obsidian vault")
    report_parser.add_argument("--title", default="Hermes CLI Report")
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
                "service": "hermes",
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
        print_json({"service": "hermes", "capabilities": collect_capabilities(settings)})
        return 0

    if command == "license":
        print_json({"service": "hermes", "license": load_license(settings.license_file, settings.license_secret)})
        return 0

    if command == "jobs":
        print_json({"service": "hermes", "jobs": list_jobs(settings.data_dir)})
        return 0

    if command == "document-ingests":
        print_json({"service": "hermes", "document_ingests": list_document_ingests(settings.data_dir)})
        return 0

    if command == "audit":
        print_json({"service": "hermes", "audit": list_audit_events(settings.data_dir)})
        return 0

    if command == "migrate":
        result = run_migrations(settings)
        print_json({"service": "hermes", "database": result})
        return 0 if result.status == "ready" else 1

    if command == "heartbeat":
        print_json({"service": "hermes", "heartbeat": build_platform_heartbeat(settings)})
        return 0

    if command == "paths":
        print_json(
            {
                "service": "hermes",
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
        print_json({"service": "hermes", "runtime_readiness": collect_runtime_readiness(settings)})
        return 0

    if command == "memory":
        memory_command = args.memory_command or "status"
        if memory_command == "status":
            print_json({"service": "hermes", "memory": as_payload(everos_status(settings))})
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
            print_json({"service": "hermes", "memory": as_payload(result)})
            return 0 if result.status == "completed" else 1
        if memory_command == "flush":
            payload = build_flush_payload(session_id=args.session_id, app_id=args.app_id, project_id=args.project_id)
            result = flush_memory(settings, payload)
            print_json({"service": "hermes", "memory": as_payload(result)})
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
            print_json({"service": "hermes", "memory": as_payload(result)})
            return 0 if result.status == "completed" else 1
        parser.error(f"unknown memory command: {memory_command}")
        return 2

    if command == "intel":
        intel_command = args.intel_command or "status"
        if intel_command == "status":
            print_json({"service": "hermes", "intelligence": trendradar_payload(trendradar_status(settings))})
            return 0
        if intel_command == "doctor-command":
            print_json({"service": "hermes", "intelligence": trendradar_payload(build_doctor_command(settings))})
            return 0
        if intel_command == "schedule-command":
            print_json({"service": "hermes", "intelligence": trendradar_payload(build_schedule_command(settings))})
            return 0
        if intel_command == "mcp-command":
            print_json(
                {
                    "service": "hermes",
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
            print_json({"service": "hermes", "simulation": mirofish_payload(mirofish_status(settings))})
            return 0
        if simulation_command == "setup-command":
            print_json({"service": "hermes", "simulation": mirofish_payload(build_setup_command(settings))})
            return 0
        if simulation_command == "backend-command":
            print_json({"service": "hermes", "simulation": mirofish_payload(build_backend_command(settings))})
            return 0
        if simulation_command == "frontend-command":
            print_json({"service": "hermes", "simulation": mirofish_payload(build_frontend_command(settings))})
            return 0
        if simulation_command == "dev-command":
            print_json({"service": "hermes", "simulation": mirofish_payload(build_dev_command(settings))})
            return 0
        parser.error(f"unknown simulation command: {simulation_command}")
        return 2

    if command == "search":
        search_command = args.search_command or "status"
        if search_command == "status":
            print_json({"service": "hermes", "search": searxng_payload(searxng_status(settings))})
            return 0
        if search_command == "docker-command":
            print_json({"service": "hermes", "search": searxng_payload(build_searxng_docker_command(settings, host_port=args.host_port))})
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
            print_json({"service": "hermes", "search": searxng_payload(result)})
            return 0 if result.status == "completed" else 1
        parser.error(f"unknown search command: {search_command}")
        return 2

    if command == "index":
        index_command = args.index_command or "status"
        if index_command == "status":
            print_json({"service": "hermes", "index": sonic_payload(sonic_status(settings))})
            return 0
        if index_command == "docker-command":
            print_json({"service": "hermes", "index": sonic_payload(build_sonic_docker_command(settings, host_port=args.host_port))})
            return 0
        if index_command == "ping":
            result = sonic_ping(settings)
            print_json({"service": "hermes", "index": sonic_payload(result)})
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
            print_json({"service": "hermes", "index": sonic_payload(result)})
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
            print_json({"service": "hermes", "index": sonic_payload(result)})
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
            print_json({"service": "hermes", "voice_asr": funasr_payload(funasr_status(settings))})
            return 0
        if asr_command == "server-command":
            print_json({"service": "hermes", "voice_asr": funasr_payload(build_funasr_server_command(settings, device=args.device, model=args.model))})
            return 0
        if asr_command == "docker-command":
            print_json({"service": "hermes", "voice_asr": funasr_payload(build_funasr_docker_command(settings, host_port=args.host_port))})
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
            print_json({"service": "hermes", "voice_asr": funasr_payload(result)})
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
            print_json({"service": "hermes", "document_parse": mineru_payload(mineru_status(settings))})
            return 0
        if parse_command == "install-command":
            print_json({"service": "hermes", "document_parse": mineru_payload(build_mineru_install_command(settings))})
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
            print_json({"service": "hermes", "document_parse": mineru_payload(plan)})
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
            print_json({"service": "hermes", "document_ingest": ingest, "document_parse": mineru_payload(plan)})
            return 0
        parser.error(f"unknown document parse command: {parse_command}")
        return 2

    if command == "job":
        job = create_job(settings.data_dir, title=args.title, prompt=args.prompt, route=args.route)
        print_json({"service": "hermes", "job": job})
        return 0

    if command == "chat":
        result = complete_chat(settings, args.prompt, system=args.system)
        print_json({"service": "hermes", "chat": result})
        return 0 if result.status == "completed" else 1

    if command == "report":
        report = write_obsidian_report(settings.obsidian_vault_dir, settings.data_dir, title=args.title, body=args.body)
        print_json({"service": "hermes", "report": report})
        return 0

    parser.error(f"unknown command: {command}")
    return 2


def main() -> None:
    raise SystemExit(run())
