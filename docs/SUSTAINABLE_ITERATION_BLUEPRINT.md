# Sustainable Iteration Blueprint

## 1. North Star

Build a durable personal and company AI operating system, not a one-off chatbot.

The system must become useful through repeated safe iterations:

- Plan a narrow phase.
- Deploy or document one working slice.
- Verify it.
- Write a Chinese owner-facing report.
- Capture lessons into Obsidian.
- Clean memory and remove noise.
- Decide the next phase.

## 2. Permanent Architecture

The architecture has three stable planes.

### 2.1 Company Management Plane

Primary surface: Feishu.

Purpose:

- Projects.
- Customers.
- Sales pipeline.
- Receivables.
- Daily reports.
- Tasks.
- Meetings.
- Approvals.
- Risk register.
- Company briefings.

Rule:

Feishu is the first production surface because company management needs structure, permissions, and audit trails.

### 2.2 Personal Companion Plane

Primary surface: WeChat and BaiLongma.

Purpose:

- Personal check-ins.
- Lightweight reminders.
- Quick capture.
- Companion chat.
- Important personal alerts.

Rule:

WeChat should stay personal and low-risk. It should not become the first company command channel.

### 2.3 Backend Intelligence Plane

Primary engine: Hermes.

Purpose:

- Task orchestration.
- Research.
- Scheduled jobs.
- API calls.
- Feishu analysis.
- Obsidian write-back.
- Memory governance.
- Owner approval queue.
- Logs and health checks.

Rule:

The VPS is an orchestrator. Heavy model work should be API-first unless a future GPU environment is intentionally added.

## 3. Memory Strategy

The system uses associative memory, not timestamp-only memory.

Time is metadata. Relationships are the memory structure.

Durable memory should link to:

- People.
- Projects.
- Goals.
- Customers.
- Decisions.
- Events.
- Risks.
- Reports.
- Repeated patterns.

Obsidian is the durable source of truth. Feishu is the operational workspace. Vector search and search engines are indexes, not truth.

## 4. Documentation System

The repository should keep these document roles clear:

| Document | Role |
| --- | --- |
| `README.md` | Entry point and current recommendation |
| `docs/SUSTAINABLE_ITERATION_BLUEPRINT.md` | Top-level operating model for long-term iteration |
| `docs/MASTER_PLAN.md` | Full product and system plan |
| `docs/ARCHITECTURE.md` | Technical architecture and flows |
| `docs/OPTIMIZED_ARCHITECTURE.md` | Company/personal/backend plane design |
| `docs/CANDIDATE_PROJECT_EVALUATION.md` | External project fit, license, and adoption plan |
| `docs/PHASE_01_RUNTIME_FOUNDATION.md` | Minimal Hermes runtime, health checks, deployment commands, and safe-mode defaults |
| `docs/MEMORY_GOVERNANCE.md` | Memory intake, graph, cleanup, correction, and index policy |
| `docs/API_INTEGRATIONS.md` | API-first search, OCR, image, speech, and video strategy |
| `docs/RISK_AND_GUARDRAILS.md` | Safety, approvals, secrets, trading, WeChat, Feishu, memory risks |
| `docs/ROADMAP.md` | Phase-by-phase delivery plan |
| `docs/CHINESE_REPORT_POLICY.md` | Required Chinese owner-facing reporting rule |
| `reports/*.zh-CN.md` | Phase reports for the owner |

## 5. Iteration Loop

Every phase follows the same loop.

```text
1. Phase brief
2. Scope lock
3. Implementation or documentation update
4. Verification
5. Chinese owner report
6. Memory update and cleanup
7. Risk review
8. Next-phase decision
```

### 5.1 Phase Brief

Define:

- Goal.
- Owner value.
- Scope.
- Non-goals.
- Required credentials or accounts.
- Risk level.
- Done criteria.

### 5.2 Scope Lock

Each phase should have one primary outcome.

Examples:

- "Hermes runs on VPS."
- "Feishu bot sends company briefing."
- "Obsidian memory vault accepts governed write-back."
- "Search and image APIs work through adapters."

### 5.3 Verification

Verification must be specific.

Examples:

- Service health endpoint responds.
- Feishu receives a test message.
- One report is written to Obsidian.
- One memory passes through inbox review.
- One stale note is archived.
- One API result is source-backed and written as a note.

### 5.4 Chinese Owner Report

Every phase must produce a Chinese report under:

```text
reports/
```

The report must include:

- 阶段目标
- 已完成内容
- 当前效果
- 风险与边界
- 需要主人确认的事项
- 下一阶段计划

Research notes may stay in English. Owner-facing phase reports must be Chinese.

### 5.5 Memory Cleanup

Every phase must end with memory hygiene:

- What should become durable memory?
- What should stay as a report?
- What should be archived?
- What should be deleted?
- Which Obsidian links or Canvas maps need updating?
- Does the search/vector index need rebuilding?

## 6. Quality Gates

A phase is not complete until it passes these gates.

### 6.1 Functionality Gate

