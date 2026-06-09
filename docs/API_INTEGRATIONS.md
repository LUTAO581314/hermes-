# API Integrations

## 1. Decision

The first production version should be API-first for heavy model capabilities, but search is project-runtime-first.

The AI model provider should be configured as an OpenAI-compatible multi-model gateway. See [AI Model Gateway](AI_MODEL_GATEWAY.md).

The lightweight VPS is enough when it only runs:

- Hermes orchestration.
- Feishu and optional WeChat/MOXI frontend adapters.
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
- Sticker/media expression through a metadata-only bridge, with optional runtime image generation after review.

Temporarily out of scope:

- Video understanding.
- AI video generation.
- Music generation.
- Voice cloning.
- Autonomous trading.

These out-of-scope capabilities can be added later after the core loop is stable.

## 4. Current Server State

Verified current state:

- Brain UI is running behind `https://bairui.chat/brain-ui.html` while the backend converges to Hermes.
- MOXI Brain UI has a visible hotspot button that opens the current hot-list/public-opinion panel.
- Main model is configured as a custom OpenAI-compatible endpoint using `gpt-5.5`.
- Hermes is installed and available on the server.
- TrendRadar MCP is enabled for Hermes at `127.0.0.1:3333/mcp`.
- Hermes `/hotspots` is the target hotspot backend. It normalizes TrendRadar-backed news/RSS output for the Brain UI panel. BaiLongma's hotspot code is migration reference, not the final backend authority.
- Local Whisper `tiny` is installed in a dedicated virtual environment and verified through BaiLongma voice WebSocket flow.
- Brain UI voice output now has a no-cost browser SpeechSynthesis fallback when `/tts/stream` fails because provider credentials are missing.
- Image understanding should be owned by Hermes through the configured multimodal gateway. The existing Brain UI image attachment behavior is a frontend pattern to preserve during migration.
- Hermes now includes a metadata-only sticker bridge for cute/kawaii/anime-style prepared stickers. It records sticker intent, provider query, style, license notes, and channel send instructions without committing image files. The current image API can be used later as an optional `image_generation` provider for original MOXI/Moxi stickers after content review and runtime upload.
- Brain UI should expose a read-only governed memory graph from Hermes/Obsidian-derived state; Obsidian remains the durable source of truth.
- Feishu personal/bot chat webhook is configured and verified at `https://bairui.chat/social/feishu/webhook`; callback challenge passes through Nginx without Basic Auth, encrypted callback verification is supported, and the backend can obtain a Feishu tenant access token.
- Feishu inbound identity now keeps each Feishu sender as a separate company-context user (`FEISHU:<open_id>`) while preserving `feishu:open_id:<open_id>` as the reply target.

Known gaps:

- BaiLongma's own `/settings/web-search` provider keys are irrelevant to the final architecture. Search should use Hermes + TrendRadar first.
- TTS provider settings exist, but no production TTS key is configured yet. Browser speech fallback is usable for web testing, but it is not a stable provider-grade TTS path.
- MiniMax is not required for image understanding, including Brain UI image attachments and WeChat inbound image reading. MiniMax is not configured yet, so MiniMax image/music/lyrics/TTS generation stays disabled. The current API path can now provide image generation as a separate runtime provider, but it remains distinct from GPT-5.5 vision/image understanding and should be review-gated before chat delivery.
- Feishu chat callback and sender identity separation are ready, but file/document and company-management workflows are not implemented yet.

## 5. Capability Map

