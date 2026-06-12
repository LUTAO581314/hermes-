# bairui Activation 3D Interaction Design Prompt

This document is the design-and-build brief for upgrading the existing bairui
Activation screen into a 3D interactive system-core setup experience. It is not
a marketing landing page. It must preserve the current backend contract,
approval boundaries, and bairui-only public brand.

## 1. Requirement Summary

Product: bairui local/server Agent product.

Target screen: `web/bairui-console` Activation screen.

Current implementation anchors:

- `renderActivation`
- `renderActivationProgress`
- `renderActivationEvidence`
- `renderActivationRepairCard`
- `renderActivationStepOperations`
- `activation_flow` from `GET /frontend/contract`
- safe config diagnostics from `GET /config/status`

User goal:

Turn the Activation screen into a premium sci-fi control-room experience with a
3D system core that reacts to activation steps. The first screen must still be
the usable product setup flow, not a public website or hero landing page.

Non-negotiable rules:

- Public UI exposes only `bairui`.
- Do not show legacy brands, upstream project names, or old route labels in
  customer-facing copy.
- Customer-facing examples, screenshots, and setup prompts should use
  `BAIRUI_*` names. Internal compatibility variables may remain in backend
  implementation, but they must not leak into the Activation UI.
- Every visible operation must map to an existing backend contract or be marked
  as visual-only.
- External send, long-term memory write, and dangerous operations remain owner
  reviewed.
- 3D must support reduced motion and mobile fallback.
- The 3D core cannot block status text, repair guidance, or activation actions.

## 2. Aesthetic Reference Synthesis

No external site should be copied. Use these extracted design signals only:

- Control-room layout: dense operational shell, not marketing whitespace.
- Holographic object language: a central object made of rings, plates, status
  bands, nodes, and faint volumetric grids.
- Motion rhythm: slow idle loop, short state transitions, precise pointer
  parallax, no chaotic particles.
- Enterprise readability: compact typography, crisp labels, accessible contrast,
  visible status badges.
- Industrial sci-fi materials: dark graphite shell, translucent glass rings,
  cyan/blue emissive traces, amber warning accents, green readiness alignment.

## 3. Art Direction

### Mood

Premium industrial AI operations console. The feeling should be calm,
technical, and controlled. It should look like the user is activating a serious
local/server AI system, not browsing a product homepage.

### Palette

Use the current console tokens as the base:

- Canvas: near-black graphite.
- Panel: dark blue-black.
- Primary accent: cyan green.
- Secondary accent: clean blue.
- Warning: muted amber.
- Danger: controlled red.
- Success: signal green.

Avoid one-note purple gradients, decorative orbs, beige themes, and large
marketing hero gradients.

### Typography

Compact enterprise sans for UI text. Tabular mono for IDs, endpoints, commands,
and diagnostic counters. No oversized hero typography inside the workbench.

### Layout Motif

Three-part activation cockpit:

1. Left: activation stepper and progress.
2. Center: 3D system core stage.
3. Right: selected step detail, repair guidance, evidence, operations.

On mobile, collapse to:

1. status summary
2. static/fallback core
3. stepper
4. selected detail

### Motion Language

- Idle: slow rotation and breathing glow.
- Step selection: core rotates to a named angle and reveals the step layer.
- Pointer: subtle perspective shift, maximum 6 degrees.
- Status change: blocked layers pulse amber/red; ready layers align and glow.
- Reduced motion: freeze camera and show status rings as static CSS/canvas.

## 4. Activation Information Architecture

Keep the existing Activation content. Add 3D state mapping, not new fake
workflow.

Activation steps:

| Step | Current contract | 3D visual layer | Camera behavior |
| --- | --- | --- | --- |
| Brand Lock | `/frontend/contract`, `/version` | center nameplate and brand seal | front view, rings locked |
| Runtime Health | `/health`, `/ready`, `/runtime/readiness` | outer readiness ring and blocker gates | zoom out to full shell |
| License And Platform | `/license`, `/platform/heartbeat`, `/audit` | identity plate and audit pulse | slight top angle |
| Model Gateway | `/capabilities`, `POST /chat` probe | model port ring and signal beam | rotate 35 degrees right |
| Document Runtime | `/document/parse/status` | document shards entering parser lane | rotate 25 degrees left |
| Memory Review | `/document/parse/memory-review-pending` | linked memory nodes behind approval gate | close on node graph |
| Reports And Sources | `/reports`, `/document/ingest-reports`, `/source-refs` | report plate with source reference threads | tilt down |
| Channels | channel status/approval screens | outbound gate locked by approval shield | rotate right with gate closed |
| Avatar | `/avatar/status`, `/avatar/manifest` | small avatar state satellite | orbit to satellite |
| CodeGraph | `/codegraph/status`, repos, overview | code lattice and scan grid | orbit to wireframe layer |