The promised result works, or the report clearly says it does not.

### 6.2 Safety Gate

No secrets are committed. High-risk actions require owner approval. Sensitive data is not stored casually.

### 6.3 Memory Gate

Important outputs are written into Obsidian or the correct report. Raw noise is not promoted to durable memory.

### 6.4 Documentation Gate

README, roadmap, and relevant design docs are updated when the architecture or plan changes.

### 6.5 Chinese Report Gate

The owner receives a Chinese phase report.

### 6.6 Git Gate

Changes are committed and pushed to GitHub when the phase modifies the repository.

## 7. Phase Sequence

Recommended sustainable sequence:

### Phase 0: Planning Foundation

Status: completed in documentation.

Deliverables:

- Architecture.
- Optimized architecture.
- Memory governance.
- API-first strategy.
- Risk guardrails.
- Chinese reports.

### Phase 1: VPS Runtime Foundation

Goal:

Deploy the minimal runtime safely on the VPS.

Deliverables:

- Non-root service user.
- Docker or service runner.
- Environment template.
- Health check.
- Basic logging.
- Chinese deployment report.

### Phase 2: Feishu Company Management MVP

Goal:

Make Feishu the first useful production surface.

Deliverables:

- Feishu app.
- Company bot.
- Project/customer/sales/receivables/risk/report tables.
- Morning briefing.
- Owner approval queue.
- Chinese phase report.

### Phase 3: Obsidian Governed Memory MVP

Goal:

Create durable, visual, owner-correctable memory.

Deliverables:

- Vault layout.
- Inbox review flow.
- MOC notes.
- Canvas memory maps.
- Write-back template.
- Correction/deletion workflow.
- Cleanup schedule.
- Chinese phase report.

### Phase 4: API-First Research and Multimodal Layer

Goal:

Add external search, crawl, OCR, image, speech, and video intelligence through APIs.

Deliverables:

- Search adapter.
- Web extraction adapter.
- OCR/image adapter.
- Speech/video workflow.
- Cost/rate limits.
- Obsidian write-back.
- Chinese phase report.

Candidate additions:

- TrendRadar for external trend/news intelligence, isolated because of GPL-3.0.
- Graphify for graph and corpus mapping, especially when memory/document visualization is needed.

### Phase 5: Company Workflow Hardening

Goal:

Move from basic Feishu bot to reliable company operating assistant.

Deliverables:

- Task reminders.
- Daily/weekly company reports.
- Meeting notes.
- Exception alerts.
- Approval boundary.
- Audit logs.
- Chinese phase report.

### Phase 6: Personal Companion Layer

Goal:

Add BaiLongma/WeChat-style personal interaction after company and memory foundations are stable.

Deliverables:

- Personal check-in.
- Quick capture.
- Lightweight alerts.
- Personal memory boundaries.
- WeChat risk review.
- Chinese phase report.

### Phase 7: MiroFish Simulation Lab

Goal:

Add scenario simulation and decision rehearsal.

Deliverables:

- Simulation brief template.
- Obsidian export.
- MiroFish run.
- Report import.
- Decision note.
- Chinese phase report.

Candidate additions:

- Nuwa Skill for advisory-board persona generation and simulation roles.

### Phase 8: Optional Execution Integrations

Goal:

Only after strong approval gates, consider real-world execution APIs.

Examples:

- Broker API.
- Payment.
- Cloud provider write actions.
- Public posting.

Default:

Disabled until a separate safety design exists.

Candidate additions:

- Evolver may be evaluated later as an external phase-retrospective reviewer, but it must not self-modify production prompts, memory, or configuration.

## 8. Operating Cadence

Suggested cadence:

- Daily: system health, company briefing, task checks.
- Weekly: company report, memory cleanup, roadmap check.
- Monthly: architecture review, stale memory review, cost review.
- Quarterly: security review, permission review, index rebuild, strategy reset.

## 9. Owner Control Model

The owner remains the final authority.

The system can:

- Research.
- Summarize.
- Draft.
- Remind.
- Detect risks.
- Recommend.
- Prepare approvals.

The system cannot by default:

- Spend money.
- Trade.
- Sign contracts.
- Make HR decisions.
- Send external commitments.
- Delete important data.
- Store secrets in Git.

## 10. Definition of Sustainable

The project is sustainable when:

- Each phase is small enough to finish.
- Each phase produces a Chinese report.
- Memory stays clean and visual.
- The owner can correct the system.
- Risky actions have approval gates.
- The VPS stays lightweight.
- External APIs are replaceable.
- The repository remains the source of implementation truth.
- Obsidian remains the source of long-term memory truth.

## 11. Current Recommendation

The next implementation phase should be:

```text
Phase 1: VPS Runtime Foundation
```

But if Feishu credentials are ready, Phase 1 can include a very small Feishu smoke test:

```text
Hermes/service runner on VPS
+ health check
+ one Feishu test message
+ one Obsidian write-back placeholder
+ Chinese Phase 1 report
```
