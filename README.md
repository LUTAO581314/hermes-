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
- Search, image recognition, and video understanding are API-first integrations; the lightweight VPS runs orchestration, not heavy local models.

## Current Status

This repository currently contains the full architecture and rollout plan. Runtime deployment files will be added after the model provider, domain, communication channels, and security boundaries are confirmed.

## Documents

- [Sustainable Iteration Blueprint](docs/SUSTAINABLE_ITERATION_BLUEPRINT.md)
- [Master Plan](docs/MASTER_PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Optimized Architecture](docs/OPTIMIZED_ARCHITECTURE.md)
- [Candidate Project Evaluation](docs/CANDIDATE_PROJECT_EVALUATION.md)
- [Memory Governance](docs/MEMORY_GOVERNANCE.md)
- [API Integrations](docs/API_INTEGRATIONS.md)
- [Roadmap](docs/ROADMAP.md)
- [Risk and Guardrails](docs/RISK_AND_GUARDRAILS.md)
- [Chinese Report Policy](docs/CHINESE_REPORT_POLICY.md)
- [Current Chinese Phase Report](reports/phase-00-architecture-plan.zh-CN.md)
- [Memory Governance Chinese Report](reports/phase-00-memory-governance.zh-CN.md)
- [Sustainable Iteration Chinese Report](reports/phase-00-sustainable-iteration.zh-CN.md)
- [Candidate Projects Chinese Report](reports/phase-00-candidate-projects.zh-CN.md)

## Recommended First Milestone

Build a minimal but useful system through the sustainable iteration loop:

1. Deploy the minimal Hermes/runtime foundation on the VPS.
2. Add a Feishu smoke test if credentials are ready.
3. Create the governed Obsidian memory structure.
4. Add Feishu company tables for projects, customers, sales pipeline, receivables, risks, and employee reports.
5. Write every important output back to Obsidian through the memory intake gate.
6. Add external APIs for search, OCR, image understanding, speech transcription, and video understanding.
7. End every phase with verification, memory cleanup, and a Chinese owner report.

WeChat companionship, BaiLongma persona features, MiroFish simulations, and trading execution should be added only after the company-management and memory loop is stable.

## Guiding Principle

Memory must remain portable and readable. Automation must remain reversible and auditable. Any high-risk action must stop at a human confirmation boundary.

Memory must be associative and governed. Time is metadata, not the main structure. The system should remember fewer, better, relationship-rich, source-backed, owner-correctable facts instead of storing every chat message, log, and API output as permanent memory.

## Reporting Rule

Every implementation phase must produce a Chinese report for the owner. Research notes and source materials may remain in English, but phase summaries, delivery status, decisions, risks, and next actions must be written in Chinese.

## Iteration Rule

Every phase follows the same loop: phase brief, scope lock, implementation, verification, Chinese report, memory cleanup, risk review, and next-phase decision.