State rules:

- `ready`: layer aligns to the core and glows green/cyan.
- `partial`: layer stays visible but dim, with blue/amber edge.
- `missing_config`: layer shows an amber missing segment.
- `blocked`: gate segment closes and pulses red/amber.
- `needs_review`: approval gate lights amber, not green.

## 5. Spline 3D Scene Brief

Create a Spline 3D scene for the bairui Activation screen.

Scene concept:

- Core object: a compact holographic "bairui system core", made from a dark
  graphite central cylinder, two translucent glass rings, and small emissive
  status plates.
- Supporting objects:
  - 10 small status modules arranged in orbit, one per activation step.
  - thin source-reference lines.
  - approval gate plate for memory/channel.
  - code lattice mini-grid.
  - document shard stream.
  - avatar satellite node.
- Environment: dark product cockpit stage, no starscape, no fantasy background.
- Camera: three-quarter perspective, object centered, enough negative space for
  UI panels.
- Materials:
  - graphite matte metal for base shell.
  - transparent glass for rings.
  - cyan and blue emissive line material for active layers.
  - amber emissive material for missing_config/needs_review.
  - red low-intensity emissive material for blocked.
- Lighting:
  - soft top key.
  - cyan rim light from lower left.
  - blue fill from upper right.
  - low ambient so labels remain readable.

Named objects required:

- `core_root`
- `ring_outer`
- `ring_inner`
- `brand_lock_layer`
- `runtime_health_layer`
- `license_platform_layer`
- `model_gateway_layer`
- `document_runtime_layer`
- `memory_review_layer`
- `reports_sources_layer`
- `channels_layer`
- `avatar_layer`
- `codegraph_layer`
- `approval_gate`
- `blocker_gate`
- `status_beam`

Interactions:

- Idle:
  - `core_root` rotates slowly on Y.
  - rings counter-rotate at different speeds.
  - status plates breathe opacity subtly.
- Pointer:
  - camera moves 2-6 degrees based on pointer position.
  - hovered layer brightens; no large scale jumps.
- Step selection:
  - selected layer moves forward 4-8 units.
  - matching ring segment brightens.
  - camera transitions to the step angle within 450 ms.
- Status updates:
  - `ready`: selected layer aligns and emits cyan/green.
  - `missing_config`: layer edge becomes amber.
  - `blocked`: blocker gate closes.
  - `needs_review`: approval gate glows amber but remains closed.
- Reduced motion:
  - no continuous rotation.
  - state change becomes a simple 150 ms opacity transition.

Performance:

- Keep geometry simple.
- Avoid heavy shadows, high particle counts, transparent overdraw storms.
- Target scene size under 3 MB if exported.
- Provide a static fallback PNG or CSS core.
- Do not require the scene to load before the Activation stepper is usable.

## 6. AI Website Design Prompt

Use this prompt for an AI website/design generator. It should produce a design
spec or visual mock, not replace the existing app.

