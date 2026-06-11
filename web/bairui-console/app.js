const api = {
  async get(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) throw new Error(`${path} ${response.status}`);
    return response.json();
  },
  async post(path, payload = {}) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.message || `${path} ${response.status}`);
    return data;
  },
};

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
  capabilities: [],
  jobs: [],
  audit: [],
  events: [],
  agents: [],
  agentSessions: [],
  selectedAgentSessionId: "",
  selectedAgentIds: [],
  agentEvents: [],
  promotionResults: {},
  avatarStatus: null,
  avatarManifest: null,
  runtimeStatus: {},
  documentSessions: [],
  selectedIngestId: "",
  documentSession: null,
  memoryQueue: null,
  memoryCandidates: [],
  memoryReviews: [],
  reports: [],
  sourceRefs: [],
  channels: null,
  channelTargets: [],
  channelDiagnostics: [],
  channelApprovals: [],
  codegraph: null,
  codegraphRepos: [],
  codegraphQuery: null,
  codegraphImpact: null,
  demoSeed: null,
  selectedEntity: null,
  selectedStep: "brand_lock",
  loading: new Set(),
  errors: {},
};

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

function setBusy(key, active) {
  if (active) state.loading.add(key);
  else state.loading.delete(key);
}

async function runAction(key, fn, after = refreshScreenData) {
  setBusy(key, true);
  state.errors[key] = "";
  render();
  try {
    const result = await fn();
    await after();
    return result;
  } catch (error) {
    state.errors[key] = error.message;
    render();
    return null;
  } finally {
    setBusy(key, false);
    render();
  }
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
      <section class="panel system-core-stage">
        <div class="system-core" aria-hidden="true"></div>
        <div class="core-label">
          <strong>bairui core</strong>
          <span>${escapeHtml(state.readiness?.runtime_readiness?.summary || "diagnostic startup")}</span>
        </div>
      </section>
      <section class="panel pad">
        <h2 class="panel-title">${escapeHtml(selected?.title || "Activation detail")}</h2>
        <div class="agent-meta">${pill(selectedState)}<span class="chip">${escapeHtml(selected?.blocking ? "blocking" : "guided")}</span></div>
        <p class="muted">${escapeHtml(selected?.complete_when || "Load backend contract to inspect activation.")}</p>
        ${renderActivationDiagnostics(selected, selectedState)}
        <div class="grid">
          ${(selected?.read || []).map((path) => `<span class="status-pill">${escapeHtml(path)}</span>`).join("")}
        </div>
        ${selected?.action ? `<div class="activation-action-card"><span>Action</span><strong>${escapeHtml(selected.action.method || "POST")} ${escapeHtml(selected.action.path || "")}</strong><p>${escapeHtml(selected.action.id || "")}</p></div>` : ""}
        <hr class="rule">
        ${renderReadinessBlockers()}
      </section>
    </div>`;
  el.body.querySelectorAll("[data-step]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedStep = button.dataset.step;
      renderActivation();
    });
  });
  document.getElementById("refresh-activation")?.addEventListener("click", refresh);
  document.getElementById("open-activation-target")?.addEventListener("click", async () => {
    if (!targetScreen) return;
    state.screen = targetScreen;
    render();
    await refreshScreenData();
  });
}

function inferStepState(step) {
  if (!state.readiness) return "partial";
  const capabilities = Object.fromEntries(state.capabilities.map((item) => [item.name, item.status]));
  const runtimeItems = Object.fromEntries((state.readiness.runtime_readiness?.items || []).map((item) => [item.name, item.status]));
  if (step?.id === "brand_lock") return state.contract?.brand?.public_brand === "bairui" ? "ready" : "blocked";
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

function lookupStatus(map, fragment) {
  const key = Object.keys(map || {}).find((name) => name.includes(fragment));
  return key ? map[key] : "";
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

function activationNextAction(stepId, stepState) {
  if (stepState === "blocked" || stepState === "missing_config") {
    return { title: "Fix missing configuration", detail: "Open the linked workbench and complete the visible missing_config items." };
  }
  if (stepId === "memory_review") return { title: "Review candidates", detail: "Approve or reject pending memory candidates before promoting long-term memory." };
  if (stepId === "channels") return { title: "Check approvals", detail: "Create or review outbound drafts; backend still records will_send=false." };
  if (stepId === "codegraph") return { title: "Register source", detail: "Register a source repository, scan it, then query source structure separately from memory." };
  if (stepId === "avatar") return { title: "Probe avatar state", detail: "Use the Avatar screen to switch idle/thinking states and confirm the state layer." };
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
    <button class="ghost-btn" id="create-sample-job" type="button">Create Job</button>`;
  const demo = state.demoSeed?.demo_seed;
  el.body.innerHTML = `
    <div class="grid three">
      <section class="panel pad">
        <h2 class="panel-title">Readiness</h2>
        ${pill(state.readiness?.runtime_readiness?.status || "partial")}
        <p class="muted">${escapeHtml(state.readiness?.runtime_readiness?.summary || "Runtime readiness pending.")}</p>
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
          <p class="muted compact-copy">Create safe local data for product demos: task, draft report, memory review item, and channel approval draft.</p>
        </div>
        ${pill(demo?.status || "ready", demo?.status || "not seeded")}
      </div>
      ${renderDemoSeedState(demo)}
      ${state.errors["demo-seed"] ? `<p class="error-text">${escapeHtml(state.errors["demo-seed"])}</p>` : ""}
    </section>
    <div class="grid two top-gap">
      <section class="panel pad">
        <h2 class="panel-title">Jobs</h2>
        ${renderTable(["title", "route", "status"], state.jobs.map((job) => ({ title: job.title, route: job.route, status: job.status })))}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Audit</h2>
        ${renderTable(["action", "resource_type", "risk_level"], state.audit.slice(-8).reverse())}
      </section>
    </div>
    ${state.selectedEntity?.type === "job" ? renderSelectedEntityPanel() : ""}`;
  bindEntityActions();
  document.getElementById("seed-demo-data")?.addEventListener("click", async () => {
    const result = await runAction("demo-seed", () => api.post("/demo/seed", { force: false }), refresh);
    state.demoSeed = result || state.demoSeed;
    if (result?.demo_seed?.status === "completed") {
      const job = result.demo_seed.job;
      state.selectedEntity = job ? { type: "job", title: job.title, status: job.status, ref: job.id, raw: job } : state.selectedEntity;
    }
    await refresh();
  });
  document.getElementById("create-sample-job")?.addEventListener("click", async () => {
    await runAction("job", () => api.post("/jobs", { title: "Frontend console check", prompt: "Inspect bairui dashboard state", route: "operations" }));
  });
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
        <div class="conversation">
          ${
            state.agentEvents.length
              ? state.agentEvents.map((event) => renderMessage(event)).join("")
              : `<div class="empty-state">Create a session and run a round to record governed agent events.</div>`
          }
        </div>
      </section>
    </div>`;
  document.getElementById("refresh-agents")?.addEventListener("click", refreshScreenData);
  el.body.querySelectorAll("[data-agent-toggle]").forEach((input) => {
    input.addEventListener("change", () => {
      const next = new Set(state.selectedAgentIds);
      if (input.checked) next.add(input.dataset.agentToggle);
      else next.delete(input.dataset.agentToggle);
      state.selectedAgentIds = [...next];
      renderCommand();
    });
  });
  el.body.querySelectorAll("[data-agent-session]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedAgentSessionId = button.dataset.agentSession;
      const selected = state.agentSessions.find((item) => item.id === state.selectedAgentSessionId);
      state.selectedAgentIds = selected?.agent_ids?.length ? [...selected.agent_ids] : state.selectedAgentIds;
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
  el.body.querySelectorAll("[data-open-promotion]").forEach((button) => {
    button.addEventListener("click", async () => {
      await openPromotionResource(button.dataset.openPromotion, button.dataset.resourceId);
    });
  });
  document.getElementById("create-agent-session")?.addEventListener("click", async () => {
    const result = await runAction("agent-session", () =>
      api.post("/agents/session", {
        title: "bairui command session",
        agent_ids: state.selectedAgentIds.length ? state.selectedAgentIds : agents.map((agent) => agent.id),
      }),
    );
    state.selectedAgentSessionId = result?.agent_session?.id || state.selectedAgentSessionId;
    state.selectedAgentIds = result?.agent_session?.agent_ids || state.selectedAgentIds;
    await loadAgents();
    render();
  });
  document.getElementById("run-agent-round")?.addEventListener("click", async () => {
    const promptText = el.commandInput.value.trim() || "Inspect current bairui workspace state.";
    await runAction("agent-round", () => api.post(`/agents/session/${state.selectedAgentSessionId}/round`, { prompt: promptText }));
    await loadAgents();
    render();
  });
}

function agentName(agentId) {
  return state.agents.find((agent) => agent.id === agentId)?.display_name || agentId || "Agent";
}

function agentProfile(agentId) {
  return state.agents.find((agent) => agent.id === agentId) || {};
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
  const actionable = event.agent_id !== "owner" && event.status !== "missing_config";
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
            ? `<div class="message-actions">
                <button class="ghost-btn mini" type="button" data-promote-event="${escapeHtml(event.id)}" data-promote-target="job">Task</button>
                <button class="ghost-btn mini" type="button" data-promote-event="${escapeHtml(event.id)}" data-promote-target="report">Report</button>
                <button class="ghost-btn mini" type="button" data-promote-event="${escapeHtml(event.id)}" data-promote-target="memory_review">Memory Review</button>
                <button class="ghost-btn mini" type="button" data-promote-event="${escapeHtml(event.id)}" data-promote-target="channel_draft">Channel Draft</button>
              </div>`
            : ""
        }
        ${renderPromotionResults(event.id)}
      </div>
    </article>`;
}

