# Roadmap

This roadmap follows the sustainable iteration loop:

```text
phase brief -> scope lock -> implementation -> verification -> Chinese report -> memory cleanup -> risk review -> next phase
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
- Future phases have reporting and memory cleanup rules.

## Phase 1: VPS Runtime Foundation

Goal: deploy the minimal runtime safely on the VPS.

Tasks:

- Create non-root service user.
- Install Docker or selected service runner.
- Create `/opt/hermes-system`.
- Add environment template.
- Add health check.
- Add basic logs.
- Add safe stop/start/update commands.
- Optional: send one Feishu test message if credentials are ready.
- Write Phase 01 Chinese report.

Verification:

- Service starts.
- Health check responds.
- Logs are readable.
- No secrets are committed.
- Chinese report records access method, risks, and next steps.

## Phase 2: Feishu Company Management MVP

Goal: make Feishu the first useful production surface.

Tasks:

- Create Feishu app.
- Configure event subscription.
- Add company bot.
- Create project table.
- Create customer table.
- Create sales pipeline table.
- Create receivables table.
- Create daily report table.
- Create risk register.
- Add morning briefing job.
- Add owner approval queue.
- Write Phase 02 Chinese report.

Verification:

- Owner receives a company briefing in Feishu.
- Agent can detect one delayed task, missed follow-up, or risk item.
- Sensitive actions wait for owner approval.
- Report records configured tables, permissions, and remaining risks.

## Phase 3: Obsidian Governed Memory MVP

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
- Add weekly cleanup workflow.
- Add stale-memory review metadata.
- Write Phase 03 Chinese report.

Verification:

- One report is written to Obsidian.
- One memory candidate passes through inbox review.
- New durable memory links to at least one relationship axis.
- Owner can correct, archive, delete, or relink memory.
- Search/vector index policy is documented.

## Phase 4: API-First Research and Multimodal Layer

Goal: let the system search, crawl, read images, transcribe speech, and summarize video through APIs.

Tasks:

- Add search API adapter.
- Add crawl/extraction adapter.
- Evaluate TrendRadar as an isolated external trend/news intelligence runtime.
- Add OCR or image-understanding adapter.
- Add speech transcription workflow.
- Add video summary workflow.
- Add cost/rate-limit controls.
- Add Obsidian write-back templates.
- Write Phase 04 Chinese report.

Verification:

- One search result is summarized with sources.
- One webpage is extracted to a structured note.
- One image or OCR task is processed.
- One speech/video workflow is tested.
- No heavy local model is required on the VPS.

## Phase 5: Feishu Workflow Hardening

Goal: move from a bot to a reliable company operating assistant.

Tasks:

- Add task reminder workflow.
- Add daily and weekly company reports.
- Add meeting-note workflow.
- Add exception alert thresholds.
- Add structured audit logs.
- Add approval boundary checks.
- Write Phase 05 Chinese report.

Verification:

- Owner can request a company summary.
- System can push daily briefing and weekly report.
- Reminders and exception alerts are logged.
- Sensitive actions require owner approval.

## Phase 6: Research and Market Watch

Goal: create a research-only financial and opportunity watch pipeline.

Tasks:

- Create watchlist.
- Add market data source.
- Add news/research source.
- Add bull/bear/risk analysis template.
- Add daily market summary.
- Add Feishu summary.
- Write Phase 06 Chinese report.

Verification:

- A daily market brief is generated.
- Output is research-only.
- No broker or trading API is connected.
- Risk language is explicit.

## Phase 7: BaiLongma Personal Interaction Layer

Goal: add Chinese persona and richer personal interaction.

Tasks:

- Deploy BaiLongma or create adapter.
- Evaluate Nuwa Skill for optional advisory persona generation.
- Define personal memory boundary.
- Configure Feishu or WeChat-compatible interaction path.
- Add personal check-in.
- Add quick capture.
- Add Brain UI access boundary if used.
- Write Phase 07 Chinese report.

Verification:

- Owner can interact in Chinese.
- Personal notes do not bypass memory governance.
- Company-sensitive actions remain in Feishu/admin approval flows.

## Phase 8: WeChat Bridge Review

Goal: support WeChat only within acceptable risk boundaries.

Tasks:

- Prefer official channels where possible.
- Review personal-account automation risks.
- Avoid bypassing platform restrictions.
- Add rate limits.
- Add manual confirmation.
- Keep sensitive commands disabled.
- Write Phase 08 Chinese report.

Verification:

- WeChat route is documented.
- Owner understands trade-offs.
- No high-risk automation is enabled by default.

## Phase 9: MiroFish Simulation Lab

Goal: add structured multi-agent simulation and decision rehearsal.

Tasks:

- Deploy or connect MiroFish.
- Create simulation brief template.
- Build Obsidian export process.
- Build report import process.
- Test one company/project simulation.
- Test one market scenario simulation.
- Write Phase 09 Chinese report.

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