```text
You are a senior creative technologist and product UI design director.

Design the bairui Activation screen for a local/server Agent product. This is
not a marketing website. It is the first screen of a real operations console
where users activate the system, inspect missing configuration, and proceed to
real workbenches.

Public brand rule:
- Only use the brand name "bairui".
- Do not expose legacy project names, vendor names, or upstream UI names.

Product context:
- bairui has a multi-agent command center, document knowledge ingestion,
  long-term memory review, report output, channel approval, CodeGraph, Avatar
  state, and runtime diagnostics.
- Dangerous operations are approval-gated.
- External send and long-term memory write must never appear as automatic
  success.

Screen goal:
- Make Activation feel like a premium industrial sci-fi setup cockpit.
- Keep the existing three-zone workbench: left stepper, center 3D system core,
  right step detail.
- The 3D system core must react to selected activation steps and backend state.

Activation steps:
1. Brand Lock
2. Runtime Health
3. License And Platform
4. Model Gateway
5. Document Runtime
6. Memory Review
7. Reports And Sources
8. Channels
9. Avatar
10. CodeGraph

3D behavior:
- Central object: holographic bairui system core.
- Step selection rotates the core and highlights the related layer.
- Model Gateway shows a model port ring.
- Document Runtime shows document shards entering a parser lane.
- Memory Review shows linked nodes behind an approval gate.
- Channels shows an outbound gate with will_send=false.
- CodeGraph shows a code lattice separate from memory.
- Avatar shows a small satellite state node.
- Ready states glow cyan/green.
- Partial states dim blue.
- Missing config states glow amber.
- Blocked states close a gate and pulse red/amber.

Layout:
- Left panel: activation stepper and progress.
- Center: full-height 3D system core stage, not inside a decorative card.
- Right panel: selected step evidence, repair card, operation card, and
  backend endpoints.
- Keep text compact, readable, and dashboard-like.

Visual style:
- Dark graphite canvas.
- Cyan/blue operational accents.
- Amber warning accents.
- No decorative gradient blobs.
- No generic SaaS hero.
- No oversized marketing headline.
- Dense but calm enterprise sci-fi console.

Interaction states:
- Hover, focus-visible, active, loading, disabled.
- Keyboard-accessible stepper.
- Reduced-motion mode.
- Mobile fallback: static core image or CSS/canvas core, step details stacked.

Quality bar:
- User understands within 3 seconds: this is bairui Activation.
- User can see what is ready, missing, blocked, and needs review.
- 3D never hides repair guidance.
- No fake success state.
- No external send or memory write is implied.
```

## 7. Frontend Implementation Prompt

Use this prompt for an implementation agent working inside the current
`web/bairui-console` codebase.

```text
Implement the bairui Activation 3D system-core upgrade in the existing
web/bairui-console frontend.

Do not create a landing page. Preserve the current app shell, navigation,
backend calls, and Activation screen contract.

Current files:
- web/bairui-console/app.js
- web/bairui-console/styles.css

Current Activation anchors:
- renderActivation()
- renderActivationProgress()
- renderActivationEvidence()
- renderActivationRepairCard()
- renderActivationStepOperations()
- activationTargetScreen()
- activationConfigTarget()
- activation_flow from /frontend/contract
- config status from /config/status

Implementation requirements:
1. Replace the static .system-core visual inside Activation only with an
   interactive system-core component.
2. The component must derive state from:
   - state.selectedStep
   - inferStepState(step)
   - state.readiness.runtime_readiness
   - state.configStatus.config_status
3. Add a lightweight data model:
   - activation3dStepState(stepId)
   - activation3dLayerClass(stepId, status)
   - activation3dCameraState(stepId)
4. If using Spline:
   - lazy-load the Spline iframe or runtime only after the core container is
     visible.
   - expose a fallback .system-core-fallback if Spline fails or reduced motion
     is enabled.
   - send selected step/status to Spline via postMessage or runtime object
     variables if available.
5. If not using Spline yet:
   - implement a CSS/Canvas/DOM pseudo-3D version first.
   - center object has rotating rings, layer chips, and pointer parallax.
   - step changes update transform, ring color, and active layer.
6. Do not add any fake action button.
7. Keep all existing activation repair/evidence/operation panels visible.
8. Keep external send and memory write language explicit:
   - will_send=false
   - no automatic long-term memory write
   - owner review required
9. Respect prefers-reduced-motion.
10. Mobile:
    - no heavy 3D.
    - show static core and stacked status layers.

Suggested functions:
- renderActivationCoreStage(flow, selectedStep)
- activationCoreLayer(step, index, status)
- activationCoreStateClass(status)
- bindActivationCorePointer()

Testing requirements:
- node --check web/bairui-console/app.js
- python -m unittest discover -s tests
- scripts/smoke-test.ps1 -FullAcceptance
- HTTP check /console and /console/app.js
- Browser screenshot checks when Playwright is available:
  - 1440x900 Activation
  - 768x1024 Activation
  - 390x844 Activation

Acceptance:
- Activation still loads without 3D asset.
- Stepper remains usable before 3D loads.
- Selected step changes the core visual state.
- Missing/blocked states are visually distinct.
- No public copy contains any brand except bairui.
```

