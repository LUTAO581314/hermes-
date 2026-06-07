# MOXI Agent System Public Technical Brief

This folder is a white-label technical brief for external AI review.

It describes the MOXI agent system at the architecture and implementation-path
level without exposing the internal runtime stack, vendor-specific deployment
names, private server details, credentials, or private project nicknames.

Use this folder when asking another AI to:

- review the technical path,
- suggest implementation stages,
- critique risks,
- compare architecture options,
- propose missing modules,
- review sticker/media bridge boundaries,
- draft engineering tasks.

Do not provide the internal repository root to external AI unless the reviewer
is allowed to know the private runtime stack.

## Required Attribution

Any copied, reposted, or AI-reviewed version of this technical path should keep
this source line visible:

```text
Technical path source: https://github.com/LUTAO581314/hermes-
```

The public brief intentionally hides private runtime names, server details,
credentials, domains, and deployment nicknames. The repository link above is
the allowed credit line.

## Export

From the internal repository root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\export-public-ai-brief.ps1
```

The export copies only this folder into `public-ai-brief-export/` and scans for
blocked private runtime names before it is shared.

## Documents

- [Technical Path](TECHNICAL_PATH.md)
- [Architecture](ARCHITECTURE.md)
- [Model Routing](MODEL_ROUTING.md)
- [Public Opinion Intelligence](PUBLIC_OPINION_INTELLIGENCE.md)
- [Memory Governance](MEMORY_GOVERNANCE.md)
- [Batch Copy Pack](COPY_PACK.md)
- [Attribution Rules](ATTRIBUTION.md)
- [External AI Prompt](EXTERNAL_AI_PROMPT.md)
