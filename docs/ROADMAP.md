# Roadmap

This roadmap follows the sustainable iteration loop:

```text
phase brief -> scope lock -> implementation -> verification -> Chinese report -> memory dream -> reviewed cleanup -> risk review -> next phase
```

## Phase 0: Planning Foundation

Status: completed in documentation.

Goal: turn the empty repository into a complete, sustainable planning base.

Completed:

- Master plan.
- Technical architecture.
- Optimized company/personal/backend architecture.
- API-first integration strategy.
- Memory governance.
- Chinese report policy.
- Risk guardrails.
- Sustainable iteration blueprint.
- Phase 00 Chinese reports.

Exit criteria:

- Repository explains the intended system.
- Every core decision has a document.
- Future phases have reporting, memory dream, and reviewed cleanup rules.

## Phase 1: VPS Runtime Foundation

Status: completed for the first safe-mode runtime deployment.

Goal: deploy the minimal runtime safely on the VPS.

Tasks:

- Create non-root service user.
- Install selected service runner. Completed with systemd on the VPS.
- Create `/opt/hermes-system`. Completed on the VPS.
- Add environment template. Completed locally.
- Add health check. Completed locally.
- Add readiness check. Completed locally.
- Add basic logs. Completed locally.
- Add safe stop/start/update commands. Completed locally.
- Add Docker/Compose deployment files. Completed locally.
- Add local tests. Completed locally.
- Add AI model gateway configuration discovery. Completed locally and on VPS.
- Add WeChat companion-channel safe configuration placeholders. Completed locally.
- Add WeChat companion-channel strategy and guardrails. Completed locally.
- Fix graceful systemd shutdown behavior. Completed locally.
- Optional: send one Feishu test message if credentials are ready.
- Write Phase 01 Chinese report. Completed.

Verification:

- Service starts locally.
- Health check responds locally.
- Readiness check responds locally.
- Logs are readable.
- VPS SSH TCP reachability is confirmed.
- Remote service starts through `hermes-runtime.service`.
- Remote health check returns `ok`.
- Remote readiness check returns `ready`.
- Health check reports AI and WeChat configuration state without exposing secrets.
- WeChat mode remains disabled by default.
- WeChat personal-account bridge remains disabled by default.
- No secrets are committed.
- Chinese report records access method, risks, and next steps.

## Phase 2: Core Hermes and BaiLongma MVP

Status: core MVP verified; still open for Obsidian automation, memory dream actions, and provider-grade TTS.

Goal: stabilize the personal core before expanding into company workflows or video.

Locked scope:

- Hermes core runtime.
- BaiLongma Brain UI.
- GPT-5.5 custom model gateway.
- TrendRadar as external project search runtime.
- Human-like memory governance.
- Tool calling.
- Image understanding and OCR.
- Voice input through local Whisper.

Explicitly out of scope for this phase:

- Video understanding.
- AI video generation.
- Autonomous trading.
- Feishu company operations.
- Voice cloning.

Completed:

- BaiLongma is running behind the protected `bairui.chat` domain.
- GPT-5.5 is configured as the active custom model.
- Hermes is installed on the server.
- TrendRadar MCP is enabled for Hermes.
- WeChat ClawBot has restored saved credentials.
- Local Whisper `tiny` is installed and returns real transcripts through BaiLongma `/voice/cloud`.
- Brain UI has browser SpeechSynthesis fallback for web voice replies when cloud TTS credentials are missing.
- BaiLongma image understanding is available through `analyze_image`.
- Brain UI image attachments and WeChat ClawBot inbound images both route to `analyze_image`; one real WeChat image retest has passed.
- WeChat image-reading turns have a first performance guard: higher local priority, locked queue handling, typing hint attempt, and intake latency logging.
- Video understanding is intentionally not exposed.
- Write Phase 02 Chinese report. Completed.
- Add a core capability verification runbook. Completed locally.
- Add an Obsidian write-back workflow. Completed locally.
- Add a memory dream runbook for BaiLongma runtime memories. Completed locally.
- Add a read-only memory dream report tool. Completed locally.

Remaining:

- Turn Obsidian write-back into a Hermes tool or script.
- Turn BaiLongma memory dream suggestions into reviewed forget/merge/inbox/promote actions.
- Configure provider-grade TTS only after the owner provides MiniMax, Doubao, OpenAI TTS, or another approved key.
- Keep BaiLongma web-search settings empty unless a dedicated provider or SearXNG is selected; use Hermes + TrendRadar first.