function renderPromotionResults(eventId) {
  const results = state.promotionResults[eventId] || [];
  if (!results.length) return "";
  return `
    <div class="promotion-results">
      ${results
        .map((promotion) => {
          const resource = promotion.created_resource || {};
          return `
            <div class="promotion-result">
              <div>
                ${pill(resource.status || promotion.status || "planned")}
                <span class="chip">${escapeHtml(promotion.target)}</span>
                <span class="chip mono">${escapeHtml(shortId(resource.id))}</span>
              </div>
              <button class="ghost-btn mini" type="button" data-open-promotion="${escapeHtml(resource.type)}" data-resource-id="${escapeHtml(resource.id)}">View</button>
            </div>`;
        })
        .join("")}
    </div>`;
}

async function openPromotionResource(resourceType, resourceId) {
  const target = promotionScreenFor(resourceType);
  if (target === "dashboard") await loadDashboard();
  if (target === "reports") await loadReports();
  if (target === "memory") await loadMemory();
  if (target === "channels") await loadChannels();
  const entity = findResourceEntity(resourceType, resourceId);
  state.selectedEntity = entity || { type: resourceType, title: resourceType, status: "created", ref: resourceId, raw: { id: resourceId } };
  state.screen = target;
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

function renderDocuments() {
  setScreenHead("Documents", "ingest workbench");
  const selected = state.documentSession;
  el.actions.innerHTML = `
    <button class="ghost-btn" id="refresh-documents" type="button">Refresh</button>
    <button class="primary-btn" id="run-next-document" type="button" ${!state.selectedIngestId ? "disabled" : ""}>Run Next</button>
    <button class="ghost-btn" id="run-until-blocked" type="button" ${!state.selectedIngestId ? "disabled" : ""}>Run Until Blocked</button>`;
  el.body.innerHTML = `
    <div class="documents-layout">
      <section class="panel pad">
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
      <section class="panel pad">
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
          <h3 class="sub-title">Latest report</h3>
          ${selected.report ? renderObjectCard(selected.report, ["title", "status", "path"]) : `<div class="empty-state">No report generated yet.</div>`}
          <h3 class="sub-title">Review queue</h3>
          ${selected.review_queue?.pending_count ? pill("needs_review", `${selected.review_queue.pending_count} pending`) : pill("ready", "no pending review")}
        `
            : `<div class="empty-state">Session details appear here after selection.</div>`
        }
      </section>
    </div>`;
  el.body.querySelectorAll("[data-ingest]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedIngestId = button.dataset.ingest;
      await loadDocumentSession();
      renderDocuments();
    });
  });
  document.getElementById("refresh-documents")?.addEventListener("click", refreshScreenData);
  document.getElementById("run-next-document")?.addEventListener("click", () => runDocumentStep("/document/parse/workbench-next", "doc-next"));
  document.getElementById("run-until-blocked")?.addEventListener("click", () => runDocumentStep("/document/parse/workbench-run-until-blocked", "doc-run"));
}

async function runDocumentStep(path, key) {
  if (!state.selectedIngestId) return;
  await runAction(key, () => api.post(path, { ingest_id: state.selectedIngestId, max_steps: 10 }), refreshScreenData);
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
    <button class="ghost-btn" id="batch-reject-memory" type="button" ${!pending.length ? "disabled" : ""}>Reject Pending</button>`;
  el.body.innerHTML = `
    <div class="grid two">
      <section class="panel pad">
        <h2 class="panel-title">Pending queue</h2>
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
        <div class="empty-state">Memory candidates are not written as long-term memory until an owner review action returns an approved state.</div>
      </section>
    </div>
    ${state.selectedEntity?.type === "memory" ? renderSelectedEntityPanel() : ""}`;
  bindEntityActions();
  document.getElementById("refresh-memory")?.addEventListener("click", refreshScreenData);
  document.getElementById("batch-reject-memory")?.addEventListener("click", async () => {
    const candidateIds = pending.map((candidate) => candidate.id);
    await runAction("memory-batch", () =>
      api.post("/document/parse/memory-review-batch", {
        candidate_ids: candidateIds,
        decision: "reject",
        reviewer_ref: "owner",
        note: "Rejected from bairui console batch action.",
      }),
    );
  });
  el.body.querySelectorAll("[data-review]").forEach((button) => {
    button.addEventListener("click", async () => {
      await runAction(`review-${button.dataset.candidate}`, () =>
        api.post("/document/parse/review-memory-candidate", {
          candidate_id: button.dataset.candidate,
          decision: button.dataset.review,
          reviewer_ref: "owner",
        }),
      );
    });
  });
}

