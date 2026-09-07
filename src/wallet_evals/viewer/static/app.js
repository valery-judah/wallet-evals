"use strict";

const state = {
  runs: [],
  selectedArtifact: null,
  selectedCaseId: null,
  loadedArtifact: null,
};

const THEME_STORAGE_KEY = "wallet-evals-viewer-theme";

const nodes = {
  status: document.getElementById("viewer-status"),
  resultsDirectory: document.getElementById("results-directory"),
  runCount: document.getElementById("run-count"),
  runList: document.getElementById("run-list"),
  caseCount: document.getElementById("case-count"),
  runSummary: document.getElementById("run-summary"),
  caseList: document.getElementById("case-list"),
  caseView: document.getElementById("case-view"),
  themeToggle: document.getElementById("theme-toggle"),
};

function preferredTheme() {
  const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme, persist = false) {
  document.documentElement.dataset.theme = theme;
  nodes.themeToggle.textContent = theme === "dark" ? "Light theme" : "Dark theme";
  nodes.themeToggle.setAttribute("aria-pressed", String(theme === "dark"));
  nodes.themeToggle.setAttribute(
    "aria-label",
    theme === "dark" ? "Switch to light theme" : "Switch to dark theme",
  );
  if (persist) window.localStorage.setItem(THEME_STORAGE_KEY, theme);
}

function initializeTheme() {
  applyTheme(preferredTheme());
  nodes.themeToggle.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme, true);
  });
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function append(parent, ...children) {
  parent.append(...children.filter(Boolean));
  return parent;
}

function jsonBlock(value) {
  return element("pre", "json", JSON.stringify(value, null, 2));
}

function details(label, value) {
  const container = element("details");
  append(container, element("summary", null, label), jsonBlock(value));
  return container;
}

function badge(text, isError = false) {
  return element("span", isError ? "badge error" : "badge", text);
}

function setStatus(message) {
  nodes.status.textContent = message;
}

function selectedFromUrl() {
  const parameters = new URLSearchParams(window.location.search);
  return { artifact: parameters.get("run"), caseId: parameters.get("case") };
}

