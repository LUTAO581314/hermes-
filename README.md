# Hermes Personal Agent System

This repository is the planning and deployment home for a personal and company agent system built around Hermes, Obsidian, BaiLongma, MiroFish, Feishu, WeChat, and API-first intelligence adapters.

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
- [Optimized Technical Path](docs/OPTIMIZED_TECHNICAL_PATH.md) - the current internal engineering path, module boundaries, performance plan, and copy/credit strategy.
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
```

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
