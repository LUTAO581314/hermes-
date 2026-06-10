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