| Capability | Recommended First Approach | Notes |
| --- | --- | --- |
| Web search and trends | External project runtime: TrendRadar first, SearXNG optional | Use source-backed output and cache repeated searches |
| Hot-list/public-opinion panel | MOXI Brain UI `/hotspots` first, TrendRadar/deeper runtime for analysis | Panel shows crawled hot lists and TrendRadar feed cards; Hermes can later send selected topics to TrendRadar for clustering, risk scoring, and reports |
| Web crawling | Firecrawl or equivalent API | Convert pages to Markdown or structured JSON |
| Private memory search | Meilisearch or lightweight local index | Index Obsidian notes, not a replacement for Obsidian |
| OCR | Active multimodal model first, dedicated OCR API later | Use for screenshots, PDFs, receipts, tables, and images with text |
| Image understanding | Active multimodal model API | Move the current image-read behavior behind Hermes; Brain UI and WeChat inbound images should share the Hermes path; does not require MiniMax |
| Image generation | Current image-capable API provider | Separate from image understanding; use for reviewed original stickers or assets, not for reading images |
| Sticker bridge | Metadata-only provider bridge first; Stipop/GIPHY/image generation later | `outbound_media` now defines upload-or-text-fallback behavior; do not commit sticker files; Feishu sends by uploaded `image_key`, WeChat by runtime bridge/media id when verified |
| Speech transcription | Local Whisper tiny first, cloud ASR later if needed | Current transition solution is local Whisper on the VPS |
| Feishu chat and identity | Official Feishu event callback first | Webhook path must bypass site Basic Auth; encrypted events are supported; each Feishu sender is separated by open_id |
| Feishu files and docs | Read-only Feishu Drive/Docs/Search APIs first | Drive/docs search remains planned until tenant scopes are confirmed |
| Feishu company data | Bitable read-only first, write actions later | Phase 23 adds read-only user lookup and Bitable record-list tools; real data requires app permissions and configured app/table ids |
| Feishu tasks/calendar/approval | Confirmation-gated tools | Read first; create/update/approve only after cards, policy gates, and audit logs exist |
| Video understanding | Deferred | Do not expose in the current core phase |
| Financial data | Market data API | Research-only until a separate trading safety design exists |

## 6. Suggested First Providers

The exact providers can change. The architecture should hide providers behind adapters.

Search and crawling:

- TrendRadar as the first search/trend/news/RSS runtime.
- MOXI hotspot panel as the first visual surface for already-collected hot lists and external trend feed cards.
- SearXNG for self-hosted metasearch if needed.
- Firecrawl for crawl and extraction workflows.
- Hosted search providers are not part of the current plan unless the owner explicitly changes direction later.

Model routing for public-opinion work:

- `gpt-5.4-mini` or another cheap/fast model can handle high-volume labels, clustering, deduplication, sentiment tags, risk tags, and brief summaries.
- `gpt-5.4` can handle readable summaries, topic clustering, hotspot digests, daily/weekly public-opinion drafts, and medium-depth trend synthesis.
- `gpt-5.5` or another strongest available model should be reserved for final synthesis, strategy judgment, sensitive business decisions, or owner-facing reports.
- Crawling and source collection must remain a tool/runtime responsibility, not a model responsibility.

Image and OCR:

- A hosted multimodal model API for general image understanding.
- A dedicated OCR API when accuracy on Chinese text, tables, or documents matters.

Sticker/media expression:

- Stipop is the preferred first prepared-sticker provider because it is built for messaging sticker APIs.
- GIPHY stickers can be used only where attribution and API terms can be respected.
- OpenMoji and Noto Emoji are fallback emoji-style sources, not the main anime/kawaii style.
- The current image-generation API can create original MOXI sticker candidates at runtime. Keep it review-gated, do not imitate existing anime IP, and never commit generated images.
- Feishu and WeChat adapters should upload runtime images to the platform and send by platform token (`image_key`, `media_id`, or bridge equivalent).
- If a channel cannot upload media yet, adapters must send `outbound_media.text_fallback` and log `outbound_media.fallback_reason` instead of silently dropping the image reply.

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

Feishu company workflow:

- Use the official Feishu event callback or Channel SDK as the conversation layer.
- Treat Feishu CLI/OpenAPI MCP as an execution layer, not the public entry layer.
- Start with real-message verification, group @ context, contact/department lookup, and read-only document/Bitable search.
- Require explicit owner confirmation cards before task creation, calendar creation, table writes, announcements, or approval actions.
- Keep a structured audit log for actor, action, tool, input summary, output summary, and confirmation result.
- See [Feishu Company Management Plan](FEISHU_COMPANY_MANAGEMENT.md) for the full staged plan.

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
2. Hermes can call the main model through the custom `gpt-5.5` gateway.
3. Hermes or its approved media adapter can use local Whisper for voice input.
4. Hermes can analyze one image through the configured multimodal gateway.
5. Memory growth is governed by explicit intake, dream consolidation, review, and cleanup rules.
6. Brain UI can visualize runtime memory as a governed candidate graph without promoting it automatically.
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
