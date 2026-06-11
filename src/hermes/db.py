from __future__ import annotations

from dataclasses import dataclass

from .config import Settings


SCHEMA_SQL = """
create table if not exists audit_logs (
    id text primary key,
    actor_type text not null,
    actor_ref text not null,
    action text not null,
    resource_type text not null,
    resource_ref text not null,
    risk_level text not null,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null
);

create table if not exists jobs (
    id text primary key,
    title text not null,
    route text not null,
    status text not null,
    input text not null,
    owner_confirmation_required boolean not null default false,
    result_pointer text not null default '',
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create table if not exists obsidian_writes (
    id text primary key,
    title text not null,
    path text not null,
    created_at timestamptz not null
);

create table if not exists source_refs (
    id text primary key,
    source_type text not null,
    source_ref text not null,
    provider text not null,
    title text not null,
    url text not null default '',
    confidence text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null
);

create index if not exists idx_source_refs_source on source_refs (source_type, source_ref);
create index if not exists idx_source_refs_provider on source_refs (provider);

create table if not exists codegraph_repos (
    id text primary key,
    name text not null,
    root_path text not null,
    status text not null,
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create table if not exists codegraph_scans (
    id text primary key,
    repo_id text not null,
    status text not null,
    file_count integer not null default 0,
    symbol_count integer not null default 0,
    import_count integer not null default 0,
    skipped_count integer not null default 0,
    detail text not null,
    created_at timestamptz not null
);

create table if not exists codegraph_files (
    id text primary key,
    scan_id text not null,
    repo_id text not null,
    path text not null,
    relative_path text not null,
    language text not null,
    size_bytes bigint not null default 0,
    sha256 text not null,
    symbol_count integer not null default 0,
    import_count integer not null default 0
);

create table if not exists codegraph_symbols (
    id text primary key,
    scan_id text not null,
    repo_id text not null,
    file_id text not null,
    name text not null,
    qualname text not null,
    kind text not null,
    language text not null,
    path text not null,
    line_start integer not null default 0,
    line_end integer not null default 0,
    parent text not null default ''
);

create table if not exists codegraph_imports (
    id text primary key,
    scan_id text not null,
    repo_id text not null,
    file_id text not null,
    source_path text not null,
    module text not null,
    name text not null,
    line integer not null default 0
);

create index if not exists idx_codegraph_symbols_repo_name on codegraph_symbols (repo_id, name);
create index if not exists idx_codegraph_files_repo_path on codegraph_files (repo_id, relative_path);

create table if not exists agent_sessions (
    id text primary key,
    title text not null,
    agent_ids jsonb not null default '[]'::jsonb,
    status text not null,
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create table if not exists agent_events (
    id text primary key,
    session_id text not null,
    agent_id text not null,
    type text not null,
    status text not null,
    role text not null,
    model text not null,
    permission text not null,
    content text not null,
    error text not null default '',
    created_at timestamptz not null
);

create index if not exists idx_agent_events_session on agent_events (session_id, created_at);
"""


@dataclass(frozen=True)
class DatabaseStatus:
    status: str
    detail: str


def _import_psycopg():
    try:
        import psycopg  # type: ignore
    except ImportError as exc:
        raise RuntimeError("psycopg is not installed. Install requirements.txt for PostgreSQL support.") from exc
    return psycopg


def database_status(settings: Settings) -> DatabaseStatus:
    if not settings.has_database:
        return DatabaseStatus(status="missing_config", detail="HERMES_DATABASE_URL is empty")
    try:
        psycopg = _import_psycopg()
    except RuntimeError as exc:
        return DatabaseStatus(status="missing_dependency", detail=str(exc))
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("select 1")
                cur.fetchone()
    except Exception as exc:  # pragma: no cover - depends on external DB state
        return DatabaseStatus(status="unavailable", detail=str(exc))
    return DatabaseStatus(status="ready", detail="PostgreSQL connection verified")


def run_migrations(settings: Settings) -> DatabaseStatus:
    if not settings.has_database:
        return DatabaseStatus(status="missing_config", detail="HERMES_DATABASE_URL is empty")
    try:
        psycopg = _import_psycopg()
    except RuntimeError as exc:
        return DatabaseStatus(status="missing_dependency", detail=str(exc))
    try:
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
    except Exception as exc:  # pragma: no cover - depends on external DB state
        return DatabaseStatus(status="failed", detail=str(exc))
    return DatabaseStatus(status="ready", detail="PostgreSQL schema is ready")
