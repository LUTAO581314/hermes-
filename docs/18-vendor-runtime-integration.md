# Vendor Runtime Integration

## 1. Productization Decision

The product direction is mature-source-first, not blank-slate AI rewriting.
Hermes may directly use mature open-source runtime code when it helps the
product become more reliable and deployable.

The commercialization requirement is a quality bar:

- the product must be deployable, testable, observable, and maintainable;
- brand and customer-facing fields must default to `bairui`;
- licenses, notices, upstream names, and attribution must remain visible;
- GPL/AGPL runtimes can be used when the project accepts the corresponding
  public-source obligations or keeps them isolated as services;
- third-party runtime source belongs under `vendor/runtimes/` or another
  explicit boundary;
- our added value is productization: adapters, platform contract, deployment,
  license flow, readiness checks, audit, operations, and support workflow.

Do not replace mature working internals with AI-written blank-slate code just
to claim self-development. Prefer source-level control over source-level
reinvention.

## 2. Current Runtime Sources

| Runtime | Path | Purpose | License | Integration status |
| --- | --- | --- | --- | --- |
| EverOS | `vendor/runtimes/everos` | Automatic memory extraction and retrieval | Apache-2.0 | first source-level adapter |
| TrendRadar | `vendor/runtimes/trendradar` | Trend, RSS, hot-list, and public-opinion intelligence | GPLv3 | source-level adapter |
| MiroFish | `vendor/runtimes/mirofish` | Scenario simulation and multi-agent rehearsal | AGPLv3 | source-level adapter |
| SearXNG | Docker or Linux checkout | Optional metasearch | AGPLv3 | planned HTTP service adapter |

## 3. Adapter Boundary

Hermes adapter code belongs under `src/hermes/adapters/`.

Each adapter is responsible for:

- runtime source discovery;
- license and source boundary reporting;
- health and readiness checks;
- normalized request and response contracts;
- timeout and error handling;
- audit events for runtime calls;
- capability status exposure.

The upstream runtime remains responsible for its own internal algorithms,
storage layout, CLI, server, and domain logic.

## 4. EverOS Adapter Contract

EverOS is the first source-level productization target because it is already
present under `vendor/runtimes/everos` and uses Apache-2.0.

Hermes owns:

- `src/hermes/adapters/everos.py`;
- CLI commands under `python -m src.hermes memory ...`;
- HTTP routes under `/memory/...`;
- audit events for memory calls;
- operational configuration through `EVEROS_BASE_URL`,
  `EVEROS_MEMORY_ROOT`, and `EVEROS_TIMEOUT_SECONDS`.

EverOS owns:

- memory extraction;
- markdown memory layout;
- SQLite/LanceDB internals;
- `/api/v1/memory/add`;
- `/api/v1/memory/flush`;
- `/api/v1/memory/search`;
- `/api/v1/memory/get`.

This keeps the product honest: Bairui productizes, operates, brands, deploys,
tests, and supports the memory runtime while preserving the mature upstream
source boundary.

## 5. TrendRadar Adapter Contract

TrendRadar is the first intelligence runtime integration. Because it is GPLv3,
Hermes treats it as an isolated runtime with an explicit source and license
boundary.

Hermes owns:

- `src/hermes/adapters/trendradar.py`;
- CLI commands under `python -m src.hermes intel ...`;
- HTTP status route under `/intel/status`;
- operational configuration through `TRENDRADAR_PROJECT_ROOT`,
  `TRENDRADAR_MCP_URL`, and `TRENDRADAR_TIMEOUT_SECONDS`;
- capability and commercial-boundary reporting.

TrendRadar owns:

- hot-list crawling;
- RSS and trend data collection;
- AI filtering and report generation;
- notification formatting and dispatch;
- the `trendradar` CLI;
- the `mcp_server.server` MCP service.

Hermes must not copy TrendRadar internals into core code. Use the upstream CLI,
MCP server, process boundary, or service boundary.

## 6. MiroFish Adapter Contract

MiroFish is the scenario simulation and decision rehearsal runtime. Because it
is AGPLv3, Hermes treats it as an isolated runtime with an explicit hosted-use
source-delivery boundary.

Hermes owns:

- `src/hermes/adapters/mirofish.py`;
- CLI commands under `python -m src.hermes simulation ...`;
- HTTP status route under `/simulation/status`;
- operational configuration through `MIROFISH_PROJECT_ROOT`,
  `MIROFISH_BACKEND_BASE_URL`, `MIROFISH_FRONTEND_BASE_URL`, and
  `MIROFISH_TIMEOUT_SECONDS`;
- capability and commercial-boundary reporting.

MiroFish owns:

- Flask backend;
- Vite frontend;
- graph building;
- simulation creation, preparation, start, stop, and status APIs;
- report generation;
- `backend/scripts/run_twitter_simulation.py`;
- `backend/scripts/run_reddit_simulation.py`;
- `backend/scripts/run_parallel_simulation.py`;
- npm and uv dependency installation.

Hermes must not copy MiroFish internals into core code. Use the upstream npm
scripts, Flask API, process boundary, or service boundary.

## 7. Commercial Boundaries

Apache-2.0 runtimes such as EverOS are suitable for deeper productized
integration, while preserving LICENSE, NOTICE, upstream name, and attribution.

GPLv3 runtimes such as TrendRadar require source-code availability obligations
when distributed as part of the product package.

AGPLv3 runtimes such as MiroFish and SearXNG require special care for hosted
network service use. Before formal sale, distribution, or customer-hosted
operation, complete a license review and delivery-source checklist.

This document is general engineering guidance, not legal advice.

## 8. Integration Order

1. EverOS adapter for memory candidates and retrieval.
2. TrendRadar adapter for intelligence input.
3. MiroFish adapter for simulation briefs and reports.
4. SearXNG as an optional Docker-based metasearch runtime after Linux/server
   deployment.

## 9. Verification Requirements

Each runtime integration must prove:

- Hermes starts;
- `/health`, `/ready`, and `/capabilities` still work;
- CLI status command exposes runtime state;
- missing runtime configuration fails explicitly instead of pretending success;
- license/source status is visible;
- tests cover the adapter boundary.
