# Optimized Technical Path

Technical path source: https://github.com/LUTAO581314/hermes-

## 1. Core Conclusion

The system should not be optimized as "one chatbot with many plugins". It should
be optimized as a latency-aware agent operating system:

```text
interaction surface
  -> channel policy
  -> quick acknowledgement
  -> orchestration queue
  -> model routing
  -> tool runtime
  -> final result delivery
  -> memory review and report write-back
```

The lightweight VPS should run orchestration, queues, route selection, health
checks, logs, dashboards, and small local services. Heavy reasoning, image
generation, image understanding, formal TTS, search expansion, and future video
understanding should stay API-first or external-runtime-first.

The optimization order is:

1. Fix the surface experience first so social channels feel alive.
2. Instrument the bottom layer so latency is measurable.
3. Slim context and tools for normal chat.
4. Move slow work to async jobs.
5. Add model routing so small models handle high-volume work and strong models
   handle final judgment.

## 2. Human-Visible Performance Targets

| Target | Budget | Rule |
| --- | ---: | --- |
| Social quick acknowledgement | 1-2 seconds | Send a short natural message before slow work. |
| Simple social reply | <= 5 seconds | Do not load heavy tools or long memory. |
| Slow task acknowledgement | <= 5 seconds | If the result cannot finish quickly, acknowledge and continue in background. |
| Image generation | async | Send "wait while I take/make it", then send the generated image. |
| Image reading | async when needed | Send "I am looking at it", then send analysis. |
| Search / public opinion | async when needed | Send "I will check", then send source-backed results. |
| Final result | required | Acknowledgements do not count as final delivery. |

## 3. Surface-First Optimization

This layer fixes the feeling of silence before deeper performance work is done.

### 3.1 Quick Acknowledgement

Social channels should not wait silently for a long model or tool call. The
runtime should send short, human-like acknowledgements:

- Image reading: "我看一下这张图，等我一下哦～"
- Image generation: "等我拍一下，马上给你～"
- Search: "我查一下，别急～"
- Complex thinking: "我想想哦，马上回你～"

Rules:

- Do not send an acknowledgement for tiny messages such as "ok" or "好".
- Deduplicate acknowledgements by channel and sender.
- An acknowledgement is progress, not the final answer.
- The final answer must still be delivered after the tool or model result.

### 3.2 Social Tone

WeChat and Feishu replies should read like real chat messages:

- 1-3 short sentences by default.
- No report headings for ordinary chat.
- No repeated summaries.
- No process narration unless the user is waiting on a slow task.
- Use richer structure only for company reports, plans, audits, or documents.

### 3.3 Visible Work State

The web UI can show thinking indicators. Social channels usually cannot, so the
runtime should simulate presence through short messages and later final results.

## 4. Bottom-Layer Optimization

This layer makes the system actually faster.

### 4.1 Latency Telemetry

Every inbound turn should record:

- intake time,
- quick acknowledgement time,
- context build time,
- first model token time,
- tool start and end time,
- final send time,
- total user-visible latency.

The minimal runtime exposes safe performance budgets through `/performance` and
safe stage timing through `/latency`. Secrets and API keys must never appear in
performance payloads.

### 4.2 Intent Router

Before the heavy model call, classify the message into one of these route types:

| Route | Fast path |
| --- | --- |
| casual_chat | small context, no heavy tools |
| quick_question | short context, answer directly |
| image_read | quick ack, image tool, final result |
| image_generate | quick ack, async image job, final image |
| search | quick ack, search runtime, source-backed result |
| company_task | Feishu identity, permission gate, async workflow |
| memory_update | working memory first, durable memory only after review |
| high_risk | stop at confirmation boundary |

### 4.3 Context Slimming

Normal social messages should not carry the full brain:

- Keep only identity, channel, latest conversation window, and critical memory.
- Load tool schemas only when the intent router says they are needed.
- Skip memory consolidation on the live reply path.
- Move dream consolidation to background or phase-end cleanup.

The minimal runtime exposes `/context?message=...` so a connector can inspect
the route-specific budget before loading memory or tools.

For real social connectors, the preferred entry is `POST /social/turn`. It
returns the first visible action, acknowledgement text, route, context budget,
and optional slow-job metadata in one safe payload.

When the same channel and target already have an unfinished slow job,
`POST /social/turn` returns `append_to_active_job` instead of creating another
job. This keeps follow-up messages from cancelling or duplicating image,
search, public-opinion, and company workflows.

### 4.4 Async Slow Jobs

Slow tasks should be represented as jobs:

```text
received -> acknowledged -> running -> completed | failed -> delivered
```