function renderMemoryCandidate(candidate) {
  return `
    <article class="review-card">
      <div class="step-title">
        <span>${escapeHtml(candidate.candidate_type || "memory candidate")}</span>
        ${pill(candidate.status || "pending_review")}
      </div>
      <p>${escapeHtml(candidate.text || "")}</p>
      <div class="agent-meta">
        <span class="chip mono">${escapeHtml(shortId(candidate.id))}</span>
        <span class="chip">${escapeHtml(candidate.confidence ?? "")}</span>
        <span class="chip">${escapeHtml(candidate.source_path || "")}</span>
      </div>
      <div class="action-row">
        <button class="primary-btn" type="button" data-review="approve" data-candidate="${escapeHtml(candidate.id)}">Approve</button>
        <button class="ghost-btn" type="button" data-review="reject" data-candidate="${escapeHtml(candidate.id)}">Reject</button>
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
      <div class="entity-field-grid">
        ${fields.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value || "-")}</strong></div>`).join("")}
      </div>
      ${renderEntityBody(entity)}
      ${renderEntityActions(entity)}
    </section>`;
}

function entityFields(entity) {
  const raw = entity.raw || {};
  if (entity.type === "job") return [["Route", raw.route], ["Status", raw.status], ["Job ID", raw.id], ["Created", raw.created_at]];
  if (entity.type === "report") return [["Status", raw.status], ["Source", raw.source_type || "document"], ["Reference", raw.source_ref || raw.ingest_id], ["Path", raw.path]];
  if (entity.type === "memory") return [["Candidate", raw.candidate_type], ["Confidence", raw.confidence], ["Source", raw.source_path], ["Created", raw.created_at]];
  if (entity.type === "channel") return [["Target", raw.target_id], ["Channel", raw.channel_type], ["Media", raw.media_kind], ["Review", raw.review_status || raw.status]];
  return [["Status", entity.status || raw.status], ["Reference", entity.ref || raw.id], ["Type", entity.type], ["Created", raw.created_at]];
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
    return `<div class="entity-actions"><button class="ghost-btn" type="button" data-entity-action="inspect-path" data-entity-id="${escapeHtml(raw.path)}">Inspect Path</button></div>`;
  }
  if (entity.type === "job") {
    return `<div class="entity-actions"><button class="ghost-btn" type="button" data-entity-action="open-events" data-entity-id="${escapeHtml(raw.id)}">View Events</button></div>`;
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
    render();
    return;
  }
  if (action === "open-events") {
    state.screen = "events";
    await refreshScreenData();
    return;
  }
  if (action === "inspect-path") {
    state.selectedEntity = { type: "report", title: "Report path", status: "source_ready", ref: id, raw: { path: id } };
    render();
  }
}

function entityIcon(type) {
  return ({ job: "T", report: "R", memory: "M", channel: "C", source: "S" }[type] || "E");
}

function renderSelectedEntityPanel() {
  const entity = state.selectedEntity;
  if (!entity) return "";
  return `<div class="top-gap">${renderEntityCard(entity, "Selected resource")}</div>`;
}

function renderReports() {
  setScreenHead("Reports", "deliverables and evidence");
  el.actions.innerHTML = `<button class="primary-btn" id="write-report" type="button">Write Manual Report</button>`;
  el.body.innerHTML = `
    <div class="grid two">
      <section class="panel pad">
        <h2 class="panel-title">Reports</h2>
        ${renderTable(["title", "status", "path", "source_ref_count"], state.reports.slice().reverse())}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Source references</h2>
        ${renderTable(["source_type", "provider", "title", "confidence"], state.sourceRefs.slice(-14).reverse())}
      </section>
    </div>
    ${state.selectedEntity?.type === "report" ? renderSelectedEntityPanel() : ""}`;
  bindEntityActions();
  document.getElementById("write-report")?.addEventListener("click", async () => {
    const title = prompt("Report title", "bairui Operator Note");
    const body = prompt("Report body", "Operator note from bairui console.");
    if (!body) return;
    await runAction("write-report", () => api.post("/ob" + "sidian/reports", { title, body }));
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
  el.body.innerHTML = `
    <div class="channels-layout">
      <section class="panel pad">
        <h2 class="panel-title">Status</h2>
        ${pill(state.channels?.channels?.status || "missing_config")}
        ${renderWarnings(state.channels?.channels?.blockers || [], state.channels?.channels?.warnings || [])}
        <h3 class="sub-title">Targets</h3>
        ${state.channelTargets.map((target) => renderObjectCard(target, ["id", "label", "channel_type", "status"])).join("") || `<div class="empty-state">No targets configured.</div>`}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Plan outbound action</h2>
        <label class="form-label">Target</label>
        <select class="field" id="channel-target">${state.channelTargets.map((target) => `<option value="${escapeHtml(target.id)}">${escapeHtml(target.label || target.id)}</option>`).join("")}</select>
        <label class="form-label">Media</label>
        <select class="field" id="channel-media"><option>text</option><option>image</option><option>video</option><option>file</option></select>
        <label class="form-label">Message</label>
        <textarea class="textarea" id="channel-text" rows="5" placeholder="Draft message for owner approval"></textarea>
        <button class="primary-btn top-gap" id="plan-channel" type="button" ${!firstTarget ? "disabled" : ""}>Create Approval Plan</button>
        ${state.errors.channel ? `<p class="error-text">${escapeHtml(state.errors.channel)}</p>` : ""}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Approvals</h2>
        ${state.channelApprovals.map(renderChannelApproval).join("") || `<div class="empty-state">No approval requests yet. Planning an action records a review item; it does not send externally.</div>`}
      </section>
    </div>
    ${state.selectedEntity?.type === "channel" ? renderSelectedEntityPanel() : ""}`;
  bindEntityActions();
  document.getElementById("refresh-channels")?.addEventListener("click", refreshScreenData);
  document.getElementById("plan-channel")?.addEventListener("click", async () => {
    await runAction("channel", () =>
      api.post("/channels/send", {
        target_id: document.getElementById("channel-target").value,
        media_kind: document.getElementById("channel-media").value,
        text: document.getElementById("channel-text").value,
        owner_confirmation: true,
      }),
    );
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
      );
    });
  });
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
        <button class="ghost-btn" type="button" data-channel-review="approve" data-request="${escapeHtml(item.id)}" ${reviewed ? "disabled" : ""}>Approve Record</button>
        <button class="ghost-btn" type="button" data-channel-review="reject" data-request="${escapeHtml(item.id)}" ${reviewed ? "disabled" : ""}>Reject</button>
      </div>
    </article>`;
}

