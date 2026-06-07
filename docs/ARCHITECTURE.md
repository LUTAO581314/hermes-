# Architecture

## 1. Design Principles

- Human-readable memory first.
- Agent execution must be logged.
- High-risk operations require explicit owner confirmation.
- Each tool should have a narrow role.
- Company management and personal companionship should be separated by channel and permission.
- The system should be advanced through small verified phases, not one large deployment.
- Deployment should be reproducible from this repository.
- Secrets must stay outside committed files.

## 2. Layered Architecture

```text
Interaction Layer
  Feishu company-management bot
  WeChat personal-companion official channel
  BaiLongma UI
  CLI

Channel Policy Layer
  company-management plane
  personal-companion plane
  admin plane
  approval gate

Orchestration Layer
  Hermes
  job scheduler
  tool router
  MCP and CLI adapters

Company Operations Layer
  Feishu tasks
  Feishu bitable
  Feishu docs/wiki
  Feishu approvals
  Feishu calendar

Knowledge Layer
  Obsidian vault
  SQLite metadata
  vector/Zep search if needed

Simulation Layer
  MiroFish
  multi-agent scenario reports

External Data Layer
  search engines
  crawl/extraction APIs
  OCR APIs
  vision APIs
  speech-to-text APIs
  video understanding APIs
  GitHub
  market data
  news
  server metrics
```

## 3. Data Flow

### 3.1 Command Flow

```text
Owner command
  -> Feishu / WeChat / CLI
  -> channel policy router
  -> BaiLongma or Hermes command router
  -> Hermes task planner
  -> tools and data sources
  -> result summary
  -> Obsidian write-back
  -> notification to owner
```

### 3.2 Memory Flow

```text
Raw input
  -> temporary task context
  -> extracted facts and decisions
  -> Obsidian note
  -> optional vector index
  -> future retrieval
```

Obsidian remains the canonical readable record. Vector search is an index, not the source of truth.

### 3.3 Company Management Flow

```text
Feishu project/customer/task/report data
  -> Hermes company-management jobs
  -> delay, risk, missing-report, and follow-up detection
  -> low-risk reminders
  -> owner approval queue for sensitive actions
  -> Feishu company summary
  -> Obsidian durable operating report
```

Feishu is the system of action for company workflows. Obsidian is the durable memory and review archive.

### 3.4 Personal Companionship Flow

```text
Owner personal message or scheduled check-in
  -> WeChat official channel or BaiLongma
  -> personal context retrieval
  -> companion response policy
  -> lightweight reply or reminder
  -> important facts routed through Obsidian memory intake
```

WeChat should be personal and lightweight. Official channels, such as a WeChat Official Account or WeCom customer-service flow, are preferred. Personal-account bridges remain disabled until a separate risk review and owner acceptance. Company decisions, money, approvals, and employee management should stay in Feishu or owner-confirmed admin flows.

### 3.5 Feishu Tool Flow

```text
Feishu app callback or Channel SDK event
  -> channel policy router
  -> Hermes company workflow
  -> Feishu CLI or MCP tool layer when an approved action needs execution
  -> audit log
  -> Feishu or Obsidian summary
```

Feishu CLI and MCP tools are execution tools, not the first message-entry layer. They should be invoked only behind the channel policy router, minimal permissions, and approval gates.

### 3.6 API-First Multimodal Flow

```text
Image / PDF / voice / web URL
  -> Hermes task router
  -> external API provider or approved local lightweight service
  -> normalized text, entities, timestamps, and confidence notes
  -> Obsidian report
  -> optional private search index
  -> owner summary through Feishu or WeChat
```

The VPS should not run heavy local image or video models by default. It should coordinate API calls, validate outputs, keep logs, and write final artifacts.

Current core phase exception:

- Local Whisper `tiny` is allowed as a temporary CPU ASR service because it is lightweight enough for the current VPS.
- Image understanding uses the active multimodal model through the configured gateway.
- Video is frozen and should not be exposed through the current tool route.

