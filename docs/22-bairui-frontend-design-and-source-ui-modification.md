# bairui Frontend Design And Source UI Modification

Status: design and implementation brief for the first source-UI frontend pass.

This document adapts the `ai-website-design-prompt` workflow to the `bairui`
product console. It is not a marketing-site prompt. The first screen must be a
usable operations workbench connected to the frozen backend contract.

Source UI reference is used only for interaction structure, component density,
activation rhythm, realtime panels, and media/channel ergonomics. Customer
surfaces must expose only `bairui`.

## 1. Requirement Summary

Product:

- `bairui`, an industrial agent product console.

Audience:

- owner/operator users who need to configure, inspect, and approve agent
  workflows;
- business users who need documents, memory review, reports, channels, and
  runtime readiness without touching raw backend files;
- future customer deployments where safety, auditability, and brand cleanliness
  matter more than decorative spectacle.

Goal:

- deliver a connected product UI, not a landing page;
- use the approved source UI as a substrate for interaction patterns;
- connect the frozen backend contract before visual polish expands;
- keep all public copy, routes, empty states, activation text, and chrome under
  the `bairui` brand.

Backend source of truth:

- `GET /frontend/contract`
- `docs/21-backend-contract-freeze-for-frontend.md`

## 2. Aesthetic Reference Synthesis

Named source UI:

- Internal reference: `../_external/BaiLongma`
- Role: workbench shell, activation/awakening card rhythm, realtime activity
  panels, voice/media/channel surface ideas, compact interaction density.

Design signals to keep:

- left-side command/status navigation;
- right-side activity/detail panel;
- central graph/workbench canvas;
- activation card with staged progress;
- dense controls and status chips;
- media/channel controls as operational tools, not marketing demos;
- event stream as the living nervous system of the UI.

Design signals to remove:

- upstream brand, names, route labels, and default assistant identity;
- prototype copy and any toy-like tonal choices;
- decorative-only backgrounds that do not communicate system state;
- direct references to runtime implementation names in customer surfaces;
- optimistic "sent", "activated", or "ready" labels when backend state is only
  partial, blocked, pending, or approval-required.

Assumption:

- The first pass will prioritize a React-style component architecture if the
  source UI already uses it. If the source stack differs, preserve the source
  project conventions but keep this document's contract and brand rules.

## 3. Committed Art Direction

Direction:

- premium sci-fi operations console;
- dense, readable, commercial, not a hero landing page;
- an industrial command room for documents, memory, runtime status, reports,
  and approval-controlled channels.

Palette:

- canvas: `#070A0F`
- surface: `#0E141D`
- panel: `#121B24`
- line: `#253241`
- text: `#EAF2F8`
- muted: `#8FA3B5`
- accent: `#35E6C7`
- accent secondary: `#67A8FF`
- warning: `#F6C85F`
- danger: `#FF5C7A`
- success: `#5EF0A4`

Rules:

- avoid all-purple, all-blue, beige, brown, or one-note palettes;
- keep status colors semantically consistent;
- use accents sparingly for current state, active paths, and primary controls;
- no gradient-orb or bokeh decoration.

Typography:

- compact enterprise sans for UI;
- tabular mono only for ids, timestamps, ports, status values, and event names;
- no viewport-scaled fonts;
- no hero-scale type inside workbench panels.

Layout motif:

- app shell first;
- left rail for core surfaces;
- top command/status bar;
- central workbench/graph stage;
- right drawer for selected detail, blockers, source refs, audit, and next
  actions;
- bottom command console or action input.

Motion:

- short transitions for status changes, drawer open/close, tab switch, and event
  arrival;
- no long decorative animations that block work;
- reduced-motion mode must preserve all information with fades disabled and
  numeric progress visible.

Graph/3D language:

- optional functional graph stage, not a landing hero;
- graph nodes represent documents, memory candidates, jobs, reports, source
  refs, channels, and runtime capabilities;
- every node click opens a real detail drawer or documented empty state;
- if a 3D/Spline scene is used later, it must be a lightweight status object
  embedded inside the workbench, never a full-screen marketing hero.

## 4. Information Architecture

Frozen first-pass screens:

1. Activation
2. Dashboard
3. Command
4. Documents
5. Memory Review
6. Reports
7. Channels
8. Settings

Navigation labels must use only these customer-facing names or shorter neutral
variants. Do not use source-project or runtime names as navigation labels.

### Activation

Purpose:

- prove the UI is connected to `bairui`;
- show whether the product is usable, blocked, partial, or waiting for owner
  review.

Must render:

- seven activation steps from `/frontend/contract`;
- blocking/non-blocking step state;
- exact blocker copy without secret values;
- model probe action;
- document runtime step;
- memory review step;
- report/source step.

### Dashboard

Purpose:

- one-screen operational truth.

Must render:

- readiness summary;
- blocker list;
- jobs table;
- audit/event tail;
- platform heartbeat;
- environment/license/database/server cards;
- selected item detail drawer.