function renderAvatar() {
  setScreenHead("Avatar", "character state layer");
  el.actions.innerHTML = `<button class="ghost-btn" id="avatar-thinking" type="button">Thinking</button><button class="ghost-btn" id="avatar-idle" type="button">Idle</button>`;
  el.body.innerHTML = `
    <div class="grid two">
      <section class="panel system-core-stage"><div class="avatar-core avatar-preview"></div><div class="core-label"><strong>Avatar preview</strong><span>${escapeHtml(state.avatarManifest?.avatar_manifest?.engine?.status || "runtime pending")}</span></div></section>
      <section class="panel pad"><h2 class="panel-title">Manifest</h2><pre class="mono muted code-block">${escapeHtml(JSON.stringify(state.avatarManifest?.avatar_manifest || state.avatarStatus?.avatar || {}, null, 2))}</pre></section>
    </div>`;
  document.getElementById("avatar-thinking")?.addEventListener("click", () => runAction("avatar", () => api.post("/avatar/state", { state: "thinking", text: "Working" })));
  document.getElementById("avatar-idle")?.addEventListener("click", () => runAction("avatar", () => api.post("/avatar/state", { state: "idle" })));
}

function renderSettings() {
  setScreenHead("Settings", "runtime status");
  const statuses = [
    ["Memory", state.runtimeStatus.memory?.memory?.status],
    ["Voice", state.runtimeStatus.voice?.voice_asr?.status],
    ["Documents", state.runtimeStatus.document?.document_parse?.status],
    ["Intelligence", state.runtimeStatus.intel?.intelligence?.status],
    ["Simulation", state.runtimeStatus.simulation?.simulation?.status],
    ["Search", state.runtimeStatus.search?.search?.status],
    ["Index", state.runtimeStatus.index?.index?.status],
    ["Avatar", state.avatarStatus?.avatar?.status],
    ["CodeGraph", state.runtimeStatus.codegraph?.codegraph?.status],
  ].map(([name, status]) => ({ name, status: status || "missing_config", detail: "contract-bound runtime status" }));
  el.body.innerHTML = `
    <div class="grid two">
      <section class="panel pad"><h2 class="panel-title">Runtime surfaces</h2>${renderTable(["name", "status", "detail"], statuses)}</section>
      <section class="panel pad"><h2 class="panel-title">Capabilities</h2>${renderTable(["name", "status", "detail"], state.capabilities)}</section>
    </div>`;
}

