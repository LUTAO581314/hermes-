# Frontend: MOXI / Brain UI

## 1. Frontend Decision

MOXI / Brain UI is the primary frontend surface.

The frontend calls Hermes directly. It does not call any legacy external
frontend backend as a long-term authority, and new product UI should be
source-owned under MOXI.

## 2. Product Requirements

The UI must provide:

- chat-first command surface;
- capability dashboard;
- runtime settings;
- memory review inbox;
- task and job progress;
- approval queue;
- source-backed report viewer;
- simulation reports;
- social connector status;
- admin and deployment status.

## 3. Contract-First UI

The frontend reads:

- `/frontend/contract`;
- `/capabilities`;
- `/jobs`;
- `/runtime/readiness`;
- `/platform/heartbeat`;
- `/document/parse/session-list`;
- `/document/parse/session-summary`;
- `/document/parse/workbench-next`;
- `/document/parse/workbench-run-until-blocked`;
- `/document/parse/memory-review-pending`;
- `/document/parse/memory-review-batch`;
- `/document/ingest-reports`;
- `/source-refs`.

The frontend must not hard-code capability readiness.

`/frontend/contract` is now implemented by Hermes and is also available from
the CLI:

```bash
python -m src.hermes frontend-contract
```

It returns the product brand fields, supported UI screens, stable API groups,
status sources, user actions, and state values such as `ready`, `partial`,
`blocked`, `missing_config`, and `needs_review`. Planned endpoints must stay
outside the ready screen/action lists until the backend implements them.

## 4. Framework Path

Short term:

- preserve useful Brain UI assets and interaction patterns;
- serve static frontend behind Nginx;
- use Hermes APIs only.

Medium term:

- extract to Vite + React + TypeScript;
- define typed API client;
- add component tests;
- add role-aware admin views.

## 5. Node Package Manager Support

The current repository does not require a Node package manager because the
usable deployment target is the Hermes backend plus existing static assets.

When MOXI / Brain UI is extracted into a real frontend application, the standard
layout is:

```text
frontend/
  package.json
  package-lock.json
  src/
  public/
  dist/
```

Deployment scripts must detect `frontend/package.json` and run:

```text
npm ci && npm run build
```

The supported package managers are:

| Lockfile | Package manager | Install command | Build command |
| --- | --- | --- | --- |
| `package-lock.json` | npm | `npm ci` | `npm run build` |
| `pnpm-lock.yaml` | pnpm | `pnpm install --frozen-lockfile` | `pnpm run build` |
| `yarn.lock` | yarn | `yarn install --frozen-lockfile` | `yarn run build` |
| `bun.lockb` or `bun.lock` | bun | `bun install --frozen-lockfile` | `bun run build` |

If no lockfile exists, scripts may run npm install for early development, but
commercial releases must use one lockfile for reproducible builds.

The backend should serve built frontend files or let Nginx serve them directly.
Runtime secrets must never be bundled into frontend JavaScript.

## 6. UX Rules

The UI should show:

- what is running;
- what is waiting for owner approval;
- what data source was used;
- whether a capability is missing configuration;
- whether a reply is from memory, latest search, or simulation.

No UI should pretend a planned backend feature is already available.
