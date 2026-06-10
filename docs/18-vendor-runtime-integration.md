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
| FunASR | Docker/Linux service or `vendor/runtimes/funasr` | Voice ASR and OpenAI-compatible transcription | MIT | HTTP service adapter |
| MinerU | Docker/Linux service or `vendor/runtimes/mineru` | PDF/image/Office document parsing | MinerU Open Source License | CLI/service adapter |
| TrendRadar | `vendor/runtimes/trendradar` | Trend, RSS, hot-list, and public-opinion intelligence | GPLv3 | source-level adapter |
| MiroFish | `vendor/runtimes/mirofish` | Scenario simulation and multi-agent rehearsal | AGPLv3 | source-level adapter |
| SearXNG | Docker or Linux checkout | Optional metasearch | AGPLv3 | HTTP service adapter |
| Sonic | Docker/Linux service | Local internal search index | MPL-2.0 | TCP service adapter |

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

## 5. FunASR Adapter Contract

FunASR is the voice ASR runtime for transcription, voice commands, meeting
notes, and customer service call analysis. Hermes treats it as an isolated
service behind an OpenAI-compatible transcription API.

Hermes owns:

- `src/hermes/adapters/funasr.py`;
- CLI commands under `python -m src.hermes voice asr ...`;
- HTTP routes under `/voice/asr/status` and `/voice/asr/transcribe`;
- operational configuration through `FUNASR_PROJECT_ROOT`, `FUNASR_BASE_URL`,
  `FUNASR_PUBLIC_BASE_URL`, `FUNASR_MODEL`, and `FUNASR_TIMEOUT_SECONDS`;
- capability and commercial-boundary reporting.

FunASR owns:

- acoustic models;
- streaming and batch ASR internals;
- speaker, emotion, and multilingual ASR capabilities where configured;
- the upstream server process;
- `/v1/audio/transcriptions`.

Hermes must not pretend ASR is available until `FUNASR_BASE_URL` is configured.
The first integration surface is OpenAI-compatible file transcription; streaming
ASR and diarization controls can be added after the server contract is proven.

## 6. MinerU Adapter Contract

MinerU is the document parsing runtime for PDF, image, and Office ingestion.
Hermes treats it as a local CLI/service runtime because parsing can be heavy and
customer documents must stay inside the controlled deployment boundary.

Hermes owns:

- `src/hermes/adapters/mineru.py`;
- `src/hermes/document_pipeline.py`;
- CLI commands under `python -m src.hermes document parse ...`;
- file-backed planned ingestion records in `document_ingests.jsonl`;
- file-backed execution records in `document_ingest_runs.jsonl`;
- file-backed artifact records in `document_artifacts.jsonl`;
- file-backed Sonic indexing records in `document_index_runs.jsonl`;
- file-backed memory candidate records in `document_memory_candidates.jsonl`;
- file-backed memory review records in `document_memory_reviews.jsonl`;
- file-backed source reference records in `source_refs.jsonl`;
- file-backed Obsidian ingest report records in
  `document_ingest_reports.jsonl`;
- HTTP routes under `/document/parse/status`, `/document/parse/ingest-plan`,
  `/document/parse/run-ingest`, `/document/parse/register-artifacts`,
  `/document/parse/index-artifacts`, `/document/parse/memory-candidates`,
  `/document/parse/review-memory-candidate`,
  `/document/parse/memory-review-pending`,
  `/document/parse/memory-review-batch`, `/document/parse/source-refs`,
  `/document/parse/ingest-report`, `/document/parse/workbench-state`,
  `/document/parse/workbench-next`,
  `/document/parse/workbench-run-until-blocked`, `/document/ingests`,
  `/document/ingest-runs`, `/document/ingest-reports`, `/document/artifacts`,
  `/document/index-runs`, `/document/memory-candidates`, and
  `/document/memory-reviews`, plus `/source-refs`;
- PostgreSQL migration SQL for the production `source_refs` table and lookup
  indexes;
- Obsidian graph notes for reviewed candidates under
  `00-Inbox/everos-candidates/`, including YAML frontmatter, tags, a MOC note,
  and internal links to `[[Document Memory Candidates]]`, `[[Bairui]]`,
  `[[Hermes]]`, `[[EverOS]]`, and `[[Document Ingest <short-id>]]`;
- Obsidian graph reports for complete ingestion summaries under
  `05_Reports/document-ingests/`, including YAML frontmatter, tags, a MOC note,
  and internal links to `[[Document Ingest Reports]]`, `[[Document Memory
  Candidates]]`, `[[Bairui]]`, `[[Hermes]]`, `[[MinerU]]`, `[[Sonic]]`,
  `[[EverOS]]`, and `[[Obsidian]]`;
- operational configuration through `MINERU_PROJECT_ROOT`,
  `MINERU_OUTPUT_DIR`, `MINERU_BACKEND`, `MINERU_DEVICE`, and
  `MINERU_TIMEOUT_SECONDS`;
- capability and commercial-boundary reporting.

`/document/parse/workbench-state` is the UI/workbench contract for one ingest
workflow. It aggregates the ingest plan, parser runs, registered artifacts,
Sonic index runs, memory candidates and reviews, source references, Obsidian
ingest reports, blockers, warnings, counts, latest records, and the next safe
action into a single response. `/document/parse/workbench-next` executes that
next safe action and returns the refreshed state.
`/document/parse/workbench-run-until-blocked` repeats safe actions until the
workflow completes or stops on `needs_review`, `failed`, `not_found`,
`no_progress`, or `step_limit_reached`. It stops with `needs_review` for memory
candidate review so owner authorization remains explicit. Missing runtime
configuration is surfaced as a warning or blocker instead of being hidden
behind fake success.

