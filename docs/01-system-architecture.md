# System Architecture

## 1. Architecture Decision

The system converges to one backend and one frontend:

- Backend authority: Hermes.
- Frontend surface: MOXI / Brain UI.
- Production database: PostgreSQL.
- Durable memory source: Obsidian.
- Automatic memory engine: EverOS.
- Simulation runtime: MiroFish.
- Search and intelligence runtimes: TrendRadar first, SearXNG optional.

No long-term external frontend backend authority remains. Historical frontend
work may be used only as reference material, but new backend capabilities belong
to Hermes.

## 2. Logical Architecture

```text
-----------------------+
| Owner / Company User |
+-----------+-----------+
            |
            v
+-----------------------+
| MOXI / Brain UI       |
| Feishu / WeChat / QQ  |
| CLI / Admin Console   |
+-----------+-----------+
            |
            v
+-----------------------+
| Hermes Backend        |
| routing / jobs / auth |
| tools / policy / API  |
+-----+------+-----+----+
      |      |     |
      |      |     +--------------------+
      |      |                          |
      v      v                          v
+---------+ +----------------+ +------------------+
|Postgres | | Obsidian Vault | | External Runtimes|
|state/audit| memory/reports | | EverOS/MiroFish  |
+---------+ +----------------+ | TrendRadar/SearX |
                               +------------------+
```

## 3. Domain Boundaries

### Hermes Backend

Hermes owns:

- HTTP API contracts;
- route classification;
- async job lifecycle;
- connector-neutral social turns;
- model gateway calls;
- tool orchestration;
- memory candidate pipeline;
- simulation brief generation;
- PostgreSQL persistence;
- audit events;
- owner approval gates.

### PostgreSQL

PostgreSQL owns structured machine state:

- users and identities;
- channels and connector bindings;
- jobs and job events;
- approvals;
- audit logs;
- memory candidates;
- search source references;
- simulation runs;
- report metadata;
- configuration records.

PostgreSQL does not replace Obsidian. It stores state, indexes, and audit facts.

### Obsidian

Obsidian owns readable durable knowledge:

- owner preferences;
- stable project facts;
- company reports;
- decision logs;
- research reports;
- simulation reports;
- postmortems;
- curated long-term memory.

Obsidian is not used as a transactional database.

### EverOS

EverOS owns automatic memory extraction and retrieval:

- episodes;
- atomic facts;
- user memory;
- agent memory;
- skill memory;
- semantic and hybrid recall.

EverOS output must pass Hermes memory governance before it becomes Obsidian
truth.

### MiroFish

MiroFish owns decision simulation:

- multi-agent debate;
- market and product scenarios;
- risk and opportunity rehearsal;
- final simulation reports.

MiroFish does not execute actions and does not own durable memory.

## 4. Runtime Contracts

The backend should expose stable contract groups:

- `/health`, `/ready`, `/version`;
- `/frontend/contract`;
- `/capabilities`, `/runtime/readiness`, `/platform/heartbeat`;
- `/jobs`;
- `/chat`;
- `/memory/status`;
- `/document/parse/session-list`, `/document/parse/session-summary`;
- `/document/parse/workbench-state`, `/document/parse/workbench-next`;
- `/document/parse/workbench-run-until-blocked`;
- `/document/parse/memory-review-pending`;
- `/document/parse/review-memory-candidate`;
- `/document/parse/memory-review-batch`;
- `/document/ingest-reports`, `/source-refs`;
- `/voice/asr/status`, `/document/parse/status`, `/intel/status`;
- `/simulation/status`, `/search/status`, `/index/status`.

Only endpoints proven by code should be shown as ready. Future endpoints must be
reported as `planned` or `missing_config`.
