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

## 3. Capability Map

| Capability | Recommended First Approach | Notes |
| --- | --- | --- |
| Web search and trends | External project runtime: TrendRadar first, SearXNG optional | Use source-backed output and cache repeated searches |
| Web crawling | Firecrawl or equivalent API | Convert pages to Markdown or structured JSON |
| Private memory search | Meilisearch or lightweight local index | Index Obsidian notes, not a replacement for Obsidian |
| OCR | OCR API or multimodal OCR | Use for screenshots, PDFs, receipts, tables, and images with text |
| Image understanding | Vision model API | Analyze screenshots, charts, documents, product photos, and UI states |
| Speech transcription | Whisper-compatible API | Convert audio/video speech to text |
| Video understanding | Video API or transcription plus sampled frames | Summarize clips, extract timelines, detect key moments |
| Financial data | Market data API | Research-only until a separate trading safety design exists |

## 4. Suggested First Providers

The exact providers can change. The architecture should hide providers behind adapters.

Search and crawling:

- TrendRadar as the first search/trend/news/RSS runtime.
- SearXNG for self-hosted metasearch if needed.
- Firecrawl for crawl and extraction workflows.
- Hosted search providers are not part of the current plan unless the owner explicitly changes direction later.

Image and OCR:

- A hosted multimodal model API for general image understanding.
- A dedicated OCR API when accuracy on Chinese text, tables, or documents matters.

Speech and video:

- Whisper-compatible speech-to-text API.
- Video-capable multimodal API for direct video understanding.
- Fallback workflow: extract audio transcript and sample frames, then summarize both.

Private memory:

- Obsidian remains the source of truth.
- Meilisearch or SQLite FTS can provide fast local search.
- Vector search can be added as an index, not as the only memory store.

## 5. Adapter Contract

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

## 6. Cost and Rate Limits

Required controls:

- Per-provider timeout.
- Retry limit.
- Daily cost estimate.
- Max file size.
- Max video length.
- Max pages per crawl.
- Cache repeated URL analysis.
- Log failures without retry loops.

## 7. Privacy Rules

Do not send sensitive data to external APIs unless the owner has approved that provider and workflow.

Sensitive examples:

- Passwords and API keys.
- Private chat screenshots.
- Financial account screenshots.
- Identity documents.
- Private contracts.
- Unpublished business documents.

## 8. Obsidian Write-Back

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

For video:

```text
title
duration
transcript summary
timeline
key frames
decisions or tasks
```

## 9. Minimal MVP

The first API MVP should prove:

1. Hermes can read one search/trend result from an external project runtime.
2. Hermes can crawl one page and write a source-backed note.
3. Hermes can analyze one image through a vision/OCR API.
4. Hermes can summarize one short video through transcript plus frames or a direct video API.
5. Every output is written to Obsidian and summarized to Feishu.

## 10. Iteration Policy

API integrations should be added one capability at a time.

Recommended order:

1. Search.
2. Web crawl/extraction.
3. OCR/image understanding.
4. Speech transcription.
5. Video summary.
6. Financial data.

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