Verification:

- Main model status shows `custom / gpt-5.5`.
- Hermes version command works.
- Hermes MCP list shows TrendRadar enabled.
- BaiLongma `/status` returns running and memory count.
- Local Whisper returns `asr_status`, `config_ok`, and a real transcript through `/voice/cloud`.
- `analyze_image` can OCR a PNG test image.
- Memory count is monitored after setup tests.

## Phase 3: Feishu Company Management MVP

Goal: make Feishu the first useful production surface.

Reference plan: [Feishu Company Management Plan](FEISHU_COMPANY_MANAGEMENT.md).

Tasks:

- Owner retests one real Feishu group @ event and confirms the reply appears in the same group.
- Verify one real Feishu single-chat event after the current identity patch.
- Review latest Feishu logs and conversation rows after real retest.
- Event idempotency by `event_id` or `message_id`. Completed for the first Feishu callback implementation.
- Fast callback ACK plus async processing queue. Completed for the first Feishu callback implementation.
- Feishu group-reply routing by `chat_id`. Completed for the first Feishu callback implementation.
- Add Feishu contact, department, role, and group/project context mapping.
- Add read-only document and file search.
- Add read-only Bitable record search.
- Create project, customer, sales, receivables, task, risk, daily report, approval queue, and audit-log tables.
- Add morning briefing and evening summary jobs.
- Add owner confirmation cards before any task/calendar/table write.
- Write Phase 03 Chinese report.

Verification:

- Owner receives a company briefing in Feishu based on real Feishu data.
- Agent can detect one delayed task, missed follow-up, or risk item.
- Agent can answer one company-document or Bitable question with a source link.
- Sensitive actions wait for owner approval.
- Report records configured tables, permissions, and remaining risks.

## Phase 3.5: Optimized Technical Path And Public Copy Pack

Status: completed locally for the documentation path; website publishing is the
next optional step.

Goal: make the architecture easy to copy, review, and attribute without exposing
private deployment details.

Completed:

- Add [Optimized Technical Path](OPTIMIZED_TECHNICAL_PATH.md) as the internal
  current engineering route.
- Rewrite [Public Technical Path](../public-ai-brief/TECHNICAL_PATH.md) as a
  white-label, copyable architecture and implementation sequence.
- Add [Batch Copy Pack](../public-ai-brief/COPY_PACK.md) for classmates and
  external AI reviewers.
- Add [Attribution Rules](../public-ai-brief/ATTRIBUTION.md) with the required
  repository source line.
- Update README and public brief entry points.
- Ignore local remote mirrors and exported public-brief folders.

Verification:

- Public copy materials must export without blocked private runtime terms.
- Secret scan must not find real credentials in committed docs.
- Chinese phase report records the optimization decision and next actions.

Next:

- Add or update the public website page from the public copy pack.
- Push the documentation update to GitHub after verification.

## Phase 4: Obsidian Governed Memory MVP

Goal: create durable, visual, owner-correctable memory.

Tasks:

- Create vault structure.
- Add `00-Inbox/needs-review`.
- Add owner preferences and corrections notes.
- Add MOC topic maps.
- Add Canvas visual memory map plan.
- Evaluate Graphify for optional corpus/memory graph generation.
- Add report templates.
- Add decision log template.
- Add memory intake gate.
- Add correction/deletion workflow.
- Add weekly memory dream and reviewed cleanup workflow.
- Add stale-memory review metadata.
- Write Phase 04 Chinese report.

Verification:

- One report is written to Obsidian.
- One memory candidate passes through inbox review.
- New durable memory links to at least one relationship axis.
- Owner can correct, archive, delete, or relink memory.
- Search/vector index policy is documented.

## Phase 5: Search Runtime and API-First Multimodal Layer

Goal: let the system search through external projects, then crawl, read images, transcribe speech, and later summarize video through APIs.

Tasks:

- Add external search-project adapter.
- Add crawl/extraction adapter.
- Evaluate and configure TrendRadar as an isolated external trend/news/search runtime.
- Add optional SearXNG configuration only if plain metasearch is still needed.
- Add OCR or image-understanding adapter.
- Add speech transcription workflow.
- Add metadata-only sticker bridge for prepared cute/kawaii/anime stickers.
- Add optional reviewed image-generation provider for original MOXI stickers.
- Add video summary workflow only after the core phase is stable.
- Add cost/rate-limit controls.
- Add Obsidian write-back templates.
- Write Phase 05 Chinese report.

