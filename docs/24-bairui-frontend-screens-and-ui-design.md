# bairui Frontend Screens And UI Design

Status: product UI design source of truth for the first bairui console frontend.

This document is grounded in:

- bairui backend contract: `GET /frontend/contract`
- backend contract freeze: `docs/21-backend-contract-freeze-for-frontend.md`
- source UI modification brief: `docs/22-bairui-frontend-design-and-source-ui-modification.md`
- Avatar backend contract: `docs/23-bairui-avatar-runtime-backend-integration.md`
- source UI substrate: `_external/BaiLongma`

The source UI is used as an interaction and component substrate only. Customer
surfaces must expose only `bairui`.

## 1. Product UI Direction

The first screen is the product console, not a marketing site.

Art direction:

- premium sci-fi operations console;
- dense but readable industrial workbench;
- dark graphite canvas with teal/blue active states;
- amber review states, red blockers, green completion;
- no toy-like theme switching, public upstream names, or decorative-only visual
  effects.

Aesthetic reference synthesis:

- ReactBits-style signal: use animated, interactive component polish for small
  UI feedback, not page-level spectacle. Apply it to status chips, tab changes,
  command composer focus, drawer transitions, and hover/focus states.
- Spline-style signal: when 3D is used, design a production-ready interactive
  object with clear materials, lighting, camera, and fallback. Use modest
  geometry and state-driven interaction.
- MotionSites-style signal: use cinematic rhythm only where the user benefits
  from an onboarding or reveal sequence. Do not turn repeated work screens into
  scroll-driven showpieces.

Committed visual language:

```text
Functional Spatial Console
  industrial sci-fi
  dark graphite control room
  holographic glass
  precision metal
  emissive data circuits
  quiet diagnostic motion
  state-bound glow
  readable dense panels
```

Visual anti-patterns:

- full-page 3D marketing hero;
- generic spaceship/lab scenery;
- floating gradient orbs and bokeh blobs;
- every screen having 3D regardless of use;
- playful theme picker as a product feature;
- motion that delays approvals, reviews, or document work.

Global shell:

```text
Top status bar
  brand / environment / readiness / event count / Avatar state

Left rail
  Activation
  Dashboard
  Command
  Documents
  Memory Review
  Knowledge Graph
  Entity Detail
  Reports
  Intelligence Radar
  Channels
  Avatar
  Settings
  Events

Main workbench
  screen-specific content

Right drawer
  selected entity, blockers, source refs, approvals, or runtime detail

Bottom command console
  command input, event tail, current action state

Avatar dock
  optional Live2D browser-rendered agent state layer
```

3D and spatial effects:

- The console may use 3D, but only as functional state visualization.
- Do not build a full-screen marketing 3D hero.
- Do not use decorative gradient orbs, bokeh blobs, or empty sci-fi scenery.
- 3D surfaces must reveal real product state: knowledge relationships,
  intelligence geography, runtime health, agent activity, or Avatar presence.
- All 3D surfaces need a 2D fallback and reduced-motion mode.

Recommended 3D layers:

```text
Knowledge Graph
  2.5D node graph for documents, reports, memory nodes, entities, source refs

Intelligence Radar
  optional globe/region heat layer for trends and signals

Activation
  compact system-core object showing readiness steps and blockers

Avatar Dock
  Live2D character layer, not 3D, but visually shares the spatial status layer

Dashboard
  small runtime topology strip, not a decorative scene
```

3D distribution by screen:

| Screen | 3D Level | Rule |
| --- | --- | --- |
| Activation | Primary 3D | Holographic system core as the main onboarding object. |
| Dashboard | Light 2.5D | Small runtime topology only; no large scene. |
| Command | No primary 3D | Use multi-agent avatars, model chips, message rhythm, and optional Avatar Dock. |
| Documents | No 3D | Prioritize stepper, tables, logs, and clear actions. |
| Memory Review | No 3D | Approval clarity beats spatial effects. |
| Knowledge Graph | Primary 2.5D | Relationship graph is the main spatial experience. |
| Entity Detail | No 3D | Drawer/card readability. |
| Reports | No 3D | Reading and source evidence first. |
| Intelligence Radar | Primary 3D optional | Globe/radar only when backed by real trend data. |
| Channels | No 3D | Diagnostics and approval queue first. |
| Avatar | Spatial character layer | Live2D preview/dock, not Three.js scene. |
| Settings | No 3D | Runtime status and config clarity. |
| Events | No 3D | Timeline/table clarity. |

3D implementation guidance:

- Use Three.js only where 3D adds real information value.
- Keep the primary 3D scene unframed or integrated into the workbench canvas,
  not inside a decorative card.
- Validate with desktop, tablet, and mobile screenshots.
- Verify canvas is nonblank, correctly framed, interactive where expected, and
  does not overlap controls.
- If WebGL is unavailable, render the same data as a 2D graph/list/table.

Spline / 3D scene prompt rule:

- Write a specific scene brief before implementation: core object, supporting
  objects, camera, materials, lighting, idle motion, pointer interaction,
  state mapping, performance budget, and fallback.
- Do not ship a 3D scene whose states cannot be explained from backend data.

Global states:

- `ready`, `completed`: positive, user can proceed.
- `partial`, `source_ready`: available but not fully live.
- `missing_config`, `blocked`, `failed`: blocking, show exact missing step and
  disable unsafe actions.
- `needs_review`, `approval_required`, `pending_review`: owner action required.
- `not_found`, `already_reviewed`, `step_limit_reached`: neutral warning.
- `thinking`, `speaking`, `hidden`, `invalid_state`: Avatar-specific states.

Global safety rules:

- Do not expose non-`bairui` public brand labels.
- Do not expose secrets, raw tokens, vendor credentials, internal runtime ports,
  local sensitive paths, or upstream product names in route labels, titles,
  empty states, or action copy.
- Do not show external send success for channel actions. Current backend records
  approval and `will_send=false`.
- Do not auto-promote long-term memory. Memory write decisions must be explicit
  owner actions.
- Do not read backend storage files directly from frontend code. Use product
  APIs only.

## 2. Source UI Inventory

Reusable source files:

- `_external/BaiLongma/brain-ui.html`: thin entry for the main UI shell.
- `_external/BaiLongma/activation.html`: activation flow prototype.
- `_external/BaiLongma/src/ui/brain-ui/app-shell.js`: core shell generator:
  graph stage, primary/secondary panels, settings modal, voice/video/music/image
  panels, hotspot panel, person card panel, doc panel.
- `_external/BaiLongma/src/ui/brain-ui/app.js`: core interaction controller,
  graph behavior, event stream handling, panel mode switching, voice/TTS hooks.
- `_external/BaiLongma/src/ui/brain-ui/styles.css`: visual system and panel
  styles to be rewritten into bairui tokens.
- `_external/BaiLongma/src/ui/brain-ui/chat.js`: command/chat area behavior.
- `_external/BaiLongma/src/ui/brain-ui/doc.js` and `doc-panel.js`: document
  panel substrate.
- `_external/BaiLongma/src/ui/brain-ui/person-card.js` and
  `person-card-panel.js`: entity card substrate.
