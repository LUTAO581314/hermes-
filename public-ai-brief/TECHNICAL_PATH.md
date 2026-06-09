# MOXI Technical Path

Technical path source: https://github.com/LUTAO581314/hermes-

## 1. Goal

MOXI is a lightweight personal and company agent system. It should combine
natural conversation, tool calling, governed memory, public-opinion
intelligence, image understanding, voice interaction, sticker/media expression,
and later company workflow management.

The first engineering target is not "an agent that can do everything". The
first target is a stable, auditable, copyable core loop:

```text
user message
  -> interaction surface
  -> channel policy
  -> orchestration core
  -> governed memory context
  -> selected tools or external runtimes
  -> model response
  -> visible result
  -> reviewed memory or report write-back
```

## 2. Architecture Decision

Use the server as an orchestrator, not as a heavy model host.

The lightweight VPS should run:

- web and messaging entry points,
- queues and task routing,
- model gateway calls,
- memory governance,
- tool adapters,
- logs and health checks,
- static panels and dashboards.

Heavy or specialized work should be API-first or external-runtime-first:

- large reasoning models,
- image/OCR understanding,
- formal TTS,
- sticker/media expression through APIs, provider metadata, or runtime image
  upload,
- search expansion,
- crawling and extraction,
- future video understanding,
- high-volume public-opinion analysis.

The repository itself is the technical-path and control-plane source. Large
upstream projects should be installed as external runtimes or separate forks,
then shaped by documented overlays and patches. This keeps the main repository
small, auditable, and easy for classmates or external AI reviewers to copy
without hiding the source credit.

## 3. Module Boundaries

| Module | Responsibility | First-version rule |
| --- | --- | --- |
| Interaction surface | Web chat, personal channel, future company channel, voice controls, visual panels | Keep UI thin and observable |
| Channel policy | Decide whether a message is personal, company, admin, or high-risk | Do not let one chat surface control everything |
| Orchestration core | Queueing, task routing, tool calls, model selection, retries | One normalized task format |
| Model gateway | Fast, summary, reasoning, and vision model slots | No hard-coded model everywhere |
| Memory governor | Intake rules, review, dream consolidation, durable write-back | Working memory is not permanent memory |
| Tool runtime | Search, crawl, documents, company data, media, server checks | Tools return structured evidence |
| Public-opinion intelligence | Hot lists, feed cards, source expansion, clustering, reports | Hot items are not facts until verified |
| Sticker bridge | Prepared-sticker metadata, provider IDs, generated-sticker review, channel upload instructions | Do not bundle third-party or generated sticker files |
| Company workflow | Tasks, docs, calendar, tables, approvals, reports | Read first, write only after approval |
| Safety and audit | Permission levels, approval gates, logs, secret handling | High-risk actions are disabled by default |
| Capability matrix | Secret-safe readiness state for frontend and connector dashboards | UI reads capability state instead of guessing from raw config |

## 3.1 Repository And Upstream Boundary

| Area | Owned by this repository | External or forked runtime |
| --- | --- | --- |
| Technical path | Yes | No |
| Runtime contracts | Yes | Adapter-specific implementation |
| CI and hygiene checks | Yes | Separate runtime CI when needed |
| Secrets and sessions | Never committed | Server-only configuration |
| BaiLongma-style UI changes | Overlay docs and patches | Upstream checkout or dedicated fork |
| Attribution | Source line required | Preserve upstream license |

The preferred dependency model is:

```text
main MOXI repository
  -> documents architecture, reports, CI, and integration contracts
  -> installs upstream runtimes under an external directory
  -> applies focused overlays or patches
  -> keeps real secrets, logs, media, and sessions out of Git
```

Hermes keeps its own native agent logic. MOXI should connect to that logic
through runtime contracts and frontend adapters instead of duplicating it in
every chat surface.

## 4. Optimized Implementation Sequence

### Stage 1: Runtime Foundation