Status update:

- Metadata-only sticker bridge is implemented locally.
- `/health` reports sticker bridge status without exposing keys.
- Runtime image generation is recognized as a supported optional provider path, but it remains disabled by default and review-gated.
- No sticker images or generated images are committed to Git.

Verification:

- One TrendRadar or search-project result is summarized with sources.
- One webpage is extracted to a structured note.
- One image or OCR task is processed.
- One speech workflow is tested.
- Video remains frozen unless explicitly reopened.
- No heavy local model is required on the VPS.

## Phase 6: Feishu Workflow Hardening

Goal: move from a bot to a reliable company operating assistant.

Tasks:

- Add task reminder workflow.
- Add daily and weekly company reports.
- Add meeting-note workflow.
- Add exception alert thresholds.
- Add structured audit logs.
- Add approval boundary checks.
- Write Phase 06 Chinese report.

Verification:

- Owner can request a company summary.
- System can push daily briefing and weekly report.
- Reminders and exception alerts are logged.
- Sensitive actions require owner approval.

## Phase 7: Research and Market Watch

Goal: create a research-only financial and opportunity watch pipeline.

Tasks:

- Create watchlist.
- Add market data source.
- Add news/research source.
- Add bull/bear/risk analysis template.
- Add daily market summary.
- Add Feishu summary.
- Write Phase 07 Chinese report.

Verification:

- A daily market brief is generated.
- Output is research-only.
- No broker or trading API is connected.
- Risk language is explicit.

## Phase 8: BaiLongma Personal Interaction Layer

Goal: add Chinese persona and richer personal interaction.

Tasks:

- Deploy BaiLongma or create adapter.
- Evaluate Nuwa Skill for optional advisory persona generation.
- Define personal memory boundary.
- Configure Feishu or official WeChat-compatible interaction path.
- Add personal check-in.
- Add quick capture.
- Add natural Chinese companion response policy.
- Add proactive-chat schedule, limit, mute, and audit controls before enabling proactive messages.
- Add Brain UI access boundary if used.
- Write Phase 08 Chinese report.

Verification:

- Owner can interact in Chinese.
- Personal notes do not bypass memory governance.
- Company-sensitive actions remain in Feishu/admin approval flows.

## Phase 9: WeChat Bridge Review

Goal: support real WeChat messaging only within acceptable risk boundaries.

Tasks:

- Prefer official channels where possible.
- Choose WeChat Official Account or WeCom customer-service path before any personal bridge.
- Add callback signature or token verification.
- Add message receive and reply adapter.
- Review personal-account automation risks.
- Avoid bypassing platform restrictions.
- Add rate limits.
- Add manual confirmation.
- Keep sensitive commands disabled.
- Write Phase 09 Chinese report.

Verification:

- WeChat route is documented.
- Owner understands trade-offs.
- No high-risk automation is enabled by default.

## Phase 10: MiroFish Simulation Lab

Goal: add structured multi-agent simulation and decision rehearsal.

Tasks:

- Deploy or connect MiroFish.
- Create simulation brief template.
- Build Obsidian export process.
- Build report import process.
- Test one company/project simulation.
- Test one market scenario simulation.
- Write Phase 10 Chinese report.

Verification:

- Simulation starts from Obsidian context.
- Final report returns to Obsidian.
- Decision output is marked as analysis, not certainty.

## Phase 10: Operations Hardening

Goal: make the system maintainable.

Tasks:

- Add backup script.
- Add restore runbook.
- Add log rotation.
- Add update procedure.
- Add health monitor.
- Add alerting.
- Add secret rotation notes.
- Add quarterly memory/index review.
- Evaluate Evolver only as an external retrospective reviewer, not as an autonomous production mutator.
- Write Phase 10 Chinese report.

Verification:

- System can be stopped, started, updated, backed up, and restored.
- Logs and alerts work.
- Recovery procedure is documented.

## Phase 11: Optional Execution Integrations

Goal: evaluate whether any real-world action APIs should be connected.

Examples:

- Broker API.
- Payment.
- Cloud provider write operations.
- Public posting.
- Deployment automation.

Required before enabling:

- Separate threat model.
- Owner approval flow.
- Spending or position limits.
- Full audit log.
- Kill switch.
- Dry-run mode.
- Chinese risk report.

Exit criteria:

- No irreversible action is enabled without a written safety design.
