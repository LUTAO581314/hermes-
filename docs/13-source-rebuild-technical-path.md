# Source Rebuild Technical Path

## 1. Decision

MOXI Industrial Agent OS will be rebuilt as a source-owned product, but this
does not mean every subsystem must be written from a blank file.

The corrected decision is mature-source-first productization:

- use existing mature source code directly when it reduces product risk;
- keep licenses, notices, upstream names, and attribution;
- make the bairui/Hermes product boundary, deployment, configuration, tests,
  readiness, and platform contract ours;
- avoid AI-only blank-slate rewrites for complex agent internals unless the
  owned rewrite is clearly smaller and safer than integration.

The phrase "commercialization" is a quality standard: durable code, repeatable
deployment, observable operations, safe configuration, test coverage, and clear
handoff. It is not a requirement to close-source every component or hide public
upstream origins.

External projects are allowed only as:

- product substrate under `vendor/runtimes/`;
- isolated runtime dependencies;
- adapter targets;
- reference implementations;
- temporary migration aids;
- license-reviewed integrations.

They must not define the product architecture, backend authority, memory truth,
deployment model, or commercial user experience.

## 2. Target Source Tree

The repository should converge toward this structure:

```text
.
  src/                   # rebuilt Hermes backend source
  frontend/              # MOXI / Brain UI source, when created
  migrations/            # PostgreSQL migrations
  deploy/                # Nginx, systemd, container templates
  scripts/               # product deployment and verification scripts
  docs/                  # current product documentation only
  reports/               # historical phase summaries
  tests/                 # backend and product contract tests
```

What should not remain in the product repository:

- copied external application source trees;
- patch overlay collections for another product;
- public copy packs;
- generated export folders;
- legacy demo pages not used by the product;
- old deployment scripts that compete with the new deployment path.

## 3. Build The Product In Layers

### Layer 1: Product Runtime Foundation

Build:

- typed configuration;
- health and readiness;
- PostgreSQL connection;
- migration status;
- structured logging;
- audit logging;
- one-command deployment.

Acceptance:

- deploy command starts PostgreSQL and Hermes;
- `/health`, `/ready`, `/capabilities` work;
- database migration status is visible;
- logs and audit records are written.

### Layer 2: Durable Backend State

Build:

- jobs table;
- job events table;
- approvals table;
- connector events table;
- source refs table;
- memory candidates table.

Acceptance:

- jobs survive process restart;
- lifecycle events are queryable;
- sensitive actions produce approval rows;
- all important user-visible actions create audit rows.

### Layer 3: Frontend Source Ownership

Build:

- `frontend/` application;
- package-manager lockfile;
- production build;
- typed Hermes API client;
- capability dashboard;
- job progress UI;
- memory review UI;
- approval queue UI.

Acceptance:

- one-command deployment detects and builds frontend;
- built frontend calls Hermes only;
- no runtime secrets are bundled;
- planned features render as disabled or missing configuration.

### Layer 4: Memory Product Layer

Build:

- EverOS adapter;
- Obsidian writer;
- memory candidate review;
- promotion and rejection flow;
- source/evidence links.

Acceptance:

- one event enters EverOS;
- one candidate enters PostgreSQL;
- one reviewed memory writes to Obsidian;
- rejected memory remains out of durable notes.

### Layer 5: Intelligence Product Layer

Build:

- model gateway adapter;
- TrendRadar adapter;
- optional SearXNG adapter;
- source-backed research records;
- Obsidian report writer.

Acceptance:

- one source-backed trend report is generated;
- sources are stored in PostgreSQL;
- owner-facing summary distinguishes evidence and inference.

### Layer 6: Connector Product Layer

Build:

- Feishu official callback adapter;
- WeChat official/personal boundary adapter;
- QQ official/personal boundary adapter;
- media plan delivery;
- owner approval channel.

Acceptance:

- platform messages enter `/social/turn`;
- slow tasks use durable jobs;
- media delivery uses `/media/plan-send`;
- high-risk actions wait for owner approval.

### Layer 7: Simulation Product Layer

Build:

- simulation brief generator;
- MiroFish adapter;
- simulation run metadata;
- simulation report write-back;
- decision checkpoint.

Acceptance:

- one project simulation completes;
- one market scenario completes;
- final decision note is created only after owner confirmation.

## 4. Dependency Policy

Backend:

- start with Python standard library where practical;
- add third-party libraries only when they remove real product risk;
- prefer `uv` or `pip + requirements.txt` for dependency management;
- add PostgreSQL driver when database work begins;
- lock dependencies before commercial release.

Frontend:

- support npm, pnpm, yarn, and bun based on lockfile;
- require one lockfile for commercial builds;
- do not bundle runtime secrets.

Infrastructure:

- Docker Compose for usable local/server deployment;
- Nginx for domain server production;
- PostgreSQL for production data;
- external runtimes isolated behind adapters.

## 5. Verification Policy

Every meaningful phase must run:

- unit tests;
- compile checks;
- repository hygiene check;
- deployment config validation;
- doc link sanity for touched docs;
- manual smoke check for runtime endpoints when deployment changes.

Commercial milestones must also include:

- backup restore test;
- migration rollback plan;
- security review;
- license review;
- release note;
- owner-facing Chinese report.
