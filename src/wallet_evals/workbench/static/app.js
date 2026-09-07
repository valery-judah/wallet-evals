"use strict";

const state = {
  cases: [],
  cohorts: [],
  selected: new Set(),
  selectedCohortId: null,
  links: {},
  run: null,
  savedRuns: [],
  pollTimer: null,
};

const nodes = {
  datasetViewer: document.getElementById("dataset-viewer-link"),
  traceViewer: document.getElementById("trace-viewer-link"),
  cohort: document.getElementById("cohort-select"),
  search: document.getElementById("case-search"),
  clear: document.getElementById("clear-selection"),
  selectionCount: document.getElementById("selection-count"),
  datasetSummary: document.getElementById("dataset-summary"),
  caseList: document.getElementById("case-list"),
  model: document.getElementById("model-input"),
  walletRepository: document.getElementById("wallet-repository"),
  runButton: document.getElementById("run-button"),
  runBadge: document.getElementById("run-badge"),
  runPanel: document.getElementById("run-panel"),
  runTitle: document.getElementById("run-title"),
  runMessage: document.getElementById("run-message"),
  progressBar: document.getElementById("progress-bar"),
  runOutput: document.getElementById("run-output"),
  resultCard: document.getElementById("result-card"),
  resultTitle: document.getElementById("result-title"),
  resultMeta: document.getElementById("result-meta"),
  openResult: document.getElementById("open-result"),
  savedRunCount: document.getElementById("saved-run-count"),
  savedRuns: document.getElementById("saved-runs"),
};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { Accept: "application/json", "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed with ${response.status}`);
  return body;
}

function messageForCase(item) {
  const messages = Array.isArray(item.messages) ? item.messages : [];
  return messages.join(" → ") || "No generated message recorded";
}

function renderCases() {
  const query = nodes.search.value.trim().toLowerCase();
  const matching = state.cases.filter(
    (item) => !query || `${item.case_id} ${messageForCase(item)}`.toLowerCase().includes(query),
  );
  const selectedMatches = matching.filter((item) => state.selected.has(item.case_id));
  const otherMatches = matching.filter((item) => !state.selected.has(item.case_id));
  const visible = [
    ...selectedMatches,
    ...otherMatches.slice(0, Math.max(0, 80 - selectedMatches.length)),
  ];
  nodes.caseList.replaceChildren();
  for (const item of visible) {
    const label = element("label", `case-row${state.selected.has(item.case_id) ? " selected" : ""}`);
    const checkbox = element("input");
    checkbox.type = "checkbox";
    checkbox.checked = state.selected.has(item.case_id);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) state.selected.add(item.case_id);
      else state.selected.delete(item.case_id);
      state.selectedCohortId = null;
      nodes.cohort.value = "";
      renderSelection();
      renderCases();
    });
    const copy = element("span", "case-copy");
    copy.append(
      element("strong", null, item.case_id),
      element("span", "case-message", messageForCase(item)),
      element("span", "case-meta", `${item.interaction_form} · ${item.tuple_id}`),
    );
    label.append(checkbox, copy);
    nodes.caseList.append(label);
  }
  if (!visible.length) nodes.caseList.append(element("p", "empty-message", "No matching cases."));
}

function renderSelection() {
  const count = state.selected.size;
  nodes.selectionCount.textContent = `${count} selected`;
  nodes.runButton.disabled = count === 0 || state.run?.status === "running";
  nodes.runButton.textContent = count ? `Run ${count} selected case${count === 1 ? "" : "s"}` : "Run selected cases";
}

function selectCohort(cohortId) {
  const cohort = state.cohorts.find((item) => item.cohort_id === cohortId);
  state.selected = new Set(cohort ? cohort.case_ids : []);
  state.selectedCohortId = cohort ? cohort.cohort_id : null;
  renderSelection();
  renderCases();
}

function statusLabel(status) {
  return { idle: "Ready", running: "Running", succeeded: "Captured", failed: "Needs attention" }[status] || status;
}

function traceUrl(artifactName, caseId = null) {
  if (!artifactName) return state.links.trace_viewer;
  const url = new URL(state.links.trace_viewer);
  url.searchParams.set("run", artifactName);
  if (caseId) url.searchParams.set("case", caseId);
  return url.toString();
}

