# API Integrations

## 1. Decision

The first production version should be API-first for heavy model capabilities, but search is project-runtime-first.

The AI model provider should be configured as an OpenAI-compatible multi-model gateway. See [AI Model Gateway](AI_MODEL_GATEWAY.md).

The lightweight VPS is enough when it only runs:

- Hermes orchestration.
- Feishu and optional WeChat/BaiLongma adapters.
- API request routing.
- External search project routing.
- Queues, retries, and rate limits.
- Lightweight caching.
- Obsidian write-back.
- Logs and health checks.

The VPS should not run heavy local models for image recognition, video understanding, or large language model inference.

## 2. Why API-First And Project-First

Benefits:

- Fits a 4-core, 4 GB-class VPS.
- Faster to deploy.
- Lower maintenance.
- Easier upgrades when better models appear.
- Allows provider switching.
- Keeps GPU needs out of the first milestone.
- Allows search to use maintained projects such as TrendRadar or SearXNG without requiring a hosted search provider key.

Trade-offs:

- API cost must be tracked.
- Rate limits must be handled.
- Sensitive inputs need privacy review.
- Provider outages need fallback behavior.

## 3. Current Core Scope

Current scope is deliberately narrower than "all media capabilities".

Core capabilities to solve first:

- Hermes as the orchestration core.
- Human-like governed memory.
- Tool calling and external project routing.
- Image understanding and OCR through the active multimodal model.
- Voice input through local Whisper as a transitional ASR.

Temporarily out of scope:

- Video understanding.
- AI video generation.
- Music generation.
- Voice cloning.
- Autonomous trading.

These out-of-scope capabilities can be added later after the core loop is stable.

## 4. Current Server State

Verified current state:

- BaiLongma backend is running behind `https://bairui.chat/brain-ui.html`.
- Main model is configured as a custom OpenAI-compatible endpoint using `gpt-5.5`.
- Hermes is installed and available on the server.
- TrendRadar MCP is enabled for Hermes at `127.0.0.1:3333/mcp`.
- Local Whisper `tiny` is installed in a dedicated virtual environment and reachable through BaiLongma voice WebSocket flow.
- BaiLongma image understanding tool is available through `analyze_image`; video is intentionally not exposed.
- BaiLongma Brain UI exposes a read-only governed memory graph through `/memory/graph`; Obsidian remains the durable source of truth.

Known gaps:

- BaiLongma's own `/settings/web-search` provider keys are empty. Search should use Hermes + TrendRadar first.
- TTS provider settings exist, but no TTS key is configured yet.
- MiniMax is not configured yet, so MiniMax image/music/lyrics/TTS generation stays disabled.
- Feishu credentials are not configured yet.

## 5. Capability Map

| Capability | Recommended First Approach | Notes |
| --- | --- | --- |
| Web search and trends | External project runtime: TrendRadar first, SearXNG optional | Use source-backed output and cache repeated searches |
| Web crawling | Firecrawl or equivalent API | Convert pages to Markdown or structured JSON |
| Private memory search | Meilisearch or lightweight local index | Index Obsidian notes, not a replacement for Obsidian |
| OCR | Active multimodal model first, dedicated OCR API later | Use for screenshots, PDFs, receipts, tables, and images with text |
| Image understanding | Active multimodal model API | Implemented as BaiLongma `analyze_image` using the current `gpt-5.5` gateway |
| Speech transcription | Local Whisper tiny first, cloud ASR later if needed | Current transition solution is local Whisper on the VPS |
| Video understanding | Deferred | Do not expose in the current core phase |
| Financial data | Market data API | Research-only until a separate trading safety design exists |

## 6. Suggested First Providers

The exact providers can change. The architecture should hide providers behind adapters.

Search and crawling:

- TrendRadar as the first search/trend/news/RSS runtime.
- SearXNG for self-hosted metasearch if needed.
- Firecrawl for crawl and extraction workflows.
- Hosted search providers are not part of the current plan unless the owner explicitly changes direction later.

