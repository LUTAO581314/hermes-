const api = {
  async get(path) {
    const response = await fetch(path, { cache: "no-store", headers: ownerAuthHeaders() });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw createApiError(path, response.status, data);
    return data;
  },
  async post(path, payload = {}) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...ownerAuthHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw createApiError(path, response.status, data);
    return data;
  },
};

const OWNER_TOKEN_KEY = "bairui.console.ownerToken.v1";

function getOwnerToken() {
  try {
    return localStorage.getItem(OWNER_TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

function setOwnerToken(value) {
  try {
    const token = String(value || "").trim();
    if (token) {
      localStorage.setItem(OWNER_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(OWNER_TOKEN_KEY);
    }
    return true;
  } catch {
    return false;
  }
}

function ownerAuthHeaders() {
  const token = getOwnerToken();
  return token ? { "X-Bairui-Owner-Token": token } : {};
}

function createApiError(path, status, data = {}) {
  const message = data?.message || data?.chat?.error || data?.error || data?.detail || `${path} ${status}`;
  const error = new Error(message);
  error.path = path;
  error.status = status;
  error.code = data?.error || data?.config_apply?.status || data?.chat?.status || data?.status || "";
  error.payload = data;
  return error;
}

const screens = [
  ["activation", "Activation", "A1"],
  ["dashboard", "Dashboard", "D1"],
  ["command", "Command", "C1"],
  ["documents", "Documents", "D2"],
  ["memory", "Memory Review", "M1"],
  ["graph", "Knowledge Graph", "G1"],
  ["entity", "Entity Detail", "E1"],
  ["reports", "Reports", "R1"],
  ["intel", "Intelligence Radar", "I1"],
  ["channels", "Channels", "C2"],
  ["avatar", "Avatar", "A2"],
  ["codegraph", "CodeGraph", "CG"],
  ["settings", "Settings", "S1"],
  ["events", "Events", "E2"],
];

const state = {
  screen: "activation",
  contract: null,
  health: null,
  ready: null,
  readiness: null,
  platform: null,
  license: null,
  configStatus: null,
  capabilities: [],
  jobs: [],
  audit: [],
  events: [],
  agents: [],
  agentSessions: [],
  selectedAgentSessionId: "",
  selectedAgentIds: [],
  agentEvents: [],
  agentEventsPage: null,
  agentPromotions: [],
  agentEventOffset: 0,
  agentEventLimit: 20,
  agentComposerMode: "round",
  promotionResults: {},
  avatarStatus: null,
  avatarManifest: null,
  avatarValidation: null,
  avatarActionResult: null,
  runtimeStatus: {},
  documentSessions: [],
  selectedIngestId: "",
  documentSession: null,
  memoryQueue: null,
  memoryCandidates: [],
  memoryReviews: [],
  memoryReviewResult: null,
  documentActionResult: null,
  reportWriteResult: null,
  reports: [],
  sourceRefs: [],
  documentPlanDraft: { input_path: "", title: "", output_dir: "", backend: "", language: "", device: "cpu" },
  channels: null,
  channelTargets: [],
  channelDiagnostics: [],
  channelApprovals: [],
  channelApprovalReviews: [],
  channelPlanResult: null,
  channelReviewResult: null,
  codegraph: null,
  codegraphRepos: [],
  selectedCodegraphRepoId: "",
  codegraphOverview: null,
  codegraphQuery: null,
  codegraphImpact: null,
  codegraphActionResult: null,
  activationProbe: null,
  activationAction: null,
  demoSeed: null,
  demoFlow: null,
  auditFilter: "all",
  selectedEntity: null,
  selectedStep: "brand_lock",
  loading: new Set(),
  errors: {},
  errorDetails: {},
};

const UI_STATE_KEY = "bairui.console.ui.v1";
const validScreenIds = new Set(screens.map(([id]) => id));

const el = {
  rail: document.getElementById("left-rail"),
  title: document.getElementById("screen-title"),
  kicker: document.getElementById("screen-kicker"),
  actions: document.getElementById("screen-actions"),
  body: document.getElementById("screen-body"),
  topbar: document.getElementById("topbar-status"),
  drawer: document.getElementById("detail-drawer"),
  drawerContent: document.getElementById("drawer-content"),
  drawerClose: document.getElementById("drawer-close"),
  commandMeta: document.getElementById("command-meta"),
  commandInput: document.getElementById("global-command"),
  commandSend: document.getElementById("global-command-send"),
  avatarState: document.getElementById("avatar-state"),
};

function clsStatus(value = "") {
  return `status-pill is-${String(value || "unknown").replaceAll("-", "_")}`;
}

function pill(value, label = value) {
  return `<span class="${clsStatus(value)}">${escapeHtml(label || value || "unknown")}</span>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function shortId(value) {
  const text = String(value || "");
  return text.length > 12 ? text.slice(0, 8) : text || "-";
}

function firstNonEmpty(...values) {
  return values.find((value) => value !== undefined && value !== null && String(value).trim() !== "") || "";
}

function exportTimestamp() {
  return new Date().toISOString().replaceAll(":", "").replaceAll(".", "").replace("T", "-").replace("Z", "Z");
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function exportConsoleData(kind, payload) {
  downloadJson(`bairui-${kind}-${exportTimestamp()}.json`, {
    product: "bairui",
    export_kind: kind,
    exported_at: new Date().toISOString(),
    safety: {
      secrets_included: false,
      external_send_performed: false,
      long_term_memory_auto_write: false,
    },
    payload,
  });
}

function setBusy(key, active) {
  if (active) state.loading.add(key);
  else state.loading.delete(key);
}

function persistUiState() {
  try {
    const entity = state.selectedEntity
      ? {
          type: state.selectedEntity.type || "",
          title: state.selectedEntity.title || "",
          status: state.selectedEntity.status || "",
          ref: state.selectedEntity.ref || state.selectedEntity.raw?.id || state.selectedEntity.raw?.path || "",
        }
      : null;
    const snapshot = {
      screen: validScreenIds.has(state.screen) ? state.screen : "activation",
      selectedStep: state.selectedStep || "brand_lock",
      selectedIngestId: state.selectedIngestId || "",
      selectedAgentSessionId: state.selectedAgentSessionId || "",
      selectedAgentIds: Array.isArray(state.selectedAgentIds) ? state.selectedAgentIds.slice(0, 12) : [],
      agentComposerMode: state.agentComposerMode || "round",
      selectedCodegraphRepoId: state.selectedCodegraphRepoId || "",
      auditFilter: state.auditFilter || "all",
      selectedEntity: entity,
    };
    localStorage.setItem(UI_STATE_KEY, JSON.stringify(snapshot));
  } catch (error) {
    console.warn("Could not persist bairui UI state", error);
  }
}

function restoreUiState() {
  try {
    const snapshot = JSON.parse(localStorage.getItem(UI_STATE_KEY) || "{}");
    if (!snapshot || typeof snapshot !== "object") return;
    if (validScreenIds.has(snapshot.screen)) state.screen = snapshot.screen;
    if (typeof snapshot.selectedStep === "string") state.selectedStep = snapshot.selectedStep || state.selectedStep;
    if (typeof snapshot.selectedIngestId === "string") state.selectedIngestId = snapshot.selectedIngestId;
    if (typeof snapshot.selectedAgentSessionId === "string") state.selectedAgentSessionId = snapshot.selectedAgentSessionId;
    if (Array.isArray(snapshot.selectedAgentIds)) state.selectedAgentIds = snapshot.selectedAgentIds.filter(Boolean).slice(0, 12);
    if (["round", "message"].includes(snapshot.agentComposerMode)) state.agentComposerMode = snapshot.agentComposerMode;
    if (typeof snapshot.selectedCodegraphRepoId === "string") state.selectedCodegraphRepoId = snapshot.selectedCodegraphRepoId;
    if (typeof snapshot.auditFilter === "string") state.auditFilter = snapshot.auditFilter || "all";
    if (snapshot.selectedEntity?.type && snapshot.selectedEntity?.ref) {
      state.selectedEntity = {
        type: snapshot.selectedEntity.type,
        title: snapshot.selectedEntity.title || snapshot.selectedEntity.ref,
        status: snapshot.selectedEntity.status || "partial",
        ref: snapshot.selectedEntity.ref,
        raw: { id: snapshot.selectedEntity.ref, restored: true },
      };
    }
  } catch (error) {
    console.warn("Could not restore bairui UI state", error);
  }
}

async function runAction(key, fn, after = refreshScreenData) {
  setBusy(key, true);
  state.errors[key] = "";
  state.errorDetails[key] = null;
  render();
  try {
    const result = await fn();
    await after();
    return result;
  } catch (error) {
    const detail = productErrorGuide(error, key);
    state.errors[key] = detail.summary;
    state.errorDetails[key] = detail;
    render();
    return null;
  } finally {
    setBusy(key, false);
    render();
  }
}

async function copyText(text) {
  const value = String(text || "");
  if (!value) return false;
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch (error) {
    // fallback below
  }
  const fallback = document.createElement("textarea");
  fallback.value = value;
  fallback.setAttribute("readonly", "readonly");
  fallback.style.position = "fixed";
  fallback.style.top = "-9999px";
  fallback.style.opacity = "0";
  document.body.appendChild(fallback);
  fallback.select();
  const copied = document.execCommand("copy");
  document.body.removeChild(fallback);
  return copied;
}

function errorConfigTarget(key = "", error = {}) {
  const text = `${key} ${error?.path || ""} ${error?.code || ""} ${error?.message || ""}`.toLowerCase();
  if (/codegraph|repo|scan|source/.test(text)) return "codegraph_root";
  if (/doc|mineru|parse|ingest/.test(text)) return "document_output_dir";
  if (/memory|vault|obsidian/.test(text)) return "memory_vault";
  if (/channel|approval|send/.test(text)) return "channel_targets";
  if (/avatar|live2d/.test(text)) return "avatar_assets";
  if (/database|postgres/.test(text)) return "database";
  if (/license/.test(text)) return "license";
  if (/agent|chat|model|command/.test(text)) return "model_gateway";
  if (/settings|config/.test(text)) return "model_gateway";
  return "";
}

function configStatusItem(id) {
  return (state.configStatus?.config_status?.items || []).find((item) => item.id === id) || null;
}

function configChecklistStep(id) {
  return (state.configStatus?.config_status?.checklist?.steps || []).find((step) => step.id === id || (id === "document_output_dir" && step.id === "documents")) || null;
}

function configRepairGuide(key = "", error = {}) {
  const target = errorConfigTarget(key, error);
  const checklist = state.configStatus?.config_status?.checklist || {};
  const item = configStatusItem(target);
  const step = configChecklistStep(target);
  const command = (checklist.commands || [])[0] || "python -m src.hermes config-status";
  if (!target) {
    return {
      target: "runtime",
      fix: "Open Settings, refresh checks, then use the visible blocker list to repair the missing runtime.",
      verify: command,
    };
  }
  if (target === "model_gateway") {
    return {
      target,
      fix: "Set BAIRUI_MODEL_BASE_URL, BAIRUI_MODEL_API_KEY, and BAIRUI_MODEL_NAME, then refresh Settings.",
      verify: command,
    };
  }
  if (target === "channel_targets") {
    return {
      target,
      fix: "Configure BAIRUI_CHANNEL_TARGETS_JSON only for owner-reviewed targets. This still creates approvals only; will_send=false.",
      verify: command,
    };
  }
  const path = item?.fields?.path || step?.detail || "";
  return {
    target,
    fix: path ? `Create or configure ${target}: ${path}` : step?.detail || "Open Settings and complete the mapped configuration item.",
    verify: command,
  };
}

function productErrorGuide(error, key = "") {
  const path = error?.path || "";
  const status = error?.status || "";
  const raw = error?.message || "Action failed.";
  const code = error?.code || "";
  const repair = configRepairGuide(key, error);
  const guide = {
    title: "Action needs attention",
    summary: raw,
    reason: "The backend returned an error before completing the requested action.",
    next: "Review the visible configuration and try again after the missing input is fixed.",
    fix: repair.fix,
    verify: repair.verify,
    safety: "No external send or long-term memory write was completed.",
    technical: [path, status ? `HTTP ${status}` : "", code, repair.target ? `config=${repair.target}` : "", raw].filter(Boolean).join(" | "),
  };
  if (status === 400 || code === "invalid_request" || /required/i.test(raw)) {
    guide.title = "Required input is missing";
    guide.reason = "The action did not have all required fields.";
    guide.next = "Fill the highlighted path, id, message, decision, or prompt field, then run the action again.";
  }
  if (status === 401 && code === "owner_token_required") {
    guide.title = "Owner token required";
    guide.reason = "The server is in owner-gated mode and refused a write API request without the local owner token.";
    guide.next = "Open Settings, save the owner token for this browser, then retry the action.";
    guide.fix = "Use the Owner token for this browser field. The token is sent as X-Bairui-Owner-Token and is never included in exports.";
    guide.verify = "Open Settings and refresh /config/status; owner_gate should be configured.";
    guide.safety = "No write action was completed before owner authorization.";
  }
  if (status === 404 || code === "not_found" || /not found/i.test(raw)) {
    guide.title = "Record was not found";
    guide.reason = "The selected item no longer exists or the page is using an outdated reference.";
    guide.next = "Refresh this screen, select the item again, then retry.";
  }
  if (status === 503 || code === "missing_config" || /missing_config|disabled|not configured/i.test(raw)) {
    guide.title = "Runtime is not configured";
    guide.reason = "A required local runtime, model, channel, parser, or path is missing.";
    guide.next = "Open Activation or Settings, complete the mapped missing_config item, then return here.";
    guide.fix = repair.fix;
    guide.verify = repair.verify;
  }
  if (status === 409 || /already/i.test(raw)) {
    guide.title = "Already reviewed";
    guide.reason = "This review item has already been handled.";
    guide.next = "Refresh the queue and open the latest review record.";
  }
  if (status === 409 && code === "confirmation_required") {
    guide.title = "Dangerous change needs confirmation";
    guide.reason = "The requested configuration touches admin-level or restart-sensitive fields.";
    guide.next = "Type the exact confirmation phrase shown in Settings, then save again.";
    guide.fix = "Review dangerous_fields, type APPLY BAIRUI CONFIG, and retry only if this is an intentional owner action.";
    guide.safety = "The backend did not save the high-risk configuration because confirmation was missing.";
  }
  if (key.startsWith("codegraph")) {
    guide.next = "Register a source repository, select it, scan it, then run query or impact again.";
    guide.fix = "Open CodeGraph, register the repository path, run Scan, then retry the query or impact action.";
    guide.verify = "python -m src.hermes codegraph status";
    guide.safety = "CodeGraph reads source structure only and does not write long-term memory.";
  }
  if (key.startsWith("doc") || key === "documents") {
    guide.next = "Check the document path and selected ingest session, then advance the workbench one step.";
    guide.fix = "Open Documents, confirm the local input path exists, then run Next Step or Run Until Blocked.";
    guide.verify = "python -m src.hermes document parse status";
    guide.safety = "Document parsing may create candidates, but memory still requires owner review.";
  }
  if (key.startsWith("channel")) {
    guide.next = "Check channel target diagnostics, message text, media type, and attachment path.";
    guide.fix = "Open Channels, inspect target diagnostics, then create or review the approval draft.";
    guide.verify = "python -m src.hermes channels diagnostics";
    guide.safety = "Channel actions only create approval records; will_send remains false.";
  }
  if (key.startsWith("demo")) {
    guide.next = "Run Seed Demo first if resources are empty, then run Demo Flow again.";
    guide.fix = "Open Dashboard and run Seed Demo, then Run Demo Flow. If configuration is blocked, copy the Settings checklist.";
    guide.verify = ".\\scripts\\smoke-test.ps1 -FullAcceptance";
    guide.safety = "Demo Flow verifies approvals without sending externally or writing memory automatically.";
  }
  return guide;
}

function renderProductError(key) {
  const detail = state.errorDetails[key];
  if (!detail) return "";
  return `
    <div class="product-error" role="alert">
      <div class="step-title"><span>${escapeHtml(detail.title)}</span>${pill("blocked", "needs action")}</div>
      <p>${escapeHtml(detail.summary)}</p>
      <div class="error-guide-grid">
        <div><span>Why</span><strong>${escapeHtml(detail.reason)}</strong></div>
        <div><span>Next</span><strong>${escapeHtml(detail.next)}</strong></div>
        <div><span>Fix</span><strong>${escapeHtml(detail.fix)}</strong></div>
        <div><span>Verify</span><strong>${escapeHtml(detail.verify)}</strong></div>
        <div><span>Safety</span><strong>${escapeHtml(detail.safety)}</strong></div>
      </div>
      <p class="muted mono compact-copy">${escapeHtml(detail.technical)}</p>
    </div>`;
}

function renderRail() {
  el.rail.innerHTML = screens
    .map(
      ([id, label, icon]) => `
        <button class="nav-btn ${state.screen === id ? "active" : ""}" type="button" data-screen="${id}" title="${label}">
          <span class="nav-icon">${icon}</span>
          <span class="nav-label">${label}</span>
        </button>`,
    )
    .join("");
  el.rail.querySelectorAll("[data-screen]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.screen = button.dataset.screen;
      persistUiState();
      render();
      await refreshScreenData();
    });
  });
}

function renderTopbar() {
  const health = state.health?.status || "loading";
  const ready = state.ready?.status || "partial";
  const runtime = state.readiness?.runtime_readiness?.status || "loading";
  const eventCount = state.events.length || state.audit.length || 0;
  el.topbar.innerHTML = [
    pill(health, `health ${health}`),
    pill(ready, `ready ${ready}`),
    pill(runtime, `runtime ${runtime}`),
    `<span class="status-pill">events ${eventCount}</span>`,
  ].join("");
  el.commandMeta.textContent = state.contract ? `contract ${state.contract.contract_version || "loaded"}` : "contract loading";
  el.avatarState.textContent = state.avatarStatus?.avatar?.status || state.avatarManifest?.avatar_manifest?.engine?.status || "idle";
}

function setScreenHead(title, kicker = "bairui") {
  el.title.textContent = title;
  el.kicker.textContent = kicker;
  el.actions.innerHTML = "";
}

function renderActivation() {
  setScreenHead("Activation", "startup sequence");
  const flow = state.contract?.activation_flow || [];
  const selected = flow.find((step) => step.id === state.selectedStep) || flow[0];
  if (!state.selectedStep && selected) state.selectedStep = selected.id;
  const selectedState = inferStepState(selected || {});
  const targetScreen = activationTargetScreen(selected?.id || "");
  el.actions.innerHTML = `
    <button class="ghost-btn" type="button" id="refresh-activation">Refresh</button>
    <button class="primary-btn" type="button" id="open-activation-target" ${!targetScreen ? "disabled" : ""}>Open Step</button>`;
  el.body.innerHTML = `
    <div class="activation-layout">
      <section class="panel pad">
        <h2 class="panel-title">Activation steps</h2>
        ${renderActivationProgress(flow)}
        <div class="step-list">
          ${flow
            .map((step) => {
              const stepState = inferStepState(step);
              return `
                <button class="step-item ${selected?.id === step.id ? "active" : ""}" type="button" data-step="${step.id}">
                  <div class="step-title">
                    <span>${escapeHtml(step.title)}</span>
                    ${pill(stepState)}
                  </div>
                  <div class="step-copy">${escapeHtml(step.complete_when || "")}</div>
                  <div class="agent-meta">
                    ${(step.read || []).slice(0, 3).map((path) => `<span class="chip mono">${escapeHtml(path)}</span>`).join("")}
                  </div>
                </button>`;
            })
            .join("") || `<div class="empty-state">Backend contract is loading.</div>`}
        </div>
      </section>
      ${renderActivationCoreStage(flow, selected)}
      <section class="panel pad">
        <h2 class="panel-title">${escapeHtml(selected?.title || "Activation detail")}</h2>
        <div class="agent-meta">${pill(selectedState)}<span class="chip">${escapeHtml(selected?.blocking ? "blocking" : "guided")}</span></div>
        <p class="muted">${escapeHtml(selected?.complete_when || "Load backend contract to inspect activation.")}</p>
        ${renderActivationEvidence(selected?.id || "")}
        ${renderActivationDiagnostics(selected, selectedState)}
        ${renderActivationRepairCard(selected, selectedState, targetScreen)}
        ${renderActivationStepOperations(selected, selectedState, targetScreen)}
        <div class="grid">
          ${(selected?.read || []).map((path) => `<span class="status-pill">${escapeHtml(path)}</span>`).join("")}
        </div>
        ${renderActivationAction(selected)}
        <hr class="rule">
        ${renderReadinessBlockers()}
      </section>
    </div>`;
  el.body.querySelectorAll("[data-step]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedStep = button.dataset.step;
      persistUiState();
      renderActivation();
    });
  });
  document.getElementById("refresh-activation")?.addEventListener("click", refresh);
  document.getElementById("open-activation-target")?.addEventListener("click", async () => {
    if (!targetScreen) return;
    state.screen = targetScreen;
    persistUiState();
    render();
    await refreshScreenData();
  });
  document.getElementById("activation-run-action")?.addEventListener("click", () => runActivationStepAction(selected));
  bindActivationCoreInteractions();
}

function renderActivationCoreStage(flow, selected) {
  const steps = flow.length ? flow : [{ id: "loading", title: "Contract", complete_when: "Backend contract is loading." }];
  const selectedId = selected?.id || steps[0]?.id || "loading";
  const selectedState = selected ? inferStepState(selected) : "partial";
  const camera = activationCoreCameraState(selectedId);
  const ready = steps.filter((step) => inferStepState(step) === "ready").length;
  const blocked = steps.filter((step) => ["blocked", "missing_config", "failed", "error"].includes(inferStepState(step))).length;
  const review = steps.filter((step) => ["needs_review", "approval_required", "pending_review"].includes(inferStepState(step))).length;
  const summary = state.readiness?.runtime_readiness?.summary || "diagnostic startup";
  return `
    <section class="panel activation-core-stage" aria-label="bairui activation system core">
      <div class="activation-core-head">
        <div>
          <span class="section-label">bairui core</span>
          <strong>${escapeHtml(selected?.title || "Activation")}</strong>
        </div>
        ${pill(selectedState)}
      </div>
      <div class="activation-core-viewport" data-core-viewport style="--core-base-x: ${camera.x}; --core-base-y: ${camera.y}; --core-focus-z: ${camera.z};">
        <div class="activation-core-shell is-${escapeHtml(activationCoreStateClass(selectedState))}" data-core-shell>
          <div class="activation-core-ring ring-outer" aria-hidden="true"></div>
          <div class="activation-core-ring ring-inner" aria-hidden="true"></div>
          <div class="activation-core-grid" aria-hidden="true"></div>
          <div class="activation-core-brand">
            <strong>bairui</strong>
            <span>${escapeHtml(selectedState)}</span>
          </div>
          ${steps.map((step, index) => renderActivationCoreLayer(step, index, steps.length, selectedId)).join("")}
        </div>
      </div>
      <div class="activation-core-footer">
        <div><span>Ready</span><strong>${escapeHtml(String(ready))}</strong></div>
        <div><span>Review</span><strong>${escapeHtml(String(review))}</strong></div>
        <div><span>Blocked</span><strong>${escapeHtml(String(blocked))}</strong></div>
      </div>
      <p class="activation-core-summary">${escapeHtml(summary)}</p>
    </section>`;
}

function renderActivationCoreLayer(step, index, total, selectedId) {
  const status = step?.id === "loading" ? "partial" : inferStepState(step);
  const className = activationCoreStateClass(status);
  const angle = total ? Math.round((360 / total) * index - 90) : -90;
  const depth = index % 2 ? 42 : 70;
  const isActive = step.id === selectedId;
  const label = step.title || step.id || "Activation";
  return `
    <button
      class="activation-core-layer is-${escapeHtml(className)} ${isActive ? "active" : ""}"
      type="button"
      data-core-step="${escapeHtml(step.id || "")}"
      style="--layer-angle: ${angle}deg; --layer-depth: ${depth}px;"
      aria-label="${escapeHtml(`Select ${label}`)}"
      ${step.id === "loading" ? "disabled" : ""}
    >
      <span class="activation-core-node" aria-hidden="true"></span>
      <span class="activation-core-layer-copy">
        <strong>${escapeHtml(label)}</strong>
        <small>${escapeHtml(status)}</small>
      </span>
    </button>`;
}

function activationCoreStateClass(status) {
  if (["ready", "completed", "configured", "done"].includes(status)) return "ready";
  if (["blocked", "missing_config", "failed", "error"].includes(status)) return "blocked";
  if (["needs_review", "approval_required", "pending_review"].includes(status)) return "review";
  if (["loading", "checking", "running", "thinking"].includes(status)) return "checking";
  return "partial";
}

function activationCoreCameraState(stepId) {
  return (
    {
      brand_lock: { x: "0deg", y: "0deg", z: "24px" },
      runtime_health: { x: "4deg", y: "-12deg", z: "30px" },
      license_and_platform: { x: "-4deg", y: "18deg", z: "32px" },
      model_gateway: { x: "2deg", y: "34deg", z: "42px" },
      document_runtime: { x: "3deg", y: "-30deg", z: "38px" },
      memory_review: { x: "-12deg", y: "8deg", z: "52px" },
      reports_and_sources: { x: "-8deg", y: "-16deg", z: "36px" },
      channels: { x: "6deg", y: "28deg", z: "46px" },
      avatar: { x: "10deg", y: "-38deg", z: "50px" },
      codegraph: { x: "-10deg", y: "42deg", z: "48px" },
    }[stepId] || { x: "0deg", y: "0deg", z: "24px" }
  );
}

function bindActivationCoreInteractions() {
  const viewport = el.body.querySelector("[data-core-viewport]");
  if (!viewport) return;
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  el.body.querySelectorAll("[data-core-step]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!button.dataset.coreStep) return;
      state.selectedStep = button.dataset.coreStep;
      persistUiState();
      renderActivation();
    });
  });
  if (reduceMotion) return;
  viewport.addEventListener("pointermove", (event) => {
    const box = viewport.getBoundingClientRect();
    const x = ((event.clientX - box.left) / box.width - 0.5) * 10;
    const y = ((event.clientY - box.top) / box.height - 0.5) * -8;
    viewport.style.setProperty("--core-pointer-y", `${x.toFixed(2)}deg`);
    viewport.style.setProperty("--core-pointer-x", `${y.toFixed(2)}deg`);
  });
  viewport.addEventListener("pointerleave", () => {
    viewport.style.setProperty("--core-pointer-y", "0deg");
    viewport.style.setProperty("--core-pointer-x", "0deg");
  });
}

function inferStepState(step) {
  if (!state.readiness) return "partial";
  const capabilities = Object.fromEntries(state.capabilities.map((item) => [item.name, item.status]));
  const runtimeItems = Object.fromEntries((state.readiness.runtime_readiness?.items || []).map((item) => [item.name, item.status]));
  if (step?.id === "brand_lock") {
    return state.contract?.brand?.name === "bairui" && state.contract?.visibility_policy?.public_brand === "bairui" ? "ready" : "blocked";
  }
  if (step?.id === "model_gateway") return capabilities.model_gateway || "missing_config";
  if (step?.id === "document_runtime") return lookupStatus(runtimeItems, "document_parse") || lookupStatus(capabilities, "document_parse") || "missing_config";
  if (step?.blocking && state.readiness.runtime_readiness?.blockers?.length) return "blocked";
  if (step?.id === "memory_review") return (state.memoryQueue?.pending_count || 0) > 0 ? "needs_review" : "ready";
  if (step?.id === "reports_and_sources") return state.reports.length || state.sourceRefs.length ? "ready" : "partial";
  if (step?.id === "channels") return state.channels?.channels?.status || "missing_config";
  if (step?.id === "avatar") return state.avatarStatus?.avatar?.status || state.avatarManifest?.avatar_manifest?.engine?.status || "missing_config";
  if (step?.id === "codegraph") return runtimeItems.bairui_codegraph || state.codegraph?.codegraph?.status || "missing_config";
  return "ready";
}

function activationTargetScreen(stepId) {
  return (
    {
      runtime_health: "dashboard",
      license_and_platform: "settings",
      model_gateway: "settings",
      document_runtime: "documents",
      memory_review: "memory",
      reports_and_sources: "reports",
      channels: "channels",
      avatar: "avatar",
      codegraph: "codegraph",
      brand_lock: "dashboard",
    }[stepId] || ""
  );
}

function activationConfigTarget(stepId) {
  return (
    {
      license_and_platform: "license",
      model_gateway: "model_gateway",
      document_runtime: "document_output_dir",
      channels: "channel_targets",
      avatar: "avatar_assets",
      codegraph: "codegraph_root",
    }[stepId] || ""
  );
}

function activationRepairDetail(step, stepState, targetScreen) {
  const stepId = step?.id || "";
  const target = activationConfigTarget(stepId);
  const item = configStatusItem(target);
  const checklist = state.configStatus?.config_status?.checklist || {};
  const stepRepair = configChecklistStep(target);
  const command = (checklist.commands || [])[0] || "python -m src.hermes config-status";
  if (target === "model_gateway") {
    return {
      title: "Set model gateway env",
      target,
      status: item?.status || stepState || "missing_config",
      fix: "Set BAIRUI_MODEL_BASE_URL, BAIRUI_MODEL_API_KEY, and BAIRUI_MODEL_NAME, then run the probe.",
      verify: command,
    };
  }
  if (target === "channel_targets") {
    return {
      title: "Prepare owner-reviewed channel targets",
      target,
      status: item?.status || stepState || "missing_config",
      fix: "Set BAIRUI_CHANNEL_TARGETS_JSON only for approved targets. Activation still shows will_send=false.",
      verify: "python -m src.hermes channels diagnostics",
    };
  }
  if (target) {
    const path = item?.fields?.path || stepRepair?.detail || "";
    return {
      title: `Check ${target}`,
      target,
      status: item?.status || stepState || "partial",
      fix: path ? `Create or configure this path: ${path}` : stepRepair?.detail || "Refresh Settings and follow the generated deployment checklist.",
      verify: command,
    };
  }
  return {
    title: stepState === "ready" ? "Evidence is healthy" : "Continue guided setup",
    target: targetScreen || "workflow",
    status: stepState || "partial",
    fix: targetScreen ? `Open ${screens.find(([id]) => id === targetScreen)?.[1] || targetScreen} and complete the visible next action.` : "Refresh Activation and inspect runtime blockers.",
    verify: command,
  };
}

function renderActivationProgress(flow) {
  if (!flow.length) return "";
  const states = flow.map((step) => inferStepState(step));
  const ready = states.filter((status) => status === "ready").length;
  const needsReview = states.filter((status) => status === "needs_review").length;
  const blocked = states.filter((status) => ["blocked", "missing_config"].includes(status)).length;
  const percent = Math.round((ready / flow.length) * 100);
  return `
    <div class="activation-progress" aria-label="Activation progress">
      <div class="conversation-head">
        <div>
          <span class="section-label">Startup readiness</span>
          <strong>${escapeHtml(String(percent))}%</strong>
        </div>
        <div class="agent-meta">
          ${pill("ready", `${ready} ready`)}
          ${pill(needsReview ? "needs_review" : "ready", `${needsReview} review`)}
          ${pill(blocked ? "blocked" : "ready", `${blocked} blocked`)}
        </div>
      </div>
      <div class="activation-progress-track"><span style="width: ${Math.max(0, Math.min(100, percent))}%"></span></div>
    </div>`;
}

function renderActivationRepairCard(step, stepState, targetScreen) {
  if (!step) return "";
  const repair = activationRepairDetail(step, stepState, targetScreen);
  return `
    <div class="activation-repair-card">
      <div>
        <span>Repair</span>
        <strong>${escapeHtml(repair.title)}</strong>
        <p>${escapeHtml(repair.fix)}</p>
      </div>
      <div>
        <span>Mapped config</span>
        ${pill(repair.status || "partial")}
        <p>${escapeHtml(repair.target || "workflow")}</p>
      </div>
      <div>
        <span>Verify</span>
        <strong>${escapeHtml(repair.verify)}</strong>
        <p>Refresh Activation after the command reports ready or partial without required blockers.</p>
      </div>
    </div>`;
}

function lookupStatus(map, fragment) {
  const key = Object.keys(map || {}).find((name) => name.includes(fragment));
  return key ? map[key] : "";
}

function renderActivationEvidence(stepId) {
  const db = state.ready?.database || state.platform?.heartbeat?.database || {};
  const license = state.license?.license || {};
  const heartbeat = state.platform?.heartbeat || {};
  const model = state.capabilities.find((item) => item.name === "model_gateway") || {};
  const document = state.runtimeStatus.document?.document_parse || {};
  const memoryPending = state.memoryQueue?.pending_count || 0;
  const channelStatus = state.channels?.channels || {};
  const avatarStatus = state.avatarStatus?.avatar_state || state.avatarStatus?.avatar || {};
  const avatarEngine = state.avatarManifest?.avatar_manifest?.engine || {};
  const codegraphStatus = state.codegraph?.codegraph || state.runtimeStatus.codegraph?.codegraph || {};
  const reportsCount = state.reports.length;
  const sourcesCount = state.sourceRefs.length;
  const base = [
    ["Health", state.health?.status || "loading", state.health?.version || "service pending"],
    ["Database", db.status || "missing_config", db.error || db.detail || "PostgreSQL readiness"],
    ["License", license.status || state.ready?.license || "missing_config", license.error || license.license_id || license.path || "license file"],
    ["Platform", heartbeat.health_status || state.ready?.platform || "missing_config", heartbeat.server_id || state.ready?.server_id || "server id pending"],
  ];
  const extras = {
    runtime_health: [
      ["Runtime", state.readiness?.runtime_readiness?.status || "partial", state.readiness?.runtime_readiness?.summary || "runtime readiness pending"],
      ["Blockers", state.readiness?.runtime_readiness?.blockers?.length || 0, "required blockers visible before use"],
    ],
    license_and_platform: [
      ["Audit", state.audit.length ? "ready" : "partial", `${state.audit.length} audit events loaded`],
      ["Server", heartbeat.server_id || state.ready?.server_id || "missing_config", heartbeat.protocol_version || "heartbeat protocol pending"],
    ],
    model_gateway: [["Model Gateway", model.status || "missing_config", state.activationProbe?.detail || model.detail || "Run probe to verify /chat."]],
    document_runtime: [
      ["Document Parser", document.status || "missing_config", document.detail || "parser runtime status"],
      ["Workbench", state.documentSessions.length ? "ready" : "partial", `${state.documentSessions.length} ingest sessions loaded`],
    ],
    memory_review: [
      ["Pending Review", memoryPending ? "needs_review" : "ready", `${memoryPending} memory candidates need owner decision`],
      ["Reviews", state.memoryReviews.length ? "ready" : "partial", `${state.memoryReviews.length} review records loaded`],
    ],
    reports_and_sources: [
      ["Reports", reportsCount ? "ready" : "partial", `${reportsCount} report objects loaded`],
      ["Sources", sourcesCount ? "ready" : "partial", `${sourcesCount} source references loaded`],
    ],
    channels: [
      ["Channels", channelStatus.status || "missing_config", channelStatus.detail || "approval-bound outbound planning"],
      ["Approvals", state.channelApprovals.length ? "needs_review" : "ready", `${state.channelApprovals.length} approval records loaded; will_send=false`],
    ],
    avatar: [
      ["Avatar State", avatarStatus.state || avatarStatus.status || "idle", state.activationAction?.detail || "browser state layer"],
      ["Avatar Engine", avatarEngine.status || "missing_config", avatarEngine.package || "renderer package pending"],
    ],
    codegraph: [
      ["CodeGraph", codegraphStatus.status || "missing_config", codegraphStatus.memory_boundary || "source structure stays separate from memory"],
      ["Repositories", state.codegraphRepos.length ? "ready" : "partial", `${state.codegraphRepos.length} registered source repositories`],
    ],
  };
  return `
    <div class="activation-evidence">
      ${[...base, ...(extras[stepId] || [])]
        .map(
          ([label, status, detail]) => `
            <div class="evidence-card">
              <span>${escapeHtml(label)}</span>
              ${pill(status)}
              <p>${escapeHtml(detail)}</p>
            </div>`,
        )
        .join("")}
    </div>`;
}

function renderActivationDiagnostics(step, stepState) {
  if (!step) return "";
  const next = activationNextAction(step.id, stepState);
  const counts = {
    reads: (step.read || []).length,
    actions: step.action ? 1 : 0,
    blockers: state.readiness?.runtime_readiness?.blockers?.length || 0,
    warnings: state.readiness?.runtime_readiness?.warnings?.length || 0,
  };
  return `
    <div class="activation-diagnostics">
      ${renderCountStrip(counts)}
      <div class="activation-next">
        <span>Next</span>
        <strong>${escapeHtml(next.title)}</strong>
        <p>${escapeHtml(next.detail)}</p>
      </div>
    </div>`;
}

function renderActivationStepOperations(step, stepState, targetScreen) {
  if (!step) return "";
  const action = step.action || null;
  const safety = activationSafetyBoundary(step.id);
  const target = targetScreen ? screens.find(([id]) => id === targetScreen)?.[1] || targetScreen : "No linked workbench";
  return `
    <div class="activation-operations">
      <div class="operation-card">
        <span>Reads</span>
        <strong>${escapeHtml(String((step.read || []).length))} status endpoints</strong>
        <p>${escapeHtml((step.read || []).join(" | ") || "No read endpoint declared.")}</p>
      </div>
      <div class="operation-card">
        <span>Action</span>
        <strong>${escapeHtml(action ? `${action.method} ${action.path}` : "Open linked workbench")}</strong>
        <p>${escapeHtml(action?.id || `Continue in ${target}`)}</p>
      </div>
      <div class="operation-card">
        <span>Safety</span>
        <strong>${escapeHtml(safety.title)}</strong>
        <p>${escapeHtml(safety.detail)}</p>
      </div>
      <div class="operation-card">
        <span>State</span>
        <strong>${escapeHtml(stepState || "partial")}</strong>
        <p>${escapeHtml(targetScreen ? `Open ${target} for the next real operation.` : "This step is verified from backend evidence only.")}</p>
      </div>
    </div>`;
}

function activationSafetyBoundary(stepId) {
  const map = {
    brand_lock: ["bairui only", "Public UI, setup copy, and contract labels must expose only bairui."],
    runtime_health: ["diagnostic only", "Health and readiness checks do not execute external actions."],
    license_and_platform: ["no secret echo", "License and heartbeat status are shown without exposing secret values."],
    model_gateway: ["probe only", "The chat probe sends a minimal local readiness prompt and does not create resources."],
    document_runtime: ["candidate gated", "Document parsing may create review candidates, but memory writes still require owner approval."],
    memory_review: ["owner decision", "Long-term memory promotion requires explicit approve or reject decisions."],
    reports_and_sources: ["source traceable", "Reports must keep source references visible for audit and follow-up."],
    channels: ["will_send=false", "Channel actions create approval records only; no external send is performed here."],
    avatar: ["state only", "Avatar activation updates local browser state; Live2D assets are not generated here."],
    codegraph: ["memory separated", "CodeGraph indexes source structure and never auto-promotes code facts into memory."],
  };
  const [title, detail] = map[stepId] || ["governed", "This step uses backend contract evidence and keeps risky actions gated."];
  return { title, detail };
}

function renderActivationAction(step) {
  if (!step?.action) return "";
  const isProbe = step.action.id === "send_chat_probe";
  const isAvatarState = step.action.id === "set_avatar_state";
  const key = isProbe ? "activation-probe" : "activation-action";
  const loading = state.loading.has(key);
  const probe = state.activationProbe;
  const action = state.activationAction;
  const error = state.errors[key];
  const status = probe?.status || action?.status || (error ? "missing_config" : "ready");
  const buttonLabel = isProbe ? "Run Probe" : isAvatarState ? "Set Idle" : "";
  const busyLabel = isProbe ? "Probing" : "Running";
  return `
    <div class="activation-action-card">
      <div class="conversation-head">
        <div>
          <span>Action</span>
          <strong>${escapeHtml(step.action.method || "POST")} ${escapeHtml(step.action.path || "")}</strong>
          <p>${escapeHtml(step.action.id || "")}</p>
        </div>
        ${buttonLabel ? `<button class="primary-btn mini" id="activation-run-action" type="button" ${loading ? "disabled" : ""}>${loading ? busyLabel : buttonLabel}</button>` : ""}
      </div>
      ${
        (probe || action || error)
          ? `<div class="probe-result">${pill(status)}<p>${escapeHtml(probe?.detail || action?.detail || error)}</p></div>`
          : ""
      }
    </div>`;
}

async function runActivationStepAction(step) {
  if (step?.action?.id === "set_avatar_state") {
    await runActivationAvatarAction();
    return;
  }
  if (step?.action?.id !== "send_chat_probe") return;
  setBusy("activation-probe", true);
  state.errors["activation-probe"] = "";
  state.activationProbe = null;
  render();
  try {
    const result = await api.post("/chat", {
      system: "You are a bairui activation probe. Reply with a short readiness confirmation.",
      prompt: "Confirm bairui model gateway readiness in one short sentence.",
    });
    const chat = result?.chat || {};
    state.activationProbe = {
      status: chat.status || "completed",
      detail: [chat.provider, chat.model, chat.content || chat.error].filter(Boolean).join(" | "),
    };
    await refresh();
  } catch (error) {
    state.errors["activation-probe"] = error.message;
    state.activationProbe = { status: "missing_config", detail: error.message };
  } finally {
    setBusy("activation-probe", false);
    render();
  }
}

async function runActivationAvatarAction() {
  setBusy("activation-action", true);
  state.errors["activation-action"] = "";
  state.activationAction = null;
  render();
  try {
    const result = await api.post("/avatar/state", {
      state: "idle",
      text: "bairui activation check",
      audio_url: "",
      lip_sync: false,
    });
    const next = result?.avatar_state || {};
    state.activationAction = {
      status: next.status || "accepted",
      detail: `Avatar state accepted: ${next.state || "idle"}`,
    };
    state.avatarStatus = next.state ? { avatar_state: next, avatar: { status: next.state } } : state.avatarStatus;
    await refresh();
  } catch (error) {
    state.errors["activation-action"] = error.message;
    state.activationAction = { status: "missing_config", detail: error.message };
  } finally {
    setBusy("activation-action", false);
    render();
  }
}

function activationNextAction(stepId, stepState) {
  if (stepId === "model_gateway") {
    if (stepState === "ready") return { title: "Run gateway probe", detail: "Send a minimal /chat request and confirm the configured model answers." };
    return { title: "Configure model gateway", detail: "Set BAIRUI_MODEL_BASE_URL, BAIRUI_MODEL_API_KEY, and BAIRUI_MODEL_NAME, then run the probe." };
  }
  if (stepState === "blocked" || stepState === "missing_config") {
    return { title: "Fix missing configuration", detail: "Open the linked workbench and complete the visible missing_config items." };
  }
  if (stepId === "memory_review") return { title: "Review candidates", detail: "Approve or reject pending memory candidates before promoting long-term memory." };
  if (stepId === "channels") return { title: "Check approvals", detail: "Create or review outbound drafts; backend still records will_send=false." };
  if (stepId === "codegraph") return { title: "Register source", detail: "Register a source repository, scan it, then query source structure separately from memory." };
  if (stepId === "avatar") return { title: "Set avatar idle", detail: "Run the safe /avatar/state check here, then open Avatar for thinking/speaking states." };
  return { title: "Continue", detail: "This step is connected to real status endpoints. Open the linked screen to continue setup." };
}

function renderReadinessBlockers() {
  const blockers = state.readiness?.runtime_readiness?.blockers || [];
  const warnings = state.readiness?.runtime_readiness?.warnings || [];
  if (!blockers.length && !warnings.length) {
    return `<div class="empty-state">No blocking runtime issues detected. Continue with product checks.</div>`;
  }
  return `
    <div class="grid">
      ${blockers.map((item) => `<div class="panel pad mini-card">${pill("blocked", "blocked")} <p>${escapeHtml(item)}</p></div>`).join("")}
      ${warnings.map((item) => `<div class="panel pad mini-card">${pill("partial", "warning")} <p>${escapeHtml(item)}</p></div>`).join("")}
    </div>`;
}

function renderDashboard() {
  setScreenHead("Dashboard", "operational truth");
  el.actions.innerHTML = `
    <button class="primary-btn" id="seed-demo-data" type="button">Seed Demo</button>
    <button class="primary-btn" id="run-demo-flow" type="button">Run Demo Flow</button>
    <button class="ghost-btn" id="create-sample-job" type="button">Create Job</button>`;
  const demo = state.demoSeed?.demo_seed;
  const demoFlow = state.demoFlow?.demo_flow;
  el.body.innerHTML = `
    <div class="grid three">
      <section class="panel pad">
        <h2 class="panel-title">Readiness</h2>
        ${pill(state.readiness?.runtime_readiness?.status || "partial")}
        <p class="muted">${escapeHtml(state.readiness?.runtime_readiness?.summary || "Runtime readiness pending.")}</p>
        <div class="top-gap">${renderRuntimeDiagnostics()}</div>
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Platform</h2>
        ${pill(state.ready?.platform === "configured" ? "ready" : "missing_config", state.ready?.platform || "missing_config")}
        <p class="muted mono">${escapeHtml(state.ready?.server_id || "server pending")}</p>
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Capabilities</h2>
        <p class="metric">${state.capabilities.length}</p>
        <p class="muted">runtime surfaces detected</p>
      </section>
    </div>
    <section class="panel pad top-gap">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Demo walkthrough</h2>
          <p class="muted compact-copy">Seed safe records or run the real product closure flow across Command, Reports, Memory Review, Channels, and CodeGraph.</p>
        </div>
        ${pill(demoFlow?.status || demo?.status || "ready", demoFlow?.status || demo?.status || "not run")}
      </div>
      ${renderDemoSeedState(demo)}
      ${renderDemoFlowState(demoFlow)}
      ${renderProductError("demo-seed")}
      ${renderProductError("demo-flow")}
    </section>
    <div class="grid two top-gap">
      <section class="panel pad">
        <h2 class="panel-title">Jobs</h2>
        ${renderTable(["title", "route", "status"], state.jobs.map((job) => ({ title: job.title, route: job.route, status: job.status })))}
      </section>
      <section class="panel pad">
        <div class="conversation-head">
          <h2 class="panel-title">Recent audit</h2>
          <button class="ghost-btn mini" type="button" id="open-events-screen">Open Events</button>
        </div>
        ${renderAuditCards(state.audit.slice(-8).reverse())}
      </section>
    </div>
    ${state.selectedEntity?.type === "job" ? renderSelectedEntityPanel() : ""}`;
  bindEntityActions();
  bindAuditCards();
  document.getElementById("open-events-screen")?.addEventListener("click", async () => {
    state.screen = "events";
    persistUiState();
    await refreshScreenData();
  });
  document.getElementById("seed-demo-data")?.addEventListener("click", async () => {
    const result = await runAction("demo-seed", () => api.post("/demo/seed", { force: false }), refresh);
    state.demoSeed = result || state.demoSeed;
    if (result?.demo_seed?.status === "completed") {
      const job = result.demo_seed.job;
      state.selectedEntity = job ? { type: "job", title: job.title, status: job.status, ref: job.id, raw: job } : state.selectedEntity;
      persistUiState();
    }
    await refresh();
  });
  document.getElementById("run-demo-flow")?.addEventListener("click", async () => {
    const result = await runAction("demo-flow", () => api.post("/demo/flow", { force_seed: false }), refresh);
    state.demoFlow = result || state.demoFlow;
    if (result?.demo_flow?.reports?.latest) {
      const report = result.demo_flow.reports.latest;
      state.selectedEntity = { type: "report", title: report.title, status: report.status, ref: report.id, raw: report };
      persistUiState();
    }
    await refresh();
  });
  document.getElementById("create-sample-job")?.addEventListener("click", async () => {
    await runAction("job", () => api.post("/jobs", { title: "Frontend console check", prompt: "Inspect bairui dashboard state", route: "operations" }));
  });
}

function renderDemoFlowState(flow) {
  if (!flow) {
    return `<div class="empty-state top-gap">Run Demo Flow to verify the full product path with real backend contracts and safe approval gates.</div>`;
  }
  const checkpoints = flow.checkpoints || {};
  const counts = {
    checkpoints: Object.values(checkpoints).filter(Boolean).length,
    reports: flow.reports?.count || 0,
    channel_reviews: flow.channel?.review_count || 0,
    memory_reviews: flow.memory?.review_count || 0,
    code_results: flow.codegraph?.query?.results?.length || 0,
  };
  return `
    <div class="demo-flow-panel top-gap">
      <div class="conversation-head">
        <div>
          <h3 class="sub-title">Product closure flow</h3>
          <p class="muted compact-copy">Command -> report, memory review, channel approval, CodeGraph query, and audit marker.</p>
        </div>
        ${pill(flow.status || "partial")}
      </div>
      ${renderCountStrip(counts)}
      <div class="agent-meta top-gap">
        ${Object.entries(checkpoints)
          .map(([key, ok]) => pill(ok ? "ready" : "blocked", `${key}=${ok ? "true" : "false"}`))
          .join("")}
      </div>
      <div class="agent-meta top-gap">
        ${pill(flow.channel?.plan?.will_send === false ? "ready" : "blocked", "will_send=false")}
        ${pill(flow.memory?.will_write_long_term_memory === false ? "ready" : "blocked", "will_write_memory=false")}
        <span class="chip">contract-bound</span>
      </div>
    </div>`;
}

function renderDemoSeedState(demo) {
  const safety = demo?.audit_marker?.payload || {};
  const counts = demo?.status === "completed"
    ? {
        jobs: demo.job ? 1 : 0,
        reports: demo.report ? 1 : 0,
        memory_candidates: demo.memory_candidate ? 1 : 0,
        channel_drafts: demo.channel_approval ? 1 : 0,
      }
    : {
        jobs: state.jobs.length,
        reports: state.reports.length,
        memory_candidates: state.memoryCandidates.length,
        channel_drafts: state.channelApprovals.length,
      };
  return `
    ${renderCountStrip(counts)}
    <div class="agent-meta top-gap">
      ${pill(safety.will_send === false ? "ready" : "partial", "will_send=false")}
      ${pill(safety.will_write_long_term_memory === false ? "ready" : "partial", "will_write_memory=false")}
      <span class="chip">local data only</span>
      <span class="chip">owner review required</span>
    </div>
    <p class="muted compact-copy top-gap">${
      demo?.status === "skipped"
        ? "Demo data already exists. Existing review queues and reports remain available."
        : "The seed action writes local demo records only. Channel drafts and memory candidates still require explicit owner review."
    }</p>`;
}

function renderCommand() {
  setScreenHead("Command", "multi-agent workspace");
  const agents = state.agents.length ? state.agents : [];
  const session = state.agentSessions.find((item) => item.id === state.selectedAgentSessionId) || state.agentSessions.at(-1);
  if (session && !state.selectedAgentSessionId) state.selectedAgentSessionId = session.id;
  if (!state.selectedAgentIds.length) {
    state.selectedAgentIds = session?.agent_ids?.length ? [...session.agent_ids] : agents.map((agent) => agent.id);
  }
  const selectedCount = state.selectedAgentIds.length;
  el.actions.innerHTML = `
    <button class="ghost-btn" id="refresh-agents" type="button">Refresh</button>
    <button class="primary-btn" id="create-agent-session" type="button">New Session (${selectedCount})</button>
    <button class="ghost-btn" id="save-agent-title" type="button" ${!state.selectedAgentSessionId ? "disabled" : ""}>Save Title</button>
    <button class="ghost-btn" id="append-agent-message" type="button" ${!state.selectedAgentSessionId ? "disabled" : ""}>Append Message</button>
    <button class="ghost-btn" id="run-agent-round" type="button" ${!state.selectedAgentSessionId ? "disabled" : ""}>Run Round</button>`;
  el.body.innerHTML = `
    <div class="agent-layout">
      <section class="panel pad">
        <h2 class="panel-title">Agent roster</h2>
        <p class="muted compact-copy">Choose the agents that join the next session. Approval agents can draft review items only.</p>
        <div class="agent-roster">
          ${agents.map((agent) => renderAgentRow(agent)).join("") || `<div class="empty-state">No agent roster loaded yet.</div>`}
        </div>
        <div class="session-stack top-gap">
          <h3 class="section-label">Sessions</h3>
          ${
            state.agentSessions
              .slice(-5)
              .reverse()
              .map(
                (item) => `
                  <button class="session-item ${item.id === state.selectedAgentSessionId ? "active" : ""}" type="button" data-agent-session="${escapeHtml(item.id)}">
                    <span>${escapeHtml(item.title || "bairui command session")}</span>
                    <span class="chip mono">${escapeHtml(shortId(item.id))}</span>
                  </button>`,
              )
              .join("") || `<div class="empty-state">No sessions yet.</div>`
          }
        </div>
      </section>
      <section class="panel pad">
        <div class="conversation-head">
          <div>
            <h2 class="panel-title">Conversation ${session ? `<span class="chip mono">${escapeHtml(shortId(session.id))}</span>` : ""}</h2>
            <p class="muted compact-copy">${escapeHtml(session?.status || "no active session")} - ${escapeHtml(String(session?.agent_ids?.length || selectedCount || 0))} agents</p>
          </div>
          ${pill(state.errors["agent-round"] ? "blocked" : "ready", state.errors["agent-round"] ? "blocked" : "governed")}
        </div>
        ${renderAgentComposer(session, selectedCount)}
        <div class="command-session-tools">
          <input class="field" id="agent-session-title" placeholder="Session title" value="${escapeHtml(session?.title || "")}" ${!session ? "disabled" : ""} />
          <div class="pager-actions">
            <button class="ghost-btn mini" type="button" id="agent-events-prev" ${!state.agentEventsPage?.pagination?.previous_offset && state.agentEventsPage?.pagination?.previous_offset !== 0 ? "disabled" : ""}>Previous</button>
            <span class="chip mono">${escapeHtml(agentPageLabel())}</span>
            <button class="ghost-btn mini" type="button" id="agent-events-next" ${state.agentEventsPage?.pagination?.next_offset === null || state.agentEventsPage?.pagination?.next_offset === undefined ? "disabled" : ""}>Next</button>
          </div>
        </div>
        ${renderCommandResourceClosure()}
        ${renderProductError("agent-session")}
        ${renderProductError("agent-title")}
        ${renderProductError("agent-message")}
        ${renderProductError("agent-round")}
        ${renderProductError("agent-promote")}
        ${renderProductError("agent-retry")}
        <div class="conversation">
          ${
            state.agentEvents.length
              ? state.agentEvents.map((event) => renderMessage(event)).join("")
              : `<div class="empty-state">Create a session and run a round to record governed agent events.</div>`
          }
        </div>
        ${renderAgentPromotionLedger()}
      </section>
    </div>`;
  document.getElementById("refresh-agents")?.addEventListener("click", refreshScreenData);
  el.body.querySelectorAll("[data-agent-toggle]").forEach((input) => {
    input.addEventListener("change", () => {
      const next = new Set(state.selectedAgentIds);
      if (input.checked) next.add(input.dataset.agentToggle);
      else next.delete(input.dataset.agentToggle);
      state.selectedAgentIds = [...next];
      persistUiState();
      renderCommand();
    });
  });
  el.body.querySelectorAll("[data-agent-composer]").forEach((button) => {
    button.addEventListener("click", () => {
      state.agentComposerMode = button.dataset.agentComposer || "round";
      persistUiState();
      renderCommand();
    });
  });
  el.body.querySelectorAll("[data-agent-session]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedAgentSessionId = button.dataset.agentSession;
      state.agentEventOffset = 0;
      const selected = state.agentSessions.find((item) => item.id === state.selectedAgentSessionId);
      state.selectedAgentIds = selected?.agent_ids?.length ? [...selected.agent_ids] : state.selectedAgentIds;
      persistUiState();
      await loadAgents();
      render();
    });
  });
  el.body.querySelectorAll("[data-promote-event]").forEach((button) => {
    button.addEventListener("click", async () => {
      const eventId = button.dataset.promoteEvent;
      const target = button.dataset.promoteTarget;
      const result = await runAction("agent-promote", () => api.post(`/agents/session/${state.selectedAgentSessionId}/promote`, { event_id: eventId, target }));
      const promotion = result?.agent_promotion;
      if (promotion?.created_resource) {
        const list = state.promotionResults[eventId] || [];
        state.promotionResults[eventId] = [...list.filter((item) => item.target !== target), promotion];
      }
      await loadAgents();
      render();
    });
  });
  el.body.querySelectorAll("[data-retry-event]").forEach((button) => {
    button.addEventListener("click", async () => {
      await runAction("agent-retry", () => api.post(`/agents/session/${state.selectedAgentSessionId}/retry`, { event_id: button.dataset.retryEvent }), loadAgents);
      render();
    });
  });
  el.body.querySelectorAll("[data-open-promotion]").forEach((button) => {
    button.addEventListener("click", async () => {
      await openPromotionResource(button.dataset.openPromotion, button.dataset.resourceId);
    });
  });
  document.getElementById("save-agent-title")?.addEventListener("click", async () => {
    const title = document.getElementById("agent-session-title")?.value || "";
    await runAction("agent-title", () => api.post(`/agents/session/${state.selectedAgentSessionId}/title`, { title }), loadAgents);
    render();
  });
  document.getElementById("append-agent-message")?.addEventListener("click", async () => {
    const content = el.commandInput.value.trim();
    if (!content) {
      state.errors["agent-message"] = "message is required";
      render();
      return;
    }
    await submitAgentCommand(content, { mode: "message" });
  });
  document.getElementById("agent-events-prev")?.addEventListener("click", async () => {
    const previous = state.agentEventsPage?.pagination?.previous_offset;
    if (previous === null || previous === undefined) return;
    state.agentEventOffset = previous;
    await loadAgents();
    render();
  });
  document.getElementById("agent-events-next")?.addEventListener("click", async () => {
    const next = state.agentEventsPage?.pagination?.next_offset;
    if (next === null || next === undefined) return;
    state.agentEventOffset = next;
    await loadAgents();
    render();
  });
  document.getElementById("create-agent-session")?.addEventListener("click", async () => {
    const result = await runAction("agent-session", () =>
      api.post("/agents/session", {
        title: "bairui command session",
        agent_ids: state.selectedAgentIds.length ? state.selectedAgentIds : agents.map((agent) => agent.id),
      }),
    );
    state.selectedAgentSessionId = result?.agent_session?.id || state.selectedAgentSessionId;
    state.agentEventOffset = 0;
    state.selectedAgentIds = result?.agent_session?.agent_ids || state.selectedAgentIds;
    await loadAgents();
    render();
  });
  document.getElementById("run-agent-round")?.addEventListener("click", async () => {
    const promptText = el.commandInput.value.trim() || "Inspect current bairui workspace state.";
    await submitAgentCommand(promptText, { mode: "round" });
  });
}

function renderAgentComposer(session, selectedCount) {
  const mode = state.agentComposerMode || "round";
  const activeAgents = selectedAgentLabels(session).join(", ") || "selected agents";
  return `
    <section class="agent-composer-card" aria-label="Command composer">
      <div>
        <div class="section-label">Composer target</div>
        <div class="agent-meta">
          <span class="chip">${escapeHtml(activeAgents)}</span>
          <span class="chip">${escapeHtml(String(selectedCount || 0))} selected</span>
          <span class="chip">event source tracked</span>
        </div>
      </div>
      <div class="composer-toggle" role="group" aria-label="Command mode">
        <button class="ghost-btn mini ${mode === "message" ? "active" : ""}" type="button" data-agent-composer="message">Append Only</button>
        <button class="ghost-btn mini ${mode === "round" ? "active" : ""}" type="button" data-agent-composer="round">Run Round</button>
      </div>
      <div class="composer-safety">
        ${pill("ready", "no external send")}
        ${pill("ready", "no auto memory write")}
        ${pill(session ? "ready" : "partial", session ? "session ready" : "session will be created")}
      </div>
      <p class="muted compact-copy">Use the bottom command bar. Append Only records the owner message; Run Round records the owner message and calls the governed multi-agent backend.</p>
    </section>`;
}

function agentPageLabel() {
  const page = state.agentEventsPage?.pagination;
  if (!page) return "events 0";
  const start = page.total ? page.offset + 1 : 0;
  const end = Math.min(page.offset + page.limit, page.total);
  return `${start}-${end}/${page.total}`;
}

function agentName(agentId) {
  return state.agents.find((agent) => agent.id === agentId)?.display_name || agentId || "Agent";
}

function agentProfile(agentId) {
  return state.agents.find((agent) => agent.id === agentId) || {};
}

function selectedAgentLabels(session) {
  const ids = session?.agent_ids?.length ? session.agent_ids : state.selectedAgentIds;
  return ids.slice(0, 4).map((id) => agentName(id));
}

function renderAgentRow(agent) {
  const selected = state.selectedAgentIds.includes(agent.id);
  return `
    <label class="agent-row ${selected ? "selected" : ""}">
      <input class="agent-check" type="checkbox" data-agent-toggle="${escapeHtml(agent.id)}" ${selected ? "checked" : ""}>
      <div class="agent-avatar">${escapeHtml(agent.avatar_initials || agent.role.slice(0, 2))}</div>
      <div>
        <div class="agent-name">${escapeHtml(agent.display_name)}</div>
        <div class="agent-meta">
          <span class="chip">${escapeHtml(agent.role)}</span>
          <span class="chip">${escapeHtml(agent.model)}</span>
          <span class="chip">${escapeHtml(agent.permission)}</span>
          ${pill(agent.status)}
        </div>
      </div>
    </label>`;
}

function renderMessage(event) {
  const profile = agentProfile(event.agent_id);
  const role = event.role || profile.role || event.agent_id || "agent";
  const content = event.content || event.error || "";
  const actionable = event.agent_id !== "owner" && !["missing_config", "failed", "blocked"].includes(event.status || "");
  const retryable = ["failed", "missing_config", "blocked"].includes(event.status || "");
  return `
    <article class="message">
      <div class="agent-avatar">${escapeHtml(profile.avatar_initials || role.slice(0, 2))}</div>
      <div class="message-body">
        <div class="message-titleline">
          <div class="agent-name">${escapeHtml(agentName(event.agent_id))}</div>
          <span class="chip mono">${escapeHtml(shortId(event.id))}</span>
        </div>
        <div class="agent-meta">
          <span class="chip">${escapeHtml(role)}</span>
          <span class="chip">${escapeHtml(event.model || profile.model || "")}</span>
          <span class="chip">${escapeHtml(event.permission || profile.permission || "")}</span>
          ${pill(event.status)}
        </div>
        <p>${escapeHtml(content)}</p>
        ${
          actionable
            ? `<div class="message-actions">${renderPromotionAction(event, "job", "Task")}${renderPromotionAction(event, "report", "Report")}${renderPromotionAction(event, "memory_review", "Memory Review")}${renderPromotionAction(event, "channel_draft", "Channel Draft")}</div>`
            : ""
        }
        ${
          retryable
            ? `<div class="message-actions">
                <button class="ghost-btn mini" type="button" data-retry-event="${escapeHtml(event.id)}">Retry</button>
              </div>`
            : ""
        }
        ${renderPromotionResults(event.id)}
      </div>
    </article>`;
}

function renderPromotionAction(event, target, label) {
  const promotion = promotionForEventTarget(event.id, target);
  const resource = promotion?.created_resource || {};
  if (resource.id) {
    const viewLabel = promotionNextAction(promotion).button;
    return `<button class="ghost-btn mini is-linked" type="button" data-open-promotion="${escapeHtml(resource.type)}" data-resource-id="${escapeHtml(resource.id)}">${escapeHtml(viewLabel)}</button>`;
  }
  return `<button class="ghost-btn mini" type="button" data-promote-event="${escapeHtml(event.id)}" data-promote-target="${escapeHtml(target)}">${escapeHtml(label)}</button>`;
}

function promotionResourceSummary(promotion) {
  const resource = promotion?.created_resource || {};
  const type = resource.type || promotion?.resource_type || "resource";
  const label =
    {
      job: "Task",
      report: "Report",
      document_memory_candidate: "Memory candidate",
      channel_approval_request: "Channel draft",
    }[type] || type;
  const reviewRequired = resource.review_required || promotion?.review_required;
  const screen = promotionScreenFor(type);
  return {
    label,
    type,
    screen,
    status: resource.status || promotion?.resource_status || promotion?.status || "planned",
    resource_id: resource.id || promotion?.resource_id || "",
    review_required: Boolean(reviewRequired),
    safety: reviewRequired ? "owner review required" : "no external action",
    source_ref: resource.source?.source_ref || promotion?.source?.source_ref || promotion?.event_id || "",
    promotion_id: promotion?.promotion_id || promotion?.id || "",
    duplicate: Boolean(promotion?.duplicate),
  };
}

function promotionNextAction(promotion) {
  const summary = promotionResourceSummary(promotion);
  if (summary.type === "job") return { button: "Open Dashboard", detail: "Task is local and traceable from Dashboard." };
  if (summary.type === "report") return { button: "Open Reports", detail: "Report draft is ready for review with source reference." };
  if (summary.type === "document_memory_candidate") return { button: "Open Review Queue", detail: "Owner must approve or reject before long-term memory write." };
  if (summary.type === "channel_approval_request") return { button: "Open Channels", detail: "Owner must review the draft; will_send=false." };
  return { button: "Open Entity", detail: "Open the entity detail card and inspect source trace." };
}

function promotionForEventTarget(eventId, target) {
  const transient = state.promotionResults[eventId] || [];
  const persisted = state.agentPromotions.filter((promotion) => promotion.event_id === eventId && promotion.target === target).map(normalizeAgentPromotion);
  return [...transient, ...persisted].at(-1) || null;
}

function renderPromotionResults(eventId) {
  const persisted = state.agentPromotions.filter((promotion) => promotion.event_id === eventId).map(normalizeAgentPromotion);
  const byTarget = new Map();
  [...persisted, ...(state.promotionResults[eventId] || [])].forEach((promotion) => byTarget.set(promotion.target, promotion));
  const results = [...byTarget.values()];
  if (!results.length) return "";
  return `
    <div class="promotion-results">
      ${results
        .map((promotion) => {
          const resource = promotion.created_resource || {};
          const summary = promotionResourceSummary(promotion);
          const next = promotionNextAction(promotion);
          return `
            <div class="promotion-result">
              <div class="promotion-result-main">
                <div class="promotion-result-head">
                  ${pill(summary.status)}
                  <strong>${escapeHtml(summary.label)}</strong>
                  <span class="chip">${escapeHtml(promotion.duplicate ? "reused" : "created")}</span>
                  <span class="chip">${escapeHtml(summary.safety)}</span>
                </div>
                <p>${escapeHtml(next.detail)}</p>
                <div class="promotion-result-meta">
                  <span class="chip mono">resource ${escapeHtml(shortId(summary.resource_id))}</span>
                  <span class="chip mono">src ${escapeHtml(shortId(summary.source_ref))}</span>
                  <span class="chip mono">promotion ${escapeHtml(shortId(summary.promotion_id))}</span>
                  <span class="chip">screen ${escapeHtml(summary.screen)}</span>
                </div>
              </div>
              <button class="ghost-btn mini" type="button" data-open-promotion="${escapeHtml(resource.type)}" data-resource-id="${escapeHtml(resource.id)}">${escapeHtml(next.button)}</button>
            </div>`;
        })
        .join("")}
    </div>`;
}

function renderAgentPromotionLedger() {
  const rows = allPromotionRecords().slice(-8).reverse();
  if (!rows.length) {
    return `<section class="promotion-ledger top-gap"><div class="empty-state compact">Promotion ledger is empty. Promote an agent event to create a traceable resource.</div></section>`;
  }
  return `
    <section class="promotion-ledger top-gap">
      <div class="conversation-head">
        <div>
          <h3 class="sub-title">Promotion ledger</h3>
          <p class="muted compact-copy">Agent event to resource trace. Memory and channel outputs still require owner review.</p>
        </div>
        <span class="chip mono">${escapeHtml(rows.length)} tracked</span>
      </div>
      <div class="promotion-ledger-list">
        ${rows
          .map((promotion) => {
            const resource = promotion.created_resource || {};
            const source = resource.source || promotion.source || {};
            const summary = promotionResourceSummary(promotion);
            const next = promotionNextAction(promotion);
            return `
              <div class="promotion-ledger-row">
                <div class="promotion-ledger-main">
                  <div class="agent-meta">
                    ${pill(summary.status)}
                    <span class="chip">${escapeHtml(summary.label)}</span>
                    <span class="chip">${escapeHtml(promotion.target || source.target || "")}</span>
                    <span class="chip">${escapeHtml(summary.safety)}</span>
                    <span class="chip">${escapeHtml(summary.duplicate ? "reused" : "created")}</span>
                    <span class="chip mono">event ${escapeHtml(shortId(summary.source_ref))}</span>
                    <span class="chip mono">promotion ${escapeHtml(shortId(summary.promotion_id))}</span>
                  </div>
                  <strong>${escapeHtml(summary.label)} ${escapeHtml(shortId(summary.resource_id))}</strong>
                  <p>${escapeHtml(next.detail)} ${escapeHtml(promotion.detail || "Promotion recorded for owner review.")}</p>
                </div>
                <button class="ghost-btn mini" type="button" data-open-promotion="${escapeHtml(resource.type || promotion.resource_type || "")}" data-resource-id="${escapeHtml(resource.id || promotion.resource_id || "")}">${escapeHtml(next.button)}</button>
              </div>`;
          })
          .join("")}
      </div>
    </section>`;
}

function renderCommandResourceClosure() {
  const rows = allPromotionRecords();
  const counts = {
    resources: rows.length,
    jobs: rows.filter((item) => item.created_resource?.type === "job").length,
    reports: rows.filter((item) => item.created_resource?.type === "report").length,
    reviews: rows.filter((item) => item.created_resource?.review_required).length,
    reused: rows.filter((item) => item.duplicate).length,
  };
  return `
    <section class="command-resource-closure">
      <div class="conversation-head">
        <div>
          <h3 class="sub-title">Resource closure</h3>
          <p class="muted compact-copy">Every promoted agent event keeps event_id + target idempotency, source_ref, promotion_id, and owner review status visible.</p>
        </div>
        ${pill(rows.length ? "ready" : "partial", rows.length ? "traceable" : "no resources")}
      </div>
      ${renderCountStrip(counts)}
      <div class="promotion-trace-strip">
        <span class="chip">idempotency=event_id+target</span>
        <span class="chip">will_execute_external_action=false</span>
        <span class="chip">memory/channel require owner review</span>
      </div>
    </section>`;
}

function normalizeAgentPromotion(promotion) {
  return {
    target: promotion.target,
    status: promotion.status || "planned",
    detail: promotion.detail || "Promotion recorded for owner review.",
    duplicate: Boolean(promotion.duplicate),
    promotion_id: promotion.promotion_id || promotion.id || "",
    will_execute_external_action: promotion.will_execute_external_action === true,
    created_resource: promotion.created_resource || {
      type: promotion.resource_type,
      id: promotion.resource_id,
      status: promotion.resource_status,
      review_required: promotion.review_required,
      source: promotion.source || {},
    },
  };
}

function allPromotionRecords() {
  const byResource = new Map();
  const persisted = state.agentPromotions.map(normalizeAgentPromotion);
  const transient = Object.values(state.promotionResults).flat().map(normalizeAgentPromotion);
  [...persisted, ...transient].forEach((promotion) => {
    const resource = promotion.created_resource || {};
    const key = `${resource.type || ""}:${resource.id || ""}:${promotion.target || ""}`;
    if (resource.id) byResource.set(key, promotion);
  });
  return [...byResource.values()];
}

async function openPromotionResource(resourceType, resourceId) {
  const target = promotionScreenFor(resourceType);
  if (target === "dashboard") await loadDashboard();
  if (target === "reports") await loadReports();
  if (target === "memory") await loadMemory();
  if (target === "channels") await loadChannels();
  const entity = findResourceEntity(resourceType, resourceId);
  const promotion = allPromotionRecords().find((item) => String(item.created_resource?.id || "") === String(resourceId));
  state.selectedEntity = enrichPromotionEntity(
    entity || {
      type: entityTypeForResource(resourceType),
      title: resourceType,
      status: promotion?.created_resource?.status || "created",
      ref: resourceId,
      raw: { id: resourceId },
    },
    promotion,
  );
  state.screen = target;
  persistUiState();
  render();
}

function promotionScreenFor(resourceType) {
  return (
    {
      job: "dashboard",
      report: "reports",
      document_memory_candidate: "memory",
      channel_approval_request: "channels",
    }[resourceType] || "entity"
  );
}

function findResourceEntity(resourceType, resourceId) {
  const collections = {
    job: state.jobs.map((item) => ({ type: "job", title: item.title, status: item.status, ref: item.id, raw: item })),
    report: state.reports.map((item) => ({ type: "report", title: item.title, status: item.status, ref: item.id || item.path, raw: item })),
    document_memory_candidate: state.memoryCandidates.map((item) => ({ type: "memory", title: item.candidate_type, status: item.status, ref: item.id, raw: item })),
    channel_approval_request: state.channelApprovals.map((item) => ({ type: "channel", title: item.media_kind, status: item.review_status || item.status, ref: item.id, raw: item })),
  };
  return (collections[resourceType] || []).find((item) => String(item.ref) === String(resourceId) || String(item.raw?.id) === String(resourceId));
}

function entityTypeForResource(resourceType) {
  return (
    {
      document_memory_candidate: "memory",
      channel_approval_request: "channel",
    }[resourceType] || resourceType
  );
}

function enrichPromotionEntity(entity, promotion) {
  if (!promotion?.created_resource) return entity;
  const source = promotion.created_resource.source || {};
  return {
    ...entity,
    status: entity.status || promotion.created_resource.status || promotion.status,
    ref: entity.ref || promotion.created_resource.id,
    raw: {
      ...(entity.raw || {}),
      source: entity.raw?.source || source,
      promotion_id: entity.raw?.promotion_id || promotion.promotion_id || "",
      promotion_status: promotion.status || "",
      promotion_duplicate: Boolean(promotion.duplicate),
      will_execute_external_action: promotion.will_execute_external_action === true,
    },
  };
}

function renderDocuments() {
  setScreenHead("Documents", "ingest workbench");
  const selected = state.documentSession;
  el.actions.innerHTML = `
    <button class="ghost-btn" id="refresh-documents" type="button">Refresh</button>
    <button class="primary-btn" id="create-document-plan" type="button">Create Plan</button>
    <button class="primary-btn" id="run-next-document" type="button" ${!state.selectedIngestId ? "disabled" : ""}>Run Next</button>
    <button class="ghost-btn" id="run-until-blocked" type="button" ${!state.selectedIngestId ? "disabled" : ""}>Run Until Blocked</button>
    <button class="ghost-btn" id="open-document-memory" type="button" ${!selected?.review_queue?.pending_count ? "disabled" : ""}>Review Memory</button>`;
  el.body.innerHTML = `
    <div class="documents-layout">
      <section class="panel pad">
        <h2 class="panel-title">Create ingest</h2>
        <div class="document-plan-form">
          <label class="form-label">Document path</label>
          <input class="field" id="doc-input-path" placeholder="C:\\path\\to\\file.pdf" value="${escapeHtml(state.documentPlanDraft.input_path)}" />
          <label class="form-label">Title</label>
          <input class="field" id="doc-title" placeholder="bairui knowledge brief" value="${escapeHtml(state.documentPlanDraft.title)}" />
          <div class="form-grid two-cols">
            <label>
              <span class="form-label">Backend</span>
              <select class="field" id="doc-backend">
                ${["", "pipeline", "vlm-transformers", "hybrid-http-client"].map((value) => `<option value="${escapeHtml(value)}" ${state.documentPlanDraft.backend === value ? "selected" : ""}>${escapeHtml(value || "auto")}</option>`).join("")}
              </select>
            </label>
            <label>
              <span class="form-label">Device</span>
              <select class="field" id="doc-device">
                ${["cpu", "cuda"].map((value) => `<option value="${escapeHtml(value)}" ${state.documentPlanDraft.device === value ? "selected" : ""}>${escapeHtml(value)}</option>`).join("")}
              </select>
            </label>
          </div>
          <div class="form-grid two-cols">
            <label>
              <span class="form-label">Language</span>
              <input class="field" id="doc-language" placeholder="zh / en / auto" value="${escapeHtml(state.documentPlanDraft.language)}" />
            </label>
            <label>
              <span class="form-label">Output directory</span>
              <input class="field" id="doc-output-dir" placeholder="optional" value="${escapeHtml(state.documentPlanDraft.output_dir)}" />
            </label>
          </div>
          <p class="muted compact-copy">Creates a local ingest plan only. Parsing and memory writes still require explicit workflow and review steps.</p>
          ${renderProductError("documents")}
          ${renderProductError("doc-plan")}
          ${renderProductError("doc-next")}
          ${renderProductError("doc-run")}
          ${renderProductError("doc-command")}
          ${renderProductError("doc-source-refs")}
          ${renderProductError("doc-ingest-report")}
        </div>
        <hr class="rule" />
        <h2 class="panel-title">Ingest sessions</h2>
        <div class="step-list">
          ${state.documentSessions
            .map(
              (session) => `
                <button class="step-item ${state.selectedIngestId === session.ingest_id ? "active" : ""}" type="button" data-ingest="${escapeHtml(session.ingest_id)}">
                  <div class="step-title">
                    <span>${escapeHtml(session.title)}</span>
                    ${pill(session.current_stage || session.status)}
                  </div>
                  <div class="step-copy mono">${escapeHtml(shortId(session.ingest_id))} - ${escapeHtml(session.progress_percent)}%</div>
                  ${progressBar(session.progress_percent)}
                </button>`,
            )
            .join("") || `<div class="empty-state">No ingest sessions yet. Create an ingest plan from the API or CLI, then refresh.</div>`}
        </div>
      </section>
      <section class="panel pad document-pipeline-panel">
        <h2 class="panel-title">${escapeHtml(selected?.title || "Pipeline")}</h2>
        ${
          selected
            ? `
          <div class="pipeline-grid">
            ${(selected.stages || []).map((stage) => stageCard(stage.label, stage.status)).join("")}
          </div>
          <div class="top-gap">${renderWarnings(selected.blockers, selected.warnings)}</div>
          <h3 class="sub-title">Next actions</h3>
          ${renderActionList(selected.workbench?.next_actions || (selected.primary_action ? [selected.primary_action] : []))}
          ${renderDocumentActionResult()}
          <div class="action-row top-gap">
            <button class="ghost-btn" type="button" data-document-action="source-refs">Generate Source Refs</button>
            <button class="ghost-btn" type="button" data-document-action="ingest-report">Generate Report</button>
            <button class="ghost-btn" type="button" data-document-action="open-reports">Open Reports</button>
            <button class="ghost-btn" type="button" data-document-action="open-memory" ${!selected.review_queue?.pending_count ? "disabled" : ""}>Open Review Queue</button>
          </div>
        `
            : `<div class="empty-state">Select a session to inspect pipeline state, blockers, review queue, and report readiness.</div>`
        }
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Session evidence</h2>
        ${
          selected
            ? `
          ${renderCountStrip(selected.counts || {})}
          ${renderDocumentResourceRoutes(selected)}
          <h3 class="sub-title">Latest report</h3>
          ${
            selected.report
              ? `<button class="object-card button-card" type="button" data-document-report="${escapeHtml(selected.report.id || selected.report.path || "")}">
                  ${renderObjectCardInner(selected.report, ["title", "status", "path"])}
                </button>`
              : `<div class="empty-state">No report generated yet. Generate source refs first, then create a report.</div>`
          }
          <h3 class="sub-title">Review queue</h3>
          <div class="review-route">
            ${selected.review_queue?.pending_count ? pill("needs_review", `${selected.review_queue.pending_count} pending`) : pill("ready", "no pending review")}
            <button class="ghost-btn mini" type="button" data-document-action="open-memory" ${!selected.review_queue?.pending_count ? "disabled" : ""}>Review</button>
          </div>
        `
            : `<div class="empty-state">Session details appear here after selection.</div>`
        }
      </section>
    </div>`;
  el.body.querySelectorAll("[data-ingest]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedIngestId = button.dataset.ingest;
      persistUiState();
      await loadDocumentSession();
      renderDocuments();
    });
  });
  document.getElementById("refresh-documents")?.addEventListener("click", refreshScreenData);
  document.getElementById("create-document-plan")?.addEventListener("click", createDocumentPlan);
  document.getElementById("run-next-document")?.addEventListener("click", () => runDocumentStep("/document/parse/workbench-next", "doc-next"));
  document.getElementById("run-until-blocked")?.addEventListener("click", () => runDocumentStep("/document/parse/workbench-run-until-blocked", "doc-run"));
  document.getElementById("open-document-memory")?.addEventListener("click", openDocumentMemoryReview);
  el.body.querySelectorAll("[data-document-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      await runDocumentAction(button.dataset.documentAction);
    });
  });
  el.body.querySelectorAll("[data-document-command]").forEach((button) => {
    button.addEventListener("click", async () => {
      await runDocumentCommand(button.dataset.documentCommand);
    });
  });
  el.body.querySelectorAll("[data-document-report]").forEach((button) => {
    button.addEventListener("click", async () => {
      await loadReports();
      const reportId = button.dataset.documentReport;
      state.selectedEntity =
        state.reports
          .map((item) => ({ type: "report", title: item.title, status: item.status, ref: item.id || item.path, raw: item }))
          .find((item) => String(item.ref) === String(reportId) || String(item.raw?.path) === String(reportId)) || state.selectedEntity;
      state.screen = "reports";
      persistUiState();
      render();
    });
  });
}

async function runDocumentStep(path, key) {
  if (!state.selectedIngestId) return;
  const result = await runAction(key, () => api.post(path, { ingest_id: state.selectedIngestId, max_steps: 10 }), refreshScreenData);
  state.documentActionResult = documentActionSummary(result, path);
  const status = result?.document_workbench_step?.status || result?.document_workbench_run?.status || "";
  if (status === "needs_review") await openDocumentMemoryReview();
}

async function createDocumentPlan() {
  const draft = readDocumentPlanDraft();
  state.documentPlanDraft = draft;
  if (!draft.input_path.trim()) {
    state.errors.documents = "Document path is required.";
    renderDocuments();
    return;
  }
  state.errors.documents = "";
  const result = await runAction("doc-plan", () => api.post("/document/parse/ingest-plan", draft), refreshScreenData);
  state.documentActionResult = documentActionSummary(result, "/document/parse/ingest-plan");
  state.selectedIngestId = result?.document_ingest?.id || state.selectedIngestId;
  persistUiState();
  state.documentPlanDraft = { input_path: "", title: "", output_dir: "", backend: "", language: "", device: "cpu" };
  await refreshScreenData();
}

function readDocumentPlanDraft() {
  return {
    input_path: document.getElementById("doc-input-path")?.value || "",
    title: document.getElementById("doc-title")?.value || "",
    output_dir: document.getElementById("doc-output-dir")?.value || "",
    backend: document.getElementById("doc-backend")?.value || "",
    language: document.getElementById("doc-language")?.value || "",
    device: document.getElementById("doc-device")?.value || "cpu",
  };
}

async function runDocumentAction(action) {
  if (action === "open-memory") {
    await openDocumentMemoryReview();
    return;
  }
  if (action === "open-reports") {
    state.screen = "reports";
    persistUiState();
    await refreshScreenData();
    return;
  }
  if (action === "open-source-refs") {
    await openDocumentSourceRefs();
    return;
  }
  if (!state.selectedIngestId) return;
  if (action === "source-refs") {
    const result = await runAction("doc-source-refs", () => api.post("/document/parse/source-refs", { ingest_id: state.selectedIngestId }), refreshScreenData);
    state.documentActionResult = documentActionSummary(result, "/document/parse/source-refs");
    return;
  }
  if (action === "ingest-report") {
    const result = await runAction("doc-ingest-report", () => api.post("/document/parse/ingest-report", { ingest_id: state.selectedIngestId }), refreshScreenData);
    state.documentActionResult = documentActionSummary(result, "/document/parse/ingest-report");
  }
}

async function runDocumentCommand(command) {
  if (!command || !state.selectedIngestId) return;
  if (command === "review-memory-candidate") {
    await openDocumentMemoryReview();
    return;
  }
  if (command === "done") {
    state.screen = "reports";
    persistUiState();
    await refreshScreenData();
    return;
  }
  const path = documentCommandPath(command);
  if (!path) return;
  const result = await runAction("doc-command", () => api.post(path, documentCommandPayload(command)), refreshScreenData);
  state.documentActionResult = documentActionSummary(result, path);
  const status = result?.document_workbench_step?.status || result?.document_workbench_run?.status || result?.document_memory_candidate_generation?.status || "";
  if (status === "needs_review") await openDocumentMemoryReview();
}

function documentCommandPath(command) {
  return (
    {
      "run-ingest": "/document/parse/run-ingest",
      "register-artifacts": "/document/parse/register-artifacts",
      "index-artifacts": "/document/parse/index-artifacts",
      "memory-candidates": "/document/parse/memory-candidates",
      "source-refs": "/document/parse/source-refs",
      "ingest-report": "/document/parse/ingest-report",
    }[command] || ""
  );
}

function documentCommandPayload(command) {
  const payload = { ingest_id: state.selectedIngestId };
  if (command === "index-artifacts") Object.assign(payload, { collection: "bairui", bucket: "documents" });
  if (command === "memory-candidates") Object.assign(payload, { max_candidates: 20 });
  return payload;
}

function documentActionSummary(result, path) {
  if (!result) return null;
  const payload =
    result.document_workbench_step ||
    result.document_workbench_run ||
    result.document_ingest ||
    result.document_pipeline ||
    result.document_artifact_registration ||
    result.document_index ||
    result.document_memory_candidate_generation ||
    result.document_source_refs ||
    result.document_ingest_report ||
    {};
  return {
    path,
    status: payload.status || "completed",
    detail: payload.detail || payload.title || "Document action completed.",
  };
}

function renderDocumentActionResult() {
  const result = state.documentActionResult;
  if (!result) return "";
  return `
    <div class="document-action-result">
      <div>
        ${pill(result.status || "completed")}
        <span class="chip mono">${escapeHtml(result.path || "")}</span>
      </div>
      <p>${escapeHtml(result.detail || "Document action completed.")}</p>
    </div>`;
}

async function openDocumentMemoryReview() {
  state.screen = "memory";
  persistUiState();
  await refreshScreenData();
}

async function openDocumentSourceRefs() {
  await loadReports();
  const source = state.sourceRefs.find((item) => item.metadata?.ingest_id === state.selectedIngestId);
  if (source) {
    state.selectedEntity = {
      type: "source",
      title: source.title,
      status: source.confidence,
      ref: source.source_ref || source.id,
      raw: source,
    };
  }
  state.screen = "reports";
  persistUiState();
  render();
}

function renderDocumentResourceRoutes(session) {
  const counts = session.counts || {};
  const pending = session.review_queue?.pending_count || 0;
  const hasReport = Boolean(session.report);
  const hasSources = Number(counts.source_refs || 0) > 0;
  return `
    <div class="document-routes">
      <button class="document-route" type="button" data-document-action="open-memory" ${!pending ? "disabled" : ""}>
        <span>Memory review</span>
        ${pill(pending ? "needs_review" : "ready", pending ? `${pending} pending` : "clear")}
      </button>
      <button class="document-route" type="button" data-document-action="open-reports" ${!hasReport ? "disabled" : ""}>
        <span>Report</span>
        ${pill(hasReport ? "ready" : "partial", hasReport ? "available" : "not generated")}
      </button>
      <button class="document-route" type="button" data-document-action="open-source-refs" ${!hasSources ? "disabled" : ""}>
        <span>Source refs</span>
        ${pill(hasSources ? "ready" : "partial", `${counts.source_refs || 0} refs`)}
      </button>
    </div>`;
}

function renderMemory() {
  setScreenHead("Memory Review", "owner-governed memory");
  const queue = state.memoryQueue;
  const pending = queue?.candidates || [];
  const reviewRows = state.memoryReviews.slice(-12).reverse().map((review) => ({
    candidate_id: review.candidate_id,
    decision: review.decision,
    status: review.status,
    memory_status: review["ever" + "os_status"],
  }));
  el.actions.innerHTML = `
    <button class="ghost-btn" id="refresh-memory" type="button">Refresh</button>
    <button class="ghost-btn" id="export-memory" type="button">Export Memory</button>
    <button class="ghost-btn" id="batch-reject-memory" type="button" ${!pending.length ? "disabled" : ""}>Reject Pending</button>`;
  el.body.innerHTML = `
    <div class="grid two">
      <section class="panel pad">
        <h2 class="panel-title">Pending queue</h2>
        ${renderMemoryQueueSummary(queue, pending)}
        ${renderMemoryReviewResult()}
        ${renderProductError("memory-batch")}
        ${pending.length ? pending.map(renderMemoryCandidate).join("") : `<div class="empty-state">No pending candidates. Recent reviewed items stay visible on the right.</div>`}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Review history</h2>
        ${renderTable(["candidate_id", "decision", "status", "memory_status"], reviewRows)}
      </section>
    </div>
    <div class="grid two top-gap">
      <section class="panel pad">
        <h2 class="panel-title">All candidates</h2>
        ${renderTable(["id", "status", "candidate_type", "confidence"], state.memoryCandidates.slice(-10).reverse().map((item) => ({ ...item, id: shortId(item.id) })))}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Safety boundary</h2>
        ${renderMemorySafetyPanel()}
      </section>
    </div>
    ${state.selectedEntity?.type === "memory" ? renderSelectedEntityPanel() : ""}`;
  bindEntityActions();
  document.getElementById("refresh-memory")?.addEventListener("click", refreshScreenData);
  document.getElementById("export-memory")?.addEventListener("click", exportMemoryData);
  document.getElementById("batch-reject-memory")?.addEventListener("click", async () => {
    const candidateIds = pending.map((candidate) => candidate.id);
    const result = await runAction("memory-batch", () =>
      api.post("/document/parse/memory-review-batch", {
        candidate_ids: candidateIds,
        decision: "reject",
        reviewer_ref: "owner",
        note: "Rejected from bairui console batch action.",
      }),
    );
    state.memoryReviewResult = result?.document_memory_review_batch || null;
    await loadMemory();
    render();
  });
  el.body.querySelectorAll("[data-review]").forEach((button) => {
    button.addEventListener("click", async () => {
      const result = await runAction(`review-${button.dataset.candidate}`, () =>
        api.post("/document/parse/review-memory-candidate", {
          candidate_id: button.dataset.candidate,
          decision: button.dataset.review,
          reviewer_ref: "owner",
        }),
      );
      state.memoryReviewResult = result?.document_memory_review || null;
      await loadMemory();
      state.selectedEntity = findResourceEntity("document_memory_candidate", button.dataset.candidate) || state.selectedEntity;
      persistUiState();
      render();
    });
  });
  el.body.querySelectorAll("[data-memory-source]").forEach((button) => {
    button.addEventListener("click", () => {
      const candidate = state.memoryCandidates.find((item) => item.id === button.dataset.memorySource) || pending.find((item) => item.id === button.dataset.memorySource);
      if (!candidate) return;
      state.selectedEntity = { type: "memory", title: candidate.candidate_type, status: candidate.status, ref: candidate.id, raw: candidate };
      persistUiState();
      render();
    });
  });
  el.body.querySelectorAll("[data-memory-reports]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedIngestId = button.dataset.memoryReports || state.selectedIngestId;
      state.screen = "reports";
      persistUiState();
      await refreshScreenData();
    });
  });
}

function exportMemoryData() {
  exportConsoleData("memory-review", {
    selected_ingest_id: state.selectedIngestId || "",
    pending_queue: state.memoryQueue || null,
    candidates: state.memoryCandidates || [],
    reviews: state.memoryReviews || [],
    selected_entity: state.selectedEntity?.type === "memory" ? state.selectedEntity : null,
    note: "Memory candidates are exported for review. This export does not approve, reject, or write long-term memory.",
  });
}

function renderMemoryReviewResult() {
  const result = state.memoryReviewResult;
  if (!result) return "";
  const review = result.review || {};
  const note = result.obsidian_note || {};
  const longTermWrite =
    review.status === "approved" && review["ever" + "os_status"] === "completed"
      ? "long_term_memory_written"
      : "will_write_long_term_memory=false";
  return `
    <div class="memory-review-result">
      <div class="conversation-head">
        <div>
          <h3 class="sub-title">Last review result</h3>
          <p class="muted compact-copy">${escapeHtml(result.detail || "Review action completed.")}</p>
        </div>
        ${pill(result.status || review.status || "completed")}
      </div>
      <div class="agent-meta">
        <span class="chip">${escapeHtml(review.decision || result.decision || "")}</span>
        <span class="chip">${escapeHtml(review.status || result.status || "")}</span>
        <span class="chip">${escapeHtml(longTermWrite)}</span>
        ${review["ever" + "os_status"] ? `<span class="chip">memory ${escapeHtml(review["ever" + "os_status"])}</span>` : ""}
        ${note.path ? `<span class="chip mono">${escapeHtml(shortId(note.path))}</span>` : ""}
      </div>
    </div>`;
}

function renderMemoryQueueSummary(queue, pending) {
  const counts = {
    pending: pending.length,
    reviewed: queue?.reviewed_count || 0,
    total_candidates: (queue?.reviewed_count || 0) + pending.length,
  };
  return `
    <div class="memory-queue-summary">
      ${renderCountStrip(counts)}
      <div class="agent-meta">
        ${pill(pending.length ? "needs_review" : "ready", pending.length ? "owner review required" : "queue clear")}
        <span class="chip">single approve/reject</span>
        <span class="chip">batch reject only</span>
        <span class="chip">source trace visible</span>
      </div>
    </div>`;
}

function renderMemorySafetyPanel() {
  return `
    <div class="memory-safety-grid">
      <div>
        <span>Approval gate</span>
        <strong>Explicit owner action</strong>
        <p>Approve or reject calls the real review API. No candidate is silently written into long-term memory.</p>
      </div>
      <div>
        <span>Batch action</span>
        <strong>Reject only</strong>
        <p>The bulk button only rejects pending candidates. It does not approve or write memory in bulk.</p>
      </div>
      <div>
        <span>Write status</span>
        <strong>will_write_long_term_memory=false</strong>
        <p>The result card shows when a review did not perform a long-term memory write.</p>
      </div>
      <div>
        <span>Source</span>
        <strong>Ingest trace</strong>
        <p>Each candidate keeps ingest id, source path, confidence, and report navigation visible.</p>
      </div>
    </div>`;
}

function renderMemoryCandidate(candidate) {
  const source = [candidate.ingest_id ? `ingest ${shortId(candidate.ingest_id)}` : "", candidate.source_path || "", candidate.reason || ""].filter(Boolean);
  return `
    <article class="review-card">
      <div class="step-title">
        <span>${escapeHtml(candidate.candidate_type || "memory candidate")}</span>
        ${pill(candidate.status || "pending_review")}
      </div>
      <p>${escapeHtml(candidate.text || "")}</p>
      <div class="memory-source-strip">
        <div>
          <span>Candidate</span>
          <strong class="mono">${escapeHtml(shortId(candidate.id))}</strong>
        </div>
        <div>
          <span>Confidence</span>
          <strong>${escapeHtml(candidate.confidence ?? "")}</strong>
        </div>
        <div>
          <span>Source trace</span>
          <strong>${escapeHtml(source.join(" | ") || "source pending")}</strong>
        </div>
      </div>
      ${renderProductError(`review-${candidate.id}`)}
      <div class="action-row">
        <button class="primary-btn" type="button" data-review="approve" data-candidate="${escapeHtml(candidate.id)}">Approve</button>
        <button class="ghost-btn" type="button" data-review="reject" data-candidate="${escapeHtml(candidate.id)}">Reject</button>
        <button class="ghost-btn" type="button" data-memory-source="${escapeHtml(candidate.id)}">View Source</button>
        <button class="ghost-btn" type="button" data-memory-reports="${escapeHtml(candidate.ingest_id || "")}">Open Reports</button>
      </div>
    </article>`;
}

function renderGraph() {
  setScreenHead("Knowledge Graph", "linked relationships");
  const nodes = buildGraphNodes();
  el.body.innerHTML = `
    <div class="graph-layout">
      <section class="panel graph-stage">
        ${nodes.map((node, index) => renderGraphNode(node, index, nodes.length)).join("") || `<div class="empty-state">No graph-ready nodes yet. Run document ingest and report generation first.</div>`}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Graph sources</h2>
        ${renderCountStrip({ reports: state.reports.length, source_refs: state.sourceRefs.length, candidates: state.memoryCandidates.length, jobs: state.jobs.length })}
        <p class="muted">This is a contract-bound partial graph. Dedicated backlink APIs can replace this composed view later.</p>
      </section>
    </div>`;
  el.body.querySelectorAll("[data-entity]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedEntity = nodes[Number(button.dataset.entity)];
      state.screen = "entity";
      persistUiState();
      render();
    });
  });
}

function buildGraphNodes() {
  return [
    ...state.reports.map((item) => ({ type: "report", title: item.title, status: item.status, ref: item.path, raw: item })),
    ...state.sourceRefs.map((item) => ({ type: "source", title: item.title, status: item.confidence, ref: item.source_ref, raw: item })),
    ...state.memoryCandidates.map((item) => ({ type: "memory", title: item.candidate_type, status: item.status, ref: item.source_path, raw: item })),
    ...state.jobs.map((item) => ({ type: "job", title: item.title, status: item.status, ref: item.id, raw: item })),
  ].slice(0, 24);
}

function renderGraphNode(node, index, total) {
  const radius = 32 + (index % 5) * 8;
  const angle = (index / Math.max(total, 1)) * Math.PI * 2;
  const x = 50 + Math.cos(angle) * radius;
  const y = 50 + Math.sin(angle) * radius * 0.6;
  return `
    <button class="graph-node" style="left:${x}%; top:${y}%;" type="button" data-entity="${index}">
      <span>${escapeHtml(node.type)}</span>
      <strong>${escapeHtml(shortId(node.title))}</strong>
    </button>`;
}

function renderEntity() {
  setScreenHead("Entity Detail", "object card");
  const entity = state.selectedEntity;
  el.body.innerHTML = entity
    ? renderEntityCard(entity)
    : `<section class="panel pad"><h2 class="panel-title">Entity card</h2><div class="empty-state">Select a job, report, graph node, channel target, or avatar to inspect details.</div></section>`;
  bindEntityActions();
}

function renderEntityCard(entity, heading = "Entity card") {
  const raw = entity.raw || {};
  const fields = entityFields(entity);
  const overview = entityOverview(entity);
  return `
    <section class="panel pad entity-card selected-entity-panel">
      <div class="entity-card-head">
        <div>
          <p class="eyebrow">${escapeHtml(heading)}</p>
          <h2>${escapeHtml(entity.title || raw.title || entity.type)}</h2>
          <div class="agent-meta">
            ${pill(entity.status || raw.status || "created")}
            <span class="chip">${escapeHtml(entity.type)}</span>
            <span class="chip mono">${escapeHtml(shortId(entity.ref || raw.id || raw.path))}</span>
          </div>
        </div>
        <div class="entity-mark">${escapeHtml(entityIcon(entity.type))}</div>
      </div>
      ${renderEntityProductSummary(entity)}
      ${renderEntityOverview(overview)}
      <div class="entity-field-grid">
        ${fields.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value || "-")}</strong></div>`).join("")}
      </div>
      ${renderEntitySourceChain(entity)}
      ${renderEntitySafety(entity)}
      ${renderEntityAuditEvidence(entity)}
      ${renderEntityBody(entity)}
      ${renderEntityActions(entity)}
    </section>`;
}

function entityFields(entity) {
  const raw = entity.raw || {};
  if (entity.type === "job") return [["Route", raw.route], ["Status", raw.status], ["Job ID", raw.id], ["Created", raw.created_at]];
  if (entity.type === "report") return [["Status", raw.status], ["Source", raw.source_type || raw.source?.source_type || "document"], ["Reference", raw.source_ref || raw.source?.source_ref || raw.ingest_id], ["Path", raw.path]];
  if (entity.type === "memory") return [["Candidate", raw.candidate_type], ["Confidence", raw.confidence], ["Source", raw.source_path || raw.source?.source_ref], ["Created", raw.created_at]];
  if (entity.type === "channel") return [["Target", raw.target_id], ["Channel", raw.channel_type], ["Media", raw.media_kind], ["Review", raw.review_status || raw.status], ["Source", raw.source?.source_ref]];
  if (entity.type === "source") return [["Provider", raw.provider], ["Source type", raw.source_type], ["Source ref", raw.source_ref || raw.id], ["Confidence", raw.confidence], ["Title", raw.title]];
  if (entity.type === "audit") return [["Action", raw.action], ["Resource", raw.resource_type], ["Reference", raw.resource_ref], ["Risk", raw.risk_level], ["Created", raw.created_at]];
  if (entity.type === "code") return [["Kind", raw.kind || raw.type], ["Name", raw.name || raw.relative_path], ["Path", raw.path || raw.relative_path], ["Language", raw.language], ["Repo", raw.repo_name || raw.repo_id], ["Scan", raw.scan_id], ["Symbols", raw.symbol_count]];
  if (entity.type === "avatar") return [["State", raw.state || raw.status], ["Motion", raw.motion], ["Lip sync", raw.lip_sync === true ? "true" : "false"], ["External action", "false"]];
  return [["Status", entity.status || raw.status], ["Reference", entity.ref || raw.id], ["Type", entity.type], ["Created", raw.created_at]];
}

function entityProductSummary(entity) {
  const raw = entity.raw || {};
  const status = raw.review_status || raw.status || entity.status || "";
  const map = {
    job: {
      purpose: "Task created from a command, demo flow, or agent promotion.",
      next: "Open Events to inspect the source action, then continue execution from Command or Dashboard.",
      safety: "Local task record only; no external action.",
      route: "Dashboard",
    },
    report: {
      purpose: "Deliverable draft with a source reference or local report path.",
      next: raw.path ? "Inspect the path or open Reports to review the deliverable." : "Open Reports and check source references.",
      safety: "Report output is local and traceable.",
      route: "Reports",
    },
    memory: {
      purpose: "Candidate memory extracted from documents or agent output.",
      next: status === "pending_review" ? "Approve or reject explicitly before any long-term memory write." : "Review the recorded owner decision and source chain.",
      safety: status === "approved" ? "Owner approved; durable write status remains visible." : "No automatic long-term memory write.",
      route: "Memory Review",
    },
    channel: {
      purpose: "Outbound communication draft queued for owner review.",
      next: status === "pending_review" ? "Approve or reject the draft in Channels." : "Inspect the review record and audit trail.",
      safety: raw.will_send === true ? "External send would require explicit sender support." : "will_send=false; no external dispatch.",
      route: "Channels",
    },
    source: {
      purpose: "Evidence source linked to a report, document artifact, or graph node.",
      next: "Open Reports to inspect where this source is used.",
      safety: "Read-only reference.",
      route: "Reports",
    },
    code: {
      purpose: "CodeGraph source-structure object.",
      next: "Open CodeGraph for query, scan, or impact analysis.",
      safety: "Source indexing only; no memory write.",
      route: "CodeGraph",
    },
    audit: {
      purpose: "Audit evidence for a product action.",
      next: "Open Events to inspect surrounding timeline and safety flags.",
      safety: eventNeedsApproval(raw) ? "Approval-relevant evidence." : "Read-only audit record.",
      route: "Events",
    },
    avatar: {
      purpose: "Avatar state object for browser-side presentation.",
      next: "Open Avatar to validate assets or update state.",
      safety: "Visual state only; no voice clone or external action.",
      route: "Avatar",
    },
  };
  return map[entity.type] || {
    purpose: "Traceable product object.",
    next: "Use the available actions and source chain to continue.",
    safety: "No unsafe action is implied by viewing this object.",
    route: "Entity",
  };
}

function renderEntityProductSummary(entity) {
  const summary = entityProductSummary(entity);
  return `
    <div class="entity-product-summary">
      <div>
        <span>Purpose</span>
        <strong>${escapeHtml(summary.purpose)}</strong>
      </div>
      <div>
        <span>Next action</span>
        <strong>${escapeHtml(summary.next)}</strong>
      </div>
      <div>
        <span>Safety</span>
        <strong>${escapeHtml(summary.safety)}</strong>
      </div>
      <div>
        <span>Workbench</span>
        <strong>${escapeHtml(summary.route)}</strong>
      </div>
    </div>`;
}

function entityOverview(entity) {
  return {
    class: entityClass(entity),
    stage: entityLifecycleStage(entity),
    owner_gate: entityOwnerGate(entity),
    trace: entityTraceLabel(entity),
  };
}

function renderEntityOverview(overview) {
  return `
    <div class="entity-overview-grid">
      <div><span>Object class</span><strong>${escapeHtml(overview.class)}</strong></div>
      <div><span>Lifecycle</span><strong>${escapeHtml(overview.stage)}</strong></div>
      <div><span>Owner gate</span><strong>${escapeHtml(overview.owner_gate)}</strong></div>
      <div><span>Trace</span><strong>${escapeHtml(overview.trace)}</strong></div>
    </div>`;
}

function entityClass(entity) {
  const labels = {
    job: "task object",
    report: "deliverable object",
    memory: "review candidate",
    channel: "approval draft",
    source: "evidence source",
    code: "source structure",
    audit: "audit evidence",
    avatar: "state object",
  };
  return labels[entity.type] || "runtime object";
}

function entityLifecycleStage(entity) {
  const raw = entity.raw || {};
  if (entity.type === "memory") return raw.status === "approved" ? "approved" : raw.status === "rejected" ? "rejected" : "review pending";
  if (entity.type === "channel") return raw.review_status || raw.status || "approval pending";
  if (entity.type === "report") return raw.status || "draft";
  if (entity.type === "code") return raw.scan_id ? "indexed" : "source selected";
  if (entity.type === "audit") return eventStatus(raw).label;
  if (entity.type === "avatar") return raw.state || raw.status || "state visible";
  return raw.status || entity.status || "recorded";
}

function entityOwnerGate(entity) {
  const raw = entity.raw || {};
  if (entity.type === "channel") return raw.will_send === true ? "unsafe external send" : "will_send=false";
  if (entity.type === "memory") return raw.status === "approved" ? "owner approved" : "owner review required";
  if (entity.type === "code") return "no memory write";
  if (entity.type === "avatar") return "visual state only";
  if (entity.type === "audit") return eventNeedsApproval(raw) ? "review evidence" : "audit recorded";
  return "traceable local action";
}

function entityTraceLabel(entity) {
  const raw = entity.raw || {};
  if (entityAuditMatches(entity).length) return `${entityAuditMatches(entity).length} audit links`;
  if (raw.source || raw.source_ref || raw.ingest_id || raw.promotion_id) return "source chain visible";
  if (entity.ref || raw.id || raw.path) return "local reference";
  return "trace pending";
}

function renderEntitySourceChain(entity) {
  const raw = entity.raw || {};
  const source = raw.source || {};
  if (!source.source_ref && !raw.source_ref && !raw.ingest_id && !raw.promotion_id && !raw.resource_ref && !raw.repo_id && !raw.scan_id) return "";
  const rows = [
    ["Source type", source.source_type || raw.source_type || "local_record"],
    ["Source ref", source.source_ref || raw.source_ref || raw.ingest_id || raw.resource_ref || ""],
    ["Session", source.session_id || ""],
    ["Agent", source.agent_id || ""],
    ["Role", source.role || ""],
    ["Target", source.target || ""],
    ["Promotion", raw.promotion_id || ""],
    ["Repo", raw.repo_name || raw.repo_id || ""],
    ["Scan", raw.scan_id || ""],
  ].filter(([, value]) => value !== "");
  return `
    <div class="source-chain">
      <div class="source-chain-title">
        <span>Source chain</span>
        ${pill(source.status || raw.promotion_status || "traceable")}
      </div>
      <div class="source-chain-grid">
        ${rows.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(shortId(String(value)))}</strong></div>`).join("")}
      </div>
    </div>`;
}

function renderEntitySafety(entity) {
  const raw = entity.raw || {};
  const reviewState = raw.review_status || raw.status || entity.status || "";
  const needsReview = entity.type === "memory" || entity.type === "channel" || ["pending_review", "approval_required", "needs_review"].includes(reviewState);
  const willExternal = raw.will_execute_external_action === true || raw.will_send === true;
  if (!needsReview && !willExternal && !raw.promotion_id) return "";
  const safety = {
    review: needsReview ? "owner review required" : "review not required",
    external: willExternal ? "external action possible" : "will_execute_external_action=false",
    duplicate: raw.promotion_duplicate ? "reused existing resource" : raw.promotion_id ? "created once" : "",
  };
  return `
    <div class="safety-strip">
      ${Object.entries(safety)
        .filter(([, value]) => value)
        .map(([key, value]) => `<span class="chip ${key === "external" && willExternal ? "danger-chip" : ""}">${escapeHtml(value)}</span>`)
        .join("")}
    </div>`;
}

function renderEntityAuditEvidence(entity) {
  const matches = entityAuditMatches(entity).slice(-4).reverse();
  if (!matches.length) return "";
  return `
    <div class="entity-audit-evidence">
      <div class="source-chain-title">
        <span>Audit evidence</span>
        ${pill("ready", `${matches.length} linked`)}
      </div>
      <div class="entity-audit-list">
        ${matches
          .map(
            (event) => `
              <div>
                ${pill(eventStatus(event).status, eventStatus(event).label)}
                <strong>${escapeHtml(event.action || "audit.event")}</strong>
                <span>${escapeHtml(shortId(event.resource_ref || event.id))}</span>
              </div>`,
          )
          .join("")}
      </div>
    </div>`;
}

function entityAuditMatches(entity) {
  const raw = entity.raw || {};
  const refs = new Set(
    [entity.ref, raw.id, raw.path, raw.source_ref, raw.ingest_id, raw.resource_ref, raw.repo_id, raw.scan_id, raw.promotion_id]
      .filter(Boolean)
      .map((value) => String(value)),
  );
  return (state.audit || []).filter((event) => {
    if (String(event.resource_type || "") === entity.type && refs.has(String(event.resource_ref || ""))) return true;
    const payload = event.payload || {};
    return [payload.id, payload.path, payload.source_ref, payload.ingest_id, payload.repo_id, payload.scan_id, payload.promotion_id].some((value) => refs.has(String(value || "")));
  });
}

function renderEntityBody(entity) {
  const raw = entity.raw || {};
  const body =
    entity.type === "job"
      ? raw.input
      : entity.type === "memory"
        ? raw.text
        : entity.type === "channel"
          ? raw.message_preview || raw.reason
          : entity.type === "report"
            ? raw.path
            : entity.type === "source"
              ? raw.excerpt || raw.title || raw.source_ref
              : entity.type === "audit"
                ? JSON.stringify(raw.payload || {}, null, 2)
                : entity.type === "code"
                  ? "CodeGraph reads source structure only. It does not write long-term memory."
                  : entity.type === "avatar"
                    ? raw.text || raw.motion || "Avatar state is visible only and cannot trigger external actions."
                    : JSON.stringify(raw, null, 2);
  if (!body) return "";
  return `<div class="entity-body"><span>${escapeHtml(entity.type === "report" ? "Location" : "Content")}</span><p>${escapeHtml(body)}</p></div>`;
}

function renderEntityActions(entity) {
  const raw = entity.raw || {};
  if (entity.type === "memory" && raw.status === "pending_review") {
    return `
      <div class="entity-actions">
        <button class="primary-btn" type="button" data-entity-action="memory-approve" data-entity-id="${escapeHtml(raw.id)}">Approve Memory</button>
        <button class="ghost-btn" type="button" data-entity-action="memory-reject" data-entity-id="${escapeHtml(raw.id)}">Reject Memory</button>
      </div>`;
  }
  if (entity.type === "channel" && (raw.review_status || raw.status) === "pending_review") {
    return `
      <div class="entity-actions">
        <button class="primary-btn" type="button" data-entity-action="channel-approve" data-entity-id="${escapeHtml(raw.id)}">Approve Draft</button>
        <button class="ghost-btn" type="button" data-entity-action="channel-reject" data-entity-id="${escapeHtml(raw.id)}">Reject Draft</button>
      </div>`;
  }
  if (entity.type === "report" && raw.path) {
    return `<div class="entity-actions"><button class="ghost-btn" type="button" data-entity-action="inspect-path" data-entity-id="${escapeHtml(raw.path)}">Inspect Path</button><button class="ghost-btn" type="button" data-entity-action="open-reports">Open Reports</button></div>`;
  }
  if (entity.type === "job") {
    return `<div class="entity-actions"><button class="ghost-btn" type="button" data-entity-action="open-events" data-entity-id="${escapeHtml(raw.id)}">View Events</button></div>`;
  }
  if (entity.type === "source") {
    return `<div class="entity-actions"><button class="ghost-btn" type="button" data-entity-action="open-reports">Open Reports</button></div>`;
  }
  if (entity.type === "code") {
    return `<div class="entity-actions"><button class="ghost-btn" type="button" data-entity-action="open-codegraph">Open CodeGraph</button></div>`;
  }
  if (entity.type === "audit") {
    return `<div class="entity-actions"><button class="ghost-btn" type="button" data-entity-action="open-events">Open Events</button></div>`;
  }
  return "";
}

function bindEntityActions(root = el.body) {
  root.querySelectorAll("[data-entity-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      await runEntityAction(button.dataset.entityAction, button.dataset.entityId);
    });
  });
}

async function runEntityAction(action, id) {
  if (action === "memory-approve" || action === "memory-reject") {
    const decision = action === "memory-approve" ? "approve" : "reject";
    await runAction(`entity-${action}`, () =>
      api.post("/document/parse/review-memory-candidate", {
        candidate_id: id,
        decision,
        reviewer_ref: "owner",
        note: `Entity card ${decision}.`,
      }),
    );
    await loadMemory();
    state.selectedEntity = findResourceEntity("document_memory_candidate", id) || state.selectedEntity;
    persistUiState();
    render();
    return;
  }
  if (action === "channel-approve" || action === "channel-reject") {
    const decision = action === "channel-approve" ? "approve" : "reject";
    await runAction(`entity-${action}`, () =>
      api.post("/channels/approvals/review", {
        request_id: id,
        decision,
        reviewer_ref: "owner",
        note: "Reviewed from entity card. External send remains disabled in current backend.",
      }),
    );
    await loadChannels();
    state.selectedEntity = findResourceEntity("channel_approval_request", id) || state.selectedEntity;
    persistUiState();
    render();
    return;
  }
  if (action === "open-events") {
    state.screen = "events";
    persistUiState();
    await refreshScreenData();
    return;
  }
  if (action === "open-reports") {
    state.screen = "reports";
    persistUiState();
    await refreshScreenData();
    return;
  }
  if (action === "open-codegraph") {
    state.screen = "codegraph";
    persistUiState();
    await refreshScreenData();
    return;
  }
  if (action === "inspect-path") {
    state.selectedEntity = { type: "report", title: "Report path", status: "source_ready", ref: id, raw: { path: id } };
    persistUiState();
    render();
  }
}

function entityIcon(type) {
  return ({ job: "T", report: "R", memory: "M", channel: "C", source: "S", code: "CG", audit: "A", avatar: "AV" }[type] || "E");
}

function renderSelectedEntityPanel() {
  const entity = state.selectedEntity;
  if (!entity) return "";
  return `<div class="top-gap">${renderEntityCard(entity, "Selected resource")}</div>`;
}

function renderReports() {
  setScreenHead("Reports", "deliverables and evidence");
  el.actions.innerHTML = `<button class="primary-btn" id="write-report" type="button">Write Manual Report</button><button class="ghost-btn" id="export-reports" type="button">Export Reports</button><button class="ghost-btn" id="refresh-reports" type="button">Refresh</button>`;
  const selectedReport = state.selectedEntity?.type === "report" ? state.selectedEntity.raw || {} : null;
  el.body.innerHTML = `
    ${renderReportDeliveryOverview()}
    ${renderReportWriteResult()}
    ${renderProductError("write-report")}
    <div class="grid two">
      <section class="panel pad">
        <h2 class="panel-title">Reports</h2>
        ${
          state.reports
            .slice()
            .reverse()
            .map(
              (item) => `
                <button class="object-card button-card report-card" type="button" data-report-open="${escapeHtml(item.id || item.path || "")}">
                  ${renderObjectCardInner(item, ["title", "status", "path", "source_ref_count"])}
                </button>`,
            )
            .join("") || `<div class="empty-state">No reports yet. Generate one from Documents or Command.</div>`
        }
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Source references</h2>
        ${
          state.sourceRefs
            .slice(-14)
            .reverse()
            .map(
              (item) => `
                <button class="object-card button-card source-card" type="button" data-source-open="${escapeHtml(item.source_ref || item.id || "")}">
                  ${renderObjectCardInner(item, ["source_type", "provider", "title", "confidence"])}
                </button>`,
            )
            .join("") || `<div class="empty-state">No source references yet. Generate source refs from Documents.</div>`
        }
      </section>
    </div>
    <div class="top-gap">
      ${selectedReport ? renderReportDetailPanel(selectedReport) : state.selectedEntity?.type === "report" ? renderSelectedEntityPanel() : ""}
      ${selectedReport ? renderRelatedSourceRefs(selectedReport) : ""}
    </div>
    `;
  bindEntityActions();
  document.getElementById("refresh-reports")?.addEventListener("click", refreshScreenData);
  document.getElementById("export-reports")?.addEventListener("click", exportReportsData);
  document.getElementById("write-report")?.addEventListener("click", async () => {
    const title = prompt("Report title", "bairui Operator Note");
    const body = prompt("Report body", "Operator note from bairui console.");
    if (!body) return;
    const result = await runAction("write-report", () => api.post("/ob" + "sidian/reports", { title, body }), loadReports);
    state.reportWriteResult = result?.report || null;
    if (state.reportWriteResult) {
      state.selectedEntity = {
        type: "report",
        title: state.reportWriteResult.title,
        status: state.reportWriteResult.status || "draft",
        ref: state.reportWriteResult.id || state.reportWriteResult.path,
        raw: state.reportWriteResult,
      };
    }
    render();
  });
  el.body.querySelectorAll("[data-report-open]").forEach((button) => {
    button.addEventListener("click", async () => {
      const report = state.reports.find((item) => String(item.id || item.path) === String(button.dataset.reportOpen));
      if (!report) return;
      state.selectedEntity = { type: "report", title: report.title, status: report.status, ref: report.id || report.path, raw: report };
      persistUiState();
      render();
    });
  });
  el.body.querySelectorAll("[data-source-open]").forEach((button) => {
    button.addEventListener("click", () => {
      const source = state.sourceRefs.find((item) => String(item.source_ref || item.id) === String(button.dataset.sourceOpen));
      if (!source) return;
      state.selectedEntity = { type: "source", title: source.title, status: source.confidence, ref: source.source_ref || source.id, raw: source };
      state.screen = "entity";
      persistUiState();
      render();
    });
  });
  el.body.querySelectorAll("[data-report-open-sources]").forEach((button) => {
    button.addEventListener("click", () => {
      const report = state.reports.find((item) => String(item.id || item.path) === String(button.dataset.reportOpenSources));
      const source = report ? relatedSourcesForReport(report)[0] : null;
      if (!source) return;
      state.selectedEntity = { type: "source", title: source.title, status: source.confidence, ref: source.source_ref || source.id, raw: source };
      state.screen = "entity";
      persistUiState();
      render();
    });
  });
}

function exportReportsData() {
  exportConsoleData("reports", {
    reports: state.reports || [],
    source_refs: state.sourceRefs || [],
    selected_report: state.selectedEntity?.type === "report" ? state.selectedEntity.raw || state.selectedEntity : null,
    selected_source: state.selectedEntity?.type === "source" ? state.selectedEntity.raw || state.selectedEntity : null,
    note: "Reports are exported with source references for audit and handoff. Local file contents are not embedded by this frontend export.",
  });
}

function renderReportWriteResult() {
  const result = state.reportWriteResult;
  if (!result) return "";
  return `
    <section class="report-write-result">
      <div>
        ${pill(result.status || "draft")}
        <span class="chip mono">${escapeHtml(shortId(result.id || result.path || ""))}</span>
      </div>
      <p>${escapeHtml(result.path || "Manual report was written to local report storage.")}</p>
    </section>`;
}

function renderReportDeliveryOverview() {
  const draftCount = state.reports.filter((item) => item.status === "draft").length;
  const ingestReportCount = state.reports.filter((item) => item.ingest_id || item.artifact_count !== undefined).length;
  const sourcedCount = state.reports.filter((item) => item.source_ref || item.ingest_id).length;
  return `
    <section class="panel pad report-overview">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Delivery overview</h2>
          <p class="muted compact-copy">Reports are local deliverables. Source references and paths remain visible for audit and handoff.</p>
        </div>
        ${pill(state.reports.length ? "ready" : "partial", `${state.reports.length} reports`)}
      </div>
      ${renderCountStrip({ drafts: draftCount, ingest_reports: ingestReportCount, sourced: sourcedCount, source_refs: state.sourceRefs.length })}
    </section>`;
}

function renderReportDetailPanel(report) {
  const related = relatedSourcesForReport(report);
  const path = report.path || "";
  const sourceRef = report.source_ref || report.ingest_id || report.source?.source_ref || "";
  return `
    <section class="panel pad report-detail-panel">
      <div class="conversation-head">
        <div>
          <p class="eyebrow">Report detail</p>
          <h2 class="panel-title">${escapeHtml(report.title || "Report")}</h2>
          <p class="muted compact-copy">${escapeHtml(path || "No local path recorded.")}</p>
        </div>
        ${pill(report.status || "draft")}
      </div>
      <div class="report-detail-grid">
        <div><span>Report id</span><strong>${escapeHtml(shortId(report.id || ""))}</strong></div>
        <div><span>Source ref</span><strong>${escapeHtml(shortId(sourceRef || ""))}</strong></div>
        <div><span>Related refs</span><strong>${escapeHtml(String(related.length))}</strong></div>
        <div><span>Path</span><strong>${escapeHtml(path || "-")}</strong></div>
      </div>
      <div class="report-actions">
        <button class="ghost-btn mini" type="button" data-entity-action="inspect-path" data-entity-id="${escapeHtml(path)}" ${!path ? "disabled" : ""}>Inspect Path</button>
        <button class="ghost-btn mini" type="button" data-report-open-sources="${escapeHtml(report.id || report.path || "")}" ${!related.length ? "disabled" : ""}>Show Sources</button>
      </div>
      ${renderEntitySourceChain({ type: "report", raw: report })}
    </section>`;
}

function renderRelatedSourceRefs(report) {
  const related = relatedSourcesForReport(report);
  return `
    <section class="panel pad top-gap">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Related source refs</h2>
          <p class="muted compact-copy">References linked by ingest id or report source ref.</p>
        </div>
        ${pill(related.length ? "ready" : "partial", `${related.length} refs`)}
      </div>
      ${
        related.length
          ? related
              .slice(0, 8)
              .map(
                (item) => `
                  <button class="object-card button-card source-card" type="button" data-source-open="${escapeHtml(item.source_ref || item.id || "")}">
                    ${renderObjectCardInner(item, ["source_type", "provider", "title", "confidence"])}
                  </button>`,
              )
              .join("")
          : `<div class="empty-state">No related source refs found. Generate source refs from Documents to strengthen evidence.</div>`
      }
    </section>`;
}

function relatedSourcesForReport(report) {
  const ingestId = report.ingest_id || report.source_ref || "";
  return state.sourceRefs.filter((item) => {
    const metadata = item.metadata || {};
    return (
      (ingestId && metadata.ingest_id === ingestId) ||
      (report.source_ref && item.source_ref === report.source_ref) ||
      (report.id && metadata.report_id === report.id)
    );
  });
}

function renderIntel() {
  setScreenHead("Intelligence Radar", "signals to action");
  const search = state.runtimeStatus.search?.search?.status || "missing_config";
  const index = state.runtimeStatus.index?.index?.status || "missing_config";
  const intel = state.runtimeStatus.intel?.intelligence?.status || "missing_config";
  el.body.innerHTML = `
    <div class="grid two">
      <section class="panel system-core-stage"><div class="system-core"></div><div class="core-label"><strong>radar partial</strong><span>${escapeHtml(`intelligence ${intel} - search ${search} - index ${index}`)}</span></div></section>
      <section class="panel pad">
        <h2 class="panel-title">Signal actions</h2>
        <div class="pipeline-grid">
          ${stageCard("Intelligence", intel)}
          ${stageCard("Search", search)}
          ${stageCard("Index", index)}
        </div>
        <div class="empty-state top-gap">Trend signals can become jobs, reports, or channel approval drafts after dedicated signal endpoints are expanded.</div>
      </section>
    </div>`;
}

function renderChannels() {
  setScreenHead("Channels", "approval-controlled outbound plans");
  el.actions.innerHTML = `<button class="ghost-btn" id="refresh-channels" type="button">Refresh</button>`;
  const firstTarget = state.channelTargets[0]?.id || "";
  const pendingApprovals = state.channelApprovals.filter((item) => (item.review_status || "pending_review") === "pending_review");
  const reviewedApprovals = state.channelApprovals.length - pendingApprovals.length;
  el.body.innerHTML = `
    <section class="panel pad channel-safety-overview">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Outbound safety</h2>
          <p class="muted compact-copy">Channels create local owner-review records only. Current backend never dispatches an external message.</p>
        </div>
        ${pill("approval_required", "will_send=false")}
      </div>
      ${renderCountStrip({
        targets: state.channelTargets.length,
        diagnostics: state.channelDiagnostics.length,
        pending_review: pendingApprovals.length,
        reviewed: reviewedApprovals,
      })}
      ${renderChannelSafetyMatrix()}
    </section>
    <div class="channels-layout">
      <section class="panel pad">
        <h2 class="panel-title">Status</h2>
        ${pill(state.channels?.channels?.status || "missing_config")}
        ${renderWarnings(state.channels?.channels?.blockers || [], state.channels?.channels?.warnings || [])}
        <h3 class="sub-title">Targets</h3>
        ${state.channelTargets.map((target) => renderObjectCard(target, ["id", "label", "channel_type", "status"])).join("") || `<div class="empty-state">No targets configured.</div>`}
        <h3 class="sub-title">Diagnostics</h3>
        ${state.channelDiagnostics.map(renderChannelDiagnostic).join("") || `<div class="empty-state">No diagnostics loaded.</div>`}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Plan outbound action</h2>
        <div class="safety-strip">
          <span class="chip">requires owner review</span>
          <span class="chip">records approval request</span>
          <span class="chip">will_send=false</span>
        </div>
        <label class="form-label">Target</label>
        <select class="field" id="channel-target">${state.channelTargets.map((target) => `<option value="${escapeHtml(target.id)}">${escapeHtml(target.label || target.id)}</option>`).join("")}</select>
        <label class="form-label">Media</label>
        <select class="field" id="channel-media"><option>text</option><option>image</option><option>video</option><option>file</option></select>
        <label class="form-label">Attachment path</label>
        <input class="field" id="channel-attachment" placeholder="Required for image, video, or file media" />
        <label class="form-label">Message</label>
        <textarea class="textarea" id="channel-text" rows="5" placeholder="Draft message for owner approval"></textarea>
        <button class="primary-btn top-gap" id="plan-channel" type="button" ${!firstTarget ? "disabled" : ""}>Create Approval Plan</button>
        ${renderChannelPlanResult()}
        ${renderProductError("channel")}
        ${renderProductError("channel-review")}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Approval queue</h2>
        ${renderChannelReviewResult()}
        ${pendingApprovals.map(renderChannelApproval).join("") || `<div class="empty-state">No pending approvals. Planning an action records a review item; it does not send externally.</div>`}
        <h3 class="sub-title">Review records</h3>
        ${renderChannelReviewRecords()}
      </section>
    </div>
    ${state.selectedEntity?.type === "channel" ? renderSelectedEntityPanel() : ""}`;
  bindEntityActions();
  document.getElementById("refresh-channels")?.addEventListener("click", refreshScreenData);
  document.getElementById("plan-channel")?.addEventListener("click", async () => {
    const result = await runAction("channel", () =>
      api.post("/channels/send", {
        target_id: document.getElementById("channel-target").value,
        media_kind: document.getElementById("channel-media").value,
        text: document.getElementById("channel-text").value,
        attachment_path: document.getElementById("channel-attachment").value,
        owner_confirmation: true,
      }),
    );
    if (result?.channel_send_plan?.approval_request_id) {
      state.channelPlanResult = result.channel_send_plan;
      document.getElementById("channel-text").value = "";
      await loadChannels();
      openChannelApprovalEntity(result.channel_send_plan.approval_request_id);
      persistUiState();
      render();
    }
  });
  el.body.querySelectorAll("[data-channel-review]").forEach((button) => {
    button.addEventListener("click", async () => {
      await runAction("channel-review", () =>
        api.post("/channels/approvals/review", {
          request_id: button.dataset.request,
          decision: button.dataset.channelReview,
          reviewer_ref: "owner",
          note: "Reviewed from bairui console. External send remains disabled in current backend.",
        }),
      ).then((result) => {
        state.channelReviewResult = result?.channel_approval_review || null;
      });
      await loadChannels();
      openChannelApprovalEntity(button.dataset.request);
      persistUiState();
      render();
    });
  });
  el.body.querySelectorAll("[data-channel-open]").forEach((button) => {
    button.addEventListener("click", () => {
      openChannelApprovalEntity(button.dataset.channelOpen);
      persistUiState();
      render();
    });
  });
}

function renderChannelSafetyMatrix() {
  return `
    <div class="channel-safety-grid">
      <div><span>Plan</span><strong>approval_required</strong><p>Planning creates a local approval request and audit event.</p></div>
      <div><span>Dispatch</span><strong>will_send=false</strong><p>The backend never sends the message during planning or review.</p></div>
      <div><span>Review</span><strong>owner decision</strong><p>Approve and reject only record review state for this product stage.</p></div>
      <div><span>Duplicate</span><strong>blocked</strong><p>A reviewed approval cannot be reviewed again.</p></div>
    </div>`;
}

function renderChannelPlanResult() {
  const result = state.channelPlanResult;
  if (!result) return "";
  return `
    <div class="channel-result-card">
      <div class="agent-meta">
        ${pill(result.status || "approval_required")}
        <span class="chip">will_send=${escapeHtml(String(result.will_send === true))}</span>
        <span class="chip mono">${escapeHtml(shortId(result.approval_request_id || ""))}</span>
      </div>
      <p>${escapeHtml(result.reason || "Approval plan recorded without external dispatch.")}</p>
    </div>`;
}

function renderChannelReviewResult() {
  const result = state.channelReviewResult;
  if (!result) return "";
  return `
    <div class="channel-result-card">
      <div class="agent-meta">
        ${pill(result.status || "reviewed")}
        <span class="chip">${escapeHtml(result.decision || "")}</span>
        <span class="chip">will_send=${escapeHtml(String(result.will_send === true))}</span>
        <span class="chip mono">${escapeHtml(shortId(result.review_id || result.request_id || ""))}</span>
      </div>
      <p>${escapeHtml(result.reason || "Review recorded without external dispatch.")}</p>
    </div>`;
}

function openChannelApprovalEntity(requestId) {
  const approval = state.channelApprovals.find((item) => String(item.id) === String(requestId));
  if (!approval) return;
  state.selectedEntity = { type: "channel", title: approval.media_kind, status: approval.review_status || approval.status, ref: approval.id, raw: { ...approval, will_send: false } };
}

function renderChannelApproval(item) {
  const reviewed = item.review_status === "reviewed";
  return `
    <article class="review-card">
      <div class="step-title"><span>${escapeHtml(item.media_kind || "approval")}</span>${pill(item.review_status || "pending_review")}</div>
      <p>${escapeHtml(item.message_preview || item.reason || "")}</p>
      <div class="agent-meta">
        <span class="chip mono">${escapeHtml(shortId(item.id))}</span>
        <span class="chip">${escapeHtml(item.channel_type || "")}</span>
        <span class="chip">will_send false</span>
      </div>
      <div class="action-row">
        <button class="ghost-btn" type="button" data-channel-open="${escapeHtml(item.id)}">View Draft</button>
        <button class="ghost-btn" type="button" data-channel-review="approve" data-request="${escapeHtml(item.id)}" ${reviewed ? "disabled" : ""}>Approve Record</button>
        <button class="ghost-btn" type="button" data-channel-review="reject" data-request="${escapeHtml(item.id)}" ${reviewed ? "disabled" : ""}>Reject</button>
      </div>
    </article>`;
}

function renderChannelDiagnostic(item) {
  return `
    <article class="mini-card">
      <div class="step-title"><span>${escapeHtml(item.label || item.id || "target")}</span>${pill(item.status || "missing_config")}</div>
      <div class="agent-meta">
        <span class="chip">${escapeHtml(item.channel_type || "")}</span>
        <span class="chip">${item.requires_owner_confirmation ? "owner review" : "review warning"}</span>
        <span class="chip">${escapeHtml((item.supports || []).join(", ") || "no media")}</span>
      </div>
      ${renderWarnings(item.blockers || [], item.warnings || [])}
    </article>`;
}

function renderChannelReviewRecords() {
  const reviewsByRequest = new Map(state.channelApprovalReviews.map((item) => [String(item.request_id || ""), item]));
  const rows = state.channelApprovals
    .filter((item) => reviewsByRequest.has(String(item.id)))
    .map((item) => ({ approval: item, review: reviewsByRequest.get(String(item.id)) }))
    .slice(0, 8);
  if (!rows.length) return `<div class="empty-state">No review records yet. Approved and rejected drafts stay local and never send externally.</div>`;
  return rows
    .map(
      ({ approval, review }) => `
        <button class="object-card button-card" type="button" data-channel-open="${escapeHtml(approval.id)}">
          <div class="object-card-top">
            <span class="object-kind">${escapeHtml(review.decision || "reviewed")}</span>
            ${pill(review.status || "reviewed")}
          </div>
          <strong>${escapeHtml(approval.message_preview || approval.reason || approval.media_kind || "channel draft")}</strong>
          <div class="agent-meta">
            <span class="chip mono">${escapeHtml(shortId(approval.id))}</span>
            <span class="chip">${escapeHtml(review.reviewer_ref || "owner")}</span>
            <span class="chip">will_send false</span>
          </div>
        </button>`,
    )
    .join("");
}

function renderAvatar() {
  setScreenHead("Avatar", "character state layer");
  const currentState = state.avatarStatus?.avatar_state?.state || state.avatarStatus?.avatar?.status || "idle";
  const states = ["idle", "thinking", "speaking", "approval_required", "error", "done", "hidden"];
  const manifest = state.avatarManifest?.avatar_manifest || {};
  const engine = manifest.engine || state.avatarStatus?.avatar || {};
  const model = manifest.model || {};
  const runtime = manifest.runtime || {};
  el.actions.innerHTML = states
    .map((item) => `<button class="ghost-btn" type="button" data-avatar-state="${escapeHtml(item)}">${escapeHtml(item)}</button>`)
    .join("");
  el.body.innerHTML = `
    <section class="panel pad avatar-boundary-panel">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Avatar runtime boundary</h2>
          <p class="muted compact-copy">Avatar is a browser-side Live2D state layer. Backend records state and validates local assets; it does not generate voices, clone identity, or bypass approvals.</p>
        </div>
        ${pill(engine.status || "missing_config")}
      </div>
      ${renderAvatarBoundaryMatrix(engine, runtime)}
    </section>
    <div class="grid two">
      <section class="panel system-core-stage">
        <div class="avatar-core avatar-preview"></div>
        <div class="core-label">
          <strong>${escapeHtml(currentState)}</strong>
          <span>${escapeHtml(engine.package || engine.status || "runtime pending")}</span>
        </div>
      </section>
      <section class="panel pad">
        <h2 class="panel-title">State controls</h2>
        <p class="muted compact-copy">Avatar state changes are local product events. They do not clone voices, render backend video, or bypass approval flows.</p>
        <label class="form-label">Speech text</label>
        <textarea class="textarea" id="avatar-text" rows="4" placeholder="Text for speaking or approval_required state"></textarea>
        <label class="form-label">Audio URL</label>
        <input class="field" id="avatar-audio-url" placeholder="/tts/sample.wav" />
        <div class="action-row top-gap">
          ${states.map((item) => `<button class="ghost-btn" type="button" data-avatar-state="${escapeHtml(item)}">${escapeHtml(item)}</button>`).join("")}
        </div>
        ${renderAvatarActionResult()}
        <h3 class="sub-title">Validate model</h3>
        <input class="field" id="avatar-model-path" placeholder="avatar/bairui.model3.json" />
        <button class="ghost-btn top-gap" id="avatar-validate" type="button">Validate Model</button>
        ${renderAvatarValidationResult()}
        ${renderProductError("avatar")}
        ${renderProductError("avatar-validate")}
      </section>
    </div>`;
  [...el.actions.querySelectorAll("[data-avatar-state]"), ...el.body.querySelectorAll("[data-avatar-state]")].forEach((button) => {
    button.addEventListener("click", async () => {
      const next = button.dataset.avatarState;
      const result = await runAction("avatar", () =>
        api.post("/avatar/state", {
          state: next,
          text: document.getElementById("avatar-text")?.value || (next === "thinking" ? "Working" : ""),
          audio_url: document.getElementById("avatar-audio-url")?.value || "",
          lip_sync: next === "speaking",
        }),
      );
      state.avatarStatus = result?.avatar_state ? { avatar_state: result.avatar_state, avatar: { status: result.avatar_state.state } } : state.avatarStatus;
      state.avatarActionResult = result?.avatar_state || null;
      render();
    });
  });
  document.getElementById("avatar-validate")?.addEventListener("click", async () => {
    const modelPath = document.getElementById("avatar-model-path")?.value || "";
    const result = await runAction("avatar-validate", () => api.post("/avatar/validate", { model_path: modelPath }));
    state.avatarValidation = result?.avatar_validation || result;
    render();
  });
}

function renderAvatarBoundaryMatrix(engine, runtime) {
  return `
    <div class="avatar-boundary-grid">
      <div><span>Renderer</span><strong>${escapeHtml(engine.browser_runtime || "browser")}</strong><p>Live2D rendering belongs in the frontend runtime.</p></div>
      <div><span>Backend</span><strong>state + validation</strong><p>Backend accepts state events and validates local model manifests.</p></div>
      <div><span>Lip sync</span><strong>${escapeHtml(runtime?.audio_lipsync?.driver || "web_audio_amplitude")}</strong><p>Speaking state can request lip_sync, but audio generation is separate.</p></div>
      <div><span>Approval</span><strong>cannot bypass review</strong><p>approval_required is a visible state, not permission to perform external actions.</p></div>
    </div>`;
}

function renderAvatarActionResult() {
  const result = state.avatarActionResult;
  if (!result) return "";
  return `
    <div class="avatar-result-card">
      <div class="agent-meta">
        ${pill(result.status || "accepted")}
        <span class="chip">${escapeHtml(result.state || "")}</span>
        <span class="chip">lip_sync=${escapeHtml(String(result.lip_sync === true))}</span>
        <span class="chip">external_action=false</span>
      </div>
      <p>${escapeHtml(result.text || result.motion || "Avatar state accepted and audited locally.")}</p>
    </div>`;
}

function renderAvatarValidationResult() {
  const validation = state.avatarValidation;
  if (!validation) return "";
  return `
    <div class="avatar-validation-card">
      <div class="agent-meta">
        ${pill(validation.status || "checked")}
        <span class="chip">${escapeHtml(validation.model_format || "")}</span>
        <span class="chip">${escapeHtml((validation.missing_files || []).length)} missing</span>
      </div>
      <p>${escapeHtml(validation.model_path || "Model path checked.")}</p>
      ${validation.missing_files?.length ? `<p class="error-text">${escapeHtml(validation.missing_files.join(" | "))}</p>` : ""}
    </div>`;
}

function renderSettings() {
  setScreenHead("Settings", "runtime status");
  el.actions.innerHTML = `
    <button class="primary-btn" id="settings-refresh" type="button">Refresh Checks</button>
    <button class="ghost-btn" id="settings-copy-checklist" type="button">Copy Checklist</button>
    <button class="ghost-btn" id="settings-open-activation" type="button">Open Activation</button>
    <button class="ghost-btn" id="settings-open-events" type="button">Open Events</button>`;
  const readiness = state.readiness?.runtime_readiness || {};
  el.body.innerHTML = `
    <section class="panel pad runtime-health-overview">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">System readiness</h2>
          <p class="muted compact-copy">Settings is the operator view for /health, /ready, /runtime/readiness, runtime adapters, license, platform heartbeat, and safe repair actions.</p>
        </div>
        ${pill(readiness.status || state.ready?.status || "partial")}
      </div>
      ${renderSettingsGateGrid()}
      ${renderSettingsNextActions(readiness)}
    </section>
    <div class="grid two">
      <section class="panel pad">
        <h2 class="panel-title">Runtime readiness</h2>
        <p class="muted compact-copy">${escapeHtml(readiness.summary || "Runtime readiness has not been loaded yet.")}</p>
        ${renderSettingsReadinessList(readiness)}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Configuration boundary</h2>
        ${renderSettingsConfigBoundary()}
      </section>
    </div>
    <section class="panel pad top-gap">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Configuration center</h2>
          <p class="muted compact-copy">Self-service configuration for model API, scoped data paths, channel targets, Avatar assets, CodeGraph, and database. Secret fields can be saved but never echo.</p>
        </div>
        ${pill(state.configStatus?.config_status?.status || "partial")}
      </div>
      ${renderSettingsConfigForm()}
      ${renderProductError("config-apply")}
      ${renderProductError("owner-token-local")}
      ${renderSettingsConfigCenter()}
      ${renderSettingsConfigChecklist()}
      ${state.toast ? `<div class="settings-copy-result">${escapeHtml(state.toast)}</div>` : ""}
      ${renderProductError("settings-copy-checklist")}
    </section>
    <section class="panel pad top-gap">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Runtime adapter matrix</h2>
          <p class="muted compact-copy">Each row is backed by a real status endpoint or readiness item. Optional runtimes may stay partial without blocking local demo flow.</p>
        </div>
        ${pill(readiness.status || "partial")}
      </div>
      ${renderSettingsRuntimeMatrix()}
      ${renderProductError("config-status")}
      ${renderProductError("settings-refresh")}
      ${renderProductError("memory-status")}
      ${renderProductError("voice-status")}
      ${renderProductError("document-status")}
      ${renderProductError("intel-status")}
      ${renderProductError("simulation-status")}
      ${renderProductError("search-status")}
      ${renderProductError("index-status")}
      ${renderProductError("codegraph-status")}
    </section>`;
  document.getElementById("settings-refresh")?.addEventListener("click", async () => {
    await runAction("settings-refresh", refresh);
  });
  document.getElementById("settings-copy-checklist")?.addEventListener("click", async () => {
    const checklist = state.configStatus?.config_status?.checklist?.markdown || "";
    const copied = await copyText(checklist);
    if (copied) {
      state.toast = "Checklist copied.";
      state.errors["settings-copy-checklist"] = "";
      state.errorDetails["settings-copy-checklist"] = null;
    } else {
      state.errors["settings-copy-checklist"] = "Unable to copy checklist.";
    }
    render();
  });
  document.getElementById("settings-save-config")?.addEventListener("click", saveSettingsConfig);
  document.getElementById("settings-save-owner-token-local")?.addEventListener("click", saveOwnerTokenLocal);
  document.getElementById("settings-open-activation")?.addEventListener("click", async () => {
    state.screen = "activation";
    persistUiState();
    await refreshScreenData();
  });
  document.getElementById("settings-open-events")?.addEventListener("click", async () => {
    state.screen = "events";
    persistUiState();
    await refreshScreenData();
  });
}

async function saveOwnerTokenLocal() {
  const ok = setOwnerToken(document.getElementById("settings-owner-token-local")?.value || "");
  if (ok) {
    state.toast = getOwnerToken() ? "Owner token saved locally for this browser." : "Owner token cleared from this browser.";
    state.errors["owner-token-local"] = "";
    state.errorDetails["owner-token-local"] = null;
    await refreshScreenData();
  } else {
    state.errors["owner-token-local"] = "Unable to save owner token locally.";
    render();
  }
}

function renderSettingsConfigForm() {
  return `
    <section class="settings-config-form">
      <div class="form-grid two-cols">
        <label>
          <span class="form-label">Model base URL</span>
          <input class="field" id="settings-model-base-url" placeholder="https://models.example.com/v1" />
        </label>
        <label>
          <span class="form-label">Model name</span>
          <input class="field" id="settings-model-name" placeholder="bairui-demo-model" />
        </label>
      </div>
      <label>
        <span class="form-label">Model API key</span>
        <input class="field" id="settings-model-api-key" type="password" autocomplete="new-password" placeholder="Save new key; existing key is never shown" />
      </label>
      <div class="form-grid two-cols">
        <label>
          <span class="form-label">Owner token for this browser</span>
          <input class="field" id="settings-owner-token-local" type="password" autocomplete="current-password" placeholder="Stored locally; sent as X-Bairui-Owner-Token" />
        </label>
        <label>
          <span class="form-label">New owner token for server</span>
          <input class="field" id="settings-owner-token-new" type="password" autocomplete="new-password" placeholder="Optional; save new token, never echo" />
        </label>
      </div>
      <div class="form-grid two-cols">
        <label>
          <span class="form-label">Document output directory</span>
          <input class="field" id="settings-document-output-dir" placeholder="data\\documents or C:\\Users\\you\\bairui\\documents" />
        </label>
        <label>
          <span class="form-label">Memory vault directory</span>
          <input class="field" id="settings-memory-vault-dir" placeholder="obsidian-vault or C:\\Users\\you\\bairui\\memory-vault" />
        </label>
      </div>
      <div class="form-grid two-cols">
        <label>
          <span class="form-label">Avatar assets directory</span>
          <input class="field" id="settings-avatar-assets-dir" placeholder="data\\avatars or C:\\Users\\you\\bairui\\avatars" />
        </label>
        <label>
          <span class="form-label">Avatar default model</span>
          <input class="field" id="settings-avatar-default-model" placeholder="bairui.model3.json" />
        </label>
      </div>
      <div class="form-grid two-cols">
        <label>
          <span class="form-label">CodeGraph root</span>
          <input class="field" id="settings-codegraph-root" placeholder="data\\codegraph or C:\\Users\\you\\bairui\\codegraph" />
        </label>
        <label>
          <span class="form-label">PostgreSQL URL</span>
          <input class="field" id="settings-database-url" type="password" autocomplete="new-password" placeholder="Optional; save new URL, never echo" />
        </label>
      </div>
      <label>
        <span class="form-label">Channel targets JSON</span>
        <textarea class="textarea" id="settings-channel-targets-json" rows="4" placeholder='[{"id":"owner","label":"Owner","channel_type":"personal_chat"}]'></textarea>
      </label>
      <label>
        <span class="form-label">Dangerous change confirmation</span>
        <input class="field" id="settings-danger-confirmation" placeholder="Type APPLY BAIRUI CONFIG for owner token, PostgreSQL, memory, channel, or CodeGraph changes" />
      </label>
      <label class="settings-create-dirs">
        <input id="settings-create-dirs" type="checkbox" checked />
        <span>Create missing local directories when possible</span>
      </label>
      <div class="action-row top-gap">
        <button class="ghost-btn" id="settings-save-owner-token-local" type="button">Save Owner Token Locally</button>
        <button class="primary-btn" id="settings-save-config" type="button">Save Configuration</button>
        <span class="muted compact-copy">Saving updates local server config and refreshes diagnostics. Paths must stay inside the bairui workspace, configured data/log/vault roots, or ~/bairui / ~/.bairui. Owner token values never echo and are not included in exports.</span>
      </div>
      ${renderSettingsConfigApplyResult()}
    </section>`;
}

function renderSettingsConfigApplyResult() {
  const result = state.configApplyResult;
  if (!result) return "";
  return `
    <div class="settings-apply-result">
      <div class="agent-meta">
        ${pill(result.status || "saved")}
        <span class="chip">restart_required=${escapeHtml(String(result.restart_required === true))}</span>
        <span class="chip">secret_echo=false</span>
      </div>
      ${result.dangerous_fields?.length ? `<p class="muted compact-copy">dangerous_fields=${escapeHtml(result.dangerous_fields.join(", "))}</p>` : ""}
      ${result.confirmation_phrase ? `<p class="muted compact-copy">confirmation_phrase=${escapeHtml(result.confirmation_phrase)}</p>` : ""}
      ${result.path_scope_policy ? `<p class="muted compact-copy">path_scope=${escapeHtml(result.path_scope_policy)}</p>` : ""}
      <p>${escapeHtml(result.path || result.secret_policy || "Configuration saved.")}</p>
    </div>`;
}

async function saveSettingsConfig() {
  const values = {
    model_base_url: document.getElementById("settings-model-base-url")?.value || "",
    model_api_key: document.getElementById("settings-model-api-key")?.value || "",
    model_name: document.getElementById("settings-model-name")?.value || "",
    owner_token: document.getElementById("settings-owner-token-new")?.value || "",
    document_output_dir: document.getElementById("settings-document-output-dir")?.value || "",
    memory_vault_dir: document.getElementById("settings-memory-vault-dir")?.value || "",
    channel_targets_json: document.getElementById("settings-channel-targets-json")?.value || "",
    avatar_assets_dir: document.getElementById("settings-avatar-assets-dir")?.value || "",
    avatar_default_model: document.getElementById("settings-avatar-default-model")?.value || "",
    codegraph_root: document.getElementById("settings-codegraph-root")?.value || "",
    database_url: document.getElementById("settings-database-url")?.value || "",
  };
  const payload = {
    create_dirs: document.getElementById("settings-create-dirs")?.checked !== false,
    danger_confirmation: document.getElementById("settings-danger-confirmation")?.value || "",
    values: Object.fromEntries(Object.entries(values).filter(([, value]) => String(value || "").trim() !== "")),
  };
  setBusy("config-apply", true);
  state.errors["config-apply"] = "";
  state.errorDetails["config-apply"] = null;
  render();
  try {
    const result = await api.post("/config/apply", payload);
    state.configApplyResult = result?.config_apply || null;
    state.configStatus = result?.config_status ? { config_status: result.config_status } : state.configStatus;
    await refreshScreenData();
  } catch (error) {
    state.configApplyResult = error?.payload?.config_apply || null;
    state.configStatus = error?.payload?.config_status ? { config_status: error.payload.config_status } : state.configStatus;
    const detail = productErrorGuide(error, "config-apply");
    state.errors["config-apply"] = detail.summary;
    state.errorDetails["config-apply"] = detail;
    render();
  } finally {
    setBusy("config-apply", false);
    render();
  }
}

function renderSettingsConfigCenter() {
  const config = state.configStatus?.config_status || {};
  const items = config.items || [];
  if (!items.length) {
    return `<div class="empty-state top-gap">Configuration diagnostics are not loaded yet. Refresh Settings to call /config/status.</div>`;
  }
  return `
    <div class="settings-config-center">
      ${items
        .map(
          (item) => `
            <div class="settings-config-card">
              <div class="agent-meta">
                ${pill(item.status || "missing_config")}
                <span class="chip">${escapeHtml(item.id || "config")}</span>
              </div>
              <strong>${escapeHtml(item.label || item.id)}</strong>
              <p>${escapeHtml(item.detail || "")}</p>
              ${renderSettingsConfigFields(item.fields || {})}
            </div>`,
        )
        .join("")}
    </div>
    <div class="settings-secret-policy">
      ${pill("ready", "no secret echo")}
      <span>${escapeHtml(config.secret_policy || "Secrets are never returned to the frontend.")}</span>
    </div>`;
}

function renderSettingsConfigChecklist() {
  const checklist = state.configStatus?.config_status?.checklist || null;
  if (!checklist) {
    return `<div class="empty-state top-gap">Deployment checklist is not loaded yet. Refresh Settings to generate it.</div>`;
  }
  return `
    <section class="settings-checklist top-gap">
      <div class="conversation-head">
        <div>
          <h3 class="panel-title">Deployment checklist</h3>
          <p class="muted compact-copy">A copyable operator checklist generated from the same safe config diagnostics. It shows required blockers, optional gaps, example env values, and verification commands.</p>
        </div>
        ${pill(checklist.status || "ready")}
      </div>
      <div class="settings-checklist-grid">
        <div>
          <span>Required blockers</span>
          <strong>${escapeHtml((checklist.missing_required || []).join(", ") || "none")}</strong>
        </div>
        <div>
          <span>Optional gaps</span>
          <strong>${escapeHtml((checklist.optional_missing || []).join(", ") || "none")}</strong>
        </div>
        <div>
          <span>Verification</span>
          <strong>${escapeHtml(String((checklist.commands || []).length))} commands</strong>
        </div>
      </div>
      <div class="settings-checklist-text">
        <pre class="mono">${escapeHtml(checklist.markdown || "")}</pre>
      </div>
    </section>`;
}

function renderSettingsConfigFields(fields) {
  const entries = Object.entries(fields || {});
  if (!entries.length) return "";
  return `
    <div class="settings-config-fields">
      ${entries
        .map(([key, value]) => `<div><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></div>`)
        .join("")}
    </div>`;
}

function renderSettingsGateGrid() {
  const license = state.license?.license || {};
  const heartbeat = state.platform?.heartbeat || {};
  const gates = [
    { label: "HTTP health", status: state.health?.status || "missing_config", detail: "GET /health" },
    { label: "Deploy readiness", status: state.ready?.status || "partial", detail: "GET /ready" },
    { label: "License", status: license.status || state.ready?.license || "missing_config", detail: "license status only; secrets never echo" },
    { label: "Platform heartbeat", status: heartbeat.status || state.ready?.platform || "missing_config", detail: "server identity and platform link check" },
  ];
  return `
    <div class="settings-gate-grid">
      ${gates
        .map(
          (gate) => `
            <div>
              <span>${escapeHtml(gate.label)}</span>
              <strong>${pill(gate.status)}</strong>
              <p>${escapeHtml(gate.detail)}</p>
            </div>`,
        )
        .join("")}
    </div>`;
}

function renderSettingsReadinessList(readiness) {
  const blockers = readiness.blockers || [];
  const warnings = readiness.warnings || [];
  if (!blockers.length && !warnings.length) {
    return `<div class="empty-state top-gap">No readiness blockers. Continue with Command, Documents, Reports, and approval checks.</div>`;
  }
  return `
    <div class="settings-readiness-list top-gap">
      ${blockers.map((item) => `<div class="warning-row">${pill("blocked")}<span>${escapeHtml(customerSafeRuntimeText(item))}</span></div>`).join("")}
      ${warnings.map((item) => `<div class="warning-row">${pill("partial", "warning")}<span>${escapeHtml(customerSafeRuntimeText(item))}</span></div>`).join("")}
    </div>`;
}

function renderSettingsRuntimeMatrix() {
  const readinessItems = state.readiness?.runtime_readiness?.items || [];
  const directItems = [
    runtimeRow("memory_substrate", state.runtimeStatus.memory?.memory?.status, state.runtimeStatus.memory?.memory?.detail, true),
    runtimeRow("voice_asr", state.runtimeStatus.voice?.voice_asr?.status, state.runtimeStatus.voice?.voice_asr?.detail, false),
    runtimeRow("document_parser", state.runtimeStatus.document?.document_parse?.status, state.runtimeStatus.document?.document_parse?.detail, false),
    runtimeRow("intelligence_radar", state.runtimeStatus.intel?.intelligence?.status, state.runtimeStatus.intel?.intelligence?.detail, false),
    runtimeRow("simulation_lab", state.runtimeStatus.simulation?.simulation?.status, state.runtimeStatus.simulation?.simulation?.detail, false),
    runtimeRow("web_search", state.runtimeStatus.search?.search?.status, state.runtimeStatus.search?.search?.detail, false),
    runtimeRow("local_index", state.runtimeStatus.index?.index?.status, state.runtimeStatus.index?.index?.detail, false),
    runtimeRow("avatar_state_layer", state.avatarStatus?.avatar?.status, state.avatarStatus?.avatar?.detail, false),
    runtimeRow("code_structure", state.runtimeStatus.codegraph?.codegraph?.status, state.runtimeStatus.codegraph?.codegraph?.detail, false),
  ];
  const rows = readinessItems.length
    ? readinessItems.map((item) => runtimeRow(item.name, item.status, item.detail, item.required_for_usable))
    : directItems;
  return `
    <div class="settings-runtime-matrix">
      ${rows
        .map(
          (item) => `
            <div>
              <div class="agent-meta">
                ${pill(item.status || "missing_config")}
                <span class="chip">${item.required ? "required" : "optional"}</span>
              </div>
              <strong>${escapeHtml(runtimeDisplayName(item.name))}</strong>
              <p>${escapeHtml(customerSafeRuntimeText(item.detail || "Status endpoint connected."))}</p>
            </div>`,
        )
        .join("")}
    </div>`;
}

function renderSettingsConfigBoundary() {
  const model = capabilityByName("model_gateway");
  const database = capabilityByName("postgresql");
  const memoryVault = capabilityByName("obsidian_vault");
  const audit = capabilityByName("audit_api");
  const rows = [
    { label: "Model gateway", status: model?.status || "missing_config", detail: "OpenAI-compatible endpoint configured by environment variables." },
    { label: "Data store", status: database?.status || "partial", detail: "JSONL remains the local product store; database status is reported for migration readiness." },
    { label: "Long-term memory", status: memoryVault?.status || "missing_config", detail: "Memory candidates require owner approval before any durable write." },
    { label: "Audit trail", status: audit?.status || "ready", detail: "Every approval, state change, and generated resource must be traceable." },
    { label: "External actions", status: "approval_required", detail: "Channel planning and review keep will_send=false until a future approved sender exists." },
  ];
  return `
    <div class="settings-boundary-list">
      ${rows
        .map(
          (row) => `
            <div>
              <span>${escapeHtml(row.label)}</span>
              ${pill(row.status)}
              <p>${escapeHtml(row.detail)}</p>
            </div>`,
        )
        .join("")}
    </div>`;
}

function renderSettingsNextActions(readiness) {
  const blockers = readiness.blockers || [];
  const warnings = readiness.warnings || [];
  const action = blockers.length
    ? "Fix required runtime configuration before calling the product usable."
    : warnings.length
      ? "Optional adapters are incomplete; core demo can continue while gaps stay visible."
      : "Run the demo flow, then inspect Events for audit evidence.";
  return `
    <div class="settings-next-actions">
      <div><span>Next diagnostic action</span><strong>${escapeHtml(action)}</strong></div>
      <div><span>Safety invariant</span><strong>no external send, no automatic long-term memory write, no dangerous operation without review</strong></div>
    </div>`;
}

function runtimeRow(name, status, detail, required = false) {
  return { name, status: status || "missing_config", detail: detail || "", required: Boolean(required) };
}

function capabilityByName(name) {
  return (state.capabilities || []).find((item) => item.name === name);
}

function runtimeDisplayName(name = "") {
  const map = {
    everos_memory: "Memory substrate",
    memory_substrate: "Memory substrate",
    funasr_voice_asr: "Voice ASR",
    voice_asr: "Voice ASR",
    mineru_document_parse: "Document parser",
    document_parser: "Document parser",
    trendradar_intelligence: "Intelligence radar",
    intelligence_radar: "Intelligence radar",
    mirofish_simulation: "Simulation lab",
    simulation_lab: "Simulation lab",
    searxng_metasearch: "Web search",
    searxng_search: "Web search",
    web_search: "Web search",
    sonic_local_index: "Local index",
    local_index: "Local index",
    bairui_avatar_runtime: "Avatar state layer",
    avatar_state_layer: "Avatar state layer",
    bairui_codegraph: "Code structure",
    code_structure: "Code structure",
    bairui_agents: "Multi-agent core",
  };
  return map[name] || String(name || "Runtime").replaceAll("_", " ");
}

function customerSafeRuntimeText(text = "") {
  const oldRuntimeName = (...parts) => new RegExp(parts.join(""), "gi");
  const replacements = [
    [oldRuntimeName("Ever", "OS"), "memory substrate"],
    [oldRuntimeName("Fun", "ASR"), "voice ASR"],
    [oldRuntimeName("Miner", "U"), "document parser"],
    [oldRuntimeName("Trend", "Radar"), "intelligence radar"],
    [oldRuntimeName("Miro", "Fish"), "simulation lab"],
    [oldRuntimeName("Sear", "XNG"), "web search"],
    [oldRuntimeName("Sonic"), "local index"],
    [oldRuntimeName("Obsid", "ian"), "memory vault"],
    [oldRuntimeName("Her", "mes"), "bairui"],
    [oldRuntimeName("Bai", "Long", "ma"), "bairui"],
    [oldRuntimeName("白", "龙", "马"), "bairui"],
    [oldRuntimeName("小", "白", "龙"), "bairui"],
  ];
  return replacements.reduce((value, [pattern, replacement]) => value.replace(pattern, replacement), String(text || ""));
}

function renderCodeGraph() {
  setScreenHead("CodeGraph", "source structure index");
  el.actions.innerHTML = `<button class="ghost-btn" id="refresh-codegraph" type="button">Refresh</button>`;
  const selectedRepo = selectedCodegraphRepo();
  const overview = state.codegraphOverview || {};
  const scan = overview.scan || {};
  const files = overview.files || overview.top_files || [];
  const symbols = overview.symbols || overview.top_symbols || [];
  const imports = overview.imports || [];
  const counts = overview.counts || {};
  el.body.innerHTML = `
    <section class="panel pad codegraph-boundary">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Source boundary</h2>
          <p class="muted compact-copy">${escapeHtml(state.codegraph?.codegraph?.memory_boundary || "CodeGraph indexes source structure only; it does not write long-term memory.")}</p>
        </div>
        ${pill(state.codegraph?.codegraph?.status || "missing_config")}
      </div>
      ${renderCountStrip({ repos: state.codegraphRepos.length, files: counts.files ?? files.length, symbols: counts.symbols ?? symbols.length, imports: counts.imports ?? imports.length })}
      ${renderCodeGraphBoundaryMatrix()}
    </section>
    <div class="channels-layout">
      <section class="panel pad">
        <h2 class="panel-title">Repositories</h2>
        <label class="form-label">Active repository</label>
        <select class="field" id="codegraph-repo-select">
          ${
            state.codegraphRepos.length
              ? state.codegraphRepos.map((repo) => `<option value="${escapeHtml(repo.id)}" ${repo.id === selectedRepo?.id ? "selected" : ""}>${escapeHtml(repo.name || repo.root_path || repo.id)}</option>`).join("")
              : `<option value="">No repository</option>`
          }
        </select>
        <h3 class="sub-title">Repos</h3>
        ${
          state.codegraphRepos
            .map((repo) => `<button class="object-card button-card" type="button" data-codegraph-repo="${escapeHtml(repo.id)}">${renderObjectCardInner(repo, ["name", "status", "root_path"])}</button>`)
            .join("") || `<div class="empty-state">No source repository registered yet.</div>`
        }
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Register and scan</h2>
        <label class="form-label">Repository path</label>
        <input class="field" id="codegraph-path" placeholder="C:\\path\\to\\repo" />
        <label class="form-label">Name</label>
        <input class="field" id="codegraph-name" placeholder="bairui-source" />
        <div class="action-row top-gap">
          <button class="primary-btn" id="codegraph-register" type="button">Register</button>
          <button class="ghost-btn" id="codegraph-scan" type="button" ${!selectedRepo ? "disabled" : ""}>Scan Selected</button>
        </div>
        ${renderCodeGraphActionResult()}
        <h3 class="sub-title">Latest scan</h3>
        ${renderCodeGraphOverview(scan, files, symbols, imports)}
        <h3 class="sub-title">Query</h3>
        <input class="field" id="codegraph-query-text" placeholder="function, class, route, file" />
        <button class="ghost-btn top-gap" id="codegraph-query" type="button">Search</button>
        ${renderProductError("codegraph-register")}
        ${renderProductError("codegraph-scan")}
        ${renderProductError("codegraph-query")}
        ${renderProductError("codegraph-impact")}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Results</h2>
        ${state.codegraphQuery ? renderCodeGraphResults(state.codegraphQuery.results || []) : `<div class="empty-state">Search results appear here after scanning.</div>`}
        <h3 class="sub-title">Impact</h3>
        <input class="field" id="codegraph-impact-path" placeholder="src/service/server.py" />
        <button class="ghost-btn top-gap" id="codegraph-impact" type="button">Analyze Impact</button>
        ${state.codegraphImpact ? renderCodeGraphImpact(state.codegraphImpact) : ""}
      </section>
    </div>
    ${state.selectedEntity?.type === "code" ? renderSelectedEntityPanel() : ""}`;
  document.getElementById("refresh-codegraph")?.addEventListener("click", refreshScreenData);
  document.getElementById("codegraph-repo-select")?.addEventListener("change", async (event) => {
    state.selectedCodegraphRepoId = event.target.value;
    persistUiState();
    await loadCodeGraph();
    render();
  });
  el.body.querySelectorAll("[data-codegraph-repo]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedCodegraphRepoId = button.dataset.codegraphRepo;
      persistUiState();
      await loadCodeGraph();
      render();
    });
  });
  document.getElementById("codegraph-register")?.addEventListener("click", async () => {
    const result = await runAction("codegraph-register", () =>
      api.post("/codegraph/repos/register", {
        path: document.getElementById("codegraph-path").value,
        name: document.getElementById("codegraph-name").value,
      }),
    );
    if (result?.codegraph_repo?.id) state.selectedCodegraphRepoId = result.codegraph_repo.id;
    persistUiState();
    state.codegraphActionResult = codegraphActionSummary(result, "/codegraph/repos/register");
    await loadCodeGraph();
    render();
  });
  document.getElementById("codegraph-scan")?.addEventListener("click", async () => {
    const repo = selectedCodegraphRepo();
    const result = await runAction("codegraph-scan", () => api.post("/codegraph/repos/scan", { repo_id: repo?.id || "" }));
    state.codegraphActionResult = codegraphActionSummary(result, "/codegraph/repos/scan");
    await loadCodeGraph();
    render();
  });
  document.getElementById("codegraph-query")?.addEventListener("click", async () => {
    const repo = selectedCodegraphRepo();
    const result = await runAction("codegraph-query", () =>
      api.post("/codegraph/query", {
        query: document.getElementById("codegraph-query-text").value,
        repo_id: repo?.id || "",
        limit: 20,
      }),
    );
    state.codegraphQuery = result?.codegraph_query || state.codegraphQuery;
    state.codegraphActionResult = codegraphActionSummary(result, "/codegraph/query");
    persistUiState();
    render();
  });
  document.getElementById("codegraph-impact")?.addEventListener("click", async () => {
    const repo = selectedCodegraphRepo();
    const result = await runAction("codegraph-impact", () =>
      api.post("/codegraph/impact", {
        path: document.getElementById("codegraph-impact-path").value,
        repo_id: repo?.id || "",
      }),
    );
    state.codegraphImpact = result?.codegraph_impact || state.codegraphImpact;
    state.codegraphActionResult = codegraphActionSummary(result, "/codegraph/impact");
    persistUiState();
    render();
  });
  bindCodeGraphCards();
}

function renderCodeGraphBoundaryMatrix() {
  return `
    <div class="codegraph-boundary-grid">
      <div><span>Read scope</span><strong>source structure only</strong><p>Scans files, symbols, and imports from registered repositories.</p></div>
      <div><span>Memory</span><strong>no auto promotion</strong><p>CodeGraph does not write long-term memory or Obsidian notes.</p></div>
      <div><span>Actions</span><strong>register / scan / query / impact</strong><p>All buttons call explicit backend contracts and return visible status.</p></div>
      <div><span>Use in Command</span><strong>cite result manually</strong><p>Agent workflows can reference findings, but code facts stay separate.</p></div>
    </div>`;
}

function renderCodeGraphActionResult() {
  const result = state.codegraphActionResult;
  if (!result) return "";
  return `
    <div class="codegraph-action-result">
      <div class="agent-meta">
        ${pill(result.status || "completed")}
        <span class="chip mono">${escapeHtml(result.path || "")}</span>
        <span class="chip">memory_write=false</span>
      </div>
      <p>${escapeHtml(result.detail || "CodeGraph action completed.")}</p>
    </div>`;
}

function codegraphActionSummary(result, path) {
  if (!result) return null;
  const payload = result.codegraph_repo || result.codegraph_scan || result.codegraph_query || result.codegraph_impact || {};
  return {
    path,
    status: payload.status || "completed",
    detail: payload.detail || payload.name || payload.root_path || "CodeGraph action completed without long-term memory writes.",
  };
}

function selectedCodegraphRepo() {
  return state.codegraphRepos.find((repo) => repo.id === state.selectedCodegraphRepoId) || state.codegraphRepos[state.codegraphRepos.length - 1] || null;
}

function renderCodeGraphOverview(scan, files, symbols, imports) {
  if (!scan?.id) return `<div class="empty-state">No scan recorded for the selected repository. Register a repo, then scan it before querying.</div>`;
  return `
    <div class="source-chain">
      <div class="source-chain-title">
        <span>Scan ${escapeHtml(shortId(scan.id))}</span>
        ${pill(scan.status || "completed")}
      </div>
      <div class="source-chain-grid">
        <div><span>Files</span><strong>${escapeHtml(scan.file_count ?? files.length)}</strong></div>
        <div><span>Symbols</span><strong>${escapeHtml(scan.symbol_count ?? symbols.length)}</strong></div>
        <div><span>Imports</span><strong>${escapeHtml(scan.import_count ?? imports.length)}</strong></div>
      </div>
    </div>
    <div class="audit-card-list top-gap">
      ${files
        .slice(0, 3)
        .map(
          (item, index) => `
            <button class="object-card button-card" type="button" data-codegraph-overview-file="${index}">
              ${renderObjectCardInner(item, ["relative_path", "language", "symbol_count", "import_count"])}
            </button>`,
        )
        .join("")}
    </div>`;
}

function renderCodeGraphResults(results) {
  if (!results.length) return `<div class="empty-state">No matching files or symbols.</div>`;
  return `
    <div class="audit-card-list">
      ${results
        .map(
          (item, index) => `
            <button class="object-card button-card" type="button" data-codegraph-result="${index}">
              ${renderObjectCardInner(item, ["type", "name", "kind", "path"])}
            </button>`,
        )
        .join("")}
    </div>`;
}

function renderCodeGraphImpact(impact) {
  const files = impact.files || [];
  const symbols = impact.symbols || [];
  return `
    <div class="top-gap">
      ${renderCountStrip({ files: files.length, symbols: symbols.length, imported_by: impact.imported_by?.length || 0 })}
      <div class="audit-card-list top-gap">
        ${files
          .slice(0, 5)
          .map(
            (item, index) => `
              <button class="object-card button-card" type="button" data-codegraph-impact-file="${index}">
                ${renderObjectCardInner(item, ["relative_path", "language", "symbol_count", "import_count"])}
              </button>`,
          )
          .join("")}
        ${symbols
          .slice(0, 5)
          .map(
            (item, index) => `
              <button class="object-card button-card" type="button" data-codegraph-impact-symbol="${index}">
                ${renderObjectCardInner(item, ["name", "kind", "path", "line"])}
              </button>`,
          )
          .join("")}
      </div>
    </div>`;
}

function bindCodeGraphCards() {
  el.body.querySelectorAll("[data-codegraph-overview-file]").forEach((button) => {
    button.addEventListener("click", () => {
      const overviewFiles = state.codegraphOverview?.files || state.codegraphOverview?.top_files || [];
      const item = overviewFiles[Number(button.dataset.codegraphOverviewFile)];
      if (!item) return;
      state.selectedEntity = codeEntity({ type: "file", ...item });
      persistUiState();
      render();
    });
  });
  el.body.querySelectorAll("[data-codegraph-result]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = state.codegraphQuery?.results?.[Number(button.dataset.codegraphResult)];
      if (!item) return;
      state.selectedEntity = codeEntity(item);
      persistUiState();
      render();
    });
  });
  el.body.querySelectorAll("[data-codegraph-impact-file]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = state.codegraphImpact?.files?.[Number(button.dataset.codegraphImpactFile)];
      if (!item) return;
      state.selectedEntity = codeEntity({ type: "file", ...item });
      persistUiState();
      render();
    });
  });
  el.body.querySelectorAll("[data-codegraph-impact-symbol]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = state.codegraphImpact?.symbols?.[Number(button.dataset.codegraphImpactSymbol)];
      if (!item) return;
      state.selectedEntity = codeEntity({ type: "symbol", ...item });
      persistUiState();
      render();
    });
  });
}

function codeEntity(item) {
  const repo = selectedCodegraphRepo();
  const scan = state.codegraphOverview?.scan || {};
  return {
    type: "code",
    title: item.name || item.relative_path || item.path || "Code entity",
    status: "source_ready",
    ref: item.id || item.file_id || item.path || item.relative_path || item.name,
    raw: { ...item, repo_id: item.repo_id || repo?.id || "", repo_name: repo?.name || "", scan_id: item.scan_id || scan.id || "" },
  };
}

function renderEvents() {
  setScreenHead("Events", "audit timeline");
  el.actions.innerHTML = `
    <button class="primary-btn" id="refresh-events" type="button">Refresh Audit</button>
    <button class="ghost-btn" id="export-diagnostics" type="button">Export Diagnostics</button>
    <button class="ghost-btn" id="export-events" type="button">Export Events</button>
    <button class="ghost-btn" id="events-open-settings" type="button">Open Settings</button>
    <button class="ghost-btn" id="events-open-command" type="button">Open Command</button>`;
  const rows = filteredAuditTimeline();
  el.body.innerHTML = `
    <section class="panel pad event-command-center">
      <div class="conversation-head">
        <div>
          <h2 class="panel-title">Audit command center</h2>
          <p class="muted compact-copy">Events combines SSE live messages with /audit records so every generated resource, approval, blocked send, memory review, and runtime action remains traceable.</p>
        </div>
        ${pill(state.events.length ? "ready" : "partial", state.events.length ? "live" : "audit fallback")}
      </div>
      ${renderEventSummary()}
      ${renderEventSafetyBoundary()}
      ${renderProductError("diagnostics-export")}
    </section>
    <div class="event-layout">
      <section class="panel pad">
        <div class="conversation-head">
          <h2 class="panel-title">Timeline</h2>
          ${pill(state.auditFilter || "all")}
        </div>
        ${renderEventFilters()}
        ${renderEventTimeline(rows)}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Selected evidence</h2>
        ${renderEventEvidence()}
        <h3 class="sub-title">Live stream</h3>
        ${renderLiveEventList()}
      </section>
    </div>
    ${state.selectedEntity?.type === "audit" ? renderSelectedEntityPanel() : ""}`;
  document.getElementById("refresh-events")?.addEventListener("click", async () => {
    state.audit = await safe(() => api.get("/audit").then((data) => data.audit || []), state.audit, "audit");
    render();
  });
  document.getElementById("export-events")?.addEventListener("click", exportEventsData);
  document.getElementById("export-diagnostics")?.addEventListener("click", exportDiagnosticBundle);
  document.getElementById("events-open-settings")?.addEventListener("click", async () => {
    state.screen = "settings";
    persistUiState();
    await refreshScreenData();
  });
  document.getElementById("events-open-command")?.addEventListener("click", async () => {
    state.screen = "command";
    persistUiState();
    await refreshScreenData();
  });
  el.body.querySelectorAll("[data-audit-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.auditFilter = button.dataset.auditFilter || "all";
      persistUiState();
      render();
    });
  });
  bindAuditCards();
}

async function exportDiagnosticBundle() {
  const result = await runAction("diagnostics-export", () => api.get("/diagnostics/bundle"), async () => {});
  if (!result?.diagnostic_bundle) return;
  exportConsoleData("diagnostics", {
    diagnostic_bundle: result.diagnostic_bundle,
    note: "Redacted support bundle. Secrets are excluded; safety flags remain visible.",
  });
}

function exportEventsData() {
  exportConsoleData("events", {
    audit_filter: state.auditFilter || "all",
    audit: state.audit || [],
    filtered_audit: filteredAuditTimeline(),
    live_events: state.events || [],
    selected_audit: state.selectedEntity?.type === "audit" ? state.selectedEntity.raw || state.selectedEntity : null,
    note: "Event export combines durable audit records and this browser session's live SSE messages.",
  });
}

function renderEventSummary() {
  const counts = eventSummaryCounts();
  return renderCountStrip({
    audit: state.audit.length,
    live: state.events.length,
    approvals: counts.approvals,
    resources: counts.resources,
    blocked: counts.blocked,
    high_risk: counts.highRisk,
  });
}

function renderEventSafetyBoundary() {
  return `
    <div class="event-safety-grid">
      <div><span>External send</span><strong>review only</strong><p>Channel events must keep will_send=false until a future approved sender exists.</p></div>
      <div><span>Long-term memory</span><strong>owner approval</strong><p>Memory candidates and reviews stay visible before any durable memory write.</p></div>
      <div><span>Resource chain</span><strong>audit linked</strong><p>Jobs, reports, channels, documents, code, and avatar state changes carry resource references.</p></div>
      <div><span>Failure handling</span><strong>no fake success</strong><p>Blocked or missing_config events remain visible so the operator knows the next repair step.</p></div>
    </div>`;
}

function renderEventFilters() {
  const filters = [
    ["all", "All"],
    ["approval", "Approvals"],
    ["resource", "Resources"],
    ["memory", "Memory"],
    ["channel", "Channels"],
    ["system", "System"],
    ["blocked", "Blocked"],
  ];
  return `
    <div class="event-filter-row">
      ${filters.map(([id, label]) => `<button class="ghost-btn mini ${state.auditFilter === id ? "active" : ""}" type="button" data-audit-filter="${id}">${escapeHtml(label)}</button>`).join("")}
    </div>`;
}

function renderEventTimeline(rows) {
  if (!rows.length) return `<div class="empty-state top-gap">No audit evidence for this filter yet. Run Demo Flow, create a command session, or review a channel draft.</div>`;
  return `
    <div class="event-timeline top-gap">
      ${rows
        .map(
          (event) => `
            <button class="event-row button-card" type="button" data-audit-open="${escapeHtml(event.id)}">
              <span class="event-rail-dot"></span>
              <div class="event-row-main">
                <div class="agent-meta">
                  ${pill(event.status, event.label)}
                  <span class="chip">${escapeHtml(event.resource_type || "runtime")}</span>
                  <span class="chip mono">${escapeHtml(shortId(event.resource_ref || event.id))}</span>
                </div>
                <strong>${escapeHtml(event.action || event.type || "audit.event")}</strong>
                <p>${escapeHtml(event.detail)}</p>
              </div>
              <time>${escapeHtml(formatEventTime(event.created_at || event.ts))}</time>
            </button>`,
        )
        .join("")}
    </div>`;
}

function renderEventEvidence() {
  const selected = state.selectedEntity?.type === "audit" ? state.selectedEntity.raw : latestAuditEvent();
  if (!selected) return `<div class="empty-state">Select an event to inspect payload, resource reference, and safety flags.</div>`;
  const payload = selected.payload || {};
  const safety = {
    will_send: payload.will_send === true ? "true" : "false",
    will_write_long_term_memory: payload.will_write_long_term_memory === true ? "true" : "false",
    approval_required: eventNeedsApproval(selected) ? "true" : "false",
  };
  return `
    <div class="event-evidence-card">
      <div class="agent-meta">
        ${pill(eventStatus(selected).status, eventStatus(selected).label)}
        <span class="chip">${escapeHtml(selected.resource_type || "runtime")}</span>
        <span class="chip mono">${escapeHtml(shortId(selected.resource_ref || selected.id))}</span>
      </div>
      <h3>${escapeHtml(selected.action || "audit.event")}</h3>
      ${renderObjectCardInner(safety, ["will_send", "will_write_long_term_memory", "approval_required"])}
      <pre class="mono muted code-block top-gap">${escapeHtml(JSON.stringify(payload, null, 2))}</pre>
    </div>`;
}

function renderLiveEventList() {
  const live = state.events.slice(-8).reverse();
  if (!live.length) return `<div class="empty-state compact">SSE stream has not received live messages in this browser session. /audit remains the durable source.</div>`;
  return `
    <div class="live-event-list">
      ${live
        .map(
          (event) => `
            <div>
              ${pill(event.type || "event")}
              <span>${escapeHtml(event.data?.action || event.type || "runtime event")}</span>
            </div>`,
        )
        .join("")}
    </div>`;
}

function filteredAuditTimeline() {
  return state.audit
    .slice()
    .reverse()
    .map(normalizeAuditEvent)
    .filter((event) => eventMatchesFilter(event, state.auditFilter));
}

function normalizeAuditEvent(event) {
  const status = eventStatus(event);
  return {
    ...event,
    status: status.status,
    label: status.label,
    detail: eventDetail(event),
  };
}

function eventSummaryCounts() {
  return (state.audit || []).reduce(
    (counts, event) => {
      if (eventNeedsApproval(event)) counts.approvals += 1;
      if (["job", "report", "memory", "channel", "document", "codegraph", "avatar"].includes(event.resource_type)) counts.resources += 1;
      if (eventStatus(event).status === "blocked") counts.blocked += 1;
      if (event.risk_level === "high") counts.highRisk += 1;
      return counts;
    },
    { approvals: 0, resources: 0, blocked: 0, highRisk: 0 },
  );
}

function eventStatus(event) {
  const action = String(event?.action || "");
  const payload = event?.payload || {};
  if (action.includes("blocked") || payload.status === "blocked" || payload.status === "failed") return { status: "blocked", label: "blocked" };
  if (eventNeedsApproval(event)) return { status: "approval_required", label: "review" };
  if (action.includes("reviewed") || action.includes("created") || action.includes("finished") || action.includes("promoted")) return { status: "ready", label: "recorded" };
  return { status: event?.risk_level === "high" ? "approval_required" : "partial", label: event?.risk_level || "trace" };
}

function eventNeedsApproval(event) {
  const action = String(event?.action || "");
  const payload = event?.payload || {};
  return action.includes("approval") || action.includes("send_planned") || payload.will_send === false || payload.will_write_long_term_memory === false || event?.risk_level === "high";
}

function eventMatchesFilter(event, filter = "all") {
  if (filter === "all") return true;
  const action = String(event.action || "");
  const resource = String(event.resource_type || "");
  if (filter === "approval") return eventNeedsApproval(event);
  if (filter === "resource") return ["job", "report", "memory", "channel", "document", "codegraph", "avatar"].includes(resource);
  if (filter === "blocked") return event.status === "blocked";
  if (filter === "system") return ["runtime", "database", "avatar"].includes(resource) || action.includes("system") || action.includes("database");
  return resource.includes(filter) || action.includes(filter);
}

function eventDetail(event) {
  const payload = event?.payload || {};
  return firstNonEmpty(
    payload.title,
    payload.summary,
    payload.reason,
    payload.status,
    payload.note,
    event.resource_ref ? `${event.resource_type || "resource"} ${event.resource_ref}` : "",
    "Audit evidence recorded.",
  );
}

function formatEventTime(value) {
  if (!value) return "time pending";
  return String(value).replace("T", " ").replace("Z", "");
}

function latestAuditEvent() {
  return state.audit[state.audit.length - 1] || null;
}

function renderRuntimeDiagnostics() {
  const readiness = state.readiness?.runtime_readiness || {};
  const items = readiness.items || [];
  const blockers = items.filter((item) => ["blocked", "missing_config", "failed"].includes(item.status));
  const warnings = items.filter((item) => ["partial", "needs_review", "approval_required"].includes(item.status));
  if (!blockers.length && !warnings.length) return `<div class="empty-state compact">No runtime blockers detected.</div>`;
  return `
    <div class="diagnostic-stack">
      ${blockers.slice(0, 4).map((item) => `<div class="warning-row">${pill(item.status || "blocked")}<span>${escapeHtml(item.name || item.id || item.detail || "runtime blocker")}</span></div>`).join("")}
      ${warnings.slice(0, 3).map((item) => `<div class="warning-row">${pill(item.status || "partial", "warning")}<span>${escapeHtml(item.name || item.id || item.detail || "runtime warning")}</span></div>`).join("")}
    </div>`;
}

function renderAuditCards(events) {
  if (!events.length) return `<div class="empty-state">No audit events yet.</div>`;
  return `
    <div class="audit-card-list">
      ${events
        .map(
          (event) => `
            <button class="object-card button-card audit-card" type="button" data-audit-open="${escapeHtml(event.id)}">
              <div><span>action</span><strong>${escapeHtml(event.action || "audit.event")}</strong></div>
              <div><span>resource</span><strong>${escapeHtml(event.resource_type || "-")} / ${escapeHtml(shortId(event.resource_ref || ""))}</strong></div>
              <div><span>risk</span><strong>${escapeHtml(event.risk_level || "low")}</strong></div>
            </button>`,
        )
        .join("")}
    </div>`;
}

function bindAuditCards(root = el.body) {
  root.querySelectorAll("[data-audit-open]").forEach((button) => {
    button.addEventListener("click", () => {
      const event = state.audit.find((item) => String(item.id) === String(button.dataset.auditOpen));
      if (!event) return;
      state.selectedEntity = { type: "audit", title: event.action, status: event.risk_level || "low", ref: event.id, raw: event };
      persistUiState();
      render();
    });
  });
}

function renderTable(columns, rows) {
  if (!rows.length) return `<div class="empty-state">No records yet. The section is connected and waiting for data.</div>`;
  return `
    <div class="table-wrap">
      <table class="table">
        <thead><tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
        <tbody>
          ${rows
            .map((row) => `<tr>${columns.map((column) => `<td>${escapeHtml(row[column] ?? "")}</td>`).join("")}</tr>`)
            .join("")}
        </tbody>
      </table>
    </div>`;
}

function renderDrawer() {
  el.drawerContent.innerHTML = `
    <section class="panel pad">
      <h2 class="panel-title">Current screen</h2>
      <p class="muted">${escapeHtml(state.screen)}</p>
    </section>
    <section class="panel pad">
      <h2 class="panel-title">Safety</h2>
      <p class="muted">Actions preserve bairui-only public branding, owner review, blocked states, and no external send success claims.</p>
    </section>
    <section class="panel pad">
      <h2 class="panel-title">Selected</h2>
      <p class="muted mono">${escapeHtml(state.selectedIngestId || state.selectedEntity?.title || "none")}</p>
    </section>`;
}

function progressBar(value) {
  const percent = Math.max(0, Math.min(100, Number(value) || 0));
  return `<div class="progress"><span style="width:${percent}%"></span></div>`;
}

function stageCard(label, status) {
  return `<div class="stage-card"><span>${escapeHtml(label)}</span>${pill(status || "pending")}</div>`;
}

function renderWarnings(blockers = [], warnings = []) {
  if (!blockers.length && !warnings.length) return `<div class="empty-state compact">No blockers or warnings.</div>`;
  return `<div class="grid">${blockers.map((item) => `<div class="warning-row">${pill("blocked")}<span>${escapeHtml(item)}</span></div>`).join("")}${warnings.map((item) => `<div class="warning-row">${pill("partial", "warning")}<span>${escapeHtml(item)}</span></div>`).join("")}</div>`;
}

function renderActionList(actions) {
  if (!actions.length) return `<div class="empty-state compact">No immediate next action.</div>`;
  return `<div class="step-list">${actions
    .map(
      (action) => `
        <div class="step-item action-step">
          <div class="step-title">
            <span>${escapeHtml(action.label || action.command || action.id)}</span>
            ${pill(action.command === "done" ? "ready" : "partial", action.command || "action")}
          </div>
          <button class="ghost-btn mini" type="button" data-document-command="${escapeHtml(action.command || "")}" ${!action.command ? "disabled" : ""}>
            ${escapeHtml(action.command === "review-memory-candidate" ? "Open Review" : action.command === "done" ? "Open Reports" : "Run This Step")}
          </button>
        </div>`,
    )
    .join("")}</div>`;
}

function renderCountStrip(counts) {
  const entries = Object.entries(counts || {});
  if (!entries.length) return `<div class="empty-state compact">No counts available.</div>`;
  return `<div class="count-strip">${entries.map(([key, value]) => `<div><strong>${escapeHtml(value)}</strong><span>${escapeHtml(key)}</span></div>`).join("")}</div>`;
}

function renderObjectCard(item, keys) {
  return `<article class="object-card">${renderObjectCardInner(item, keys)}</article>`;
}

function renderObjectCardInner(item, keys) {
  return keys.map((key) => `<div><span>${escapeHtml(key)}</span><strong>${escapeHtml(item?.[key] ?? "")}</strong></div>`).join("");
}

function render() {
  renderRail();
  renderTopbar();
  renderDrawer();
  const renderer = {
    activation: renderActivation,
    dashboard: renderDashboard,
    command: renderCommand,
    documents: renderDocuments,
    memory: renderMemory,
    graph: renderGraph,
    entity: renderEntity,
    reports: renderReports,
    intel: renderIntel,
    channels: renderChannels,
    avatar: renderAvatar,
    codegraph: renderCodeGraph,
    settings: renderSettings,
    events: renderEvents,
  }[state.screen];
  renderer?.();
}

async function safe(fn, fallback, key = "") {
  try {
    return await fn();
  } catch (error) {
    console.warn(error);
    if (key) state.errors[key] = error.message;
    return fallback;
  }
}

async function refresh() {
  const [contract, health, ready, readiness, configStatus, capabilities, jobs, audit, avatarStatus, avatarManifest, platform, license] = await Promise.all([
    safe(() => api.get("/frontend/contract").then((data) => data.frontend_contract), state.contract),
    safe(() => api.get("/health"), state.health),
    safe(() => api.get("/ready"), state.ready),
    safe(() => api.get("/runtime/readiness"), state.readiness),
    safe(() => api.get("/config/status"), state.configStatus),
    safe(() => api.get("/capabilities").then((data) => data.capabilities || []), state.capabilities),
    safe(() => api.get("/jobs").then((data) => data.jobs || []), state.jobs),
    safe(() => api.get("/audit").then((data) => data.audit || []), state.audit),
    safe(() => api.get("/avatar/status"), state.avatarStatus),
    safe(() => api.get("/avatar/manifest"), state.avatarManifest),
    safe(() => api.get("/platform/heartbeat"), state.platform),
    safe(() => api.get("/license"), state.license),
  ]);
  Object.assign(state, { contract, health, ready, readiness, configStatus, capabilities, jobs, audit, avatarStatus, avatarManifest, platform, license });
  await refreshScreenData();
  render();
}

async function refreshScreenData() {
  if (state.screen === "activation") {
    await Promise.all([loadRuntimeStatus(), loadDocuments(), loadMemory(), loadReports(), loadChannels(), loadCodeGraph()]);
  }
  if (["documents", "graph", "entity"].includes(state.screen)) await loadDocuments();
  if (["memory", "graph", "entity"].includes(state.screen)) await loadMemory();
  if (["reports", "graph", "entity"].includes(state.screen)) await loadReports();
  if (["channels", "entity"].includes(state.screen)) await loadChannels();
  if (["settings", "intel", "codegraph"].includes(state.screen)) await loadRuntimeStatus();
  if (state.screen === "dashboard") await loadDashboard();
  if (state.screen === "codegraph") await loadCodeGraph();
  if (state.screen === "command") await loadAgents();
  if (state.screen === "events") {
    state.audit = await safe(() => api.get("/audit").then((data) => data.audit || []), state.audit, "audit");
  }
  render();
}

async function loadDashboard() {
  const [readiness, capabilities, jobs, audit, reports, memoryCandidates, channelApprovals] = await Promise.all([
    safe(() => api.get("/runtime/readiness"), state.readiness, "dashboard-readiness"),
    safe(() => api.get("/capabilities").then((data) => data.capabilities || []), state.capabilities, "dashboard-capabilities"),
    safe(() => api.get("/jobs").then((data) => data.jobs || []), state.jobs, "dashboard-jobs"),
    safe(() => api.get("/audit").then((data) => data.audit || []), state.audit, "dashboard-audit"),
    safe(() => api.get("/reports").then((data) => data.reports || []), state.reports, "dashboard-reports"),
    safe(() => api.get("/document/memory-candidates").then((data) => data.document_memory_candidates || []), state.memoryCandidates, "dashboard-memory"),
    safe(() => api.get("/channels/approvals").then((data) => data.channel_approvals || []), state.channelApprovals, "dashboard-channels"),
  ]);
  Object.assign(state, { readiness, capabilities, jobs, audit, reports, memoryCandidates, channelApprovals });
}

async function loadDocuments() {
  const list = await safe(() => api.post("/document/parse/session-list", { limit: 50 }).then((data) => data.document_ingest_sessions), null, "documents");
  state.documentSessions = list?.sessions || [];
  if (state.selectedIngestId && !state.documentSessions.some((session) => session.ingest_id === state.selectedIngestId)) {
    state.selectedIngestId = "";
  }
  if (!state.selectedIngestId && state.documentSessions[0]) state.selectedIngestId = state.documentSessions[0].ingest_id;
  await loadDocumentSession();
}

async function loadDocumentSession() {
  if (!state.selectedIngestId) {
    state.documentSession = null;
    return;
  }
  state.documentSession = await safe(
    () => api.post("/document/parse/session-summary", { ingest_id: state.selectedIngestId }).then((data) => data.document_ingest_session),
    state.documentSession,
    "document-session",
  );
}

async function loadMemory() {
  const [queue, candidates, reviews] = await Promise.all([
    safe(() => api.post("/document/parse/memory-review-pending", { ingest_id: state.selectedIngestId || "" }).then((data) => data.document_memory_review_queue), state.memoryQueue, "memory-queue"),
    safe(() => api.get("/document/memory-candidates").then((data) => data.document_memory_candidates || []), state.memoryCandidates, "memory-candidates"),
    safe(() => api.get("/document/memory-reviews").then((data) => data.document_memory_reviews || []), state.memoryReviews, "memory-reviews"),
  ]);
  state.memoryQueue = queue;
  state.memoryCandidates = candidates || [];
  state.memoryReviews = reviews || [];
}

async function loadReports() {
  const [reports, refs] = await Promise.all([
    safe(() => api.get("/reports").then((data) => data.reports || []), state.reports, "reports"),
    safe(() => api.get("/source-refs").then((data) => data.source_refs || []), state.sourceRefs, "source-refs"),
  ]);
  state.reports = reports || [];
  state.sourceRefs = refs || [];
}

async function loadChannels() {
  const [channels, targets, diagnostics, approvals, reviews] = await Promise.all([
    safe(() => api.get("/channels/status"), state.channels, "channels-status"),
    safe(() => api.get("/channels/targets").then((data) => data.channel_targets || []), state.channelTargets, "channels-targets"),
    safe(() => api.get("/channels/diagnostics").then((data) => data.channel_diagnostics || []), state.channelDiagnostics, "channels-diagnostics"),
    safe(() => api.get("/channels/approvals").then((data) => data.channel_approvals || []), state.channelApprovals, "channels-approvals"),
    safe(() => api.get("/channels/approvals/reviews").then((data) => data.channel_approval_reviews || []), state.channelApprovalReviews, "channels-reviews"),
  ]);
  state.channels = channels;
  state.channelTargets = targets || [];
  state.channelDiagnostics = diagnostics || [];
  state.channelApprovals = approvals || [];
  state.channelApprovalReviews = reviews || [];
}

async function loadAgents() {
  const [agents, sessions] = await Promise.all([
    safe(() => api.get("/agents").then((data) => data.agents || []), state.agents, "agents"),
    safe(() => api.get("/agents/sessions").then((data) => data.agent_sessions || []), state.agentSessions, "agent-sessions"),
  ]);
  state.agents = agents || [];
  state.agentSessions = sessions || [];
  if (state.selectedAgentSessionId && !state.agentSessions.some((item) => item.id === state.selectedAgentSessionId)) {
    state.selectedAgentSessionId = "";
  }
  if (!state.selectedAgentSessionId && state.agentSessions.length) state.selectedAgentSessionId = state.agentSessions.at(-1).id;
  const selected = state.agentSessions.find((item) => item.id === state.selectedAgentSessionId);
  if (!state.selectedAgentIds.length) state.selectedAgentIds = selected?.agent_ids?.length ? [...selected.agent_ids] : state.agents.map((agent) => agent.id);
  if (state.selectedAgentSessionId) {
    const page = await safe(
      () =>
        api
          .post(`/agents/session/${state.selectedAgentSessionId}/events`, {
            limit: state.agentEventLimit,
            offset: state.agentEventOffset,
          })
          .then((data) => data.agent_events_page),
      state.agentEventsPage,
      "agent-events",
    );
    state.agentEventsPage = page;
    state.agentEvents = page?.events || [];
    state.agentPromotions = await safe(
      () => api.get(`/agents/session/${state.selectedAgentSessionId}/promotions`).then((data) => data.agent_promotions || []),
      state.agentPromotions,
      "agent-promotions",
    );
  } else {
    state.agentPromotions = [];
  }
}

async function ensureAgentSession() {
  if (state.selectedAgentSessionId) return state.selectedAgentSessionId;
  const agents = state.agents.length ? state.agents : await safe(() => api.get("/agents").then((data) => data.agents || []), [], "agents");
  state.agents = agents || state.agents;
  const agentIds = state.selectedAgentIds.length ? state.selectedAgentIds : state.agents.map((agent) => agent.id);
  const result = await runAction("agent-session", () =>
    api.post("/agents/session", {
      title: "bairui command session",
      agent_ids: agentIds,
    }),
  );
  state.selectedAgentSessionId = result?.agent_session?.id || "";
  state.selectedAgentIds = result?.agent_session?.agent_ids || state.selectedAgentIds;
  persistUiState();
  return state.selectedAgentSessionId;
}

async function submitAgentCommand(promptText, options = {}) {
  const text = String(promptText || "").trim();
  if (!text) return;
  const sessionId = await ensureAgentSession();
  if (!sessionId) return;
  const mode = options.mode || state.agentComposerMode || "round";
  if (mode === "message") {
    await runAction("agent-message", () => api.post(`/agents/session/${sessionId}/message`, { content: text }), loadAgents);
  } else {
    await runAction("agent-round", () => api.post(`/agents/session/${sessionId}/round`, { prompt: text }));
    state.agentEventOffset = 0;
    await loadAgents();
  }
  el.commandInput.value = "";
  render();
}

async function loadRuntimeStatus() {
  const [configStatus, memory, voice, document, intel, simulation, search, index, codegraph] = await Promise.all([
    safe(() => api.get("/config/status"), state.configStatus, "config-status"),
    safe(() => api.get("/memory/status"), state.runtimeStatus.memory, "memory-status"),
    safe(() => api.get("/voice/asr/status"), state.runtimeStatus.voice, "voice-status"),
    safe(() => api.get("/document/parse/status"), state.runtimeStatus.document, "document-status"),
    safe(() => api.get("/intel/status"), state.runtimeStatus.intel, "intel-status"),
    safe(() => api.get("/simulation/status"), state.runtimeStatus.simulation, "simulation-status"),
    safe(() => api.get("/search/status"), state.runtimeStatus.search, "search-status"),
    safe(() => api.get("/index/status"), state.runtimeStatus.index, "index-status"),
    safe(() => api.get("/codegraph/status"), state.runtimeStatus.codegraph, "codegraph-status"),
  ]);
  state.configStatus = configStatus;
  state.runtimeStatus = { memory, voice, document, intel, simulation, search, index, codegraph };
}

async function loadCodeGraph() {
  const [codegraph, repos, overview] = await Promise.all([
    safe(() => api.get("/codegraph/status"), state.codegraph, "codegraph-status"),
    safe(() => api.get("/codegraph/repos").then((data) => data.codegraph_repos || []), state.codegraphRepos, "codegraph-repos"),
    safe(() => {
      const repoId = state.selectedCodegraphRepoId ? `?repo_id=${encodeURIComponent(state.selectedCodegraphRepoId)}` : "";
      return api.get(`/codegraph/overview${repoId}`).then((data) => data.codegraph || null);
    }, state.codegraphOverview, "codegraph-overview"),
  ]);
  state.codegraph = codegraph;
  state.codegraphRepos = repos || [];
  if (state.selectedCodegraphRepoId && !state.codegraphRepos.some((repo) => repo.id === state.selectedCodegraphRepoId)) {
    state.selectedCodegraphRepoId = "";
  }
  if (!state.selectedCodegraphRepoId && state.codegraphRepos.length) {
    state.selectedCodegraphRepoId = state.codegraphRepos[state.codegraphRepos.length - 1].id;
  }
  state.codegraphOverview = overview;
}

function connectEvents() {
  try {
    const events = new EventSource("/events");
    events.onmessage = (message) => {
      try {
        const parsed = JSON.parse(message.data);
        state.events = [...state.events.slice(-30), parsed];
        renderTopbar();
        if (state.screen === "events") renderEvents();
      } catch (error) {
        console.warn(error);
      }
    };
    events.onerror = () => {
      events.close();
    };
  } catch (error) {
    console.warn(error);
  }
}

el.commandSend.addEventListener("click", async () => {
  const promptText = el.commandInput.value.trim();
  if (!promptText) return;
  if (state.screen === "command") {
    await submitAgentCommand(promptText);
  } else {
    await runAction("command", () => api.post("/jobs", { title: "Command request", prompt: promptText, route: "general" }));
    el.commandInput.value = "";
  }
});

el.commandInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    el.commandSend.click();
  }
});

el.drawerClose.addEventListener("click", () => {
  el.drawer.style.display = "none";
});

restoreUiState();
renderRail();
renderTopbar();
render();
refresh();
connectEvents();