function renderRun(run) {
  state.run = run;
  const status = run?.status || "idle";
  nodes.runBadge.className = `status-pill ${status}`;
  nodes.runBadge.textContent = statusLabel(status);
  nodes.runPanel.className = `run-panel ${status}`;
  const total = run?.total_cases || 0;
  const completed = run?.completed_cases || 0;
  nodes.progressBar.style.width = `${total ? Math.min(100, (completed / total) * 100) : 0}%`;
  nodes.runOutput.textContent = run?.output?.length ? run.output.join("\n") : "No output yet.";

  if (status === "running") {
    nodes.runTitle.textContent = `Running ${total} selected cases`;
    nodes.runMessage.textContent = run.active_case_id
      ? `Exercising ${run.active_case_id}. ${completed} of ${total} cases complete.`
      : "Preparing the selected cases…";
  } else if (status === "succeeded") {
    nodes.runTitle.textContent = `Captured ${total} case traces`;
    nodes.runMessage.textContent =
      "The run completed. Case-level errors in the technical output are captured evidence.";
  } else if (status === "failed") {
    nodes.runTitle.textContent = "The run did not complete";
    nodes.runMessage.textContent = run.error || "Review the run output, adjust the setup, and retry.";
  } else {
    nodes.runTitle.textContent = "No run started";
    nodes.runMessage.textContent = "Select at least one case to begin.";
  }

  const running = status === "running";
  nodes.runButton.disabled = running || state.selected.size === 0;
  renderSelection();
  renderResult(run);
  if (running && !state.pollTimer) state.pollTimer = window.setInterval(pollRun, 1000);
  if (!running && state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function renderResult(run) {
  if (run?.status === "succeeded" && run.artifact_name) {
    nodes.resultCard.className = "result-card";
    nodes.resultTitle.textContent = `${run.total_cases} traces captured with ${run.model}`;
    nodes.resultMeta.textContent = "Open the full result, then choose any case trace.";
    nodes.openResult.className = "primary-button";
    nodes.openResult.href = traceUrl(run.artifact_name);
  } else {
    nodes.resultCard.className = "result-card empty";
    nodes.resultTitle.textContent = "Complete a run to inspect its traces";
    nodes.resultMeta.textContent = "Saved evidence remains available in the trace viewer.";
    nodes.openResult.className = "primary-button disabled";
    nodes.openResult.removeAttribute("href");
  }
}

function renderSavedRuns() {
  nodes.savedRuns.replaceChildren();
  const valid = state.savedRuns.filter((item) => item.valid);
  nodes.savedRunCount.textContent = `${valid.length} saved run${valid.length === 1 ? "" : "s"}`;
  for (const item of valid.slice(0, 6)) {
    const link = element("a", "saved-run");
    link.href = traceUrl(item.artifact_name);
    link.target = "_blank";
    link.append(
      element("strong", null, item.case_set_id || item.run_id),
      element("span", null, `${item.case_count} cases · ${item.model}`),
    );
    nodes.savedRuns.append(link);
  }
  if (!valid.length) nodes.savedRuns.append(element("p", "empty-message", "No saved runs yet."));
}

async function pollRun() {
  try {
    const data = await fetchJson("/api/run");
    state.savedRuns = data.saved_runs || [];
    renderRun(data.run);
    renderSavedRuns();
  } catch (error) {
    nodes.runMessage.textContent = error.message;
  }
}

async function startRun() {
  if (!state.selected.size) return;
  nodes.runButton.disabled = true;
  try {
    const payload = { case_ids: [...state.selected], model: nodes.model.value.trim() };
    if (state.selectedCohortId) payload.cohort_id = state.selectedCohortId;
    const data = await fetchJson("/api/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderRun(data.run);
  } catch (error) {
    nodes.runMessage.textContent = error.message;
    nodes.runPanel.className = "run-panel failed";
    nodes.runButton.disabled = false;
  }
}

async function initialize() {
  try {
    const data = await fetchJson("/api/workbench");
    state.cases = data.dataset.cases;
    state.cohorts = data.dataset.cohorts;
    state.links = data.links;
    state.savedRuns = data.saved_runs || [];
    nodes.datasetViewer.href = data.links.dataset_viewer;
    nodes.traceViewer.href = data.links.trace_viewer;
    nodes.model.value = data.defaults.model;
    nodes.walletRepository.textContent = data.defaults.wallet_repository;
    nodes.datasetSummary.textContent = `${data.dataset.case_count} cases available from ${data.dataset.name}. Selected cases appear first.`;
    for (const cohort of state.cohorts) {
      const option = element("option", null, `${cohort.cohort_id} · ${cohort.case_ids.length} cases`);
      option.value = cohort.cohort_id;
      nodes.cohort.append(option);
    }
    renderCases();
    renderSelection();
    renderRun(data.run);
    renderSavedRuns();
  } catch (error) {
    nodes.datasetSummary.textContent = `Could not load the workbench: ${error.message}`;
  }
}

nodes.cohort.addEventListener("change", () => selectCohort(nodes.cohort.value));
nodes.search.addEventListener("input", renderCases);
nodes.clear.addEventListener("click", () => {
  state.selected.clear();
  state.selectedCohortId = null;
  nodes.cohort.value = "";
  renderSelection();
  renderCases();
});
nodes.runButton.addEventListener("click", startRun);

initialize();
