# Search Runtime Strategy

## 1. Decision

Hermes does not require a hosted search provider key for the current plan.

Search and trend intelligence should be connected through external projects:

- Primary: TrendRadar.
- Optional self-hosted search supplement: SearXNG.
- No hosted search provider is required in the current plan.

This keeps the lightweight VPS in orchestration mode while still allowing search, hot-news tracking, RSS, trend monitoring, and recurring intelligence reports.

## 2. Configuration

Use project-runtime settings:

```env
HERMES_SEARCH_MODE=external_project
HERMES_SEARCH_PROJECT=trendradar
HERMES_TRENDRADAR_BASE_URL=
HERMES_TRENDRADAR_MCP_COMMAND=
HERMES_SEARXNG_BASE_URL=
```

These template values remain useful for reproducible deployment, but the active VPS already has TrendRadar attached through Hermes MCP for the core phase.

## 3. TrendRadar Role

TrendRadar should provide:

- Hot news and trend radar.
- RSS aggregation.
- Recurring market, AI, competitor, and opportunity briefings.
- MCP, HTTP, CLI, or report-file integration when available.
- Feishu and Obsidian report inputs after the adapter is built.

MOXI Brain UI hotspot panel and TrendRadar are complementary:

- The MOXI hotspot panel is the visual inspection surface. It should open directly from the UI and show already-collected hot lists, not act as decoration.
- BaiLongma's hotspot implementation is now treated as migration reference only.
- Hermes exposes `GET /hotspots` as the backend authority for the panel.
- The Hermes hotspot endpoint reads TrendRadar's latest local output as a source-backed news/RSS event feed, so the public-opinion project's crawled items appear in the visible panel instead of staying hidden in backend files.
- TrendRadar or a dedicated public-opinion runtime should do deeper work: topic clustering, source expansion, sentiment/risk scoring, recurring tracking, and report generation.
- The UI panel should be able to hand a selected hotspot/topic to Hermes + TrendRadar for deeper analysis after the adapter is built.
- Cheap models such as `gpt-5.4-mini` may be used for batch classification, sentiment labels, and deduplication.
- Mid-tier models such as `gpt-5.4` may be used for hotspot summaries, digest drafts, and medium-depth trend synthesis.
- Stronger models such as `gpt-5.5` should be reserved for final judgment, strategy, and high-stakes reports.
- Models should not replace crawlers or source-backed trend runtimes.

License boundary:

- TrendRadar is GPL-3.0.
- Keep it as an isolated external runtime.
- Do not copy TrendRadar source code, prompt bundles, or implementation internals into this repository.

## 4. SearXNG Role

SearXNG can be added later if Hermes needs a self-hosted metasearch project.

Use it as:

- A local/private search endpoint.
- A supplement to TrendRadar, not a replacement for trend intelligence.
- A project runtime with URL configuration, not an API key dependency.

## 5. Adapter Contract

Hermes should normalize search-project output into the same shape used by other intelligence adapters:

```json
{
  "provider": "trendradar",
  "capability": "search|trend|rss|news",
  "input_ref": "query-or-topic",
  "summary": "short result",
  "structured_data": {},
  "sources": [],
  "confidence": "low|medium|high",
  "created_at": "ISO-8601 timestamp"
}
```

## 6. Phase Placement

TrendRadar has moved into Phase 2 as the first working external search/trend runtime.

Later search phases should improve normalization, Obsidian write-back, source tracking, and optional metasearch.

Recommended order:

1. Keep TrendRadar as an isolated runtime.
2. Verify Hermes can see TrendRadar through MCP.
3. Normalize TrendRadar output into source-backed notes or reports.
4. Write one trend/search result to Obsidian through the intake workflow.
5. Send a short owner-facing summary through Feishu after Feishu is ready.
6. Add SearXNG only if plain metasearch is still needed.

## 7. Current Status

TrendRadar is now attached as the first external search/trend runtime for the core Hermes phase.

Current verified direction:

- TrendRadar runs as an isolated external project.
- Hermes MCP points to TrendRadar at `127.0.0.1:3333/mcp`.
- MOXI Brain UI has a visible hotspot button and Hermes `/hotspots` is the first visual hot-list surface.
- Hermes `/hotspots` returns normalized TrendRadar-backed `items`, `feed`, and `platforms` data for clickable panel cards.
- Hot-list titles are clickable. If a source item has an original URL, the UI opens that URL; otherwise it falls back to a platform search URL.
- BaiLongma's own web-search provider keys can stay empty for now.
- Search should go through Hermes + TrendRadar first.
- SearXNG remains optional and should be added only if plain metasearch is still needed.

Phase 2 acceptance check:

```bash
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.local/bin:/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  hermes mcp list
```

TrendRadar should appear enabled. Output should not include secrets.