### 3.7 Simulation Flow

```text
Obsidian notes
  -> simulation brief
  -> MiroFish multi-agent run
  -> simulation report
  -> decision note in Obsidian
  -> short owner summary
```

## 4. Suggested Obsidian Structure

```text
vault/
  00-Inbox/
  10-Owner/
    preferences.md
    goals.md
    standing-instructions.md
  20-Agents/
    hermes.md
    bailongma.md
    mirofish.md
    guardrails.md
  30-Projects/
  35-Company/
    operating-briefs/
    customers/
    sales-pipeline/
    receivables/
    risks/
    meetings/
    approvals/
  40-Research/
  50-Markets/
    watchlist.md
    daily-briefs/
    company-notes/
  60-Decisions/
  70-Reports/
    daily/
    weekly/
    simulations/
  80-Runbooks/
  90-Logs/
```

## 5. Service Layout on VPS

Recommended path:

```text
/opt/hermes-system/
  docker-compose.yml
  .env
  data/
  logs/
  obsidian-vault/
  backups/
```

The current lightweight VPS profile is enough for:

- Hermes orchestration.
- Feishu and callback adapters.
- Feishu company-management workflows.
- Search/crawl API calls.
- OCR, image, speech, and video API routing.
- Lightweight local indexing.
- Obsidian vault write-back.
- Logs, queues, retries, and backups.

It is not intended for:

- Local large language model inference.
- Local video understanding models.
- Local GPU-heavy OCR or object detection.
- High-throughput crawling.

Recommended Linux users:

- `root` only for installation and emergency maintenance.
- `hermes` for service ownership and runtime files.

## 6. Networking

Recommended default:

- Do not expose raw agent ports publicly.
- Use a reverse proxy when a domain is available.
- Protect dashboards and callbacks with authentication.
- Restrict callback endpoints to messaging platform requirements.

## 7. Secrets

Never commit:

- Model API keys.
- Feishu app secrets.
- WeChat credentials.
- Market data API keys.
- Broker credentials.
- SSH private keys.

Use `.env` locally and keep only `.env.example` in Git.

## 8. Logging

Every important agent action should record:

- Timestamp.
- Trigger source.
- Task id.
- Tools used.
- Files written.
- External services called.
- Summary.
- Whether owner approval was required.

## 9. Backups

Back up:

- Obsidian vault.
- Hermes data directory.
- SQLite databases.
- Configuration templates.
- Logs needed for audit.

Do not back up plaintext secrets into shared locations.

## 10. Failure Modes

Plan for:

- Model API outage.
- Messaging callback outage.
- Bad or hallucinated research output.
- Unexpected tool execution.
- Financial data errors.
- Disk full.
- Agent loop runaway.
- Compromised token.

Each failure should degrade to notification and manual intervention rather than silent autonomous action.

## 11. Permission Planes

### Company Plane

Primary channel: Feishu.

Allowed by default:

- Read tasks, tables, docs, calendars, and reports.
- Generate summaries.
- Send reminders.
- Draft documents.
- Detect risks and missing updates.

Requires owner approval:

- Approving expenses.
- Changing compensation.
- Sending external commitments.
- Changing legal or contract documents.
- HR disciplinary actions.

### Personal Plane

Primary channel: WeChat or BaiLongma.

Allowed by default:

- Daily check-ins.
- Personal reminders.
- Idea capture.
- Personal summaries.

Not allowed by default:

- Company-wide instructions.
- Money movement.
- Legal commitments.
- Account or credential changes.

### Admin Plane

Primary channel: CLI or protected web UI.

Requires owner confirmation for any destructive or externally visible operation.

## 12. Iteration Architecture

Every implementation phase should preserve the same control loop:

```text
phase scope
  -> implementation
  -> verification
  -> Chinese report
  -> Obsidian memory update
  -> memory dream consolidation
  -> reviewed cleanup
  -> risk review
  -> next phase
```

Architecture changes must update this document, the roadmap, and any affected phase report.