function updateUrl() {
  const url = new URL(window.location.href);
  if (state.selectedArtifact) url.searchParams.set("run", state.selectedArtifact);
  else url.searchParams.delete("run");
  if (state.selectedCaseId) url.searchParams.set("case", state.selectedCaseId);
  else url.searchParams.delete("case");
  window.history.replaceState(null, "", url);
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed with ${response.status}`);
  return body;
}

function renderRunList() {
  nodes.runList.replaceChildren();
  nodes.runCount.textContent = String(state.runs.length);
  for (const run of state.runs) {
    const button = element(
      "button",
      `nav-item${run.valid ? "" : " invalid"}${run.artifact_name === state.selectedArtifact ? " selected" : ""}`,
    );
    button.type = "button";
    button.disabled = !run.valid;
    const title = run.valid ? run.run_id : run.artifact_name;
    append(button, element("span", "item-title", title));
    if (run.valid) {
      const meta = `${run.case_count} cases · ${run.model} · ${new Date(run.modified_at).toLocaleString()}`;
      append(button, element("span", "item-meta", meta));
      if (run.case_set_id) append(button, element("span", "item-meta", `Case set: ${run.case_set_id}`));
      button.addEventListener("click", () => loadRun(run.artifact_name));
    } else {
      append(button, element("span", "item-error", `Invalid artifact: ${run.error}`));
    }
    nodes.runList.append(button);
  }
}

function responseStatus(response) {
  if (response && typeof response === "object" && Number.isInteger(response.status_code)) {
    return response.status_code;
  }
  return 200;
}

function traceIndicators(trace) {
  const events = trace.events || [];
  return {
    adaptive: events.some((event) => event.kind === "participant_action" && event.adaptive_basis),
    observation: events.some((event) => event.kind === "observable_change"),
    error: events.some(
      (event) => event.kind === "wallet_response" && responseStatus(event.response) >= 400,
    ),
  };
}

function renderCaseList(runResult) {
  nodes.caseList.replaceChildren();
  nodes.caseCount.textContent = String(runResult.traces.length);
  nodes.runSummary.replaceChildren(
    element("strong", null, runResult.run_id),
    element("div", null, `${runResult.execution_context.wallet} · ${runResult.execution_context.model}`),
  );
  for (const trace of runResult.traces) {
    const indicators = traceIndicators(trace);
    const button = element(
      "button",
      `nav-item${trace.case_id === state.selectedCaseId ? " selected" : ""}`,
    );
    button.type = "button";
    append(
      button,
      element("span", "item-title", trace.case_id),
      element(
        "span",
        "item-meta",
        `${trace.case_context.interaction_form || "unknown form"} · ${trace.events.length} events`,
      ),
    );
    const labels = [];
    if (indicators.adaptive) labels.push("adaptive");
    if (indicators.observation) labels.push("observation");
    if (indicators.error) labels.push("public error");
    if (labels.length) append(button, element("span", "item-meta", labels.join(" · ")));
    button.addEventListener("click", () => selectCase(trace.case_id));
    nodes.caseList.append(button);
  }
}

function infoCard(label, value, wide = false) {
  const card = element("article", wide ? "info-card wide" : "info-card");
  append(
    card,
    element("p", "info-label", label),
    typeof value === "string" ? element("p", "info-value", value) : jsonBlock(value),
  );
  return card;
}

function responseSummary(response) {
  if (!response || typeof response !== "object") return JSON.stringify(response);
  if (response.body && typeof response.body === "object" && response.body.detail) {
    return response.body.detail;
  }
  if (response.outcome && typeof response.outcome === "object" && response.outcome.message) {
    return response.outcome.message;
  }
  return "Captured response has no display summary.";
}

function renderAction(event) {
  const card = element("article", "event-card action");
  append(
    card,
    append(
      element("div", "event-heading"),
      element("span", "event-kind", "Participant action"),
      element("span", "event-order", `Event ${event.order}`),
    ),
    element("p", "derived-label", event.action.name),
    typeof event.action.payload === "string"
      ? element("p", "event-summary", event.action.payload)
      : jsonBlock(event.action.payload),
  );
  if (event.adaptive_basis) {
    append(card, details("Adaptive choice · cited participant-visible facts", event.adaptive_basis));
  }
  append(card, details("Exact captured action", event.action));
  return card;
}

function renderResponse(event) {
  const status = responseStatus(event.response);
  const isError = status >= 400;
  const card = element("article", isError ? "event-card error" : "event-card response");
  append(
    card,
    append(
      element("div", "event-heading"),
      element("span", "event-kind", isError ? `Wallet response · HTTP ${status}` : "Wallet response"),
      element("span", "event-order", `Event ${event.order}`),
    ),
    element("span", "derived-label", "Derived response summary"),
    element("p", "event-summary", responseSummary(event.response)),
    details("Complete captured response", event.response),
    details(
      `Participant-visible facts (${(event.participant_visible_facts || []).length})`,
      event.participant_visible_facts || [],
    ),
  );
  return card;
}

function renderObservation(event) {
  const card = element("article", "event-card observation");
  append(
    card,
    append(
      element("div", "event-heading"),
      element("span", "event-kind", "Observable change"),
      element("span", "event-order", `Event ${event.order}`),
    ),
    element("p", "event-summary", `${event.subject} · ${event.capture_point}`),
    details("Exact captured observation", event.value),
  );
  return card;
}

function renderEvent(event) {
  if (event.kind === "participant_action") return renderAction(event);
  if (event.kind === "wallet_response") return renderResponse(event);
  if (event.kind === "observable_change") return renderObservation(event);
  const card = element("article", "event-card");
  append(card, element("p", "event-summary", `Unknown event kind: ${event.kind}`), jsonBlock(event));
  return card;
}

function renderCase(trace, runResult) {
  const context = trace.case_context || {};
  const indicators = traceIndicators(trace);
  const root = document.createDocumentFragment();
  const header = element("header", "case-header");
  append(
    header,
    element("p", "eyebrow", "Whole-case evidence"),
    element("h2", null, trace.case_id),
    element("p", "case-purpose", context.purpose || "No recorded purpose."),
  );
  const badges = element("div", "badge-row");
  append(
    badges,
    badge(context.interaction_form || "unknown form"),
    badge(`${trace.events.length} events`),
  );
  if (indicators.adaptive) append(badges, badge("Adaptive choices"));
  if (indicators.observation) append(badges, badge("Observable change"));
  if (indicators.error) append(badges, badge("Public Wallet error", true));
  append(header, badges);
  root.append(header);

  const contextSection = element("section", "section");
  const contextGrid = element("div", "context-grid");
  append(
    contextGrid,
    infoCard("Failure surface", context.failure_surface || "Not recorded", true),
    infoCard("Dimensions", context.dimensions || {}),
    infoCard("Declared starting conditions", trace.starting_conditions || {}),
  );
  append(contextSection, element("h3", "section-heading", "Case context"), contextGrid);
  root.append(contextSection);

  const trajectorySection = element("section", "section");
  const trajectory = element("div", "trajectory");
  for (const event of trace.events) trajectory.append(renderEvent(event));
  append(trajectorySection, element("h3", "section-heading", "Ordered trajectory"), trajectory);
  root.append(trajectorySection);

  const provenanceSection = element("section", "section");
  const provenanceGrid = element("div", "provenance-grid");
  append(
    provenanceGrid,
    infoCard("Run ID", runResult.run_id),
    infoCard("Case execution ID", trace.case_execution_id),
    infoCard("Wallet", runResult.execution_context.wallet),
    infoCard("Model", runResult.execution_context.model),
    infoCard("Environment", runResult.execution_context.environment),
    infoCard("Settings", runResult.execution_context.settings),
  );
  append(provenanceSection, element("h3", "section-heading", "Execution provenance"), provenanceGrid);
  root.append(provenanceSection);

  const rawSection = element("section", "section");
  append(rawSection, element("h3", "section-heading", "Raw trace evidence"), details("Exact saved trace", trace));
  root.append(rawSection);

  nodes.caseView.replaceChildren(root);
}

function selectCase(caseId) {
  const runResult = state.loadedArtifact.document.run_result;
  const trace = runResult.traces.find((candidate) => candidate.case_id === caseId);
  if (!trace) return;
  state.selectedCaseId = caseId;
  renderCaseList(runResult);
  renderCase(trace, runResult);
  updateUrl();
}

async function loadRun(artifactName, preferredCaseId = null) {
  setStatus("Loading run…");
  try {
    const artifact = await fetchJson(`/api/runs/${encodeURIComponent(artifactName)}`);
    state.selectedArtifact = artifactName;
    state.loadedArtifact = artifact;
    const runResult = artifact.document.run_result;
    const requestedCase = preferredCaseId || state.selectedCaseId;
    const selected = runResult.traces.find((trace) => trace.case_id === requestedCase);
    state.selectedCaseId = selected ? selected.case_id : runResult.traces[0].case_id;
    renderRunList();
    renderCaseList(runResult);
    selectCase(state.selectedCaseId);
    setStatus(`${runResult.traces.length} traces loaded`);
  } catch (error) {
    setStatus("Run could not be loaded");
    const box = element("section", "load-error");
    append(box, element("h2", null, "Unable to load run"), element("p", null, error.message));
    nodes.caseView.replaceChildren(box);
  }
}

async function start() {
  try {
    const index = await fetchJson("/api/runs");
    state.runs = index.runs;
    nodes.resultsDirectory.textContent = index.results_directory;
    renderRunList();
    const requested = selectedFromUrl();
    const requestedRun = state.runs.find(
      (run) => run.valid && run.artifact_name === requested.artifact,
    );
    const firstValid = state.runs.find(
      (run) => run.valid && run.artifact_name === index.default_artifact_name,
    );
    const initial = requestedRun || firstValid;
    if (!initial) {
      setStatus("No valid run artifacts");
      nodes.caseCount.textContent = "0";
      return;
    }
    await loadRun(initial.artifact_name, requested.caseId);
  } catch (error) {
    setStatus("Viewer failed to load");
    const box = element("section", "load-error");
    append(box, element("h2", null, "Unable to open results"), element("p", null, error.message));
    nodes.caseView.replaceChildren(box);
  }
}

initializeTheme();
start();