- `_external/BaiLongma/src/ui/brain-ui/hotspot.js`, `hotspot-panel.js`,
  `hotspot-earth.js`: intelligence radar substrate.
- `_external/BaiLongma/src/ui/brain-ui/thought-stream.js`: event stream
  substrate.
- `_external/BaiLongma/src/ui/brain-ui/voice-*`: voice control substrate.
- `_external/BaiLongma/src/ui/brain-ui/wechat-popup.js`: channel authorization
  and approval interaction reference only.
- `_external/BaiLongma/src/ui/brain-ui/acui/components/*`: awakening,
  self-check, security confirmation, media viewer components. Several strings
  are garbled and must be rewritten.

Source files to avoid as product first screen:

- `_external/BaiLongma/website.html`: marketing-style page; not first screen.
- `_external/BaiLongma/architecture-comparison.html`: explanatory prototype.
- `_external/BaiLongma/systemPrompt.html`: prompt preview prototype, not a main
  customer route.

## 3. Backend Contract Inventory

Frozen screens in `/frontend/contract`:

- Activation
- Dashboard
- Command
- Documents
- Memory Review
- Reports
- Channels
- Avatar
- Settings

Designed product screens derived from source UI and product needs:

- Knowledge Graph
- Entity Detail
- Intelligence Radar
- Events

These four derived screens need either existing endpoint composition or later
backend contract additions. The frontend may render them with honest partial
states in the first pass.

## 4. Screen Designs

### 4.1 Activation

Business goal:

- Bring a fresh deployment from unknown state to truthful usable state.
- Prove that the UI is connected to bairui backend contract.
- Show blockers before letting the user enter normal operations.

User actions:

- Start activation check.
- Inspect readiness blockers.
- Run model probe.
- Inspect document runtime status.
- Inspect memory review availability.
- Inspect report/source readiness.
- Continue to dashboard only when blocking steps are resolved or explicitly
  acknowledged.

Layout structure:

- Left: activation stepper with seven backend steps.
- Center: current step detail, checklist, primary action.
- Right: blocker drawer and environment summary.
- Bottom: activation event tail.
- Avatar dock: optional Live2D guide. If no model is configured, show static
  bairui status core instead.
- Optional 3D: compact readiness core object. Each ring/segment maps to one
  activation step. Red segments mean blockers, amber means review/warning, green
  means ready. Must have a 2D checklist fallback.

Core components:

- `ActivationStepper`
- `ReadinessChecklist`
- `BlockerCard`
- `RuntimeProbeButton`
- `ActivationEventTail`
- `AvatarGuide`
- `SafeContinueButton`

API binding:

- `GET /frontend/contract`
- `GET /version`
- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /license`
- `GET /platform/heartbeat`
- `GET /audit`
- `GET /capabilities`
- `POST /chat`
- `GET /document/parse/status`
- `POST /document/parse/ingest-plan`
- `POST /document/parse/memory-review-pending`
- `GET /document/ingest-reports`
- `GET /source-refs`
- `GET /avatar/status`
- `GET /avatar/manifest`

Data states:

- `ready`: step complete.
- `partial`: show step as usable with warnings.
- `blocked`: do not allow final activation.
- `missing_config`: show required configuration area.
- `needs_review`: route to Memory Review.

Empty state:

- No jobs or reports yet: show "No records yet" plus a next action such as
  create a document ingest plan.
- No Avatar model: show "Avatar is optional" and do not block activation.

Error state:

- Backend unreachable: full-page service connection error with retry.
- Contract missing: disable all derived actions and show raw endpoint status.
- Probe failed: show status and missing configuration without secrets.

Permissions and safety:

- Do not ask for or display secrets directly in frontend unless a future
  backend secret-reference API exists.
- Do not show upstream runtime names in customer copy.
- Do not show activation complete if a blocking step is still blocked.

Reusable source UI:

- `activation.html`: page rhythm, centered setup flow, progressive controls.
- `acui/components/self-check-card.js`: self-check card behavior.
- `acui/components/awakening-card.js`: staged feedback card behavior.
- `acui/components/security-confirm-card.js`: confirmation card behavior.

Must rewrite:

- Old `/activation-status` and `/activate` flow.
- Old API key detection copy.
- Old assistant/product names.
- Garbled ACUI strings.
- Provider-specific setup language.

Frontend tasks:

- Build contract bootstrapping.
- Render seven activation steps from contract.
- Add blocker-aware continue logic.
- Add Avatar guide slot.
- Add responsive activation layout.

Activation 3D design prompt:

```text
Design the bairui Activation screen as a holographic industrial sci-fi system
core interface.

This is not a login page and not a marketing hero. It is the first startup
sequence of an industrial AI agent console.

Scene concept:
A dark graphite control-room interface with a floating holographic system core
in the center. The core is made of transparent glass rings, precision metal
arcs, emissive data circuits, and small diagnostic nodes. Each ring segment
represents one activation step: brand lock, backend health, license/platform,
model gateway, document runtime, memory review, reports/sources, and Avatar
status.

Interaction:
- On load, the core powers on from dim graphite to teal-blue light.
- Each activation step lights one ring segment.
- Completed steps glow green.
- Current checking step pulses blue.
- Warning steps glow amber.
- Blocking steps show a red fractured segment.
- Hovering a ring segment rotates the core slightly and highlights the matching
  step in the left checklist.
- Clicking a segment opens the detailed blocker/action panel on the right.
- When all blocking steps are complete, the rings align into a clean bairui core
  mark and reveal the Enter Console button.

Layout:
- Left panel: activation checklist with status badges.
- Center: interactive 3D system core.
- Right panel: selected step detail, blocker explanation, retry/action button.
- Bottom strip: startup event log and backend connection state.
- Optional bottom-right Live2D Avatar guide, but it must not cover the 3D core
  or action buttons.

Visual style:
Industrial sci-fi, premium control room, dark graphite, holographic glass, teal
emissive lines, electric blue selection, amber warning, red blocker, green
completion. Motion should be quiet, precise, and premium, not flashy.

Rules:
- The 3D core must reflect real backend activation states.
- No decorative orbs, bokeh blobs, generic spaceship scenery, or marketing hero
  layout.
- Text must remain readable.
- Provide 2D fallback: circular segmented progress diagram.
- Support reduced motion.
- Only public brand is bairui.
```

Activation 3D implementation brief:

```text
Implement the activation system core with Three.js or a Spline embed wrapper.
Use backend state from /frontend/contract, /health, /ready, /runtime/readiness,
/license, /platform/heartbeat, /document/parse/status, and /avatar/status.

State mapping:
- ready/completed: green emissive ring segment
- partial/source_ready: teal-blue segment with subtle pulse
- missing_config/blocked/failed: red fractured segment
- needs_review/approval_required/pending_review: amber segment
- checking/loading: electric-blue sweep around the segment

Interaction:
- Hover segment: highlight matching checklist row.
- Click segment: select row and open right detail panel.
- Reduced motion: disable rotation and pulse; preserve color and labels.
- Mobile fallback: replace 3D with 2D segmented ring and vertical checklist.