function renderCodeGraph() {
  setScreenHead("CodeGraph", "source structure index");
  el.actions.innerHTML = `<button class="ghost-btn" id="refresh-codegraph" type="button">Refresh</button>`;
  el.body.innerHTML = `
    <div class="channels-layout">
      <section class="panel pad">
        <h2 class="panel-title">Status</h2>
        ${pill(state.codegraph?.codegraph?.status || "ready")}
        <p class="muted">${escapeHtml(state.codegraph?.codegraph?.memory_boundary || "Code structure stays separate from long-term memory.")}</p>
        <h3 class="sub-title">Repos</h3>
        ${state.codegraphRepos.map((repo) => renderObjectCard(repo, ["name", "status", "root_path"])).join("") || `<div class="empty-state">No source repository registered yet.</div>`}
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Register and scan</h2>
        <label class="form-label">Repository path</label>
        <input class="field" id="codegraph-path" placeholder="C:\\path\\to\\repo" />
        <label class="form-label">Name</label>
        <input class="field" id="codegraph-name" placeholder="bairui-source" />
        <div class="action-row top-gap">
          <button class="primary-btn" id="codegraph-register" type="button">Register</button>
          <button class="ghost-btn" id="codegraph-scan" type="button" ${!state.codegraphRepos.length ? "disabled" : ""}>Scan Latest</button>
        </div>
        <h3 class="sub-title">Query</h3>
        <input class="field" id="codegraph-query-text" placeholder="function, class, route, file" />
        <button class="ghost-btn top-gap" id="codegraph-query" type="button">Search</button>
      </section>
      <section class="panel pad">
        <h2 class="panel-title">Results</h2>
        ${state.codegraphQuery ? renderTable(["type", "name", "kind", "path"], state.codegraphQuery.results || []) : `<div class="empty-state">Search results appear here after scanning.</div>`}
        <h3 class="sub-title">Impact</h3>
        <input class="field" id="codegraph-impact-path" placeholder="src/service/server.py" />
        <button class="ghost-btn top-gap" id="codegraph-impact" type="button">Analyze Impact</button>
        ${state.codegraphImpact ? renderCountStrip({ files: state.codegraphImpact.files?.length || 0, symbols: state.codegraphImpact.symbols?.length || 0, imported_by: state.codegraphImpact.imported_by?.length || 0 }) : ""}
      </section>
    </div>`;
  document.getElementById("refresh-codegraph")?.addEventListener("click", refreshScreenData);
  document.getElementById("codegraph-register")?.addEventListener("click", async () => {
    await runAction("codegraph-register", () =>
      api.post("/codegraph/repos/register", {
        path: document.getElementById("codegraph-path").value,
        name: document.getElementById("codegraph-name").value,
      }),
    );
  });
  document.getElementById("codegraph-scan")?.addEventListener("click", async () => {
    const repo = state.codegraphRepos[state.codegraphRepos.length - 1];
    await runAction("codegraph-scan", () => api.post("/codegraph/repos/scan", { repo_id: repo?.id || "" }));
  });
  document.getElementById("codegraph-query")?.addEventListener("click", async () => {
    const repo = state.codegraphRepos[state.codegraphRepos.length - 1];
    const result = await runAction("codegraph-query", () =>
      api.post("/codegraph/query", {
        query: document.getElementById("codegraph-query-text").value,
        repo_id: repo?.id || "",
        limit: 20,
      }),
    );
    state.codegraphQuery = result?.codegraph_query || state.codegraphQuery;
    render();
  });
  document.getElementById("codegraph-impact")?.addEventListener("click", async () => {
    const repo = state.codegraphRepos[state.codegraphRepos.length - 1];
    const result = await runAction("codegraph-impact", () =>
      api.post("/codegraph/impact", {
        path: document.getElementById("codegraph-impact-path").value,
        repo_id: repo?.id || "",
      }),
    );
    state.codegraphImpact = result?.codegraph_impact || state.codegraphImpact;
    render();
  });
}

