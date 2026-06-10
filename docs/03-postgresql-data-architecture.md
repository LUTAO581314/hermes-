# PostgreSQL Data Architecture

## 1. Database Decision

Production uses PostgreSQL.

SQLite is no longer the target production database. It may be used only for
local development or isolated test fixtures. The server rebuild must provision
PostgreSQL from the start.

## 2. Why PostgreSQL

PostgreSQL is selected because the commercial product needs:

- durable structured state;
- transactional job updates;
- audit logs;
- approval records;
- company workflow data;
- multi-channel identities;
- future tenant support;
- indexing and query performance;
- backup and recovery;
- migration discipline;
- compatibility with analytics and reporting tools.

Obsidian remains the long-term memory truth, but it is not suitable for
transactions, concurrent writes, queues, or approval state.

## 3. Database Roles

PostgreSQL stores machine state:

- identities;
- channels;
- sessions;
- jobs;
- job events;
- approvals;
- audit logs;
- memory candidates;
- source references;
- simulations;
- report metadata;
- connector delivery status;
- runtime configuration records.

Obsidian stores human-readable truth:

- decisions;
- reports;
- curated memory;
- project notes;
- owner preferences;
- postmortems.

EverOS stores automatic memory artifacts and indexes, then Hermes promotes
selected outputs to Obsidian after review.

## 4. Initial Schema

### identities

Stores normalized users and platform identities.

Columns:

- `id uuid primary key`
- `display_name text`
- `owner_scope text`
- `created_at timestamptz`
- `updated_at timestamptz`

### channel_accounts

Stores platform-specific bindings.

- `id uuid primary key`
- `identity_id uuid`
- `channel text`
- `platform_user_id text`
- `platform_chat_id text`
- `plane text`
- `status text`
- `created_at timestamptz`

### jobs

Stores durable async jobs.

- `id uuid primary key`
- `route text`
- `channel text`
- `target_id text`
- `input_preview_chars integer`
- `tool_name text`
- `status text`
- `owner_confirmation_required boolean`
- `result_pointer text`
- `error_message text`
- `created_at timestamptz`
- `updated_at timestamptz`
- `started_at timestamptz`
- `completed_at timestamptz`

### job_events

Stores lifecycle events.

- `id uuid primary key`
- `job_id uuid`
- `event text`
- `status_after text`
- `payload jsonb`
- `created_at timestamptz`

### approvals

Stores owner approval requests.

- `id uuid primary key`
- `requested_by_identity_id uuid`
- `risk_level text`
- `action_type text`
- `summary text`
- `payload jsonb`
- `status text`
- `approved_by text`
- `created_at timestamptz`
- `resolved_at timestamptz`

### audit_logs

Stores immutable audit records.

- `id uuid primary key`
- `actor_type text`
- `actor_ref text`
- `action text`
- `resource_type text`
- `resource_ref text`
- `risk_level text`
- `payload jsonb`
- `created_at timestamptz`

### memory_candidates

Stores memory candidates before Obsidian promotion.

- `id uuid primary key`
- `source_type text`
- `source_ref text`
- `candidate_type text`
- `summary text`
- `evidence jsonb`
- `status text`
- `obsidian_path text`
- `created_at timestamptz`
- `reviewed_at timestamptz`

### source_refs

Stores citations, external source metadata, and document pipeline provenance.
Hermes currently writes the same contract to `source_refs.jsonl` for local
operation; production migrations create the PostgreSQL `source_refs` table with
matching fields.

- `id uuid primary key`
- `source_type text`
- `source_ref text`
- `provider text`
- `title text`
- `url text`
- `confidence text`
- `metadata jsonb`
- `created_at timestamptz`

Document ingestion uses source refs to connect:

- MinerU document artifacts;
- Sonic indexing runs;
- Hermes memory candidates and owner review status;
- EverOS promotion status when a candidate was approved;
- Obsidian graph note path when a review created one.

### simulation_runs

Stores MiroFish run metadata.

- `id uuid primary key`
- `brief_path text`
- `status text`
- `result_path text`
- `decision_path text`
- `risk_summary text`
- `created_at timestamptz`
- `completed_at timestamptz`

## 5. Migration Rule

All schema changes must be migrations. No manual production schema edits.

Recommended migration table:

```sql
create table schema_migrations (
  version text primary key,
  applied_at timestamptz not null default now()
);
```

## 6. Backup Rule

Back up:

- PostgreSQL daily logical dump;
- PostgreSQL physical volume snapshot if available;
- Obsidian vault;
- Hermes configuration templates;
- audit export.

Never back up plaintext secrets into shared folders.
