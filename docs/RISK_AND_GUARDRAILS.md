# Risk and Guardrails

## 1. Core Rule

The system may research, summarize, draft, simulate, and recommend. It must not perform high-risk or irreversible actions without explicit owner confirmation.

## 2. High-Risk Areas

### 2.1 Financial Trading

Allowed by default:

- Market data collection.
- News and filing summaries.
- Watchlist monitoring.
- Risk analysis.
- Paper trading.
- Draft trade plans.

Not allowed by default:

- Real order placement.
- Broker API connection.
- Leveraged trading.
- Automatic position sizing.
- Trading based only on model output.

Requirements before real trading:

- Human confirmation.
- Position limits.
- Loss limits.
- Instrument whitelist.
- Full audit log.
- Dry-run mode.
- Kill switch.
- Separate legal and financial review.

This repository does not provide financial advice. All market outputs are research notes only.

### 2.2 WeChat

WeChat personal-account automation can create account and compliance risk.

Preferred order:

1. Feishu official app.
2. WeChat Official Account or approved official channel.
3. WeCom webhook where appropriate.
4. Personal-account bridge only after risk acceptance.

Guardrails:

- Do not spam.
- Keep proactive chat disabled unless the owner approves schedule, reason, and daily limit.
- Do not bypass login or access restrictions.
- Do not scrape private content without permission.
- Do not send sensitive commands through weakly authenticated channels.
- Keep personal-account bridges optional and disabled by default.
- Do not pretend to be a real person when identity matters; the assistant may be warm and natural, but must remain honest about being automated.
- Route company, money, legal, HR, account, and trading actions out of WeChat to Feishu or a protected approval flow.

### 2.3 Feishu

Feishu should be the first production messaging channel because it has a clearer official app model.

Guardrails:

- Verify request signatures where supported.
- Store app secrets outside Git.
- Use minimal permissions.
- Log command sender and command type.
- Require approval for sensitive actions.
- Treat Feishu CLI and MCP tools as controlled execution tools behind the app/event entry layer, not as unrestricted chat surfaces.

### 2.4 Shell and Server Automation

Allowed by default:

- Read-only health checks.
- Log inspection.
- Status commands.
- Controlled deployment scripts.

Requires confirmation:

- Deleting files.
- Stopping production services.
- Changing firewall rules.
- Rotating secrets.
- Running arbitrary scripts from the internet.
- Modifying system users or SSH settings.

### 2.5 Memory

Risks:

- Incorrect facts stored as durable memory.
- Private information leaked into summaries.
- Conflicting memories.
- Opaque vector memory becoming the hidden source of truth.

Guardrails:

- Store final durable memory in Obsidian.
- Do not store every chat message, log, and API output as permanent memory.
- Use an inbox/review flow before promoting uncertain memory.
- Link durable memories to people, projects, goals, decisions, reports, risks, or events.
- Mark uncertain information.
- Keep sources where possible.
- Use vector stores only as indexes.
- Add memory correction and deletion procedures.
- Add stale-memory review and cleanup schedules.

## 3. Approval Levels

| Level | Action Type | Default Behavior |
| --- | --- | --- |
| L0 | Read-only local or public research | allowed |
| L1 | Write notes, draft reports, create local files | allowed with logs |
| L2 | Send notifications to owner | allowed if channel is configured |
| L3 | Modify service configuration | require confirmation |
| L4 | External posting, account changes, money movement | require explicit confirmation |
| L5 | Real trading, destructive server commands | disabled until separate safety design |

## 4. Logging Requirements

Every L2 or higher action should log:

- Time.
- Actor.
- Trigger channel.
- Action.
- Target.
- Input summary.
- Output summary.
- Approval status.

## 5. Secrets Policy

Never commit:

- API keys.
- Tokens.
- Passwords.
- Private keys.
- Feishu app secrets.
- WeChat credentials.
- Broker credentials.

Use:

- `.env` on server.
- `.env.example` in Git.
- Restricted filesystem permissions.
- Secret rotation notes.

## 6. Research Quality

For research and market analysis:

- Prefer primary sources.
- Cite sources in Obsidian reports.
- Separate facts from interpretation.
- Mark stale data.
- Avoid presenting predictions as certainty.
- Keep assumptions visible.

## 7. Kill Switch

The deployed system should include:

- A command to stop all agent services.
- A way to disable messaging callbacks.
- A way to disable scheduled jobs.
- A way to revoke model/API keys.

## 8. Default Safe Mode

The first deployed system should run in safe mode:

- No broker API.
- No personal WeChat bridge.
- No arbitrary root shell.
- No public unauthenticated dashboards.
- No irreversible automation.

Safe mode is still useful because it can research, summarize, remember, and notify.

## 9. Iteration Guardrail

Each phase must pass a risk review before it is considered complete.

The review should check:

- No secrets committed.
- No unauthorized money movement.
- No unrestricted personal WeChat automation.
- No silent HR, legal, or contract action.
- No raw sensitive memory promoted to durable memory.
- No public unauthenticated agent dashboard.
- A Chinese phase report exists and states the remaining risks.

## 10. External Project License Guardrail

External projects must be reviewed before adoption.

Rules:

- GPL projects, including TrendRadar and Evolver, must remain isolated external runtimes unless a separate license review approves deeper use.
- MIT projects, including Graphify and Nuwa Skill, may be integrated more flexibly, but large source copying should still be avoided.
- Candidate tools must not receive secrets unless explicitly approved.
- Candidate tools must not self-modify production memory, prompts, or configuration.

## 11. Sticker and Generated Image Guardrail

Prepared sticker packs and generated stickers must stay inside the media bridge
boundary.

Rules:

- Do not download third-party sticker packs into Git.
- Do not commit runtime-generated images.
- Store only metadata, provider IDs, queries, license notes, and send rules.
- Respect provider terms, attribution requirements, rate limits, and API keys.
- AI-generated stickers must be original and must not imitate existing anime IP,
  celebrities, private people, platform marks, or copyrighted sticker packs.
- Generated stickers should require owner review before they become reusable
  prepared stickers.
- Platform image keys, media IDs, temporary upload files, and provider secrets
  are runtime data and must not be committed.
