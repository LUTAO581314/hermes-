# Frontend: bairui UI

## 1. Brand Rule

Customer-facing UI must expose only the `bairui` brand.

Historical project names, third-party runtime names, upstream repository names,
and internal adapter names must not appear in navigation, activation screens,
empty states, report viewers, setup copy, or customer-facing API contracts.

## 2. UI Base Strategy

The frontend should use the owner-approved open-source UI base as the source
foundation, then customize it into a bairui product. Internally, the owner may
refer to this same GitHub project as Xiaobailong or Bailongma; those names are
engineering references only and must not reach customer-facing UI or
`/frontend/contract`.

Internal source reference:

- Repository: `https://github.com/xiaoyuanda666-ship-it/BaiLongma`
- License: MIT
- Primary scope: frontend interaction, component behavior, layout rhythm,
  activation page, voice panel, media panel, and realtime UI patterns.
- Backend scope: supplemental only. Extract useful connector/media/event ideas
  into owned bairui contracts instead of replacing the existing backend.

- keep the preferred component density, workbench layout, drawers, tables, and
  interaction patterns;
- replace every public brand field, route label, page title, loading state, and
  empty state with `bairui`;
- expose third-party runtime details only as neutral capability states such as
  `configured`, `missing_config`, `blocked`, or `needs_review`;
- never bundle runtime secrets into frontend JavaScript.

Detailed source-based frontend integration, design direction, screen mapping,
backend supplement list, implementation prompt, and QA checklist live in
[`20-bairui-frontend-source-ui-integration.md`](20-bairui-frontend-source-ui-integration.md).

## 3. Core Screens

The frontend must connect these product screens to real backend contracts:

- Activation: complete setup checklist, not a single button;
- Dashboard: health, readiness, runtime blockers, platform heartbeat, jobs,
  and audit visibility;
- Command: chat action and missing configuration state;
- Documents: ingest session list, session detail, next action, and run until
  blocked;
- Memory Review: pending queue, approve/reject, batch review, and continue
  workflow;
- Reports: generated reports and source references;
- Settings: runtime status grouped by capability, with honest blockers.

## 4. Contract-First UI

The frontend reads:

- `/frontend/contract`;
- `/capabilities`;
- `/jobs`;
- `/runtime/readiness`;
- `/platform/heartbeat`;
- `/audit`;
- `/events`;
- `/channels/status`;
- `/channels/targets`;
- `/channels/send`;
- `/document/parse/session-list`;
- `/document/parse/session-summary`;
- `/document/parse/workbench-next`;
- `/document/parse/workbench-run-until-blocked`;
- `/document/parse/memory-review-pending`;
- `/document/parse/memory-review-batch`;
- `/document/ingest-reports`;
- `/source-refs`.

The CLI equivalent is:

```bash
python -m src.hermes frontend-contract
```

`/frontend/contract` returns:

- `brand`: public `bairui` brand fields;
- `visibility_policy`: customer-visible brand restrictions;
- `ui_base`: source-based customization strategy;
- `design_system`: premium sci-fi operations-console tokens;
- `activation_flow`: complete activation steps;
- `screens`: core UI surfaces;
- `forms`: renderable form schemas for actions;
- `api_groups`: stable backend contracts;
- `state_values`: status values the UI must render.

## 5. Activation Flow

Activation must show the full process:

1. Brand Lock: verify the contract exposes only `bairui`.
2. Runtime Health: load `/health`, `/ready`, and `/runtime/readiness`.
3. License And Platform: show license, server id, database, and platform status.
4. Model Gateway: run or block the chat probe with exact missing configuration.
5. Document Runtime: show parser status and render the ingest-plan form.
6. Memory Review: show pending queue and require explicit owner decisions.
7. Reports And Sources: show generated reports/source refs or actionable empty
   states.

Blocking steps must prevent the misleading final "ready" state. Optional steps
may be marked incomplete but visible.

## 6. Design Direction

The visual direction is a premium sci-fi operations console:

- dense, useful, enterprise workbench layout;
- dark canvas with teal and blue operational accents;
- crisp panels, split views, detail drawers, and status rails;
- compact typography with tabular mono only for ids/status/timestamps;
- no marketing hero as the app first screen;
- no oversized decorative cards inside tool surfaces;
- reduced-motion mode must preserve all information.

## 7. QA Rules

Before customer use, test:

- no customer-visible text contains historical or upstream project brands;
- activation flow renders all seven steps;
- every core screen has real read endpoints and honest empty states;
- action buttons are disabled when required fields or blockers are missing;
- desktop, tablet, and mobile layouts have no text overlap or horizontal scroll;
- console has no uncaught errors;
- runtime secrets are absent from built frontend assets.
