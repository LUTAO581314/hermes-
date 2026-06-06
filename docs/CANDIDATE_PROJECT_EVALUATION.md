# Candidate Project Evaluation

## 1. Purpose

This document evaluates external projects that may strengthen the Hermes personal/company agent system.

The evaluation rule is conservative:

- Do not copy external source code into this repository.
- Prefer external runtime, adapter, or concept extraction.
- Respect license boundaries.
- Add candidates only when they improve a specific system layer.

## 2. Summary Matrix

| Project | Fit | Recommended Role | Adoption Mode | Priority |
| --- | --- | --- | --- | --- |
| `sansan0/TrendRadar` | Strong | Trend/news/search intelligence runtime | Isolated external runtime or MCP/HTTP adapter | High |
| `safishamsi/graphify` | Strong | Knowledge graph and corpus mapping tool | Tool integration, generated artifacts, or optional MCP | High |
| `alchaincyf/nuwa-skill` | Medium to strong | Skill/persona/advisory-board factory | Methodology and optional skill installation | Medium |
| `EvoMap/evolver` | Experimental | Self-improvement review and phase retrospectives | External experimental tool only | Low for now |

## 3. TrendRadar

Repository:

- https://github.com/sansan0/TrendRadar

Observed characteristics:

- GPL-3.0 license.
- Python project with Docker support.
- MCP server support.
- Hot news, RSS, trend tracking, AI analysis, ranking timeline, and multi-channel push.
- Feishu/WeCom/Telegram/email-style notification support appears in the README.
- Local shallow clone was reachable at commit `a5ede43a666652312f5ba3361feeb737b73a4e23`.

System fit:

- Excellent fit for the research, search, and trend intelligence layer.
- Especially useful for AI news, company opportunity radar, market/news monitoring, and recurring briefings.
- Can feed Hermes daily intelligence jobs and Feishu company summaries.

License boundary:

- Treat as an isolated external runtime because of GPL-3.0.
- Do not copy source code, prompts, or implementation internals into this repository.
- Connect through MCP, HTTP, CLI, or generated reports.

Recommended adoption:

```text
Phase 4 or Phase 6:
TrendRadar external runtime
  -> Hermes adapter
  -> Obsidian trend report
  -> Feishu briefing
```

Verdict:

Use it. It is the strongest candidate for the search/trend radar layer.

## 4. Graphify

Repository:

- https://github.com/safishamsi/graphify

Observed characteristics:

- MIT license.
- Python package `graphifyy`.
- Maps code, docs, PDFs, images, videos, and URLs into a queryable knowledge graph.
- Supports graph JSON, HTML visualization, reports, query/path/explain commands, MCP stdio, and Obsidian-style outputs.
- README explicitly lists Codex and Hermes support.
- Security notes describe local analysis, stdio MCP, URL validation, path validation, and output sanitization.
- Local shallow clone was reachable at commit `3405c1fb96c119fc928307d91fc6c190a7118e36`.

System fit:

- Excellent fit for repository understanding, documentation graphing, and memory visualization.
- It can complement Obsidian by generating knowledge graphs and reports from code/docs/media.
- It can help Hermes inspect this repository and future company/project documents without reading everything every time.

License boundary:

- MIT license is compatible with normal integration.
- Still prefer tool invocation rather than copying large source code.

Recommended adoption:

```text
Phase 3:
Graphify for Obsidian/corpus graph experiments

Phase 10:
Graphify for repo and documentation impact mapping
```

Use carefully:

- Do not let generated `graphify-out/` become noisy memory by default.
- Commit only selected graph reports/artifacts when useful.
- Keep raw extraction cache out of durable memory unless there is a reason.

Verdict:

Use it. It is the strongest candidate for graph visualization and memory/codebase mapping.

## 5. Nuwa Skill

Repository:

- https://github.com/alchaincyf/nuwa-skill

Observed characteristics:

- MIT license.
- Agent Skill for distilling public figures or topics into reusable perspective skills.
- Provides a structured workflow: research, extraction, synthesis, validation, and skill generation.
- Includes examples for Munger, Feynman, Musk, Naval, Taleb, Karpathy, Jobs, and others.
- Works with skills-compatible runtimes including Codex and Hermes according to README.
- Local shallow clone was reachable at commit `5f17d5bb5224883fb94c021c0c809ce5d524b1d8`.

System fit:

- Useful for the advisory-board layer.
- Can help create specific perspective skills for investing, product strategy, operations, content, and risk.
- The most valuable part is the methodology: source-backed distillation, explicit limits, and validation.

License boundary:

- MIT license.
- Still avoid copying large example research bundles into this repository.

Recommended adoption:

```text
Phase 7:
Optional personal/advisory skill layer

Phase 9:
MiroFish simulation roles or decision board personas
```

Use carefully:

- Do not confuse perspective skills with facts.
- Every advisory persona must state uncertainty and limits.
- For company decisions, advisory outputs remain recommendations, not authority.

Verdict:

Use as a skill factory and advisory-board methodology, not as core infrastructure.

## 6. Evolver

Repository:

- https://github.com/EvoMap/evolver

Observed characteristics:

- README shows GPL-3.0 and notes a future source-available transition.
- Node.js >= 18.
- Self-evolution engine for AI agents using Genes/Capsules/GEP-style assets.
- CLI generates prompts and evolution events; it states it is a prompt generator, not a code patcher.
- Has review mode and loop mode.
- Local shallow clone was reachable at commit `534ede263b1d4f81aa4c8071af12cfe2fde1c890`.

System fit:

- Conceptually useful for phase retrospectives, prompt governance, and structured self-improvement.
- Not needed for the first production slice.
- Risky if allowed to run continuous autonomous loops without owner review.

License and product boundary:

- Treat as GPL/source-available-sensitive.
- Do not copy source or built-in assets into this repository.
- If evaluated, run externally and keep outputs as review suggestions only.

Recommended adoption:

```text
Phase 10 or later:
External experimental reviewer
  -> phase report suggestions
  -> owner approval
  -> manual adoption
```

Use carefully:

- Do not enable autonomous self-modification.
- Do not allow it to mutate production prompts or memory directly.
- Keep human-in-the-loop review.

Verdict:

Research later. Do not make it core now.

## 7. Updated Architecture Placement

```text
TrendRadar
  -> Search/trend intelligence runtime
  -> Hermes daily intelligence
  -> Feishu/Obsidian reports

Graphify
  -> Knowledge graph and documentation/corpus mapping
  -> Obsidian visual memory support
  -> Repo and company-document analysis

Nuwa Skill
  -> Advisory skill factory
  -> Persona/perspective layer
  -> MiroFish simulation roles

Evolver
  -> Experimental self-improvement reviewer
  -> Phase retrospectives
  -> Later-stage guarded evaluation
```

## 8. Next Actions

1. Add TrendRadar as a Phase 4/6 external runtime candidate.
2. Add Graphify as a Phase 3/10 graph/memory tooling candidate.
3. Add Nuwa as a Phase 7/9 optional advisory-skill candidate.
4. Add Evolver as a Phase 10+ experimental reviewer candidate.
5. Do a license review before any code reuse or deeper integration.
