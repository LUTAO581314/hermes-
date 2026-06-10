# Intelligence: Models, Search, And Crawling

## 1. Intelligence Decision

The lightweight server orchestrates intelligence. It does not run heavy local
models by default.

Use:

- OpenAI-compatible model gateway for model calls;
- TrendRadar for trends, RSS, hot lists, and public-opinion inputs;
- SearXNG as optional self-hosted metasearch;
- Firecrawl or equivalent API for page extraction when needed;
- OCR or multimodal APIs for image/document understanding;
- local Whisper only as a transitional lightweight ASR path.

## 2. Model Gateway

The model gateway hides provider details behind one compatible contract.

Model slots:

- fast model for quick replies;
- summary model for reports;
- reasoning model for final judgment;
- vision model for image/document understanding;
- embedding/rerank provider when needed by memory search.

Secrets must stay server-side.

## 3. TrendRadar

TrendRadar provides:

- hot news;
- RSS;
- trend tracking;
- public-opinion events;
- recurring intelligence inputs.

It remains an isolated external runtime. Do not copy its source or internals
into this repository.

Hermes integrates TrendRadar through an adapter boundary:

- source discovery under `vendor/runtimes/trendradar`;
- GPLv3 license and commercial-boundary reporting;
- CLI command planning for the upstream `trendradar` module;
- MCP server command planning for the upstream `mcp_server.server` module;
- future MCP-backed live intelligence calls through `TRENDRADAR_MCP_URL`.

Current Hermes CLI surface:

```bash
python -m src.hermes intel status
python -m src.hermes intel doctor-command
python -m src.hermes intel schedule-command
python -m src.hermes intel mcp-command --transport http --host 127.0.0.1 --port 3333
```

`TRENDRADAR_MCP_URL` enables future live MCP-backed intelligence calls. Without
it, Hermes reports `source_ready` and still exposes the real upstream commands
needed to start or diagnose TrendRadar.

## 4. SearXNG

SearXNG is optional.

Use it when:

- plain web search is needed;
- hosted search provider keys should be avoided;
- self-hosted metasearch is acceptable.

Do not use SearXNG as a trend engine. It supplements TrendRadar.

Hermes integrates SearXNG as an external Docker/Linux service, not as a Windows
worktree checkout. The SearXNG JSON API contract is:

- `GET /search?q=<query>&format=json`
- `POST /search` with `q=<query>&format=json`
- SearXNG `settings.yml` must enable the `json` output format

Current Hermes CLI surface:

```bash
python -m src.hermes search status
python -m src.hermes search docker-command
python -m src.hermes search query --query "bairui agent"
```

`SEARXNG_BASE_URL` enables live metasearch calls. Without it, Hermes reports
`missing_config` and still exposes the Docker command and API contract needed
to deploy SearXNG correctly.

## 5. Research Flow

```text
owner question
  -> Hermes route planner
  -> TrendRadar or SearXNG
  -> crawl/extract if needed
  -> source_refs in PostgreSQL
  -> model synthesis
  -> Obsidian report
  -> short owner summary
```

## 6. Source Rules

Research outputs must:

- store source references;
- distinguish evidence from inference;
- include retrieval time;
- avoid unsupported claims;
- write durable conclusions to Obsidian only after quality checks.
