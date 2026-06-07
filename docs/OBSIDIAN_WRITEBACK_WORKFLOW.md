# Obsidian Write-Back Workflow

## 1. Purpose

Obsidian is the durable, owner-readable source of truth.

BaiLongma and Hermes can hold short-term context, but they must not silently turn every chat, log, test, screenshot, or API response into long-term memory.

The write-back workflow exists to keep memory:

- useful,
- relationship-rich,
- source-backed,
- owner-correctable,
- easy to visualize,
- easy to delete or archive.

## 2. Folder Layout

Use this vault shape for the first governed memory MVP:

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
  80-Runbooks/
  90-Logs/
  Canvas/
    personal-memory-map.canvas
    company-operating-map.canvas
    agent-system-map.canvas
```

## 3. Memory Candidate Template

New uncertain memory should first land in `00-Inbox/needs-review`.

```markdown
---
type: memory-candidate
status: review
source: hermes|bailongma|wechat|feishu|manual|api|research
confidence: low|medium|high
created: YYYY-MM-DD
review_after: YYYY-MM-DD
sensitivity: public|internal|private|restricted
importance: low|medium|high|critical
links:
  people: []
  projects: []
  goals: []
  decisions: []
---

# Title

## Candidate

What might be worth remembering.

## Source

Where it came from, without secrets or raw private content.

## Why It Might Matter

How it helps future decisions, actions, personalization, or risk control.

## Relationship Links

- Person:
- Project:
- Goal:
- Decision:
- Event:
- Report:

## Review Decision

- [ ] promote
- [ ] merge
- [ ] archive
- [ ] delete
- [ ] ask owner
```

## 4. Promotion Rules

Promote a candidate only when it matches at least one condition:

- The owner explicitly asked the system to remember it.
- It is a stable owner preference.
- It is a project or runtime decision.
- It is a company fact approved for storage.
- It is a repeated pattern confirmed across multiple interactions.
- It is a source-backed research conclusion.
- It is a completed phase report, decision log, or postmortem.

Do not promote:

- greetings,
- setup friction,
- smoke-test outputs,
- temporary emotional wording,
- raw logs,
- API success strings,
- duplicate summaries,
- uncertain guesses,
- secrets,
- QR login material,
- private screenshots without approval.

## 5. Human-Like Memory Shape

The system should remember like a relationship graph, not a time-only feed.

Every promoted note should link to at least one of:

- person,
- project,
- goal,
- topic,
- decision,
- event,
- cause,
- risk,
- report,
- channel.

Example:

```text
[[Owner Preference]] -> [[Chinese Phase Reports]] -> [[Reporting Policy]]
[[Hermes Core MVP]] -> [[TrendRadar MCP]] -> [[Search Runtime Strategy]]
[[BaiLongma Working Memory]] -> [[Obsidian Inbox]] -> [[Memory Governance]]
```

## 6. Image and Voice Write-Back

Image analysis:

- Save only the conclusion, not every raw image.
- If the image is private, store no image content unless the owner approves.
- OCR outputs should include uncertainty when text is unclear.
- Screenshots with credentials must be rejected or redacted.

Voice input:

- Transcripts are temporary by default.
- Promote only stable facts, reminders, preferences, decisions, or reports.
- Do not store every voice message as a permanent note.
- If a voice transcript is important but messy, store a cleaned summary with source metadata.

## 7. Phase-End Memory Dream

At the end of each phase:

1. Record the BaiLongma memory count.
2. Inspect recent memory additions.
3. Run a memory dream report when memory grew, clusters look noisy, or the owner says memory is confused.
4. Mark setup and smoke-test memories as `forget-candidate` or `report-only`.
5. Promote only stable decisions and owner-approved facts.
5. Write useful runtime facts into the Chinese phase report.
6. Move uncertain candidates to `00-Inbox/needs-review`.
7. Update MOC notes or Canvas maps if the memory graph changed.
8. Rebuild or invalidate search indexes if notes changed.

Dream reports are read-only review artifacts. They should suggest merge,
forget, inbox, report-only, or promote actions, but they must not automatically
rewrite BaiLongma memory or Obsidian notes.

## 8. Weekly Dream And Cleanup

Weekly:

- Run a memory dream report over the current BaiLongma graph.
- Merge duplicate candidates.
- Archive closed task notes.
- Link isolated notes to a project, goal, decision, or report.
- Review stale facts whose `review_after` has passed.
- Remove failed API outputs that have no useful conclusion.
- Write one weekly memory hygiene summary.

## 9. Owner Corrections

The owner can say:

- `这条记忆错了`
- `忘掉这个`
- `以后不要记这种`
- `把这个合并到那个项目`
- `这个只保留在日报里，不要当长期事实`
- `把这个和那个人/项目/目标连起来`

The system should then:

1. Find the matching memory or note.
2. Apply correction, merge, archive, deletion, or relinking.
3. Record important corrections in `10-Owner/corrections.md`.
4. Rebuild affected indexes.
5. Confirm the exact change to the owner.

## 10. First Automation Target

The next useful automation is not a giant memory database. It is a narrow write-back tool:

```text
input: memory candidate JSON
checks: safety, duplicate, sensitivity, relationship axis
output: markdown file under 00-Inbox/needs-review
side effect: no permanent promotion without review
```

This keeps the system useful while preventing memory from turning into hidden clutter.

The companion automation is a memory dream tool:

```text
input: BaiLongma /memory/graph JSON
checks: noise, duplicate, sensitivity, isolated nodes, weak relationship axes
output: Chinese dream report under ignored runtime data
side effect: no deletion, no promotion, no Obsidian rewrite
```

The owner can then approve which dream suggestions become real memory actions.

## 11. BaiLongma Graph Boundary

The BaiLongma Brain UI graph is useful for inspection and live interaction.

Use it to see:

- current working memories,
- candidate memories,
- repeated concepts,
- people, project, tag, and concept axes,
- possible cleanup risk.

Do not treat it as automatic long-term memory.

Promotion still goes through:

```text
BaiLongma graph node
  -> memory intake gate
  -> 00-Inbox/needs-review
  -> owner correction or weekly consolidation
  -> durable Obsidian note
```

The graph may display `Obsidian 正本` as a boundary node, but it does not mean the displayed runtime memory has already been written into Obsidian.
