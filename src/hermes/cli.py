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
from .server import serve
from .storage import create_job, list_audit_events, list_jobs, write_obsidian_report


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
    subcommands.add_parser("audit", help="List recent audit events")
    subcommands.add_parser("migrate", help="Run PostgreSQL schema migrations")
    subcommands.add_parser("heartbeat", help="Print the platform heartbeat payload")
    subcommands.add_parser("paths", help="Print runtime paths and key configuration")

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