### Command

Purpose:

- controlled chat/task entry.

Must render:

- prompt form;
- model readiness;
- disabled send state for missing model config;
- response/result area;
- memory status and optional memory context toggle.

### Documents

Purpose:

- document ingestion workbench.

Must render:

- session list;
- selected session pipeline;
- next-step and run-until-blocked actions;
- artifacts, indexing, source refs, report status;
- `needs_review` routing to Memory Review.

### Memory Review

Purpose:

- owner-governed long-term memory promotion.

Must render:

- pending candidate queue;
- candidate detail;
- approve/reject segmented control;
- batch review;
- note field;
- resume workflow toggle;
- future graph/backlink preview as an empty-safe panel.

### Reports

Purpose:

- inspect generated deliverables and source references.

Must render:

- report list;
- markdown preview;
- source reference drawer;
- audit link;
- empty state with next action.

### Channels

Purpose:

- owner-approved outbound communication planning.

Must render:

- status summary;
- target list;
- target diagnostics;
- send planning form;
- approval queue;
- approval review form;
- events related to channel plans and reviews.

Hard rule:

- never show external send success. Backend currently records approval and
  `will_send=false`.

### Settings

Purpose:

- inspect runtime/capability configuration without secrets.

Must render:

- memory status;
- voice ASR status;
- document parse status;
- intelligence status;
- simulation status;
- search status;
- index status;
- license state.

## 5. Component System

Required components:

- app shell;
- left rail;
- top status bar;
- central workbench;
- right detail drawer;
- bottom command console;
- status badge;
- readiness checklist;
- activation stepper;
- segmented control;
- toggle;
- file/path input;
- id list input;
- data table;
- event stream;
- review queue;
- log panel;
- empty state;
- blocker card;
- source reference drawer;
- markdown preview.

Interaction rules:

- icon buttons need tooltips;
- destructive or risky actions need explicit labels and disabled/blocked states;
- cards must not be nested inside cards;
- fixed-format UI elements need stable dimensions;
- text must not overlap at desktop, tablet, or mobile widths;
- action buttons must show loading, success, blocked, and error states.

## 6. Backend Contract Binding

The frontend must start from:

```http
GET /frontend/contract
```

It must bind screens, actions, forms, and state values from that response before
adding hand-written UI assumptions.

Mandatory first-pass endpoints:

- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /capabilities`
- `GET /platform/heartbeat`
- `GET /jobs`
- `POST /jobs`
- `GET /audit`
- `GET /events`
- `POST /chat`
- `POST /document/parse/session-list`
- `POST /document/parse/session-summary`
- `POST /document/parse/ingest-plan`
- `POST /document/parse/workbench-next`
- `POST /document/parse/workbench-run-until-blocked`
- `POST /document/parse/memory-review-pending`
- `POST /document/parse/review-memory-candidate`
- `POST /document/parse/memory-review-batch`
- `GET /document/ingest-reports`
- `GET /source-refs`
- `GET /channels/status`
- `GET /channels/targets`
- `GET /channels/diagnostics`
- `GET /channels/approvals`
- `POST /channels/send`
- `POST /channels/approvals/review`
- `GET /memory/status`
- `GET /voice/asr/status`
- `GET /document/parse/status`
- `GET /intel/status`
- `GET /simulation/status`
- `GET /search/status`
- `GET /index/status`

## 7. AI Website Design Prompt

Use this prompt only as a design-direction brief. Do not generate a marketing
landing page from it.

```text
You are a senior creative technologist and product UI design director.

Design the first product console for bairui, an industrial agent operations
workbench. The audience is owner/operator users and business customers who need
to configure, inspect, and approve agent workflows. The primary goal is not
marketing conversion; it is a connected, usable, brand-clean product console.

The frontend is based on an approved open-source UI substrate. Use it only for
interaction structure, component density, activation rhythm, event panels,
voice/media/channel ergonomics, and workbench layout. Replace every public
brand string, route label, assistant name, page title, empty state, and report
chrome with bairui.

Art direction:
- Overall mood: premium sci-fi operations console, industrial, precise, dense.
- Layout motif: left navigation rail, top command/status bar, central
  workbench/graph stage, right detail drawer, bottom command console.
- Color behavior: near-black graphite canvas, carbon panels, teal active
  states, electric blue selection, amber warnings, red blockers, green
  completion.
- Typography mood: compact enterprise sans; tabular mono only for ids,
  timestamps, ports, and status values.
- Motion language: short precise state transitions, event arrivals, drawer
  movement, reduced-motion support.
- Graph language: functional graph nodes for documents, memory candidates,
  jobs, reports, source refs, channels, and runtime capabilities.

