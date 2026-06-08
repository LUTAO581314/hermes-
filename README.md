# MOXI Agent System

This repository is the planning, control-plane, and deployment home for a
personal and company agent system built around Hermes, Obsidian, BaiLongma,
MiroFish, Feishu, WeChat, QQ, and API-first intelligence adapters.

The goal is not to install one chatbot. The goal is to build a layered AI operating system for both personal work and company management:

- Obsidian stores durable human-readable memory.
- Hermes runs backend automation, research, tools, and scheduled jobs.
- Feishu is the primary company management console.
- WeChat is the personal companionship and lightweight reminder channel.
- BaiLongma provides a Chinese-facing interaction/persona layer across WeChat, Feishu, voice, and Brain UI style workflows.
- MiroFish acts as a scenario simulation and report lab.
- Feishu and WeChat deliver summaries, alerts, and human confirmation loops.
- Financial workflows stay research-first and require explicit human approval before any real trading action.
- Search uses external project runtimes such as TrendRadar or SearXNG; image recognition, speech, and video understanding remain API-first integrations. The lightweight VPS runs orchestration, not heavy local models.

## Current Status

Phase 0 planning and Phase 1 runtime foundation are complete. Phase 2 is now focused on the core Hermes + BaiLongma loop:

- BaiLongma Brain UI is running behind the protected `bairui.chat` domain.
- The public-facing Brain UI brand, browser title, agent profile name, and mark now show `MOXI`; BaiLongma remains the underlying runtime/project name.
- Hermes is installed on the VPS.
- TrendRadar is enabled as an isolated Hermes MCP search/trend runtime.
- The active BaiLongma model path uses the custom GPT-5.5 gateway.
- Local Whisper is configured and verified as the transitional voice-input ASR.
- Cloud TTS still needs an approved provider key; the Brain UI now falls back to browser speech synthesis when cloud TTS is unavailable.
- Image understanding is exposed through `analyze_image`.
- A metadata-only sticker bridge is available for cute/kawaii/anime-style prepared stickers. It stores intent profiles, provider queries, and channel send instructions only. Sticker images, generated images, platform media IDs, and API keys stay out of Git; runtime image generation can be enabled as a reviewed provider path.
- Video understanding is intentionally frozen for this phase.
- BaiLongma memory is treated as working memory; Obsidian remains the durable memory source of truth.
- Feishu callback, encrypted event handling, sender identity separation, event idempotency, fast ACK, and group-reply routing are implemented; real group retest by the owner is still required.

Current priority: finish the stable core while continuing Feishu Phase 3 with owner retesting, company identity mapping, read-only company data, and owner-confirmed actions.

## Documents