`/document/parse/memory-review-pending` and
`/document/parse/memory-review-batch` are the product workbench review
contracts. Batch review reuses the single-candidate review path so EverOS
promotion, duplicate protection, audit events, and Obsidian graph notes remain
consistent.

MinerU owns:

- document layout analysis;
- OCR/parsing models;
- Markdown and JSON generation;
- extracted image/table/formula artifacts;
- the upstream CLI and optional service modes.

Hermes may create a planned ingestion record before execution. That record is
not a parsed result. The supervised worker may then execute the stored MinerU
command and record stdout, stderr, exit code, timeout, or missing executable
errors. Artifact registration then scans the real output directory and stores
path, relative path, artifact type, MIME type, byte size, and sha256 for each
produced file. Sonic indexing, EverOS memory candidates, source reference
creation, and Obsidian ingest report generation remain separate pipeline
phases.
The Sonic indexing phase only indexes registered text-like artifacts
(Markdown, text, JSON, and HTML) and records skipped/failed artifacts
explicitly.
The memory candidate phase creates `pending_review` document facts only. It
does not call EverOS or promote anything into Obsidian until a later review
step approves the candidate.

## 7. TrendRadar Adapter Contract

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

## 8. MiroFish Adapter Contract

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

## 9. SearXNG Adapter Contract

SearXNG is the optional self-hosted metasearch runtime. Because the upstream
repository has Windows-incompatible checkout paths and is AGPLv3, Hermes treats
it as a Docker/Linux HTTP service instead of a vendored Windows source tree.

Hermes owns:

- `src/hermes/adapters/searxng.py`;
- CLI commands under `python -m src.hermes search ...`;
- HTTP routes under `/search/status` and `/search/query`;
- operational configuration through `SEARXNG_BASE_URL`,
  `SEARXNG_PUBLIC_BASE_URL`, and `SEARXNG_TIMEOUT_SECONDS`;
- capability and commercial-boundary reporting.

SearXNG owns:

- search engines and metasearch routing;
- the `/search` endpoint;
- output format configuration;
- its Docker image and settings files.

The JSON API requires `format=json`, and SearXNG configuration must permit the
`json` output format. Hermes must not pretend SearXNG is available until
`SEARXNG_BASE_URL` is configured.

## 10. Sonic Adapter Contract

Sonic is the local internal search index runtime. It is not a public web search
tool and does not replace SearXNG.

Hermes owns:

- `src/hermes/adapters/sonic.py`;
- CLI commands under `python -m src.hermes index ...`;
- HTTP routes under `/index/status`, `/index/ping`, `/index/push`, and
  `/index/query`;
- operational configuration through `SONIC_HOST`, `SONIC_PORT`,
  `SONIC_PASSWORD`, and `SONIC_TIMEOUT_SECONDS`;
- `infra/sonic/config.cfg` for Docker-based local service deployment;
- capability and commercial-boundary reporting.

Sonic owns:

- token indexing;
- local object lookup;
- the TCP channel protocol;
- persistence under its own store directory;
- its Docker image and upstream Rust implementation.

Hermes talks to Sonic through the upstream channel protocol instead of copying
Rust internals into Hermes core.

## 11. Unified Runtime Readiness

Hermes exposes runtime orchestration readiness through:

- `python -m src.hermes runtime-readiness`
- `GET /runtime/readiness`

This is the machine-readable bridge between adapters and deployment
orchestration. Scripts and the Bairui platform should consume readiness
blockers and warnings instead of scraping logs.

## 12. Commercial Boundaries

Apache-2.0 runtimes such as EverOS are suitable for deeper productized
integration, while preserving LICENSE, NOTICE, upstream name, and attribution.

MIT runtimes such as FunASR are suitable for productized ASR integration, while
preserving LICENSE, upstream name, and attribution.

MinerU uses a project-specific open-source license based on Apache-2.0 with
additional terms. Treat it as commercial-review-required before customer
distribution or hosted parsing service use.

GPLv3 runtimes such as TrendRadar require source-code availability obligations
when distributed as part of the product package.

AGPLv3 runtimes such as MiroFish and SearXNG require special care for hosted
network service use. Before formal sale, distribution, or customer-hosted
operation, complete a license review and delivery-source checklist.

MPL-2.0 runtimes such as Sonic can be operated as external services while
preserving license notices and any modified-file obligations if the upstream
source is changed.

This document is general engineering guidance, not legal advice.

## 13. Integration Order

1. EverOS adapter for memory candidates and retrieval.
2. FunASR adapter for voice ASR and audio-to-text ingestion.
3. MinerU adapter for document parsing and knowledge ingestion.
4. TrendRadar adapter for intelligence input.
5. MiroFish adapter for simulation briefs and reports.
6. SearXNG as an optional Docker-based metasearch runtime after Linux/server
   deployment.
7. Sonic as a Docker-based local index for Bairui-owned notes, logs, documents,
   and task records.

## 14. Verification Requirements

Each runtime integration must prove:

- Hermes starts;
- `/health`, `/ready`, and `/capabilities` still work;
- CLI status command exposes runtime state;
- missing runtime configuration fails explicitly instead of pretending success;
- license/source status is visible;
- tests cover the adapter boundary.