Screens:
1. Activation: seven-step guided setup from backend contract.
2. Dashboard: readiness, blockers, jobs, audit, events, platform state.
3. Command: chat/task form with honest model readiness.
4. Documents: ingestion sessions, pipeline, next actions, reports.
5. Memory Review: owner approval queue for memory candidates.
6. Reports: generated report list, markdown preview, source refs.
7. Channels: target diagnostics, send planning, approval queue.
8. Settings: grouped runtime/capability status without secrets.

Quality constraints:
- No landing page.
- No non-bairui public brand.
- No raw secrets, internal runtime tokens, or upstream project names.
- No optimistic success state for blocked, missing_config, needs_review,
  approval_required, or pending_review.
- Channels must not show sent/delivered because backend currently records
  approval only and will_send=false.
- Responsive at 1440x900, 768x1024, and 390x844.
- No text overlap, clipped controls, nested cards, or horizontal scroll.
```

## 8. Frontend Implementation Prompt

Use this prompt for the implementation pass after the source UI is copied or
referenced in the frontend workspace.

```text
Implement the bairui product console using the approved source UI as an
interaction substrate. Preserve useful structure and component behaviors, but
replace all public copy and brand identity with bairui.

Implementation requirements:
1. Define design tokens first: colors, spacing, typography, radius, borders,
   focus rings, shadows, and motion durations.
2. Build the app shell: left rail, top status bar, central workbench, right
   drawer, bottom command console.
3. Create a typed API client around GET /frontend/contract and the frozen API
   groups in docs/21-backend-contract-freeze-for-frontend.md.
4. Render screens from the backend contract: Activation, Dashboard, Command,
   Documents, Memory Review, Reports, Channels, Settings.
5. Render forms from contract schema before adding custom field assumptions.
6. Treat state values honestly: ready, partial, blocked, missing_config,
   needs_review, approval_required, pending_review, reviewed, failed.
7. Disable unsafe actions when required fields are missing or blockers exist.
8. Implement snapshot SSE handling for GET /events and render unknown event
   types as generic audit events.
9. Add hover, focus-visible, active, loading, disabled, empty, and error states.
10. Support prefers-reduced-motion.
11. Search built assets for forbidden public brands and secrets.

Do not implement a marketing landing page. The first screen is the operations
console.
```

## 9. Local Testing And QA Checklist

Run project-native commands where available:

```bash
npm install
npm run dev
npm run build
npm run lint
npm run typecheck
npm test
```

Skip missing scripts only after recording that they are unavailable.

Required browser QA:

- desktop: 1440 x 900;
- tablet: 768 x 1024;
- mobile: 390 x 844.

Check:

- `/frontend/contract` loads and renders without console errors;
- all eight screens render;
- activation shows all seven steps;
- Dashboard shows readiness, jobs, audit, and events;
- Documents can show session list and selected session empty state;
- Memory Review requires explicit approve/reject;
- Channels shows diagnostics and approval queue, not sent success;
- Settings shows grouped runtime status without secrets;
- no text overlap, clipping, horizontal scroll, or unreadable badges;
- all controls have hover/focus/disabled states;
- keyboard tab order reaches interactive controls;
- reduced-motion mode remains usable;
- built assets contain only `bairui` as public product brand.

Required brand leak scan targets:

- HTML;
- JavaScript bundles;
- CSS bundles;
- route labels;
- page titles;
- empty states;
- screenshots where OCR/manual inspection is available.

Forbidden customer-visible terms include upstream project names and old product
labels. Internal license/attribution files may keep upstream names.

## 10. Repair Prompt Template

Use this prompt after QA finds a frontend issue.

```text
Repair the bairui frontend.

Failing viewport: <desktop/tablet/mobile dimensions>.
Failing screen: <Activation/Dashboard/Command/Documents/Memory Review/Reports/Channels/Settings>.
Backend contract involved: <endpoint or /frontend/contract section>.
Issue: <text overlap, wrong state, brand leak, missing disabled state, broken
form, console error, event rendering problem, etc.>.
Evidence: <screenshot path, console log, test output, audit finding>.

Fix only this issue while preserving:
- bairui-only public brand;
- backend contract binding;
- honest blocked/missing_config/needs_review/approval_required states;
- reduced-motion support;
- responsive desktop/tablet/mobile layouts.

Do not introduce upstream product names, raw secrets, or optimistic success
states.
```

## 11. First Implementation Order

1. Prepare frontend workspace and copy/reference the approved source UI.
2. Remove public upstream identity from routes, nav, titles, empty states, and
   visible copy.
3. Add `bairui` design tokens.
4. Implement API client and `/frontend/contract` bootstrap.
5. Build app shell and route map.
6. Connect Activation.
7. Connect Dashboard and event stream.
8. Connect Documents.
9. Connect Memory Review.
10. Connect Reports.
11. Connect Channels diagnostics and approvals.
12. Connect Command.
13. Connect Settings.
14. Run brand, responsive, interaction, and GitHub CI checks.

Do not start deep decorative polish until steps 1-13 are connected and verified.