Build the smallest reliable service first.

- Deploy the service under a non-root runtime user.
- Keep secrets in environment files, never in Git.
- Add `/health` and `/ready`.
- Add restart policy, logs, smoke tests, and update scripts.
- Make the repository reproducible for another person.

Exit criteria:

- service starts,
- health check passes,
- readiness check passes,
- logs are readable,
- no secrets are committed.

### Stage 2: Core Agent Loop

Stabilize text chat, model calls, tool calling, image understanding, and voice
input before broad automation.

- Normalize every inbound message.
- Route tasks through a queue.
- Add model slots: `fast`, `summary`, `reasoning`, `vision`.
- Add a tool-call contract with structured outputs.
- Add image/OCR through the active vision-capable model.
- Add lightweight local ASR or an ASR provider for voice input.
- Keep formal TTS optional until a provider is selected.

Exit criteria:

- text chat works,
- image reading works,
- voice input transcribes,
- tool calls are visible in logs,
- the UI shows enough status for the user to know the agent is working.

### Stage 3: Memory Governance

Make memory useful before making it big.

- Separate working memory from durable memory.
- Store durable memory in human-readable notes.
- Use relationship axes: people, projects, goals, decisions, risks, reports,
  events, preferences.
- Treat time as metadata, not the main structure.
- Add a dream pass that clusters noise, duplicates, weak memories, and durable
  candidates.
- Require review before forgetting or promoting memory.

Exit criteria:

- test messages do not become durable memory,
- important decisions can be reviewed and corrected,
- memory can be visualized or linked,
- dream consolidation produces actionable suggestions.

### Stage 4: Public-Opinion And Search Intelligence

Turn hot lists into a real intelligence workflow.

- Show collected hot-list and feed items in the UI.
- Make titles clickable to original sources or safe search fallback links.
- Let the user select one item for deeper analysis.
- Expand sources through search or trend runtimes.
- Deduplicate and label with a fast model.
- Summarize with a summary model.
- Use the reasoning model only for final judgment, risk, strategy, or owner
  reports.
- Write final reports to durable notes only after review.

Exit criteria:

- the panel displays real collected items,
- each item has freshness and source metadata,
- one selected item can become a source-backed report,
- noisy hot-list items are not written to durable memory automatically.

### Stage 5: Company Workflow

Add company management only after identity, routing, and read-only data work.

- Distinguish who is speaking and where the message came from.
- Support single chat and group mentions without replying to the wrong place.
- Add event idempotency and fast acknowledgement.
- Build company identity mapping: users, departments, roles, groups, projects.
- Add read-only document search and table record search.
- Start company tools as read-only adapters: user/profile lookup and table
  record listing before any create/update/approval action.
- Add daily briefings and exception alerts.
- Add confirmation cards before task, calendar, table, approval, or document
  writes.

Exit criteria:

- the system knows who is speaking,
- group replies stay in the correct group,
- duplicate events do not trigger duplicate work,
- company answers include source links,
- sensitive writes wait for human approval.

### Stage 6: Rich Media And Voice Output

Keep this stage provider-driven and explicit.

- Browser TTS is enough for a first web voice reply.
- Provider-grade TTS needs a selected provider key.
- Prepared stickers should use provider metadata, provider IDs, or runtime
  image upload rather than bundled image files.
- Runtime image generation can create original stickers only after review and
  should not imitate existing anime IP, celebrities, or copyrighted sticker
  packs.
- Social media sends should use a neutral `outbound_media` envelope. If a
  channel cannot upload images yet, send the text fallback and log the reason
  instead of silently dropping the reply.
- Voice cloning must require explicit authorization and a clear use case.
- Video understanding should wait until the core loop, memory, and cost control
  are stable.

Exit criteria:

- voice output has a known provider or browser fallback,
- sticker sending has a metadata-only source path and a channel upload path,
- ASR and TTS are separated,
- video is not silently enabled,
- media costs and rate limits are visible.