Quality bar:
- 1440x900: 3D core centered, panels readable, no overlap.
- 768x1024: 3D core above details or compact center.
- 390x844: 2D fallback by default.
- WebGL unavailable: static SVG/Canvas segmented ring.
```

### 4.2 Dashboard

Business goal:

- Provide one-screen operational truth for the bairui runtime.

User actions:

- View system health and readiness.
- Inspect blockers and warnings.
- Create a job.
- Open recent jobs, audit events, or runtime details.
- Navigate to the next needed screen.

Layout structure:

- Top: readiness headline and environment chips.
- Left center: blockers and warnings.
- Main center: jobs table and current activity.
- Right drawer: selected event/job detail.
- Bottom: live event tail.

Core components:

- `ReadinessSummary`
- `BlockerList`
- `CapabilityGrid`
- `JobTable`
- `CreateJobForm`
- `AuditTail`
- `EventStream`
- `DetailDrawer`

API binding:

- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /capabilities`
- `GET /platform/heartbeat`
- `GET /jobs`
- `POST /jobs`
- `GET /audit`
- `GET /events`

Data states:

- `ready`: show usable state and active actions.
- `partial`: show warnings but allow safe actions.
- `blocked`: show blocker-first layout.
- `missing_config`: show configuration-needed cards.

Empty state:

- No jobs: show create job form and examples.
- No events: show event stream connected but idle.

Error state:

- Jobs fetch failed: keep readiness visible and show retry for jobs section.
- Event stream failed: fall back to `/audit`.

Permissions and safety:

- Job creation is safe but must show owner confirmation if future job type is
  risky.
- Do not expose raw environment secrets.

Reusable source UI:

- `app-shell.js`: primary/secondary panel layout.
- `thought-stream.js`: event stream substrate.
- `app.js`: EventSource pattern.
- `styles.css`: dense panel rhythm.

Must rewrite:

- Old `/audit/stats` assumptions.
- Old memory graph counters.
- Old product names and labels.

Frontend tasks:

- Build dashboard route.
- Bind readiness and capabilities.
- Build jobs and audit tables.
- Add event stream fallback behavior.

### 4.3 Command

Business goal:

- Give users a controlled command and chat entry point.
- Support multi-agent collaboration without turning the product into an
  unmanaged chat room.

User actions:

- Type an instruction.
- Send model-backed task.
- Inspect model readiness.
- View response or blocked reason.
- Optionally create a job from a prompt.
- Select one agent, multiple agents, or an automatic coordinator.
- Inspect each agent's name, avatar, model, role, and permission level.
- Compare agent replies and promote one result into a job, report, memory
  candidate, or channel approval draft.

Layout structure:

- Left: agent roster with avatar, name, model, role, online/readiness state.
- Center: multi-agent conversation and work result panel.
- Bottom: command composer with target selector.
- Right: memory/model readiness drawer plus selected agent profile.
- Top: active route and model status.

Core components:

- `CommandComposer`
- `AgentRoster`
- `AgentAvatar`
- `AgentModelBadge`
- `AgentPermissionBadge`
- `MessageList`
- `AgentMessageBubble`
- `CoordinatorMessage`
- `CompareRepliesPanel`
- `ModelReadinessBadge`
- `ResponsePanel`
- `MemoryStatusPanel`
- `JobFromPromptButton`

API binding:

- `GET /capabilities`
- `GET /memory/status`
- `POST /chat`
- `POST /jobs`
- `GET /events`
- Current backend has one generic chat action. Multi-agent UI can start in
  partial mode by rendering a single default bairui agent.
- Backend contract now available:
  - `GET /agents`
  - `GET /agents/{id}`
  - `POST /agents/session`
  - `POST /agents/session/{session_id}/message`
  - `POST /agents/session/{session_id}/round`
  - `GET /agents/session/{session_id}/events`
  - `POST /agents/session/{session_id}/promote`

Data states:

- `ready`: send enabled.
- `missing_config`: send disabled with exact missing model config.
- `completed`: render response.
- `failed`: render error and retry.
- `thinking`: agent is generating or waiting for a tool result.
- `speaking`: agent has active Avatar/TTS playback.
- `approval_required`: agent output needs owner approval before external action.
- `blocked`: agent model, permission, or tool route is unavailable.

Empty state:

- No conversation yet: show compact examples tied to actual screens:
  document ingest, memory review, report, channel plan.
- No agent roster yet: render one default bairui agent and show that
  multi-agent configuration is not yet connected.

Error state:

- Chat returns service unavailable: show model gateway missing/config failed.
- Empty prompt: local validation error.
- One agent fails while others succeed: keep successful replies visible and mark
  the failed agent bubble with its model/status reason.

Permissions and safety:

- No raw API key entry in this screen.
- Risky actions must route to review screens.
- Each agent must show permission class: read-only, draft, approval-required, or
  admin-only.
- Agents using different models must show model label as a runtime capability,
  not as a public product brand.
- External write/send/tool actions must be promoted into the proper review
  screen instead of executed from a message bubble.

Reusable source UI:

- `chat.js`: composer and message flow.
- `app-shell.js`: bottom console area.
- `app.js`: command shortcuts and panel routing ideas.
- `person-card-panel.js`: can be adapted into selected agent profile.
- `voice-panel.js`: can inform speaking/listening state indicators.

Must rewrite:

- Old `/agent-profile`.
- Old assistant labels.
- Old marker protocol if it exposes upstream identity.
- Single-speaker assumptions in message rendering.
- Any provider names or model brands in customer-facing navigation.

Frontend tasks:

- Replace chat API client.
- Add disabled states from capabilities.
- Render command result and errors.
- Add Agent Roster partial mode.
- Add message bubble metadata: avatar, name, model, role, state, timestamp.
- Add coordinator mode and compare replies panel.
- Add future backend contract proposal for multi-agent sessions.

Multi-agent visual model:

```text
Agent roster row
  avatar thumbnail
  display name
  role chip
  model chip
  readiness dot
  permission badge

Message bubble
  avatar
  name
  model
  role
  status: thinking / speaking / blocked / approval required
  content
  actions: quote, promote to job, promote to report, request review
```

Recommended roles:

- Coordinator: decomposes task, routes agents, summarizes.
- Research: gathers and compares information.
- Document: handles parse, source refs, report drafts.
- Memory: proposes long-term memory candidates but cannot auto-approve.
- Channel: drafts outbound messages but cannot send.
- Operator: watches readiness, logs, errors, deployment state.

Different model support:

- Each agent profile should contain `model_provider_ref`, `model_name`,
  `model_status`, `temperature`, `tool_scope`, and `permission_scope`.
- The command UI should show model name under the agent name, similar to a
  tavern-style character chat, but with enterprise status badges.
- The coordinator should be able to call multiple agents in one round and show
  replies grouped by agent.
- If an agent's model is missing, only that agent is disabled; the whole command
  screen should not fail unless the coordinator model is missing.

### 4.4 Documents

Business goal:

- Turn documents into indexed artifacts, source refs, reports, and memory
  candidates through an inspectable workflow.

User actions:

- Create ingest plan.
- Select session.
- Run next step.
- Run until blocked.
- Inspect artifacts and report state.
- Jump to Memory Review when required.