Image and OCR:

- A hosted multimodal model API for general image understanding.
- A dedicated OCR API when accuracy on Chinese text, tables, or documents matters.

Speech:

- Local Whisper `tiny` for transition.
- Cloud ASR can replace it later if latency or accuracy is not enough.
- Voice cloning is not ASR and should require explicit authorization and a separate provider.

Video:

- Frozen in the current core phase.
- Future fallback workflow: extract transcript and frames, then summarize both.

Private memory:

- Obsidian remains the source of truth.
- Meilisearch or SQLite FTS can provide fast local search.
- Vector search can be added as an index, not as the only memory store.

## 7. Adapter Contract

Every API or external-project adapter should return a normalized result:

```json
{
  "provider": "provider-name",
  "capability": "search|trend|rss|crawl|ocr|image|speech|video|market",
  "input_ref": "url-or-file-id",
  "summary": "short result",
  "structured_data": {},
  "sources": [],
  "confidence": "low|medium|high",
  "cost_estimate": "optional",
  "created_at": "ISO-8601 timestamp"
}
```

## 8. Cost and Rate Limits

Required controls:

- Per-provider timeout.
- Retry limit.
- Daily cost estimate.
- Max file size.
- Max video length when video scope is reopened.
- Max pages per crawl.
- Cache repeated URL analysis.
- Log failures without retry loops.

## 9. Privacy Rules

Do not send sensitive data to external APIs unless the owner has approved that provider and workflow.

Sensitive examples:

- Passwords and API keys.
- Private chat screenshots.
- Financial account screenshots.
- Identity documents.
- Private contracts.
- Unpublished business documents.

## 10. Obsidian Write-Back

Every useful API result should become a readable note:

```text
title
date
input
provider
summary
key facts
sources
uncertainties
next action
```

For video when the video phase is reopened:

```text
title
duration
transcript summary
timeline
key frames
decisions or tasks
```

## 11. Core MVP

The current core MVP should prove:

1. Hermes can call TrendRadar or another external project runtime.
2. BaiLongma can call the main model through the custom `gpt-5.5` gateway.
3. BaiLongma can use local Whisper for voice input.
4. BaiLongma can analyze one image through `analyze_image`.
5. Memory growth is governed by explicit intake, dream consolidation, review, and cleanup rules.
6. BaiLongma can visualize runtime memory as a governed candidate graph without promoting it automatically.
7. Each completed phase writes a Chinese report.

Operational runbook:

- Use [Core MVP Runbook](CORE_MVP_RUNBOOK.md) for service and capability verification.
- Use [Obsidian Write-Back Workflow](OBSIDIAN_WRITEBACK_WORKFLOW.md) for memory candidates, image conclusions, voice transcripts, corrections, dream consolidation, and reviewed phase cleanup.

## 12. Later API MVP

The first API MVP should prove:

1. Hermes can read one search/trend result from an external project runtime.
2. Hermes can crawl one page and write a source-backed note.
3. Hermes can analyze one image through a vision/OCR API.
4. Hermes can summarize one short video through transcript plus frames or a direct video API after video scope is reopened.
5. Every output is written to Obsidian and summarized to Feishu.

## 13. Iteration Policy

API integrations should be added one capability at a time.

Recommended order:

1. Search.
2. Web crawl/extraction.
3. OCR/image understanding.
4. Speech transcription.
5. TTS.
6. Feishu workflow.
7. Video summary.
8. Financial data.

Candidate tools:

- TrendRadar can provide trend/news intelligence through isolated MCP, HTTP, CLI, or report ingestion.
- SearXNG can provide self-hosted metasearch if plain web search is needed.
- Graphify can provide corpus graphing and document/code/media knowledge maps, especially for Obsidian and repository analysis.

Each new adapter must define:

- Provider.
- Input limits.
- Cost/rate limit.
- Privacy boundary.
- Normalized output contract.
- Obsidian write-back template.
- Chinese phase report entry.
