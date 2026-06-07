# Hermes Personal Agent System Master Plan

## 1. Vision

Build a private, long-running personal and company agent system that can remember, research, simulate, summarize, manage workflows, and assist with execution while keeping the owner in control.

This plan should be implemented through the sustainable iteration loop defined in [Sustainable Iteration Blueprint](SUSTAINABLE_ITERATION_BLUEPRINT.md). Each phase must be small, verified, reported in Chinese, and followed by memory dream consolidation plus reviewed cleanup.

The system should become a practical personal operating layer:

- A durable memory base for projects, people, company operations, preferences, decisions, research, and agent activity.
- A backend agent runner for scheduled jobs, web research, tool execution, monitoring, and structured workflows.
- A Feishu-based company management console for projects, tasks, customer follow-up, daily reports, approvals, and operating dashboards.
- A WeChat-facing personal companionship and lightweight reminder channel.
- A Chinese interaction surface through Feishu, WeChat-compatible bridges, and optional BaiLongma UI/persona features.
- A scenario simulation lab for complex decisions, market analysis, product planning, and multi-agent debate.
- A research-first financial analysis workflow with strict safety boundaries.
- External-project search plus API-first image recognition, speech transcription, and video understanding without running heavy local models on the lightweight VPS.
- Associative memory governance that prevents noisy, duplicate, stale, or sensitive data from becoming permanent memory.

Current implementation note:

The active implementation phase is narrower than the full plan. It is focused on Hermes, BaiLongma, governed human-like memory, tool calling, image understanding, and local Whisper voice input. Video, Feishu company operations, TTS, simulations, and trading remain later-stage capabilities until the core loop is stable.

## 2. Core Stack

| Layer | Tool | Role |
| --- | --- | --- |
| Durable memory | Obsidian | Human-readable long-term memory, backlinks, project notes, reports, decision records |
| Memory governance | Obsidian links, MOC notes, Canvas, inbox, review rules | Relationship-based memory, deduplication, staleness review, correction, deletion, and index rebuilds |
| Runtime agent | Hermes | Server-side automation, scheduled jobs, research, tool execution, MCP and skill orchestration |
| Company console | Feishu | Tasks, reports, projects, approvals, meetings, dashboards, and owner confirmation loops |
| Personal channel | WeChat | Companionship, personal reminders, quick capture, lightweight alerts |
| Chinese interaction | BaiLongma | WeChat/Feishu-style interaction, Brain UI, persona memory, Chinese UX |
| Simulation lab | MiroFish | Multi-agent scenario simulation, prediction, decision rehearsal, report generation |
| Messaging | Feishu first, WeChat later | Alerts, daily summaries, manual commands, confirmation loops |
| Financial research | Hermes skills + external data APIs | Watchlists, news, filings, indicators, summaries, risk analysis |
| Search runtimes | TrendRadar first, SearXNG optional | Web search, hot-news tracking, RSS, trend intelligence, research inputs |
| Crawl APIs | Firecrawl or equivalent | Webpage extraction and source conversion |
| Vision APIs | OCR and multimodal model APIs | Image OCR, screenshot analysis, chart reading, document image understanding |
| Video APIs | Speech-to-text and video understanding APIs | Transcription, scene summaries, timeline extraction, clip analysis |
| Storage/search | SQLite/Zep/vector store as needed | Machine-readable recall and semantic search |

## 3. Recommended System Shape

```text
Owner
  |
  v
Feishu / WeChat / Web UI / CLI
  |
  v
Channel router
  |-- Feishu company-management plane
  |-- WeChat personal-companion plane
  |-- CLI/admin plane
  |
  v
Hermes backend agent runner
  |
  +--> Obsidian durable memory
  +--> Feishu company tables, tasks, docs, approvals, calendar
  +--> MiroFish simulation lab
  +--> Market/news/research tools
  +--> Server and project automation
  +--> Notification adapters
```

The system should avoid placing all responsibility in one agent. Each tool should do the job it is strongest at.

## 4. Component Responsibilities

### 4.1 Obsidian

Obsidian is the main memory warehouse.

It should store:

- Owner preferences and durable instructions.
- Project files and project status.
- Agent roles, capabilities, and boundaries.
- Research notes and source summaries.
- Financial watchlists and thesis notes.
- Daily, weekly, and monthly reports.
- Decision logs and postmortems.
- MiroFish simulation outputs.
- Hermes and BaiLongma activity summaries.

Obsidian should not be treated as a hidden database. It is the readable, portable, editable source of truth.

Durable memory should not accept every raw input. Low-value chat noise, temporary drafts, unverified guesses, duplicate summaries, and raw logs should stay temporary, be summarized, or be archived. Time is only one index; durable memory should link to people, projects, goals, decisions, reports, risks, and events.

### 4.2 Hermes

Hermes is the backend operator.

It should handle:

- Scheduled research and reporting.
- Web search and source-backed summaries.
- Market watch jobs.
- GitHub/project monitoring.
- Server health checks.
- Tool and MCP orchestration.
- Command execution inside guarded environments.
- Writing summaries and reports back to Obsidian.