function renderEvents() {
  setScreenHead("Events", "audit timeline");
  const frontendEvents = state.events.map((event) => ({
    type: event.type,
    id: shortId(event.id),
    action: event.data?.action || "",
    resource_type: event.data?.resource_type || "",
  }));
  el.body.innerHTML = `
    <div class="grid two">
      <section class="panel pad"><h2 class="panel-title">Live events</h2>${renderTable(["type", "id", "action", "resource_type"], frontendEvents)}</section>
      <section class="panel pad"><h2 class="panel-title">Audit fallback</h2>${renderTable(["action", "resource_type", "risk_level", "created_at"], state.audit.slice(-20).reverse())}</section>
    </div>`;
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
  return `<div class="step-list">${actions.map((action) => `<div class="step-item"><div class="step-title"><span>${escapeHtml(action.label || action.command || action.id)}</span>${pill("partial", action.command || "action")}</div></div>`).join("")}</div>`;
}

function renderCountStrip(counts) {
  const entries = Object.entries(counts || {});
  if (!entries.length) return `<div class="empty-state compact">No counts available.</div>`;
  return `<div class="count-strip">${entries.map(([key, value]) => `<div><strong>${escapeHtml(value)}</strong><span>${escapeHtml(key)}</span></div>`).join("")}</div>`;
}

