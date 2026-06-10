# bairui Frontend Source UI Integration

This document is the working specification for turning the owner-approved
open-source frontend base into the commercial `bairui` product UI.

Customer-visible screens, activation copy, product labels, route names, setup
steps, reports, empty states, and API contracts must expose only `bairui`.
Upstream project names are internal source references only.

## 1. Objective

The frontend is not a blank-slate rewrite. The implementation path is
source-based customization:

- keep the useful workbench interaction model from the approved source UI;
- replace all customer-visible brand, copy, route labels, and imagery with
  `bairui`;
- connect every core screen to real `bairui` backend APIs;
- add backend supplements only where the source UI has proven interaction
  patterns that the current backend does not yet expose;
- preserve upstream license and attribution in internal engineering boundaries.

Internal source reference:

- Repository: `https://github.com/xiaoyuanda666-ship-it/BaiLongma`
- Current local reference path: `../_external/BaiLongma`
- License: MIT
- Scope: frontend layout, component behavior, activation patterns, realtime UI
  events, voice/media control patterns, and dense workbench ergonomics.

## 2. Requirement Summary

The first delivered frontend must be a usable product console, not a marketing
landing page. It should open directly into the `bairui` operation workbench and
show whether the product is usable, blocked, partially configured, or waiting
for owner review.

Required behavior:

- public brand is only `bairui`;
- activation is a complete guided checklist, not a single activate button;
- the UI connects all current core backend functions;
- upstream runtime names are rendered as neutral capability groups, not
  customer-facing product labels;
- missing configuration is visible and actionable;
- the UI supports owner approval flows before long-term memory promotion;
- the experience feels advanced, sci-fi, and commercial, while staying dense,
  readable, and suitable for repeated work.

## 3. Source UI Signals To Keep

The approved source UI contributes interaction patterns, not product identity.

Keep these patterns:

- fixed left command/status panel plus right activity/detail panel;
- central graph/workbench stage that can show memory, document, task, or runtime
  relationships;
- compact top status rail with live connection, task, node, link, and throughput
  metrics;
- bottom command console with slash-command affordance;
- settings modal with grouped capability tabs;
- realtime event stream for status changes, running actions, and UI cards;
- activation/awakening card pattern with progress dots, countdown, and
  dismissible feedback;
- voice, media, and connector panels as optional tool surfaces;
- theme token architecture, but narrowed to a commercial `bairui` palette.

Remove or rewrite:

- every upstream brand string, icon, page title, route label, product claim, and
  default assistant name;
- garbled or prototype copy;
- decorative themes that read as toy-like, beige-only, violet-only, or unrelated
  to the product;
- any frontend access to raw secrets, local credential stores, or upstream
  runtime implementation names.

## 4. Art Direction

Committed direction: premium sci-fi operations console.

Palette:

- canvas: near-black graphite, not pure black;
- surfaces: layered blue-black and carbon panels;
- accents: teal for active/ready, electric blue for selected/navigation,
  amber for warnings, red for blocked/danger, green for completed;
- avoid single-hue dominance, especially all-purple, all-blue, beige, or brown.

Typography:

- compact enterprise sans for body and controls;
- tabular mono only for ids, timestamps, ports, tokens, and status values;
- no viewport-scaled fonts;
- no hero-size type inside operational panels.

Layout:

- app shell first, not landing page;
- left rail: activation, dashboard, command, documents, memory review, reports,
  channels, settings;
- top command bar: environment, readiness, license, database, server id, user
  session, quick search;
- central stage: current workflow, graph, document pipeline, command transcript,
  or report preview;
- right drawer: selected item detail, blockers, audit, source references, and
  next actions;
- bottom console: prompt/action input with slash commands and disabled states.

Motion:

- short state transitions only;
- no ornamental long animations blocking work;
- reduced-motion mode keeps numeric progress and status badges.

3D/graph language:

- use a graph stage as a functional visualization, not a hero decoration;
- nodes represent documents, memory candidates, jobs, reports, source refs,
  channels, and runtime capabilities;
- every node click must open a real detail drawer or a documented empty state.

## 5. Information Architecture

The frontend should implement these product surfaces.

### Activation

Purpose: guide first-time setup to a truthful usable state.

Reads:

- `GET /frontend/contract`
- `GET /version`
- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /license`
- `GET /platform/heartbeat`
- `GET /capabilities`
- `GET /document/parse/status`
- `POST /document/parse/memory-review-pending`
- `GET /document/ingest-reports`
- `GET /source-refs`

Actions:

- `POST /chat`
- `POST /document/parse/ingest-plan`
- `POST /document/parse/memory-review-batch`

Required steps:

1. Brand Lock: verify frontend contract public brand is `bairui`.
2. Runtime Health: load liveness, readiness, and blockers.
3. License And Platform: show license, server id, database, platform heartbeat,
   and audit visibility.
4. Model Gateway: send a probe or show exact missing configuration.
5. Document Runtime: show parser status and document ingest form.
6. Memory Review: show pending candidates and require explicit owner decisions.
7. Reports And Sources: show generated reports and source references, or explain
   next steps.

Blocking rules:

- no final "ready" state if a blocking step is incomplete;
- optional steps can be incomplete but must remain visible;
- missing configuration must name the missing env/config field without exposing
  secret values.

### Dashboard

Purpose: one-screen operational truth.

Reads:

- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /capabilities`
- `GET /platform/heartbeat`
- `GET /jobs`
- `GET /audit`

Actions:

- `POST /jobs`

UI:

- readiness summary strip;
- blocker list;
- active and recent jobs;
- audit tail;
- environment/license/database/server cards;
- right drawer for selected blocker or job.

### Command

Purpose: controlled chat/task entry with honest model readiness.

Reads:

- `GET /capabilities`
- `GET /memory/status`

Actions:

- `POST /chat`
- `POST /memory/search`
- `POST /memory/ingest`
- `POST /memory/flush`

UI:

- command transcript;
- model/config status;
- memory context toggle;
- source reference preview;
- disabled send button when required configuration is missing.

### Documents

Purpose: commercial document ingestion workbench.

Reads:

- `POST /document/parse/session-list`
- `POST /document/parse/session-summary`
- `POST /document/parse/workbench-state`
- `GET /document/ingests`
- `GET /document/ingest-runs`
- `GET /document/artifacts`
- `GET /document/index-runs`

Actions:

- `POST /document/parse/ingest-plan`
- `POST /document/parse/run-ingest`
- `POST /document/parse/register-artifacts`
- `POST /document/parse/index-artifacts`
- `POST /document/parse/memory-candidates`
- `POST /document/parse/source-refs`
- `POST /document/parse/ingest-report`
- `POST /document/parse/workbench-next`
- `POST /document/parse/workbench-run-until-blocked`

UI:

- session table;
- selected session pipeline;
- artifact list;
- next-step button;
- run-until-blocked button;
- progress and error output;
- generated report/source ref preview.

### Memory Review

Purpose: prevent uncontrolled long-term memory writes.

Reads:

- `POST /document/parse/memory-review-pending`
- `GET /document/memory-candidates`
- `GET /document/memory-reviews`

Actions:

- `POST /document/parse/review-memory-candidate`
- `POST /document/parse/memory-review-batch`

UI:

- pending queue;
- approve/reject segmented control;
- batch review;
- note field;
- resume workflow toggle;
- graph preview of future note backlinks.

### Reports

Purpose: inspect generated business deliverables and trace source evidence.

Reads:

- `GET /document/ingest-reports`
- `GET /source-refs`
- `GET /document/artifacts`

Actions:

- `POST /obsidian/reports`

UI:

- report list;
- Markdown preview;
- source reference drawer;
- audit trail for report creation;
- no raw upstream project labels in report chrome.

### Channels

Purpose: future connector control surface.

Current backend status: initial neutral contract implemented.

Source UI ideas worth adopting:

- normalized message target model;
- image, video, and file payload metadata;
- QR login/status panel for personal chat bridge;
- webhook health cards;
- connector event stream.

Initial backend supplement should expose neutral `bairui` endpoints:

- `GET /channels/status`
- `GET /channels/targets`
- `POST /channels/send`
- `GET /events`

Do not expose connector vendor names as product brands. Render them as channel
types and configuration states.

The current implementation plans and audits outbound text/image/video/file
payloads, but it does not send them. Real external dispatch remains gated by
owner confirmation, target configuration, and compliance review.

### Settings

Purpose: configure capability groups without leaking secrets.

Reads:

- `GET /memory/status`
- `GET /voice/asr/status`
- `GET /document/parse/status`
- `GET /intel/status`
- `GET /simulation/status`
- `GET /search/status`
- `GET /index/status`
- `GET /license`

UI:

- grouped capability tabs;
- masked configuration status;
- local/server mode display;
- environment validation hints;
- no secret values in DOM, logs, screenshots, or built assets.

## 6. Frontend Contract Mapping

The frontend must start by loading `/frontend/contract`. Treat it as the
rendering contract for:

- brand fields;
- activation steps;
- screens;
- forms;
- endpoint groups;
- state values;
- design tokens.

The contract is the customer-visible boundary. It must not include upstream
brand names or raw runtime names. Internal docs may mention source references;
the contract must not.

## 7. Backend Supplements From Source UI