Layout structure:

- Left: ingest sessions.
- Center: selected session pipeline stepper.
- Right: artifacts, source refs, next action detail.
- Bottom: execution log/events.

Core components:

- `IngestSessionList`
- `DocumentPlanForm`
- `PipelineStepper`
- `NextActionButton`
- `RunUntilBlockedButton`
- `ArtifactTable`
- `ReportStatusCard`
- `NeedsReviewBanner`

API binding:

- `POST /document/parse/session-list`
- `POST /document/parse/session-summary`
- `POST /document/parse/ingest-plan`
- `POST /document/parse/workbench-state`
- `POST /document/parse/workbench-next`
- `POST /document/parse/workbench-run-until-blocked`
- `GET /document/ingests`
- `GET /document/ingest-runs`
- `GET /document/artifacts`
- `GET /document/index-runs`
- `GET /document/ingest-reports`

Data states:

- `completed`: stage finished.
- `needs_review`: stop workflow and route to Memory Review.
- `step_limit_reached`: show neutral warning.
- `not_found`: selected session stale.
- `failed`: show command/output details.

Empty state:

- No sessions: show document ingest plan form.
- Session has no artifacts: show current pipeline blocker.

Error state:

- Parse runtime missing: show `/document/parse/status` result.
- Workbench action failed: show failed step and retry only when safe.

Permissions and safety:

- File paths must not leak sensitive local paths beyond user-provided values.
- Memory promotion is not automatic.

Reusable source UI:

- `doc-panel.js`: document panel shell.
- `doc.js`: tabbed document content patterns.
- `app-shell.js`: right panel/detail pattern.

Must rewrite:

- Old help-doc semantics.
- Old provider quick links.
- Garbled document panel copy.

Frontend tasks:

- Build session list and summary views.
- Bind contract-generated forms.
- Add workflow action guards.

### 4.5 Memory Review

Business goal:

- Prevent uncontrolled long-term memory writes.

User actions:

- View pending memory candidates.
- Inspect source path and confidence.
- Approve or reject one candidate.
- Batch approve/reject.
- Add reviewer note.
- Resume document workflow after review.

Layout structure:

- Left: pending queue.
- Center: candidate detail and source excerpt.
- Right: decision panel and related source refs.
- Bottom: audit trail.

Core components:

- `MemoryCandidateQueue`
- `CandidateDetail`
- `SourceExcerpt`
- `ApproveRejectControl`
- `BatchReviewToolbar`
- `ReviewerNote`
- `ResumeWorkflowToggle`

API binding:

- `POST /document/parse/memory-review-pending`
- `GET /document/memory-candidates`
- `GET /document/memory-reviews`
- `POST /document/parse/review-memory-candidate`
- `POST /document/parse/memory-review-batch`
- `GET /events`

Data states:

- `pending_review`: needs owner action.
- `approved` or `rejected`: render as reviewed.
- `already_reviewed`: disable repeat review.
- `not_found`: candidate no longer available.

Empty state:

- No pending candidates: show last reviewed items and link back to Documents.

Error state:

- Review fails: keep candidate visible and show retry.
- Batch candidate list invalid: local validation error.

Permissions and safety:

- No auto-approval.
- Approval must be explicit and auditable.
- Do not show memory as written until backend returns approved/completed state.

Reusable source UI:

- `app-shell.js`: secondary panel and detail drawer.
- `thought-stream.js`: review events.
- `acui/components/security-confirm-card.js`: explicit confirmation behavior.

Must rewrite:

- Any "smart auto memory" or optimistic copy.
- Old source runtime names in customer UI.

Frontend tasks:

- Build candidate queue.
- Add single and batch review actions.
- Add `needs_review` routing from Documents.

### 4.6 Knowledge Graph

Business goal:

- Visualize bairui long-term knowledge relationships, especially Obsidian-style
  internal links and backlinks.

User actions:

- Browse graph nodes.
- Filter by type: document, report, memory, source, job, entity.
- Select a node.
- Expand neighbors.
- Open Entity Detail.

Layout structure:

- Full central graph stage.
- Left filter rail.
- Right node detail drawer.
- Bottom graph status and event tail.
- Optional 2.5D mode: layered graph depth for clusters and relationship
  distance. Do not hide labels or make graph navigation harder.

Core components:

- `KnowledgeGraphCanvas`
- `GraphFilterPanel`
- `NodeTypeLegend`
- `BacklinkList`
- `NeighborExpander`
- `GraphEntityDrawer`

API binding:

- Current usable endpoints:
  - `POST /memory/search`
  - `GET /source-refs`
  - `GET /document/ingest-reports`
  - `GET /document/memory-candidates`
  - `GET /document/memory-reviews`
- Recommended backend additions:
  - `GET /memory/graph`
  - `GET /memory/note/{id}`
  - `GET /memory/backlinks/{id}`
  - `GET /entities/{id}`

Data states:

- `source_ready`: graph source exists but live graph API is not ready.
- `partial`: render known nodes from existing lists.
- `missing_config`: show memory runtime blocker.
- `not_found`: selected node missing.

Empty state:

- No graph data: show how to create document ingest and memory review.

Error state:

- Graph API not implemented: show partial mode using current endpoints.
- Graph render too dense: show filter-first prompt.

Permissions and safety:

- Do not call this an Obsidian Canvas unless rendering `.canvas` data.
- For Obsidian-style graph, use Markdown `[[links]]`, backlinks, tags, and
  frontmatter as relationship sources.
- Do not mutate vault files from frontend.

Reusable source UI:

- `app-shell.js` graph stage.
- `app.js` force graph behavior.
- `styles.css` graph and node styles.
- Future Three.js layer may reuse the same graph data model after `/memory/graph`
  exists.

Must rewrite:

- Old `/memories?limit=120`.
- Old node labels and legend.
- Any upstream memory/runtime names in public graph UI.

Frontend tasks:

- Build graph screen in partial mode first.
- Define frontend graph data model.
- Add backend API request for `/memory/graph`.

### 4.7 Entity Detail

Business goal:

- Show a single selected object in context: customer, company, project, document,
  report, memory, source, job, channel target, or Avatar.

User actions:

- Inspect summary.
- See source evidence.
- Navigate to related documents/reports/memories.
- Create follow-up job.
- Route to approval or review when required.

Layout structure:

- Right drawer by default.
- Optional full screen route for deep detail.
- Header with type, status, title.
- Body with summary, properties, related graph nodes, actions.

Core components:

- `EntityDrawer`
- `EntityHeader`
- `PropertyGrid`
- `SourceRefList`
- `RelatedNodes`
- `EntityActionBar`

API binding:

- Current usable endpoints:
  - `GET /jobs`
  - `GET /document/ingest-reports`
  - `GET /source-refs`
  - `GET /document/memory-candidates`
  - `GET /document/memory-reviews`
  - `GET /channels/targets`
  - `GET /channels/diagnostics`
  - `GET /avatar/manifest`
- Recommended backend additions:
  - `GET /entities/{id}`
  - `GET /entities/{id}/relations`

Data states:

