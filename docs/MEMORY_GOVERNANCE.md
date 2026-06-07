# Memory Governance

## 1. Purpose

The system must not remember everything, and it must not organize memory only by time.

Human memory is associative. People remember through relationships, importance, repetition, emotion, context, goals, people, places, projects, and consequences. Time is useful, but it is only one index.

This system should imitate that pattern:

- Important memory becomes connected knowledge.
- Low-value memory expires.
- Repeated patterns become stronger.
- Contradictions are reviewed.
- The owner can inspect and correct memory.
- Obsidian visualizes relationships through backlinks, tags, properties, local graph, global graph, and curated canvas maps.

## 2. Core Principles

- Obsidian is the durable human-readable source of truth.
- Feishu is operational memory for active company work.
- Vector search is only an index, not the source of truth.
- BaiLongma runtime memory is a working memory layer, not the final source of truth.
- Logs are not memory.
- Time is metadata, not the main memory structure.
- Temporary context expires.
- Important memories need source, timestamp, confidence, and relationship links.
- Uncertain information must be marked as uncertain.
- The owner must be able to correct, archive, or delete memory.

## 2.1 Current Runtime Rule

Current core phase rule:

```text
conversation/logs
  -> BaiLongma working memory candidate
  -> intake gate
  -> Obsidian 00-Inbox/needs-review
  -> owner correction or weekly consolidation
  -> durable linked note
  -> optional search/vector index
```

BaiLongma memory may help short-term conversation, but it must not freely become permanent memory.

The current verified BaiLongma memory count is 31. Growth should be monitored. A sudden increase after setup tests, greetings, or tool checks is a cleanup signal.

Runtime write policy:

- Use `skip_recognition` when the turn is only test output, greeting, status check, or transient troubleshooting.
- Use `upsert_memory` only for stable preferences, decisions, project facts, recurring patterns, or explicit owner instructions.
- Prefer updating an existing `mem_id` over creating a near duplicate.
- Use `downgrade_memory` or archive flow for stale, noisy, or weak memory.
- Never store API keys, passwords, tokens, QR login material, or raw private screenshots.

## 3. Memory Classes

| Class | Name | Purpose | Default Retention | Storage |
| --- | --- | --- | --- | --- |
| M0 | Ephemeral context | Current task scratchpad | Hours to days | Runtime cache/logs |
| M1 | Operational memory | Active tasks, projects, customers, approvals | Until closed plus review window | Feishu tables/tasks/docs |
| M2 | Durable facts | Owner preferences, stable project/company facts | Long-term | Obsidian |
| M3 | Decisions and reports | Decisions, daily/weekly reports, postmortems | Long-term | Obsidian |
| M4 | Research artifacts | Source-backed research, market notes, API outputs | Medium to long-term | Obsidian plus optional index |
| M5 | Sensitive memory | Secrets, private identity data, financial account data | Avoid storing unless required | Restricted storage only |

## 4. Associative Memory Axes

Every durable memory should link to at least one meaningful axis besides time.

Recommended axes:

- Person: owner, employee, customer, partner, vendor.
- Project: project, product, repository, company workflow.
- Goal: revenue, delivery, hiring, learning, risk reduction.
- Topic: AI, finance, operations, sales, legal, engineering.
- Decision: chosen path, rejected path, reason, owner approval.
- Event: meeting, incident, deployment, customer call, market movement.
- Emotion/importance: frustration, urgency, high confidence, high risk.
- Causality: because, led to, blocked by, depends on.
- Repetition: recurring issue, repeated preference, repeated signal.
- Location/channel: Feishu, WeChat, Obsidian, GitHub, server.

The system should create links such as:

```text
[[Customer A]] -> [[Project X]] -> [[Receivables Risk]] -> [[2026-W23 Weekly Report]]
[[Owner Preference]] -> [[Chinese Phase Reports]] -> [[Reporting Policy]]
[[Market Thesis]] -> [[Bull Case]] -> [[Risk Trigger]]
```

## 5. Obsidian Visualization Strategy

Obsidian should make memory visible, not just searchable.

Use:

- Internal links for explicit relationships.
- Backlinks to reveal where a memory is used.
- Tags for broad categories.
- Properties/frontmatter for filtering and Graph color groups.
- MOC notes for curated maps of content.
- Local Graph for one note's neighborhood.
- Global Graph for broad structure.
- Canvas for manually curated architecture and decision maps.

### Recommended Visual Layers

| Layer | Obsidian Feature | Purpose |
| --- | --- | --- |
| Automatic relationship map | Graph view | See link clusters and isolated notes |
| Focused neighborhood | Local Graph | Understand one project/person/decision context |
| Curated map | Canvas | Show planned architecture, company model, or decision flow |
| Structured index | MOC note | Human-readable entry point for a topic |
| Filtered table | Bases or Dataview-like workflow | Review active tasks, stale notes, reports |

### 5.1 BaiLongma Runtime Graph Position

BaiLongma Brain UI can show a graph, but its graph is a runtime visualization layer, not the final memory store.

Current server implementation:

- `GET /memory/graph` exposes a read-only governed graph for the Brain UI.
- The graph separates working memory, review candidates, Obsidian source-of-truth boundary, cleanup risk, and relationship axes.
- It does not write memory, promote memory, or change Obsidian notes.
- It visualizes the current BaiLongma runtime memory pool so the owner can see what the agent is associating.

Recommended split:

```text
BaiLongma graph
  -> live working-memory and candidate visualization

Obsidian graph
  -> durable owner-approved linked memory
```

This keeps BaiLongma lively and inspectable without letting a beautiful graph become a hidden source of truth.

## 6. Recommended Obsidian Memory Layout

```text
vault/
  00-Inbox/
    needs-review/
    raw-captures/
  10-Owner/
    preferences.md
    standing-instructions.md
    corrections.md
    owner-memory-map.md
  20-Company/
    company-facts.md
    company-memory-map.md
    people/
    customers/
  30-Projects/
    project-memory-map.md
  40-Research/
    research-memory-map.md
  50-Markets/
    market-memory-map.md
  60-Decisions/
    decision-memory-map.md
  70-Reports/
    daily/
    weekly/
    phase-reports/
  80-Archive/
  90-Logs/
  Canvas/
    company-operating-map.canvas
    personal-memory-map.canvas
    agent-system-map.canvas
```

## 7. Memory Note Metadata

Durable memory notes should include frontmatter when practical:

```yaml
---
type: memory|decision|report|research|company|market|correction
status: active|review|archived|superseded
source: feishu|wechat|hermes|manual|api|research
confidence: low|medium|high
created: YYYY-MM-DD
updated: YYYY-MM-DD
review_after: YYYY-MM-DD
sensitivity: public|internal|private|restricted
importance: low|medium|high|critical
links:
  people: []
  projects: []
  goals: []
  decisions: []
---
```

## 8. What Should Not Become Durable Memory

Do not promote these by default:

- Raw chat noise.
- Repeated greetings.
- One-off emotional wording unless owner explicitly wants it remembered.
- Temporary drafts.
- Unverified guesses.
- Duplicate summaries.
- Low-value web snippets.
- API outputs without useful conclusion.
- Sensitive credentials.
- Private screenshots unless explicitly approved.
- Old task state after the task is closed and summarized.
- Tool smoke-test outputs such as "API OK", "permission fixed", or "health check passed".
- One-turn setup friction unless it becomes a reusable runbook.
- Agent affection phrases, roleplay fragments, or tone experiments unless the owner explicitly says to remember them.
- Logs from ASR/image tests unless they reveal a durable bug or configuration decision.

## 9. Memory Intake Gate

Before writing durable memory, the agent should ask:

1. Is this likely to matter after this task ends?
2. Is it stable enough to remember?
3. Is the source known?
4. Is it private or sensitive?
5. Does it duplicate an existing memory?
6. Should it be stored as a report instead of a fact?
7. Which person, project, goal, topic, decision, or event should it link to?
8. Does the owner need to approve saving it?
9. Is this a stable fact, or only a recent event?
10. Which existing note or `mem_id` should be updated instead of creating a new one?

If the answer is unclear, store it in temporary context or `00-Inbox/needs-review`, not in permanent memory.

### Current Core Intake Checklist