The current backend already covers activation, health/readiness, jobs, audit,
model gateway, memory, document pipeline, source refs, reports, and runtime
status. It also exposes `GET /events` as a snapshot SSE stream projected from
audit records, so the frontend can start rendering event panels before a
long-lived broadcaster is added.

The strongest source-backed supplements to add next are:

1. Realtime events.
   - `GET /events` exists as snapshot SSE.
   - Event shape: `{ type, data, ts }`.
   - Current events include job created, document step completed, memory review
     required/completed, command completed/blocked, and report created.
   - Next upgrade: keep the same event shape and add long-lived broadcast for
     readiness changes and running-step progress.

2. UI command cards.
   - Add an internal event type for mount/update/unmount cards.
   - Use it for activation progress, document workbench progress, and memory
     review prompts.

3. Channels and media.
   - Initial neutral dispatch contract exists for text/image/video/file payloads.
   - Store channel configuration and status separately from customer copy.
   - Do not ship personal-channel automation as default customer feature until
     compliance and consent rules are documented.

4. Voice settings.
   - Current backend has ASR status and transcribe endpoint.
   - Add a frontend voice panel bound to `GET /voice/asr/status` and
     `POST /voice/asr/transcribe`.
   - TTS should be a later endpoint group after compliance and voice consent
     policy are written.

## 8. Implementation Prompt

Use this prompt when starting the actual frontend coding pass:

```text
Build the bairui product console from the existing approved open-source
frontend UI base. Do not create a landing page. Use the source UI only for
interaction structure, component behavior, dense layout rhythm, realtime panels,
activation card patterns, voice/media panel patterns, and settings/modal
ergonomics.

The only customer-facing brand is bairui. Replace all upstream brand strings,
assistant names, route labels, page titles, empty states, logo text, activation
copy, and report chrome with bairui. Do not expose upstream project names,
runtime names, or internal repository names in the built UI or in requests to
/frontend/contract.

First screen: a premium sci-fi operations console with left navigation, top
command/status bar, central workbench/graph stage, right detail drawer, and
bottom command console. It must be dense, readable, commercial, and suitable
for repeated operations work.

Connect these screens to real backend APIs:
Activation, Dashboard, Command, Documents, Memory Review, Reports, Channels,
and Settings. Start by reading GET /frontend/contract and render activation
steps, forms, screens, state values, and design tokens from it. Use honest
blocked/missing_config/partial/needs_review states and disable action buttons
when required fields or blockers are missing.

Activation must render the full seven-step setup flow:
Brand Lock, Runtime Health, License And Platform, Model Gateway, Document
Runtime, Memory Review, Reports And Sources. It must not show a final ready
state while a blocking step is incomplete.

Use stable dimensions for panels, controls, graph nodes, badges, steppers, and
tables. No text overlap at desktop, tablet, or mobile widths. No viewport-scaled
fonts. No nested cards. Use icon buttons with tooltips for tool actions and text
buttons only for clear commands.

Add reduced-motion behavior. Ensure built assets contain no secrets and no
customer-visible non-bairui product brand.
```

## 9. Local QA Checklist

Before a frontend build is considered usable:

- load `/frontend/contract` and render without console errors;
- search built frontend assets for forbidden public brands;
- verify activation renders all seven steps;
- verify every screen has a real read endpoint and an honest empty state;
- verify every action form validates required fields before submit;
- verify blocked and missing_config states disable unsafe actions;
- verify document workbench can plan, step, run until blocked, create source
  refs, and show generated reports;
- verify memory review requires explicit approve/reject decisions;
- verify secrets are not present in HTML, JS, CSS, local storage, screenshots,
  or logs;
- run desktop, tablet, and mobile screenshots;
- inspect for text overlap, horizontal scroll, clipped buttons, and unreadable
  status badges;
- run reduced-motion mode.

## 10. Repair Prompt Template

Use this template when QA finds UI issues:

```text
Repair the bairui frontend. The failing viewport is <viewport>. The failing
screen is <screen>. The issue is <exact issue>. The affected backend contract is
<endpoint or /frontend/contract section>. Fix the UI so it preserves the bairui
brand-only rule, keeps action states honest, prevents overlap, and still works
with reduced motion. Do not introduce upstream product names or raw secrets.
```

## 11. Next Engineering Steps

1. Build the frontend app shell from the source UI structure.
2. Replace all public copy and assets with `bairui`.
3. Implement a small typed API client for current backend endpoints.
4. Render activation from `/frontend/contract`.
5. Connect Dashboard, Documents, Memory Review, and Reports first.
6. Add Command and Settings next.
7. Upgrade snapshot SSE into long-lived broadcast, then add Channels/Media.
8. Run brand leak, endpoint, screenshot, and reduced-motion QA.