- [White-label Public AI Brief](public-ai-brief/README.md) - use this folder when asking external AI for technical-path advice without exposing the private runtime stack.
- [Quickstart](QUICKSTART.md) - run the minimal MOXI control plane and verify `/health`, `/ready`, and `/capabilities`.
- [Optimized Technical Path](docs/OPTIMIZED_TECHNICAL_PATH.md) - the current internal engineering path, module boundaries, performance plan, and copy/credit strategy.
- [Performance Optimization Plan](docs/PERFORMANCE_OPTIMIZATION_PLAN.md) - the surface-first and bottom-layer plan for sub-5-second social responsiveness, async slow jobs, latency telemetry, and model routing.
- [Capability Matrix](docs/CAPABILITY_MATRIX.md) - secret-safe readiness contract for frontend settings panels and dashboards.
- [Hermes Frontend Adapter Plan](docs/HERMES_FRONTEND_ADAPTER_PLAN.md) - how MOXI connects to Hermes native logic without rewriting it in the frontend.
- [Connector Integration Runbook](docs/CONNECTOR_INTEGRATION_RUNBOOK.md) - how WeChat, Feishu, and web-chat bridges call `/social/turn` and `/jobs/event`.
- [Upstream Dependency Strategy](docs/UPSTREAM_DEPENDENCY_STRATEGY.md) - how BaiLongma and other upstream runtimes are managed without copying full source trees into this repository.
- [QQ Connector Plan](docs/QQ_CONNECTOR.md)
- [Social Settings UI Optimization](docs/SOCIAL_SETTINGS_UI_OPTIMIZATION.md)
- [Technical Path Chinese Summary](docs/TECHNICAL_PATH_SUMMARY.zh-CN.md)
- [Sustainable Iteration Blueprint](docs/SUSTAINABLE_ITERATION_BLUEPRINT.md)
- [Master Plan](docs/MASTER_PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Optimized Architecture](docs/OPTIMIZED_ARCHITECTURE.md)
- [Candidate Project Evaluation](docs/CANDIDATE_PROJECT_EVALUATION.md)
- [Phase 01 Runtime Foundation](docs/PHASE_01_RUNTIME_FOUNDATION.md)
- [Core MVP Runbook](docs/CORE_MVP_RUNBOOK.md)
- [Feishu Company Management Plan](docs/FEISHU_COMPANY_MANAGEMENT.md)
- [Search Runtime Strategy](docs/SEARCH_RUNTIME.md)
- [AI Model Gateway](docs/AI_MODEL_GATEWAY.md)
- [WeChat Companion Channel](docs/WECHAT_COMPANION.md)
- [Memory Governance](docs/MEMORY_GOVERNANCE.md)
- [Obsidian Write-Back Workflow](docs/OBSIDIAN_WRITEBACK_WORKFLOW.md)
- [API Integrations](docs/API_INTEGRATIONS.md)
- [Sticker Bridge](docs/STICKER_BRIDGE.md)
- [Roadmap](docs/ROADMAP.md)
- [Risk and Guardrails](docs/RISK_AND_GUARDRAILS.md)
- [Chinese Report Policy](docs/CHINESE_REPORT_POLICY.md)
- [Current Chinese Phase Report](reports/phase-00-architecture-plan.zh-CN.md)
- [Memory Governance Chinese Report](reports/phase-00-memory-governance.zh-CN.md)
- [Sustainable Iteration Chinese Report](reports/phase-00-sustainable-iteration.zh-CN.md)
- [Candidate Projects Chinese Report](reports/phase-00-candidate-projects.zh-CN.md)
- [Phase 01 Runtime Foundation Chinese Report](reports/phase-01-runtime-foundation.zh-CN.md)
- [WeChat Companion Readiness Chinese Report](reports/phase-01-wechat-companion-readiness.zh-CN.md)
- [Phase 02 Core Hermes and BaiLongma Chinese Report](reports/phase-02-core-hermes-bailongma.zh-CN.md)
- [Phase 03 Feishu Company Management Chinese Report](reports/phase-03-feishu-company-management.zh-CN.md)
- [Phase 04 Optimized Technical Path Chinese Report](reports/phase-04-optimized-technical-path.zh-CN.md)
- [Phase 05 Sticker Bridge Chinese Report](reports/phase-05-sticker-bridge.zh-CN.md)
- [Phase 06 Social Performance Optimization Chinese Report](reports/phase-06-social-performance-optimization.zh-CN.md)
- [Phase 07 Context Slimming And Async Jobs Chinese Report](reports/phase-07-context-slimming-async-jobs.zh-CN.md)
- [Phase 08 Social Turn Planner Chinese Report](reports/phase-08-social-turn-planner.zh-CN.md)
- [Phase 09 Active Job Follow-Up Chinese Report](reports/phase-09-active-job-follow-up.zh-CN.md)
- [Phase 10 Worker Lifecycle Events Chinese Report](reports/phase-10-worker-lifecycle-events.zh-CN.md)
- [Phase 11 Connector Client And Runbook Chinese Report](reports/phase-11-connector-client-runbook.zh-CN.md)
- [Phase 12 Server Runtime Auth Fix Chinese Report](reports/phase-12-server-runtime-auth-fix.zh-CN.md)
- [Phase 13 QQ Connector And Social Settings UI Chinese Report](reports/phase-13-qq-and-social-settings-ui.zh-CN.md)
- [Phase 14 Repository CI And Upstream Strategy Chinese Report](reports/phase-14-repo-ci-and-upstream-strategy.zh-CN.md)
- [Phase 15 Frontend Adapter And Capability Matrix Chinese Report](reports/phase-15-frontend-adapter-and-capability-matrix.zh-CN.md)
- [Phase 16 BaiLongma Capability Matrix Chinese Report](reports/phase-16-bailongma-capability-matrix.zh-CN.md)
- [Phase 17 Frontend Contract Chinese Report](reports/phase-17-frontend-contract.zh-CN.md)
- [Phase 18 Server Social Turn Bridge Chinese Report](reports/phase-18-server-social-turn-bridge.zh-CN.md)
- [Phase 19 Progress Aware Chat UI Chinese Report](reports/phase-19-progress-aware-chat-ui.zh-CN.md)
- [Phase 20 Channel Plane Badges Chinese Report](reports/phase-20-channel-plane-badges.zh-CN.md)
- [Phase 21 Tool Lifecycle Events Chinese Report](reports/phase-21-tool-lifecycle-events.zh-CN.md)
- [Phase 22 Follow-Up Job Merge Chinese Report](reports/phase-22-follow-up-job-merge.zh-CN.md)

## Repository Automation

GitHub Actions runs on push, pull request, and manual dispatch:

- `python -m unittest discover -s tests`
- `python -m compileall hermes_runtime tests`
- `./scripts/check-repo-hygiene.ps1`

The hygiene check blocks tracked runtime data paths and obvious committed API
keys or private key material. Real `.env` files, connector sessions, chat logs,
QR-code state, generated media, and Obsidian working vault data must stay out of
Git.

## Upstream Runtime Dependencies