## 5. Performance Strategy

Performance should be designed into the route, not patched only at the model
layer.

### 5.1 Surface Layer

The first optimization is human-visible responsiveness:

- send a short natural acknowledgement within 1-2 seconds for slow-looking
  social tasks,
- keep ordinary social replies short and conversational,
- show or send "thinking / looking / generating" state before image, search, or
  company workflows,
- never treat an acknowledgement as the final answer.

### 5.2 Bottom Layer

The second optimization is actual runtime latency:

- expose safe performance budgets through a runtime endpoint,
- log per-stage latency: intake, quick acknowledgement, context build, first
  token, tool call, final send,
- use a rule-first intent router before loading heavy context,
- gate tool schemas by route,
- expose a context-budget diagnostic so connectors can load only the needed
  recent messages, memory policy, and tool schemas,
- expose a connector first-action planner that returns direct-reply vs
  quick-ack, natural acknowledgement copy, route, context budget, and optional
  slow-job metadata,
- detect unfinished slow jobs for the same channel and target so follow-up
  messages append context instead of cancelling or duplicating work,
- enforce that behavior at the chat adapter boundary by returning a
  non-queued follow-up acknowledgement instead of starting another LLM turn,
- move image generation, image reading, search expansion, and company workflows
  into async jobs,
- expose safe slow-job metadata and state transitions without storing raw
  messages, screenshots, API responses, or secrets,
- expose connector lifecycle events such as acknowledgement sent, worker
  started, worker completed, and final delivered,
- implement those lifecycle events in the UI/runtime adapter itself, so an
  upstream chat loop can report native worker start, completion, failure, and
  final visible delivery without copying the whole upstream source tree,
- provide a small connector client or HTTP runbook so WeChat, Feishu, and web
  chat bridges do not duplicate the runtime state machine,
- add QQ as a first-class social connector after the runtime contract is stable,
  using the same `/social/turn` and `/jobs/event` lifecycle,
- lock slow multimodal jobs so follow-up text does not cancel them by accident,
- cache repeated public-opinion and document summaries,
- use smaller models for labels and deduplication, larger models only when the
  final answer needs judgment.

## 6. Permission Levels

| Level | Example | Default |
| --- | --- | --- |
| L0 Read | Read collected hot lists, health, source pages, documents | Allowed |
| L1 Draft | Draft a reply, summary, report, reminder | Allowed |
| L2 Notify | Send low-risk reminders or owner summaries | Allowed with logs |
| L3 Write | Create or update company tasks, tables, calendar events, notes | Approval required by scope |
| L4 Sensitive | Approval, HR, finance, legal, external promises | Owner confirmation required |
| L5 Irreversible | Trading, money movement, destructive server commands | Disabled until separate design |

## 7. Copyable Build Path

For another team to reproduce the technical path, copy this order:

1. Build the runtime foundation.
2. Add model gateway slots.
3. Add queue and callback safety.
4. Add image reading and voice input.
5. Add working memory plus durable-memory review.
6. Add public-opinion panel and source-backed reports.
7. Add company identity and read-only company data.
8. Add approval-gated company writes.
9. Add formal TTS and future video only after the core is stable.
10. Add dashboards, audit logs, cost tracking, and memory dream cleanup.

## 8. Non-Goals For The First Milestone

- autonomous trading,
- unreviewed permanent memory writes,
- broad company operations without approval gates,
- heavy local model inference on the lightweight VPS,
- hidden credential storage in committed files,
- exposing private deployment names, server details, or credentials.

## 9. Review Questions For Another AI

When asking another AI to review this path, ask it to focus on:

- whether the module boundaries are clean,
- whether the sequence is too broad,
- whether memory governance is strong enough,
- whether the public-opinion workflow is source-backed,
- whether model routing is cost-effective,
- whether the permission levels are strict enough,
- what one engineering task should be built next.