function renderObjectCard(item, keys) {
  return `<article class="object-card">${keys.map((key) => `<div><span>${escapeHtml(key)}</span><strong>${escapeHtml(item?.[key] ?? "")}</strong></div>`).join("")}</article>`;
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
  const [contract, health, ready, readiness, capabilities, jobs, audit, avatarStatus, avatarManifest, platform] = await Promise.all([
    safe(() => api.get("/frontend/contract").then((data) => data.frontend_contract), state.contract),
    safe(() => api.get("/health"), state.health),
    safe(() => api.get("/ready"), state.ready),
    safe(() => api.get("/runtime/readiness"), state.readiness),
    safe(() => api.get("/capabilities").then((data) => data.capabilities || []), state.capabilities),
    safe(() => api.get("/jobs").then((data) => data.jobs || []), state.jobs),
    safe(() => api.get("/audit").then((data) => data.audit || []), state.audit),
    safe(() => api.get("/avatar/status"), state.avatarStatus),
    safe(() => api.get("/avatar/manifest"), state.avatarManifest),
    safe(() => api.get("/platform/heartbeat"), state.platform),
  ]);
  Object.assign(state, { contract, health, ready, readiness, capabilities, jobs, audit, avatarStatus, avatarManifest, platform });
  await refreshScreenData();
  render();
}