Hermes should not be given unrestricted authority over financial trades, account settings, or irreversible operations.

### 4.3 BaiLongma

BaiLongma is the Chinese-facing interaction and persona layer.

It should handle:

- Chinese chat UX.
- Feishu and WeChat-style message surfaces.
- Brain UI style memory display.
- Lightweight companionship and continuous presence.
- Routing owner messages into Hermes workflows.
- Returning concise summaries and confirmations.

BaiLongma should not replace Obsidian as the durable memory store. It can keep interaction memory, but final durable records should be written to Obsidian.

### 4.4 Feishu

Feishu is the company management plane.

It should handle:

- Company task assignment and reminders.
- Project progress tracking.
- Customer and sales pipeline tables.
- Receivables and risk tracking.
- Daily, weekly, and monthly operating reports.
- Meeting scheduling and meeting-note workflows.
- Approval reminders and owner confirmation loops.
- Employee status collection.

Feishu should be the first production interaction channel because it has official app, bot, task, document, calendar, approval, and table APIs. It should not be used to silently approve money movement, HR actions, public promises, or contract commitments.

### 4.5 WeChat

WeChat is the personal companionship and lightweight reminder plane.

It should handle:

- Personal daily check-ins.
- Quick capture of ideas.
- Lightweight reminders.
- Personal summaries.
- Carefully selected important alerts.

WeChat should not be the first channel for company operations. Personal-account bridges should remain optional and risk-reviewed.

### 4.6 MiroFish

MiroFish is the scenario simulation and report lab.

It should handle:

- Multi-agent debates.
- Market scenario analysis.
- Product strategy simulation.
- Risk/opportunity rehearsals.
- Decision comparison reports.

MiroFish should not be the main memory database. Its best role is to consume selected context from Obsidian, run simulations, and write the final report back to Obsidian.

## 5. Advanced Workflows

### 5.1 Daily Intelligence Briefing

Inputs:

- AI news.
- GitHub repository changes.
- Project status.
- Market news.
- Watchlist movement.
- Server health.

Process:

1. Hermes collects signals on a schedule.
2. Hermes ranks signals by relevance and urgency.
3. Hermes writes a detailed report to Obsidian.
4. Feishu sends a short summary.
5. Owner can ask follow-up questions through Feishu or WeChat.

Output:

- One concise notification.
- One complete Obsidian report.

### 5.2 Company Management Loop

Feishu should become the first real production scenario.

Inputs:

- Project table.
- Customer table.
- Sales pipeline.
- Receivables table.
- Employee daily reports.
- Meeting notes.
- Approval status.
- Risk register.

Process:

1. Hermes collects Feishu table, task, calendar, document, and approval signals.
2. Hermes identifies delayed tasks, missing reports, stalled deals, overdue receivables, and unhandled risks.
3. Hermes drafts reminders or summaries.
4. Low-risk reminders are sent automatically.
5. Sensitive actions ask the owner for approval.
6. Final reports are written to Obsidian and Feishu docs.

Output:

- Morning operating briefing.
- Midday exception alerts.
- Evening company summary.
- Weekly management report.
- Owner approval queue.

### 5.3 Financial Research Pipeline

Inputs:

- Watchlist.
- Price and volume data.
- News.
- Filings and earnings reports.
- Macro events.
- Social sentiment if available.

Agent roles:

- Bull analyst.
- Bear analyst.
- Risk analyst.
- News analyst.
- Technical analyst.
- Final judge.

Output:

- Watchlist status.
- Bull thesis.
- Bear thesis.
- Key catalysts.
- Risk list.
- Suggested next review date.
- Human-only decision checkpoint.

Real trading must remain disabled until a separate approval and safety design is completed.

### 5.4 Decision Simulation

Use MiroFish when the owner needs a structured simulation.

Examples:

- Should this project be built?
- Should this stock stay on the watchlist?
- Which agent architecture is better?
- What are the second-order risks?
- What execution plan has the best risk/reward?

Workflow:

1. Select relevant Obsidian context.
2. Convert it into a simulation brief.
3. Run MiroFish multi-agent simulation.
4. Export the report.
5. Write report and final decision back to Obsidian.

### 5.5 Personal Command Center

The owner should be able to ask:

- What matters today?
- What did the agents do last night?
- Which projects are stuck?
- What market signals changed?
- What needs my approval?
- Summarize this topic from memory and latest sources.

The system should answer from both durable memory and current research, and it should clearly separate old memory from newly fetched information.

### 5.6 API-First Multimodal Intelligence

The current lightweight VPS should not run large local vision or video models. It should run:

- Hermes and adapters.
- Message callbacks.
- API routing.
- Queues and retries.
- Lightweight caching.
- Obsidian write-back.
- Logs and health checks.

Search, image recognition, OCR, speech transcription, and video understanding should be external API calls first.

Recommended capability split:

- Search: TrendRadar as external trend/news/search runtime; SearXNG optional for self-hosted metasearch.
- Crawl/extraction: Firecrawl or equivalent API if webpage extraction is needed.
- Private memory search: Meilisearch or a lightweight local index over Obsidian notes.
- OCR: PaddleOCR service, cloud OCR, or multimodal model OCR API.
- Image understanding: Qwen-VL, GPT vision, Claude vision, Gemini vision, or equivalent API.
- Speech transcription: Whisper-compatible API or hosted speech-to-text service.
- Video understanding: video-capable multimodal API, or a pipeline of transcription plus sampled-frame image understanding.

Default rule:

```text
VPS = orchestrator and memory writer
External projects = search, trend, RSS, and hot-news intelligence
External APIs = heavy crawl, vision, speech, and video intelligence
Obsidian = durable final memory
```

## 6. Deployment Strategy

### Phase 0: Repository and Planning

Status: completed as the planning foundation.

Deliverables:

- Master plan.
- Architecture doc.
- Roadmap.
- Risk guardrails.
- Initial deployment assumptions.
- Sustainable iteration blueprint.
- Phase Chinese reports.

### Phase 1: Hermes MVP

Deliverables:

- Docker-based Hermes deployment on VPS.
- Non-root deployment user.
- Environment file template.
- API-first deployment profile for lightweight VPS.
- Reverse proxy plan if a domain is available.
- Basic health check.
- One scheduled daily summary job.
- Chinese phase report.

### Phase 2: Obsidian Memory Base

Deliverables:

- Vault folder structure.
- Memory schema.
- Memory governance rules.
- Associative memory axes.
- Obsidian MOC notes and Canvas map plan.
- Inbox and review workflow.
- Correction and deletion workflow.
- Staleness, memory dream, and reviewed cleanup schedule.
- Report templates.
- Decision log templates.
- Agent activity log templates.
- Write-back convention from Hermes.
- Chinese phase report.

### Phase 3: Feishu Bot

Deliverables:

- Feishu app setup guide.
- Event callback service.
- Message command router.
- Daily briefing push.
- Manual approval command format.
- Company-management tables for projects, customers, sales pipeline, receivables, risks, and daily reports.
- Morning briefing, exception alerts, and evening company summary.
- Chinese phase report.

### Phase 4: Financial Research MVP

Deliverables:

- Watchlist file.
- Market data adapter.
- News/research adapter.
- Daily market summary.
- Risk-only output.
- No real trading.
- Chinese phase report.

### Phase 4.5: Search Runtime and Multimodal API MVP

Deliverables:

- TrendRadar external-runtime adapter.
- Optional SearXNG metasearch adapter.
- Web crawling/extraction adapter.
- OCR API adapter.
- Image understanding API adapter.
- Speech transcription API adapter.
- Video summary workflow.
- Obsidian write-back template for multimodal analysis.

The VPS should only store inputs, outputs, metadata, and logs. It should not process large local models.

- Chinese phase report.

### Phase 5: BaiLongma Integration

Deliverables:

- BaiLongma deployment or adapter.
- Chinese conversation surface.
- Memory sync boundaries.
- Feishu/WeChat routing decision.
- Chinese phase report.

### Phase 6: MiroFish Simulation Lab

Deliverables:

- MiroFish deployment.
- Simulation input template.
- Obsidian-to-MiroFish export.
- MiroFish report import back to Obsidian.
- Chinese phase report.

### Phase 7: Hardened Operations

Deliverables:

- Backups.
- Logs.
- Access control.
- Secrets management.
- Update procedure.
- Disaster recovery notes.
- Chinese phase report.

## 7. Open Decisions

These decisions must be made before runtime deployment:

- Model provider: OpenAI, OpenRouter, Anthropic, local Ollama, or mixed.
- Domain name and HTTPS strategy.
- Feishu app permissions and company-management table schema.
- WeChat bridge risk acceptance and channel boundary.
- Whether BaiLongma should run on the same VPS or separately.
- Whether MiroFish should run only on demand or as a persistent service.
- Financial data provider.
- Search runtime provider or project.
- OCR/image/video API providers.
- Whether any broker/trading API will ever be connected.

## 8. Success Criteria

The first successful version should prove:

- The owner can send a command from Feishu or CLI.
- The owner can receive a Feishu company briefing.
- The system can identify one delayed task, overdue follow-up, or company risk from structured data.
- Hermes can complete a research task.
- The result is written to Obsidian.
- A short summary is pushed back to the owner.
- The system keeps logs and can be audited.
- No high-risk action happens without confirmation.
- Every completed phase includes a Chinese owner-facing report.

## 9. Non-Goals for the First Version

- Fully autonomous trading.
- Unrestricted WeChat personal account automation.
- Letting an agent run arbitrary root commands.
- Replacing Obsidian with opaque memory.
- Saving every chat message, log, or API result as permanent memory.
- Organizing memory only by time without relationships.
- Building every integration at once.

## 10. Final Recommendation

Start with:

```text
Hermes on VPS
+ Obsidian durable memory
+ Feishu company-management bot
+ Feishu project/customer/sales/risk tables
+ research-only financial watchlist
```

Then add:

```text
BaiLongma for Chinese interaction
+ MiroFish for simulation
+ WeChat bridge only after risk review
```

This gives the owner useful automation quickly while keeping the system understandable, recoverable, and safe.