For the Hermes/BaiLongma core, a memory can pass only if it fits at least one:

- Owner preference that will affect future interaction.
- Architecture decision.
- Server/runtime configuration decision.
- Integration credential status without exposing the credential.
- Project roadmap change.
- Repeated behavior pattern confirmed by multiple interactions.
- Owner-approved company/person/project fact.

Everything else stays temporary or becomes a report note.

## 10. Promotion Rules

### Promote to Durable Memory

Promote when:

- The owner explicitly says to remember it.
- It is a stable preference.
- It is a company fact needed for future work.
- It is a decision that affects future actions.
- It is a completed report or postmortem.
- It is a recurring pattern confirmed over time.
- It is a source-backed research conclusion.
- It has meaningful links to existing people, projects, goals, decisions, or reports.

### Keep Temporary

Keep temporary when:

- It only matters for the current task.
- It is an unverified guess.
- It is a draft.
- It is a raw extraction without conclusion.
- It is a duplicate of a better memory.

### Reject or Redact

Reject or redact when:

- It contains credentials.
- It contains unnecessary private data.
- It violates the owner privacy boundary.
- It is low-value noise.

## 11. Deduplication

When a new memory overlaps an old one:

1. Prefer updating the existing canonical note.
2. Preserve the latest source and timestamp.
3. Link the related notes instead of duplicating them.
4. Archive duplicates.
5. Mark superseded notes with a pointer to the replacement.
6. Do not create parallel near-duplicate notes.

## 12. Staleness and Review

Every memory that can become stale should have `review_after`.

Suggested defaults:

- Owner preference: 180 days.
- Company process: 90 days.
- Customer status: 30 days.
- Market thesis: 7 to 30 days.
- API research output: 30 days.
- Project status: 14 days.
- Daily logs: summarize weekly, archive raw logs after 30 days.

## 13. Garbage Collection

Run memory dream consolidation regularly.

The system should not jump directly from "memory looks messy" to deletion. A
human-like memory layer should first sleep on the material: cluster related
items, identify repeated patterns, mark test noise, spot sensitive mistakes,
and produce a reviewable dream report. Cleanup is an action after review; dream
consolidation is the analysis step before that action.

Dream consolidation mode:

```text
BaiLongma runtime graph
  -> memory dream analysis
  -> noise / duplicate / sensitive / weak-axis signals
  -> Chinese dream report
  -> owner review
  -> forget, merge, inbox, report-only, or promote
```

Dream mode is read-only by default. It must not delete BaiLongma memory, promote
anything into Obsidian, or rewrite indexes without owner confirmation.

After every setup phase:

- Query recent BaiLongma memories.
- Run a memory dream report if memory count increased or the graph looks messy.
- Delete or downgrade test memories only after the dream report or owner rule makes the decision clear.
- Confirm memory count did not jump because of smoke tests.
- Write useful setup facts into a Chinese phase report instead of raw memory.
- If an item is useful but uncertain, place it in `00-Inbox/needs-review`.

### 13.1 BaiLongma Phase-End Dream Runbook

For the current Hermes/BaiLongma core, every capability test should have a small memory audit.

Before testing:

```text
record memory_count_before
mark test turns as setup/smoke-test
avoid real secrets, private screenshots, and sensitive business data
```

After testing:

```text
record memory_count_after
if memory_count_after > memory_count_before:
  inspect recent memory items
  run memory dream consolidation
  classify stable preferences, decisions, project facts, repeated patterns, or owner-approved facts
  mark test output, greetings, status checks, and temporary troubleshooting as forget-candidates
  write useful setup facts into the Chinese phase report instead of durable memory
```

Recommended labels:

- `promote-candidate`: stable and useful enough for Obsidian.
- `merge-candidate`: overlaps with an existing note or `mem_id`.
- `inbox-candidate`: useful but uncertain; place under `00-Inbox/needs-review`.
- `report-only`: useful phase fact, but not a long-term memory.
- `forget-candidate`: test garbage, duplicate, or sensitive accidental capture.

Examples:

| Item | Decision |
| --- | --- |
| `本地 Whisper tiny 已接通` | report-only or decision note |
| `图片测试识别 MOXI CORE OK` | report-only |
| `权限问题已永久解决` | delete unless tied to a reusable runbook |
| `主人希望每阶段写中文报告` | promote because it is a stable preference |
| `主人当前阶段冻结视频` | promote or decision note because it affects scope |
| raw API key, password, QR token | forget-candidate or redact immediately |

Local dream report command:

```bash
curl -fsS -u "owner:$BAILONGMA_PASS" -H "Origin: https://bairui.chat" \
  "https://bairui.chat/memory/graph?limit=120" > data/memory-graph.json
python scripts/memory-dream.py \
  --input data/memory-graph.json \
  --output data/memory-dream-report.md \
  --source "https://bairui.chat/memory/graph?limit=120"
```

The generated report belongs in ignored runtime data by default because it may
contain private memory content. Commit only a cleaned Chinese phase summary or a
general rule update.

Weekly:

- Merge duplicate inbox notes.
- Archive completed temporary notes.
- Summarize raw logs into weekly report.
- Remove empty or failed API outputs.
- Find orphan notes and either link, archive, or delete them.

Monthly:

- Review stale company and project facts.
- Archive inactive projects.
- Check owner preference changes.
- Remove dead links or mark them stale.
- Review graph clusters for noisy or disconnected memory.

Quarterly:

- Rebuild private search index.
- Review sensitive memory.
- Confirm long-term standing instructions.
- Review top graph hubs and remove accidental garbage hubs.

## 14. Correction and Deletion

The owner must be able to say:

- "这条记忆错了"
- "忘掉这个"
- "以后不要记这种"
- "把这个合并到那个项目"
- "这个只保留在日报里，不要当长期事实"
- "把这个和那个人/项目/目标连起来"

The system should then:

1. Find the relevant note.
2. Apply a correction, merge, archive, deletion, or new link.
3. Record the correction in `10-Owner/corrections.md` when useful.
4. Rebuild or invalidate search indexes.
5. Confirm what changed.

## 15. Search Index Policy

Meilisearch, SQLite FTS, vector stores, and Zep are indexes.

Rules:

- Indexes can be rebuilt.
- Indexes must not contain facts that are missing from Obsidian or Feishu.
- Deleting a note must remove it from indexes.
- Sensitive notes should be excluded unless explicitly approved.
- Graph links and Obsidian notes remain the inspectable memory layer.

## 16. Memory Quality Score

Each candidate durable memory can be scored:

| Signal | Question |
| --- | --- |
| Usefulness | Will this help future decisions or actions? |
| Stability | Is it likely to remain true? |
| Source | Do we know where it came from? |
| Specificity | Is it concrete enough to act on? |
| Relationship | Is it linked to people, projects, goals, decisions, or reports? |
| Non-duplication | Does it avoid repeating existing notes? |
| Safety | Is it safe to store? |

Only high-scoring memories should become durable memory.

## 17. Default Safe Behavior

When unsure:

- Do not write to permanent memory.
- Put it in `00-Inbox/needs-review`.
- Mark confidence as low.
- Add at least one suggested relationship link.
- Ask the owner only when the decision matters.

The system should prefer fewer, better, relationship-rich memories over many noisy time-stamped memories.

## 18. Phase Memory Gate

Every phase must end with memory hygiene:

- Promote only stable decisions, reports, and source-backed conclusions.
- Link new durable notes to people, projects, goals, decisions, risks, or reports.
- Keep raw logs out of durable memory.
- Archive or delete temporary notes.
- Update relevant MOC notes or Canvas maps.
- Rebuild or invalidate search indexes when memory changes.
- Record owner corrections when they affect future behavior.

## 19. External Graph Tools

Graph tools may help audit memory quality.

Graphify is a strong candidate for:

- Detecting isolated notes.
- Mapping relationships between reports, projects, customers, and risks.
- Creating graph reports for phase reviews.
- Helping agents query large code/document corpora without reading everything.

Rules:

- Generated graphs are analysis artifacts, not automatically durable memory.
- Keep only selected graph reports or maps.
- Do not promote raw graph cache into Obsidian without review.
- Use Obsidian links and Canvas as the owner-visible memory map.