Slow-job examples:

- image generation,
- image analysis,
- search expansion,
- public-opinion report,
- Feishu document/table read,
- company workflow update,
- long reasoning report.

The user should receive an acknowledgement quickly, then the final result when
the job completes. A follow-up text message should not cancel an in-progress
image or search job unless the user explicitly says to cancel it.

The minimal runtime exposes `GET /jobs`, `POST /jobs`, and
`POST /jobs/transition` for image, search, public-opinion, and company workflows.
The job store keeps metadata, status, timestamps, input preview length, and
result pointers only.

Connectors should prefer `POST /jobs/event` for normal lifecycle updates:
`ack_sent`, `worker_started`, `worker_completed`, `worker_failed`,
`final_delivered`, `failure_delivered`, and `cancel_requested`.

Python connectors can use `hermes_runtime.connector_client.HermesConnectorClient`
directly. Node.js connectors should mirror the same HTTP contract. The canonical
integration guide is `docs/CONNECTOR_INTEGRATION_RUNBOOK.md`.

### 4.5 Model Routing

Use model slots instead of hard-coding one model everywhere:

| Slot | Use |
| --- | --- |
| fast | acknowledgement drafts, intent classification, deduplication, labels |
| summary | public-opinion digest, daily/weekly summaries, source synthesis |
| reasoning | strategy, final judgment, company decisions, owner-facing reports |
| vision | image understanding, OCR, screenshots, charts |
| image_generation | original image/sticker generation after review |

High-volume workflows should use the fast or summary slots first. The reasoning
slot should be reserved for final judgment and complex planning.

## 5. Channel-Specific Rules

### WeChat

WeChat is personal and companion-like:

- good for lightweight chat, reminders, quick capture, images, and personal
  summaries,
- not the primary channel for company approvals or employee management,
- should always feel responsive.

### Feishu

Feishu is the company management surface:

- identify who is speaking,
- keep group replies in the group,
- deduplicate repeated webhook events,
- answer document/table questions with source links,
- require owner confirmation before sensitive writes.

### Web UI

The web UI should show:

- thinking state,
- tool running state,
- image/media panels,
- trend/public-opinion panels,
- memory graph and review state.

## 6. Memory Performance Rule

Memory must not slow down ordinary replies.

Live path:

- use small working-memory snippets,
- avoid heavy consolidation,
- do not write noisy memories immediately.

Background path:

- dream consolidation,
- merge duplicate memories,
- downgrade weak memories,
- promote durable candidates to Obsidian review,
- write Chinese phase reports after each implementation stage.

## 7. Implementation Milestones

### P0: Surface Stabilization

Deliver:

- quick acknowledgement,
- slow-tool progress text,
- final-result guarantee,
- social tone rule,
- acknowledgement deduplication.

Exit criteria:

- complex social messages receive visible feedback in 1-2 seconds,
- image generation and image reading send progress before the final result,
- acknowledgements do not suppress final answers.

### P1: Performance Instrumentation

Deliver:

- `/performance` endpoint,
- latency budgets in config,
- per-stage latency logs,
- route classification logs.

Exit criteria:

- slow turns can be diagnosed by stage,
- performance payload contains no secrets,
- deployment can report current budgets.

### P2: Fast Path Router

Deliver:

- rule-first intent classification,
- reduced context for ordinary social chat,
- tool schema gating,
- `/context` route-budget diagnostics,
- `/social/turn` connector first-action planner,
- fast-model route for simple tasks.

Exit criteria:

- simple chat does not load heavy tool sets,
- common replies target <= 5 seconds,
- slow tasks move to async flow.

### P3: Async Job Runtime

Deliver:

- job states,
- background workers,
- result callback delivery,
- cancellation and lock policy,
- retry and timeout rules.

Exit criteria:

- image/search/company jobs survive follow-up messages,
- final results are delivered after completion,
- failures are explained with a next action.
- `/jobs` records only safe metadata and status.

### P4: Model Routing And Cost Control

Deliver:

- fast / summary / reasoning / vision / image slots,
- route-specific model choice,
- cost and latency telemetry,
- cache for repeated source summaries.

Exit criteria:

- high-volume intelligence uses cheaper models first,
- strong model is reserved for judgment,
- costs and latency are visible.

## 8. Copy And Credit Rule

Classmates and external AI reviewers can copy the public technical path, but the
source line must stay:

```text
Technical path source: https://github.com/LUTAO581314/hermes-
```

Public materials should describe the architecture and build order without
exposing private deployment names, server IPs, API keys, chat logs, or internal
operator details.