- `ready`: detail available.
- `partial`: synthesized from list endpoints.
- `not_found`: entity stale.
- `needs_review`: show review action.
- `approval_required`: show approval action.

Empty state:

- No entity selected: show "Select a graph node, job, document, report, or
  channel target."

Error state:

- Source refs missing: keep core entity visible and mark evidence unavailable.

Permissions and safety:

- Do not expose internal paths unless user provided them.
- Do not expose upstream names.
- Actions must respect target screen safety rules.

Reusable source UI:

- `person-card-panel.js`: card layout.
- `person-card.js`: card update mode and command-triggered display.

Must rewrite:

- "person card" semantics.
- Public figure/person wording.
- Old image and public-profile copy.

Frontend tasks:

- Rename to Entity Card.
- Build entity adapter from each screen's selected row/node.
- Add full detail route later if needed.

### 4.8 Reports

Business goal:

- Make generated deliverables and evidence easy to inspect.

User actions:

- Browse reports.
- Preview markdown.
- Inspect source refs.
- Write a manual report.
- Navigate back to source document/session.

Layout structure:

- Left: report list.
- Center: markdown preview.
- Right: source refs and audit metadata.

Core components:

- `ReportList`
- `MarkdownPreview`
- `SourceRefDrawer`
- `ReportWriteForm`
- `ReportAuditLinks`

API binding:

- `GET /document/ingest-reports`
- `GET /source-refs`
- `POST /obsidian/reports`
- `GET /audit`

Data states:

- `completed`: report available.
- `not_found`: selected report missing.
- `missing_config`: vault path unavailable.

Empty state:

- No reports: prompt user to run Documents workflow or write manual report.

Error state:

- Report write failed: show validation or backend message.
- Markdown preview error: show raw text fallback.

Permissions and safety:

- Report chrome only says `bairui`.
- Do not expose upstream runtime names in customer-facing report titles.
- Source refs must show confidence without overstating truth.

Reusable source UI:

- `doc-panel.js`: list/content split.
- `markdown.js`: markdown rendering helper if safe after review.

Must rewrite:

- Old doc provider footer.
- Old config guide text.

Frontend tasks:

- Build report list and preview.
- Add source refs drawer.
- Add report write form.

### 4.9 Intelligence Radar

Business goal:

- Turn external and internal signals into actionable business intelligence.

User actions:

- Inspect trend sources and search status.
- Search live web/meta sources.
- Query internal index.
- View trend cards, event timeline, and confidence.
- Convert signal into job, report, or channel approval draft.

Layout structure:

- Left: filters, watchlist, source status.
- Center: trend cards, timeline, heat map or globe view.
- Right: AI summary, related entities, actions.
- Bottom: event ticker.
- Optional 3D: globe/region heat visualization adapted from the source hotspot
  earth panel. It must represent actual trend/source data and have a 2D map/list
  fallback.

Core components:

- `RadarSourceStatus`
- `WatchlistFilters`
- `TrendCardGrid`
- `TrendTimeline`
- `SourceConfidenceBadge`
- `InternalIndexQuery`
- `RadarActionPanel`

API binding:

- Current usable endpoints:
  - `GET /intel/status`
  - `POST /search/query`
  - `POST /index/query`
  - `POST /jobs`
  - `POST /obsidian/reports`
  - `GET /events`
- Recommended backend additions:
  - `GET /intel/trends`
  - `POST /intel/watchlist`
  - `POST /intel/report`
  - `POST /intel/to-channel-draft`

Data states:

- `source_ready`: source code/runtime adapter present.
- `configured`: live service configured.
- `missing_config`: show setup blocker.
- `completed`: query result available.
- `failed`: query failed.

Empty state:

- No watchlist: prompt user to add keywords, industry, market, or customer
  topics.
- No results: show search terms and next refinement.

Error state:

- Search service missing: show `/search/status` blocker.
- Index missing: show `/index/status` blocker.
- Intelligence runtime not configured: show `/intel/status`.

Permissions and safety:

- Do not claim factual certainty from unverified search results.
- Show source confidence and timestamp.
- External channel action must route to Channels approval.

Reusable source UI:

- `hotspot-panel.js`: dense radar layout, stats strip, feed, ticker.
- `hotspot-earth.js`: optional globe/region visual.
- `hotspot.js`: mode switching behavior.

Must rewrite:

- Entertainment platform labels.
- Old social/source names in public UI.
- "global alert" exaggeration unless backed by source data.
- Garbled copy.

Frontend tasks:

- Build Intelligence Radar route.
- Bind current status/search/index APIs.
- Render partial mode until `/intel/trends` exists.
- Add action bridge to Jobs, Reports, Channels.

### 4.10 Channels

Business goal:

- Provide owner-approved outbound communication planning without uncontrolled
  external dispatch.

User actions:

- Inspect channel status.
- Inspect targets.
- Diagnose blockers.
- Create send plan.
- Review approval request.
- Inspect channel events.

Layout structure:

- Left: target list and status.
- Center: diagnostics and send planning form.
- Right: approval queue and review panel.
- Bottom: channel event tail.

Core components:

- `ChannelStatusSummary`
- `TargetList`
- `TargetDiagnostics`
- `SendPlanForm`
- `ApprovalQueue`
- `ApprovalReviewForm`
- `ChannelEventTail`

API binding:

- `GET /channels/status`
- `GET /channels/targets`
- `GET /channels/diagnostics`
- `GET /channels/approvals`
- `POST /channels/send`
- `POST /channels/approvals/review`
- `GET /events`

Data states:

- `missing_config`: channels disabled or target incomplete.
- `approval_required`: send plan created and waiting.
- `pending_review`: approval queue item.
- `reviewed`: decision recorded.
- `already_reviewed`: disable repeat action.
- `unsupported_media`: show allowed media.

Empty state:

- No approvals: show target diagnostics and send plan form.

Error state:

- Target not found: refresh targets.
- Unsupported media: show text/image/video/file options from contract.

Permissions and safety:

- Never show sent/delivered success.
- Always show that current backend records approval only.
- Attachment path must be explicit and owner-reviewed.

Reusable source UI:

- `wechat-popup.js`: authorization/popup interaction reference only.
- `settings-modal` social tab structure as layout reference only.
- `thought-stream.js`: approval event stream.

Must rewrite:

- All old channel/vendor labels.
- QR-specific assumptions unless future backend supports them.
- Any external-send success copy.

Frontend tasks:

- Build diagnostics-first channel screen.
- Bind approval queue.
- Add safe review workflow.

### 4.11 Avatar

Business goal:

- Provide a browser-rendered Live2D-compatible Avatar layer for activation,
  runtime state, speech, and user trust cues.
- Avatar is not the primary 3D layer. It is a Live2D/spatial presence layer that
  reflects agent state.

User actions:

- Inspect Avatar runtime status.
- Load manifest.
- Validate model package.
- Preview state mapping.
- Set test state.
- Hide/show Avatar Dock.

Layout structure:

- Center: Avatar preview stage.
- Left: model and engine status.
- Right: state mapping and validation result.
- Bottom: state test controls.
- Global: Avatar Dock in bottom-right across screens.

Core components:

- `AvatarDock`
- `AvatarPreviewStage`
- `AvatarEngineStatus`
- `AvatarManifestViewer`
- `ModelValidateForm`
- `StateMappingTable`
- `LipSyncToggle`
- `AvatarStateTester`

API binding:

- `GET /avatar/status`
- `GET /avatar/manifest`
- `POST /avatar/validate`
- `POST /avatar/state`
- `GET /avatars/assets/*`
- `GET /events`

Data states:

- `source_ready`: backend contract ready.
- `ready`: model configured and valid.
- `missing_assets`: model manifest references missing files.
- `invalid_manifest`: model manifest cannot parse.
- `not_found`: model manifest missing.
- `idle`, `thinking`, `speaking`, `approval_required`, `error`, `done`,
  `hidden`: runtime display states.

Empty state:

- No configured model: show optional setup path and keep Avatar Dock as static
  status core.

Error state:

- WebGL unavailable: show static fallback.
- Model validation failed: list missing files.
- Asset blocked: show safe path error.
- Heavy rendering disabled: keep message/state indicators available without the
  animated Avatar.

Permissions and safety:

- Model assets are served read-only.
- Do not upload or execute arbitrary scripts through model packages.
- Avatar must not obstruct primary workbench controls.
- Voice cloning, likeness, or persona use requires later consent workflow.

Reusable source UI:

- No direct Live2D source UI exists in the substrate.
- Use `app-shell.js` dock/panel layout patterns.
- Use media panel layout for preview stage inspiration.

Must rewrite:

- Add new frontend renderer using `pixi-live2d-display-advanced`.
- Add Web Audio amplitude lip-sync.
- Add static fallback.

Frontend tasks:

- Install frontend Live2D dependency.
- Build `BairuiAvatarEngine` wrapper.
- Build global Avatar Dock.
- Build Avatar screen.
- Bind manifest and validation.

### 4.12 Settings

Business goal:

- Show runtime and capability configuration status without exposing secrets.

User actions:

- Inspect grouped runtime status.
- See missing configuration.
- Navigate to relevant screen.
- Copy safe environment variable names if needed.

Layout structure:

- Left: settings categories.
- Center: selected runtime status.
- Right: blockers and next actions.

Core components:

- `SettingsNav`
- `RuntimeStatusGroup`
- `ConfigRequirementList`
- `StatusBadge`
- `SafeCopyEnvName`
- `GoToScreenAction`

API binding:

- `GET /memory/status`
- `GET /voice/asr/status`
- `GET /document/parse/status`
- `GET /intel/status`
- `GET /simulation/status`
- `GET /search/status`
- `GET /index/status`
- `GET /avatar/status`
- `GET /runtime/readiness`

Data states:

- `configured`: live service configured.
- `source_ready`: source/runtime available.
- `missing_config`: configuration required.
- `invalid_source`: integrated source invalid.
- `missing_source`: source missing.

Empty state:

- No selected category: show readiness overview.

Error state:

- Status endpoint fails: show endpoint error and retry.

Permissions and safety:

- No raw secret display.
- Secret values must never be echoed.
- Upstream runtime names should not appear in public category labels; use
  neutral labels such as Memory, Voice, Documents, Intelligence, Search, Index,
  Avatar.

Reusable source UI:

- `app-shell.js` settings modal.
- `styles.css` settings sections.

Must rewrite:

- Old provider tabs.
- Old secret input fields.
- Vendor labels in visible copy.
- Theme list that conflicts with bairui direction.

Frontend tasks:

- Build settings screen, not only modal.
- Reuse modal for quick settings later.
- Bind runtime status endpoints.

### 4.13 Events

Business goal:

- Provide auditability and debugging visibility for owner/operator users.

User actions:

- View event stream.
- Filter by type, risk, resource.
- Open audit detail.
- Navigate to affected entity/screen.

Layout structure:

- Left: filters.
- Center: event timeline/table.
- Right: selected event JSON/detail.
- Bottom: connection state.

Core components:

- `EventTimeline`
- `EventFilterBar`
- `AuditTable`
- `EventDetailDrawer`
- `SseConnectionBadge`
- `UnknownEventFallback`

API binding:

- `GET /events`
- `GET /audit`
- `GET /jobs`

Data states:

- Connected: live stream available.
- Disconnected: fallback to audit polling.
- Unknown event type: render generic audit event.
- Empty: no audit records yet.

Empty state:

- No events: show "No activity yet" and link to create a job or run activation
  checks.

Error state:

- SSE failed: show reconnect and audit fallback.
- Audit failed: show retry and raw HTTP status.

Permissions and safety:

- Event payload may include operational details; do not expose secrets.
- Redact secret-like values before rendering if future payloads include them.

Reusable source UI:

- `thought-stream.js`
- `app.js` EventSource pattern.
- Secondary panel event widgets.

Must rewrite:

- Old event labels.
- Old channel/source names.
- Any direct raw payload that could expose secrets.

Frontend tasks:

- Build event screen.
- Add SSE connection management.
- Add filtering and detail drawer.

## 5. Development Priority

## 5. Multi-Agent Collaboration Model

Multi-agent collaboration belongs primarily to the Command screen, but its
identity and state surfaces are shared with Entity Detail, Avatar, Events, and
Settings.

Product principle:

- The experience may borrow the readability of tavern-style character chats:
  distinct avatar, name, model, role, and message ownership.
- The execution model must remain an industrial console: permission badges,
  audit events, model readiness, approval gates, and promotion workflows.

Agent identity fields:

```json
{
  "id": "research",
  "display_name": "Research",
  "role": "research",
  "avatar_id": "research-avatar",
  "model_label": "model name",
  "model_status": "ready",
  "permission_scope": "draft",
  "tool_scope": ["search", "source_refs"],
  "state": "idle"
}
```

UI surfaces:

- Agent roster: left side of Command screen.
- Agent message bubble: every answer shows avatar, name, model, role, and
  current state.
- Selected agent detail: right drawer reuses Entity Detail structure.
- Avatar Dock: represents the active coordinator or selected agent, not every
  agent at once.
- Events screen: shows multi-agent session events and failures.
- Settings screen: shows model readiness per agent once backend supports it.

Message display rules:

- User message: full-width owner message with target selector.
- Coordinator message: summary bubble with routing decisions.
- Agent message: avatar + name + model chip + role chip + content.
- Tool/action message: compact audit-like row with endpoint, state, and result.
- Failed agent message: keep visible with blocked reason.
- Approval-required message: show action bridge to Memory Review or Channels.

Model routing rules:

- Different agents may use different models.
- Missing model config disables only the affected agent unless it is the
  coordinator.
- Model labels are operational metadata, not public product branding.
- Model secrets must never appear in message metadata.

Permission rules:

- Read-only agents can inspect and summarize.
- Draft agents can produce jobs, reports, and channel drafts.
- Approval-required agents can propose memory/channel actions but must route to
  review screens.
- Admin-only agents are hidden or disabled for normal users until permission is
  proven.

Backend state:

- Current backend only exposes one generic `POST /chat`; therefore first
  frontend pass must render multi-agent as partial mode.