async function refreshScreenData() {
  if (state.screen === "activation") {
    await Promise.all([loadRuntimeStatus(), loadMemory(), loadReports(), loadChannels(), loadCodeGraph()]);
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
  const [channels, targets, diagnostics, approvals] = await Promise.all([
    safe(() => api.get("/channels/status"), state.channels, "channels-status"),
    safe(() => api.get("/channels/targets").then((data) => data.channel_targets || []), state.channelTargets, "channels-targets"),
    safe(() => api.get("/channels/diagnostics").then((data) => data.channel_diagnostics || []), state.channelDiagnostics, "channels-diagnostics"),
    safe(() => api.get("/channels/approvals").then((data) => data.channel_approvals || []), state.channelApprovals, "channels-approvals"),
  ]);
  state.channels = channels;
  state.channelTargets = targets || [];
  state.channelDiagnostics = diagnostics || [];
  state.channelApprovals = approvals || [];
}

async function loadAgents() {
  const [agents, sessions] = await Promise.all([
    safe(() => api.get("/agents").then((data) => data.agents || []), state.agents, "agents"),
    safe(() => api.get("/agents/sessions").then((data) => data.agent_sessions || []), state.agentSessions, "agent-sessions"),
  ]);
  state.agents = agents || [];
  state.agentSessions = sessions || [];
  if (!state.selectedAgentSessionId && state.agentSessions.length) state.selectedAgentSessionId = state.agentSessions.at(-1).id;
  const selected = state.agentSessions.find((item) => item.id === state.selectedAgentSessionId);
  if (!state.selectedAgentIds.length) state.selectedAgentIds = selected?.agent_ids?.length ? [...selected.agent_ids] : state.agents.map((agent) => agent.id);
  if (state.selectedAgentSessionId) {
    state.agentEvents = await safe(() => api.get(`/agents/session/${state.selectedAgentSessionId}/events`).then((data) => data.agent_events || []), state.agentEvents, "agent-events");
  }
}

async function loadRuntimeStatus() {
  const [memory, voice, document, intel, simulation, search, index, codegraph] = await Promise.all([
    safe(() => api.get("/memory/status"), state.runtimeStatus.memory, "memory-status"),
    safe(() => api.get("/voice/asr/status"), state.runtimeStatus.voice, "voice-status"),
    safe(() => api.get("/document/parse/status"), state.runtimeStatus.document, "document-status"),
    safe(() => api.get("/intel/status"), state.runtimeStatus.intel, "intel-status"),
    safe(() => api.get("/simulation/status"), state.runtimeStatus.simulation, "simulation-status"),
    safe(() => api.get("/search/status"), state.runtimeStatus.search, "search-status"),
    safe(() => api.get("/index/status"), state.runtimeStatus.index, "index-status"),
    safe(() => api.get("/codegraph/status"), state.runtimeStatus.codegraph, "codegraph-status"),
  ]);
  state.runtimeStatus = { memory, voice, document, intel, simulation, search, index, codegraph };
}

async function loadCodeGraph() {
  const [codegraph, repos] = await Promise.all([
    safe(() => api.get("/codegraph/status"), state.codegraph, "codegraph-status"),
    safe(() => api.get("/codegraph/repos").then((data) => data.codegraph_repos || []), state.codegraphRepos, "codegraph-repos"),
  ]);
  state.codegraph = codegraph;
  state.codegraphRepos = repos || [];
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
    if (!state.selectedAgentSessionId) {
      const agents = state.agents.length ? state.agents : await safe(() => api.get("/agents").then((data) => data.agents || []), [], "agents");
      state.agents = agents || state.agents;
      const result = await runAction("agent-session", () =>
        api.post("/agents/session", {
          title: "bairui command session",
          agent_ids: state.selectedAgentIds.length ? state.selectedAgentIds : state.agents.map((agent) => agent.id),
        }),
      );
      state.selectedAgentSessionId = result?.agent_session?.id || "";
      state.selectedAgentIds = result?.agent_session?.agent_ids || state.selectedAgentIds;
    }
    if (!state.selectedAgentSessionId) return;
    await runAction("agent-round", () => api.post(`/agents/session/${state.selectedAgentSessionId}/round`, { prompt: promptText }));
    await loadAgents();
  } else {
    await runAction("command", () => api.post("/jobs", { title: "Command request", prompt: promptText, route: "general" }));
  }
  el.commandInput.value = "";
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

renderRail();
renderTopbar();
renderActivation();
refresh();
connectEvents();