### 7.1 React Implementation Notes

Use this path if the console is later moved into a React/Vite/Next frontend.
The design should remain the same; only the component boundary changes.

Recommended component structure:

```text
ActivationScreen
  ActivationStepper
  ActivationProgress
  ActivationCoreStage
    ActivationSplineCore
    ActivationDomFallbackCore
  ActivationDetailPanel
  ActivationEvidenceGrid
  ActivationRepairCard
  ActivationOperationGrid
  ReadinessBlockerList
```

State ownership:

- `ActivationScreen` owns API-loaded backend state.
- `ActivationCoreStage` receives only serializable view state:
  `steps`, `selectedStepId`, `stepStatuses`, `summary`, and
  `reducedMotion`.
- `ActivationCoreStage` emits only `onSelectStep(stepId)` and never calls
  backend APIs directly.
- Backend mutations remain in screen-level handlers such as model probe or
  Avatar state check.

React data model:

```ts
type ActivationCoreStep = {
  id: string;
  title: string;
  status: "ready" | "partial" | "missing_config" | "blocked" |
    "needs_review" | "approval_required" | "pending_review" | "failed";
  targetScreen?: string;
  safetyLabel?: string;
};
```

React interaction requirements:

- `ActivationStepper` and `ActivationCoreStage` must stay synchronized by the
  same `selectedStepId`.
- Use `React.lazy` or dynamic import for any Spline/Three.js runtime.
- Render `ActivationDomFallbackCore` while 3D loads, fails, WebGL is missing,
  mobile viewport is narrow, or `prefers-reduced-motion` is active.
- Keep all API status labels and repair cards outside the lazy 3D boundary so
  setup remains usable even if 3D fails.
- Do not put secrets, raw local paths, or upstream runtime names in React props
  intended for customer-visible rendering.

### 7.2 Native Frontend Implementation Notes

Use this path for the current `web/bairui-console` app because it is plain
HTML/CSS/JavaScript.

Recommended additions:

- Add pure rendering helpers in `app.js`:
  - `renderActivationCoreStage(flow, selected)`
  - `renderActivationCoreLayer(step, index, status)`
  - `activationCoreStateClass(status)`
  - `activationCoreCameraState(stepId)`
  - `bindActivationCoreInteractions()`
- Replace the static `.system-core` block inside `renderActivation()` with
  `renderActivationCoreStage(flow, selected)`.
- Use `data-core-step="<stepId>"` on every visual layer so clicking a layer can
  reuse the existing `state.selectedStep` update path.
- Use CSS custom properties for camera angles:
  - `--core-tilt-x`
  - `--core-tilt-y`
  - `--core-focus-y`
  - `--core-focus-z`
- Use `window.matchMedia("(prefers-reduced-motion: reduce)")` to disable
  pointer tilt and continuous ring rotation.

Native implementation constraints:

- No frontend build step is required for the first version.
- Do not add a heavy package manager dependency just for the fallback core.
- Spline or Three.js can be introduced later behind a feature flag.
- Existing `node --check web\bairui-console\app.js` must remain enough to catch
  syntax errors.
- The Activation stepper must work before the 3D layer binds events.

## 8. Native Frontend Implementation Plan

This is the recommended first implementation path before importing a heavy 3D
runtime.

### Phase A: CSS/DOM Pseudo-3D Core

Add:

- `renderActivationCoreStage(flow, selected)`
- `.activation-core-stage`
- `.activation-core-shell`
- `.activation-core-ring`
- `.activation-core-layer`
- `.activation-core-layer.is-ready`
- `.activation-core-layer.is-missing_config`
- `.activation-core-layer.is-blocked`
- `.activation-core-layer.is-needs_review`

Behavior:

- Replace the center `<section class="panel system-core-stage">` content with
  generated layers.
- Each activation step becomes a small orbiting layer.
- The selected step gets `active`.
- The shell uses CSS 3D transform:
  - `transform-style: preserve-3d`
  - `rotateX`, `rotateY`, `translateZ`
- Pointer movement sets CSS variables:
  - `--core-tilt-x`
  - `--core-tilt-y`
- Reduced motion sets both to `0deg`.

### Phase B: Step-State Choreography

Map step ID to camera variables:

| Step | rotateY | rotateX | focus layer |
| --- | --- | --- | --- |
| brand_lock | 0deg | 0deg | brand |
| runtime_health | -12deg | 4deg | outer ring |
| license_and_platform | 18deg | -4deg | identity plate |
| model_gateway | 34deg | 2deg | port ring |
| document_runtime | -30deg | 3deg | document lane |
| memory_review | 8deg | -12deg | approval nodes |
| reports_and_sources | -16deg | -8deg | report plate |
| channels | 28deg | 6deg | outbound gate |
| avatar | -38deg | 10deg | satellite |
| codegraph | 42deg | -10deg | code lattice |

### Phase C: Optional Spline Upgrade

After CSS/DOM version is stable:

- Create Spline scene from the brief above.
- Export/embed scene URL.
- Add `renderSplineActivationCore()` behind a feature flag or config constant.
- Keep CSS/DOM core as fallback.
- Do not remove tests for fallback.

## 9. Local Testing And QA Checklist

Run from repository root:

```powershell
node --check web\bairui-console\app.js
python -m unittest discover -s tests
.\scripts\check-repo-hygiene.ps1
.\scripts\smoke-test.ps1 -FullAcceptance
```

HTTP checks:

```powershell
$env:BAIRUI_MODEL_BASE_URL='https://models.example.test/v1'
$env:BAIRUI_MODEL_API_KEY='dummy'
$env:BAIRUI_MODEL_NAME='bairui-demo-model'
$env:BAIRUI_HOST='127.0.0.1'
$env:BAIRUI_PORT='8877'
python -m src.hermes serve
```

If the current backend still reads internal compatibility names, the server
adapter may map `BAIRUI_HOST` and `BAIRUI_PORT` to those internal values before
startup. Do not display the compatibility names in customer-facing UI or visual
design prompts.

Then inspect:

- `http://127.0.0.1:8877/console`
- `http://127.0.0.1:8877/console/app.js`
- `http://127.0.0.1:8877/frontend/contract`
- `http://127.0.0.1:8877/config/status`

Browser QA viewports:

- Desktop: 1440 x 900
- Tablet: 768 x 1024
- Mobile: 390 x 844

Check:

- Activation communicates "bairui setup cockpit" within 3 seconds.
- Stepper works with mouse and keyboard.
- Selecting each step changes the core visual.
- Repair card remains visible.
- No text overlaps the 3D object.
- No horizontal scroll on mobile.
- Reduced motion disables continuous rotation.
- Missing/blocked states are visually distinct.
- Console has no uncaught JavaScript errors.
- No customer UI string exposes non-bairui public brand names.

Target quality score:

- First-screen impact: 18/20 or higher.
- Information clarity: 18/20 or higher.
- 3D/brand integration: 17/20 or higher.
- Interaction polish: 13/15 or higher.
- Mobile experience: 13/15 or higher.
- Operational usefulness: 9/10 or higher.

## 10. Repair Prompt Template

Use this after QA if the generated or implemented Activation screen has issues.

```text
The current bairui Activation 3D screen has these QA failures:

- Viewport: <desktop/tablet/mobile>
- Section: Activation
- Problem: <text overlap / broken step selection / Spline not loading /
  reduced motion ignored / mobile horizontal scroll / unclear missing_config>
- Evidence: <screenshot path, console error, audit note>

Revise only the Activation screen implementation.

Preserve:
- bairui-only public brand
- existing backend contract calls
- Activation stepper
- repair card
- evidence cards
- owner-review safety language
- will_send=false
- no automatic long-term memory write

Fix:
1. <specific fix>
2. <specific fix>
3. <specific fix>

Re-run:
- node --check web\bairui-console\app.js
- python -m unittest discover -s tests
- .\scripts\smoke-test.ps1 -FullAcceptance
- browser screenshots at 1440x900, 768x1024, and 390x844
```

## 11. Final Implementation Guidance

Recommended order:

1. Build CSS/DOM pseudo-3D Activation core first.
2. Verify all current tests and smoke acceptance still pass.
3. Run browser QA.
4. Only then replace or enhance the core with Spline.

Reason:

The current bairui product value is real operational flow. A heavy 3D runtime
should enhance first-screen confidence, not reduce reliability. The fallback
core must remain good enough for demos and low-performance devices.