- First implementation can show a single default bairui coordinator and a
  disabled "multi-agent roster coming from backend contract" state.
- Full implementation should deepen agent/session persistence, model routing,
  and tool orchestration behind the available endpoints.

Recommended backend additions:

```http
GET  /agents
GET  /agents/{id}
POST /agents/session
POST /agents/session/{session_id}/message
POST /agents/session/{session_id}/round
GET  /agents/session/{session_id}/events
POST /agents/session/{session_id}/promote
```

Recommended promotion targets:

- promote to job: `POST /jobs`
- promote to report: `POST /obsidian/reports`
- promote to memory review: `POST /document/parse/memory-review-batch` or a
  future memory candidate endpoint
- promote to channel draft: `POST /channels/send`

Recommended frontend component names:

- `AgentRoster`
- `AgentRosterItem`
- `AgentMessageBubble`
- `AgentModelChip`
- `AgentPermissionBadge`
- `CoordinatorTimeline`
- `AgentRoundCompare`
- `AgentProfileDrawer`
- `AgentPromotionMenu`
- `AgentStateAvatar`

Visual guidance:

- Avatar thumbnail size: 32-40px in roster, 28-36px in bubbles.
- Model chip sits below or beside the agent name; keep it small and tabular.
- Role chip uses semantic color, not random personality color.
- Thinking/speaking states may animate subtly, but reduced-motion must show a
  static state label.
- Live2D Dock should show only the active speaking/coordinator agent to avoid
  crowding the workbench.
- Do not combine multiple animated Avatar characters with a large 3D scene in
  the same viewport unless the user explicitly enters a presentation mode.

Implementation priority:

1. Single-agent command UI with message metadata.
2. Static/partial Agent Roster with default coordinator.
3. Message bubble format that already supports multiple agents.
4. Agent profile drawer using Entity Detail structure.
5. Backend contract proposal for agents and sessions.
6. True multi-agent rounds after backend support is implemented.

### P0: Contract-Connected Product Core

1. App shell and route map.
2. Contract bootstrap from `/frontend/contract`.
3. Activation.
4. Dashboard.
5. Command.
6. Documents.
7. Memory Review.

Exit criteria:

- All P0 screens render from backend contract.
- Missing/blocked/review states are honest.
- No non-`bairui` public brand leaks.
- No raw secrets rendered.

### P1: Differentiating Product Workbenches

1. Reports.
2. Knowledge Graph partial mode.
3. Entity Detail drawer.
4. Intelligence Radar partial mode.
5. Channels.
6. Avatar Dock and Avatar screen.

Exit criteria:

- Reports and channels are fully contract-bound.
- Knowledge Graph and Intelligence Radar clearly show partial mode where backend
  APIs are not yet frozen.
- Avatar Dock renders fallback when no model is configured.

### P2: Operator-Grade Finish

1. Settings.
2. Events.
3. Responsive tablet/mobile layouts.
4. Keyboard navigation and focus-visible polish.
5. Reduced-motion support.
6. Visual QA and brand scans.

Exit criteria:

- Desktop, tablet, and mobile viewports have no text overlap or horizontal
  scroll.
- All controls have hover, focus, active, loading, disabled, empty, and error
  states.
- Built assets pass brand leak scan.

## 6. Required Frontend Checks

## 6. AI Design Prompt Package

This package is adapted from the local `ai-website-design-prompt` workflow, but
the output target is a product console, not a marketing website.

Reference signals used:

- ReactBits: animated, interactive component-level polish.
- Spline: browser-based interactive 3D scene composition, materials, lighting,
  and production fallback.
- MotionSites: motion-first design prompt structure and reveal rhythm.

### 6.1 Master Design Prompt

```text
You are a senior product UI design director, creative technologist, and frontend
systems designer.

Design the bairui product console as a Functional Spatial Console.

This is not a marketing landing page. The first screen is the actual product
workspace for an industrial AI agent system.

Product:
bairui is a commercial AI agent console for activation, runtime readiness,
multi-agent command collaboration, document ingestion, memory review, Obsidian
style knowledge graph, reports, intelligence radar, channel approval, Live2D
Avatar, settings, and event audit.

Audience:
Owner/operators and business users who need high trust, clear system state,
reviewable actions, and a premium working interface.

Brand rule:
Only show bairui as the public brand. Do not expose source project names,
upstream runtime names, vendor names, old assistant names, secrets, local
sensitive paths, or implementation tokens in the customer UI.

Art direction:
Functional Spatial Console.
Industrial sci-fi, dark graphite control room, holographic glass, precision
metal, emissive data circuits, quiet diagnostic motion, state-bound glow,
readable dense panels.

Color behavior:
- canvas: #070A0F
- surface: #0E141D
- panel: #121B24
- line: #253241
- text: #EAF2F8
- muted: #8FA3B5
- accent: #35E6C7
- accent secondary: #67A8FF
- warning: #F6C85F
- danger: #FF5C7A
- success: #5EF0A4

Layout motif:
Top status bar, left navigation rail, central workbench, right detail drawer,
bottom command console, optional bottom-right Live2D Avatar Dock.

Screens:
1. Activation
2. Dashboard
3. Command
4. Documents
5. Memory Review
6. Knowledge Graph
7. Entity Detail
8. Reports
9. Intelligence Radar
10. Channels
11. Avatar
12. Settings
13. Events

3D distribution:
- Activation: primary 3D holographic system core.
- Knowledge Graph: primary 2.5D relationship graph.
- Intelligence Radar: optional 3D radar/globe when backed by real data.
- Avatar: Live2D spatial character layer.
- Dashboard: light runtime topology only.
- Command, Documents, Memory Review, Reports, Channels, Settings, Events: no
  primary 3D. Prioritize readability, queues, forms, tables, review states, and
  message clarity.

Motion language:
Short, precise, diagnostic motion. Component-level hover/focus transitions,
drawer motion, event arrival, command composer focus, and 3D state transitions.
No long cinematic motion on repeated workflow screens. Support reduced motion.

Quality constraints:
- Every screen must show loading, empty, error, disabled, and blocked states.
- Render missing_config, blocked, partial, needs_review, approval_required, and
  pending_review honestly.
- Never show external send success for current channel workflow.
- No card-inside-card layouts.
- No text overlap or horizontal scroll.
- Icon buttons need tooltips.
- 3D scenes need 2D fallback and must not cover controls.
- Responsive at 1440x900, 768x1024, and 390x844.
```

### 6.2 Activation 3D / Spline Prompt