This repository is the MOXI control plane and technical-path source. It does
not vendor full upstream applications by default.

- BaiLongma stays in a separate upstream checkout or fork.
- MOXI-specific BaiLongma changes live as overlays under
  [patches/bailongma](patches/bailongma/README.md).
- The first exported BaiLongma overlay patch adds Brain UI capability cards,
  Hermes backend bridge status, and QQ official bot settings.
- The runtime now exposes `/frontend/contract` so BaiLongma can render progress
  states, route UI labels, and personal/company permission badges from the
  Hermes adapter contract instead of hard-coding them.
- The server BaiLongma overlay now proxies `/frontend/contract` and calls
  Hermes `/social/turn` before `/message` enters the native BaiLongma queue,
  so slow routes can show a natural quick ACK and report `ack_sent`.
- The Brain UI overlay now consumes `moxi_progress` SSE events and renders a
  compact route-aware progress strip while slow work is running.
- Brain UI chat bubbles now show channel-plane badges so web/personal/company,
  runtime progress, and owner-confirmation surfaces are visibly separated.
- The server BaiLongma native turn loop now reports Hermes job lifecycle events
  through `/jobs/event`, including worker start, completion, failure, and final
  message delivery.
- BaiLongma `/message` now respects Hermes `append_to_active_job` plans: active
  job follow-ups are acknowledged and persisted as context without entering the
  queue as a new interrupting LLM turn.
- External runtime install notes live under [external](external/README.md).
- If a full BaiLongma fork becomes necessary, keep this repository as the
  canonical technical-path source and preserve the upstream MIT license.

## Public Copy And Attribution

External reviewers and classmates should use the public brief instead of the
internal architecture documents:

- [Website Copy Workspace](index.html)
- [Public Technical Path](public-ai-brief/TECHNICAL_PATH.md)
- [Batch Copy Pack](public-ai-brief/COPY_PACK.md)
- [Attribution Rules](public-ai-brief/ATTRIBUTION.md)

Required source line for copied technical paths:

```text
Technical path source: https://github.com/LUTAO581314/hermes-
```

## Run The Minimal Runtime

```powershell
python -m hermes_runtime
```

Health checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/health
Invoke-RestMethod http://127.0.0.1:8787/ready
Invoke-RestMethod http://127.0.0.1:8787/capabilities
Invoke-RestMethod http://127.0.0.1:8787/frontend/contract
Invoke-RestMethod http://127.0.0.1:8787/performance
Invoke-RestMethod "http://127.0.0.1:8787/route?message=generate%20image%20avatar"
Invoke-RestMethod "http://127.0.0.1:8787/context?message=generate%20image%20avatar"
Invoke-RestMethod http://127.0.0.1:8787/latency
Invoke-RestMethod http://127.0.0.1:8787/jobs
```

Connector quick-ack plan:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/social/turn -Method POST -ContentType "application/json" -Body '{"channel":"wechat","target_id":"user-1","message":"generate image avatar"}'
Invoke-RestMethod http://127.0.0.1:8787/jobs/event -Method POST -ContentType "application/json" -Body '{"job_id":"<job-id>","event":"worker_started"}'
```

When a connector calls a protected server URL instead of localhost, configure
`HERMES_RUNTIME_BASE_URL`, `HERMES_RUNTIME_BASIC_USER`, and
`HERMES_RUNTIME_BASIC_PASSWORD` outside Git.

## Recommended Current Milestone

Finish Phase 2 as a stable core:

1. Verify Hermes, BaiLongma, TrendRadar, image, voice, and memory count with [Core MVP Runbook](docs/CORE_MVP_RUNBOOK.md).
2. Keep video frozen until the owner reopens that scope.
3. Route useful memory candidates through [Obsidian Write-Back Workflow](docs/OBSIDIAN_WRITEBACK_WORKFLOW.md).
4. Run BaiLongma memory dream consolidation after noisy tests, then clean or merge only after review.
5. Write every phase result into a Chinese report.
6. Start Feishu company management from real-message verification, not from broad company write permissions.

WeChat companionship can be used only as a personal surface. Feishu remains the planned company-management surface. MiroFish simulations and trading execution stay later-stage capabilities with separate safety gates.

## Guiding Principle

Memory must remain portable and readable. Automation must remain reversible and auditable. Any high-risk action must stop at a human confirmation boundary.

Memory must be associative and governed. Time is metadata, not the main structure. The system should remember fewer, better, relationship-rich, source-backed, owner-correctable facts instead of storing every chat message, log, and API output as permanent memory.

## Reporting Rule

Every implementation phase must produce a Chinese report for the owner. Research notes and source materials may remain in English, but phase summaries, delivery status, decisions, risks, and next actions must be written in Chinese.

## Iteration Rule

Every phase follows the same loop: phase brief, scope lock, implementation, verification, Chinese report, memory dream consolidation, reviewed cleanup, risk review, and next-phase decision.