```text
Create a premium 3D activation scene for bairui.

Scene name:
Holographic Industrial System Core.

Purpose:
Visualize real activation state for an industrial AI agent console. This is a
functional startup interface, not a marketing hero.

Core object:
A floating system core made of nested transparent glass rings, precision metal
arcs, small diagnostic nodes, and emissive data circuits.

Ring mapping:
- brand lock
- backend health
- license/platform
- model gateway
- document runtime
- memory review
- reports/sources
- Avatar status

Materials:
- dark graphite metal frame
- transparent smoky glass rings
- teal emissive circuit lines
- electric blue active sweep
- amber warning glow
- red fractured blocker segments
- green completion glow

Camera:
Three-quarter front view, slightly above center. The core should feel tangible
and precise, not like a generic sci-fi planet.

Lighting:
Low-key graphite environment, soft teal rim light, subtle blue key light, small
emissive accents from status segments. Avoid noisy particles.

Idle animation:
Slow ring counter-rotation, subtle breathing glow, tiny diagnostic ticks.

Pointer interaction:
Hovering a segment highlights it, slightly rotates the core toward the segment,
and sends the selected activation step id to the UI.

Click interaction:
Clicking a segment selects the matching checklist row and opens the right-side
detail panel.

State animation:
- checking: blue sweep travels around the segment
- complete: segment locks into green glow
- warning: amber pulse, slow and restrained
- blocked: red fractured segment with minimal flicker

Completion:
When all blocking steps are resolved, rings align and form a clean bairui core
mark. Then reveal the Enter Console action.

Fallback:
Provide a static image and a 2D segmented ring. On mobile or reduced-motion,
show the 2D fallback by default.

Performance:
Keep geometry modest. Avoid heavy shadows, excessive particles, and fullscreen
postprocessing. The scene must load lazily and never block activation text.
```

### 6.3 Command Screen Multi-Agent Prompt

```text
Design the bairui Command screen as an industrial multi-agent collaboration
workspace with tavern-style readability but enterprise-grade controls.

Do not use a primary 3D scene here.

Layout:
- Left: Agent Roster with avatar, name, role, model, readiness dot, permission.
- Center: multi-agent conversation with clear message ownership.
- Right: selected Agent Profile and model/tool readiness.
- Bottom: command composer with target selector.
- Bottom-right: optional Live2D Avatar Dock for the active coordinator or
  currently speaking agent.

Message bubble:
Each agent message must show avatar, display name, role chip, model chip,
permission badge, timestamp, state, and content.

Agent states:
idle, thinking, speaking, blocked, approval_required, done.

Model rules:
Different agents may use different models. If one model is missing, disable
only that agent unless the coordinator model is missing.

Safety:
Memory writes, external sends, and risky tool actions must be promoted to review
screens. Do not execute them directly from the chat bubble.

Visual style:
Dense command room UI. Compact message bubbles, crisp model chips, readable
spacing, minimal motion. No playful fantasy tavern visuals.
```

### 6.4 Frontend Implementation Prompt

```text
Implement the bairui product console from the design document.

Start from the source UI substrate, but rewrite all public copy, route labels,
API clients, and brand fields to bairui.

Backend contract:
Read GET /frontend/contract first and use it to render screens, forms, actions,
and state values. Do not hard-code old source UI endpoints.

Implementation order:
1. App shell and design tokens.
2. API client for /frontend/contract and stable backend endpoints.
3. Activation with 3D system core and 2D fallback.
4. Dashboard.
5. Command with multi-agent-ready message metadata.
6. Documents.
7. Memory Review.
8. Reports.
9. Knowledge Graph partial mode.
10. Entity Detail.
11. Intelligence Radar partial mode.
12. Channels.
13. Avatar Dock and Avatar screen.
14. Settings.
15. Events.

Technical requirements:
- Use stable CSS variables for colors, spacing, typography, radii, shadows, and
  motion durations.
- Use real loading, empty, error, disabled, and blocked states.
- Add focus-visible and keyboard navigation.
- Support reduced motion.
- Lazy-load heavy 3D and Avatar assets.
- Provide 2D fallback for every 3D scene.
- Run responsive QA at 1440x900, 768x1024, and 390x844.
- Scan built assets for public brand leaks.
```

### 6.5 Repair Prompt Template

```text
Repair the bairui frontend.

Failing viewport:
[1440x900 / 768x1024 / 390x844]

Failing screen:
[Activation / Dashboard / Command / Documents / Memory Review / Knowledge Graph
/ Entity Detail / Reports / Intelligence Radar / Channels / Avatar / Settings
/ Events]

Issue:
[text overlap / 3D blocks controls / wrong state mapping / missing fallback /
brand leak / disabled action missing / event stream failure / model chip wrong /
Avatar state mismatch]

Evidence:
[screenshot path, console log, test output, endpoint response]

Fix only this issue while preserving:
- bairui-only public brand
- backend contract binding
- honest missing_config/blocked/needs_review/approval_required states
- reduced-motion support
- 2D fallback for 3D
- no optimistic channel send success

Re-run:
- build/lint/typecheck/tests when available
- Playwright screenshots for affected viewport
- brand leak scan
```

Before merging frontend work:

```bash
npm install
npm run build
npm run lint
npm run typecheck
npm test
```

If scripts are unavailable, record that clearly and run the closest available
checks.

Browser QA viewports:

- 1440 x 900
- 768 x 1024
- 390 x 844

Brand leak scan targets:

- HTML
- CSS
- JavaScript
- route labels
- empty states
- page titles
- screenshots/manual visual review

Forbidden in customer-visible UI:

- upstream project/product names;
- old assistant names;
- raw vendor labels as navigation names;
- raw secrets;
- local sensitive paths;
- external send success for current channel workflow.

## 7. Backend Contract Gaps To Track

The following UI screens can begin with partial mode but need backend contract
expansion for full product depth:

- Knowledge Graph:
  - `GET /memory/graph`
  - `GET /memory/note/{id}`
  - `GET /memory/backlinks/{id}`
- Entity Detail:
  - `GET /entities/{id}`
  - `GET /entities/{id}/relations`
- Intelligence Radar:
  - `GET /intel/trends`
  - `POST /intel/watchlist`
  - `POST /intel/report`
  - `POST /intel/to-channel-draft`
- Avatar:
  - optional future upload API;
  - optional future TTS/audio asset API;
  - optional future consent workflow for user-provided likeness or voice.

Do not fake these endpoints in the frontend. Render honest partial states until
the backend contract is added and tested.

## 8. CodeGraph Boundary

CodeGraph is a source-structure index, not long-term memory.

Product purpose:

- Let AI inspect repository layout, files, symbols, imports, and likely change
  impact without rereading the entire codebase every turn.
- Keep code structure separate from owner-reviewed long-term memory.
- Support development, review, regression investigation, and module-boundary
  reasoning.

Backend contract now available:

- `GET /codegraph/status`
- `GET /codegraph/repos`
- `GET /codegraph/overview`
- `POST /codegraph/repos/register`
- `POST /codegraph/repos/scan`
- `POST /codegraph/query`
- `POST /codegraph/impact`

Frontend screen behavior:

- The CodeGraph screen should show registered repositories, latest scan counts,
  top files, top symbols, query results, and impact analysis.
- The screen may expose local paths only to owner/operator users.
- CodeGraph must not show customer users raw source internals unless the
  deployment explicitly enables a developer role.
- Do not label CodeGraph output as memory.

Memory boundary:

- CodeGraph stores repository/file/symbol/import metadata under
  `BAIRUI_CODEGRAPH_ROOT`.
- Long-term memory remains owner-reviewed and separate.
- CodeGraph must not auto-promote source facts into memory notes.
- A user may deliberately write a report from CodeGraph findings, but that is a
  separate explicit action.
