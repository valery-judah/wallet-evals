"use strict";

const state = {
  dataset: null,
  view: "overview",
  selectedTuple: null,
  selectedCase: null,
  filters: {
    search: "",
    dimension: "",
    value: "",
    form: "",
    cohort: "",
  },
};

const content = document.getElementById("content");
const viewerStatus = document.getElementById("viewer-status");
const datasetPath = document.getElementById("dataset-path");
const searchFilter = document.getElementById("search-filter");
const dimensionFilter = document.getElementById("dimension-filter");
const valueFilter = document.getElementById("value-filter");
const formFilter = document.getElementById("form-filter");
const cohortFilter = document.getElementById("cohort-filter");
const sourceDialog = document.getElementById("source-dialog");
const sourceFile = document.getElementById("source-file");
const sourceStatus = document.getElementById("source-status");
const sourceJson = document.getElementById("source-json");

function clientLog(phase, detail) {
  console.info(`[dataset-viewer] ${phase}`, detail ?? "");
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function showFatal(error, phase) {
  const message = errorMessage(error);
  console.error(`[dataset-viewer] ${phase} failed`, error);
  viewerStatus.textContent = `Dataset viewer error during ${phase}: ${message}`;
  content.replaceChildren(
    node("section", "panel"),
  );
  add(
    content.firstChild,
    node("p", "eyebrow", "Viewer error"),
    node("h2", "", `Could not finish ${phase}`),
    node("p", "lede", message),
    node("p", "muted", "The browser console and dataset-viewer terminal contain phase logs."),
  );
}

window.addEventListener("error", (event) => showFatal(event.error || event.message, "script"));
window.addEventListener("unhandledrejection", (event) => showFatal(event.reason, "promise"));

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = String(text);
  return element;
}

function add(parent, ...children) {
  for (const child of children) {
    if (child !== null && child !== undefined) parent.append(child);
  }
  return parent;
}

function option(value, label) {
  const item = document.createElement("option");
  item.value = value;
  item.textContent = label;
  return item;
}

function button(label, className, action) {
  const item = node("button", className, label);
  item.type = "button";
  item.addEventListener("click", action);
  return item;
}

async function copyToClipboard(text) {
  let clipboardError = null;
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch (error) {
      clipboardError = error;
      console.warn("[dataset-viewer] Clipboard API failed; trying browser fallback", error);
    }
  }

  const fallback = node("textarea", "clipboard-fallback", text);
  fallback.setAttribute("readonly", "");
  document.body.append(fallback);
  fallback.select();
  fallback.setSelectionRange(0, text.length);
  const copied = document.execCommand("copy");
  fallback.remove();
  if (!copied) {
    throw clipboardError || new Error("The browser did not allow clipboard access.");
  }
}

function jsonDetails(label, value, open = false) {
  const details = node("details", "json-details");
  details.open = open;
  const summary = node("summary", "", label);
  const pre = node("pre", "json-block", JSON.stringify(value, null, 2));
  add(details, summary, pre);
  return details;
}

function labelled(label, value) {
  const wrapper = node("div", "labelled");
  add(wrapper, node("span", "field-label", label), node("p", "", value || "Not declared"));
  return wrapper;
}

function pill(text, tone = "") {
  return node("span", `pill ${tone}`.trim(), text);
}

function tupleById(tupleId) {
  return state.dataset.tuples.find((item) => item.tuple_id === tupleId);
}

function dimensionByName(dimensionName) {
  return state.dataset.dimensions.find((item) => item.name === dimensionName);
}

function caseById(caseId) {
  return state.dataset.cases.find((item) => item.case_id === caseId);
}

function assignedValues(tupleItem, dimensionName) {
  const assigned = tupleItem.record.dimensions[dimensionName];
  if (assigned === undefined) return [];
  return Array.isArray(assigned) ? assigned : [assigned];
}

function tupleMatchesDimension(tupleItem) {
  const dimensionName = state.filters.dimension;
  const value = state.filters.value;
  if (!dimensionName) return true;
  const assigned = assignedValues(tupleItem, dimensionName);
  if (!value) return assigned.length > 0;
  if (value === "__omitted__") return assigned.length === 0;
  return assigned.includes(value);
}

function caseSearchText(caseItem, tupleItem) {
  return [
    caseItem.case_id,
    caseItem.interaction_form,
    JSON.stringify(caseItem.example),
    JSON.stringify(caseItem.fixture),
    JSON.stringify(caseItem.prelude),
    JSON.stringify(tupleItem.record),
  ].join(" ").toLocaleLowerCase();
}

function filteredCases() {
  const search = state.filters.search.toLocaleLowerCase();
  return state.dataset.cases.filter((caseItem) => {
    const tupleItem = tupleById(caseItem.tuple_id);
    if (!tupleMatchesDimension(tupleItem)) return false;
    if (state.filters.form && caseItem.interaction_form !== state.filters.form) return false;
    if (state.filters.cohort && !caseItem.cohort_ids.includes(state.filters.cohort)) return false;
    return !search || caseSearchText(caseItem, tupleItem).includes(search);
  });
}

function filteredTuples(cases) {
  const tupleIds = new Set(cases.map((item) => item.tuple_id));
  return state.dataset.tuples.filter((item) => tupleIds.has(item.tuple_id));
}

function setView(view) {
  state.view = view;
  render();
  content.focus();
}

function setCoverageFilter(dimensionName, value) {
  state.filters.dimension = dimensionName;
  state.filters.value = value;
  dimensionFilter.value = dimensionName;
  populateValueFilter();
  valueFilter.value = value;
  setView("tuples");
}

function render() {
  if (!state.dataset) return;
  content.replaceChildren();
  for (const tab of document.querySelectorAll("[data-view]")) {
    const active = tab.dataset.view === state.view;
    if (active) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  }
  const cases = filteredCases();
  const tuples = filteredTuples(cases);
  viewerStatus.textContent = `${tuples.length} of ${state.dataset.totals.tuples} tuples · ${cases.length} of ${state.dataset.totals.cases} cases`;
  if (state.view === "statistics") renderStatistics(tuples, cases);
  else if (state.view === "dimensions") renderDimensions();
  else if (state.view === "tuples") renderTuples(tuples, cases);
  else if (state.view === "cases") renderCases(cases);
  else renderOverview();
}

function renderOverview() {
  const intro = node("section", "hero panel");
  add(
    intro,
    node("p", "eyebrow", `Dimension set ${state.dataset.dimension_set_version}`),
    node("h2", "", "Dataset overview"),
    node("p", "lede", state.dataset.purpose),
  );

  const identity = node("section", "panel");
  add(identity, node("h3", "", "Validated dataset"));
  const identityFacts = node("div", "two-column");
  add(
    identityFacts,
    labelled("Dimension set", state.dataset.dimension_set_name),
    labelled("Version", state.dataset.dimension_set_version),
  );
  identity.append(identityFacts);
  identity.append(labelled("Dataset directory", state.dataset.dataset_directory));

  const sources = node("section", "panel");
  add(sources, node("h3", "", "Validated source files"));
  const sourceList = node("div", "source-file-list");
  for (const filename of state.dataset.source_files) sourceList.append(node("code", "source-file-name", filename));
  sources.append(sourceList);

  const cohorts = node("section", "panel");
  add(cohorts, node("h3", "", "Case sets"));
  if (state.dataset.cohorts.length === 0) {
    cohorts.append(node("p", "muted", "No case-set documents were discovered."));
  } else {
    for (const cohort of state.dataset.cohorts) {
      const item = node("div", "cohort-row");
      add(
        item,
        node("strong", "", cohort.cohort_id),
        node("span", "muted", `${cohort.case_ids.length} cases · ${cohort.filename}`),
        node("p", "", cohort.description),
      );
      cohorts.append(item);
    }
  }
  cohorts.append(jsonDetails("Shared fixture source (kept separate)", state.dataset.shared_fixture));

  add(content, intro, identity, sources, cohorts);
}

function renderStatistics(tuples, cases) {
  const intro = node("section", "hero panel");
  add(
    intro,
    node("p", "eyebrow", "Coverage overview"),
    node("h2", "", "Dataset statistics"),
    node("p", "lede", "Coverage counts for the complete validated dataset."),
  );

  const metrics = node("section", "metrics", "");
  const values = [
    [state.dataset.totals.dimensions, "Dimensions"],
    [state.dataset.totals.tuples, "Approved tuples"],
    [state.dataset.totals.cases, "Executable cases"],
    [state.dataset.totals.cohorts, "Case sets"],
  ];
  for (const [value, label] of values) {
    const card = node("article", "metric");
    add(card, node("strong", "", value), node("span", "", label));
    metrics.append(card);
  }
  if (tuples.length !== state.dataset.totals.tuples || cases.length !== state.dataset.totals.cases) {
    const filtered = node("article", "filter-summary panel");
    add(
      filtered,
      node("p", "eyebrow", "Active filter result"),
      node("strong", "", `${tuples.length} tuples · ${cases.length} cases`),
    );
    metrics.append(filtered);
  }

  const forms = node("section", "panel");
  add(forms, node("h3", "", "Interaction forms"));
  const formPills = node("div", "pill-row");
  for (const [form, count] of Object.entries(state.dataset.totals.interaction_forms)) {
    formPills.append(pill(`${humanize(form)} · ${count}`));
  }
  forms.append(formPills);

  const heading = node("div", "section-heading");
  add(
    heading,
    node("div", "", ""),
  );
  heading.firstChild.append(node("p", "eyebrow", "Whole dataset"));
  heading.firstChild.append(node("h3", "", "Dimension coverage"));
  heading.append(node("p", "muted", "Counts are non-exclusive when a tuple has multiple values."));
  const coverageSection = node("section", "");
  coverageSection.append(heading);
  const coverageGrid = node("div", "coverage-grid");
  for (const dimension of state.dataset.coverage) {
    const card = node("article", "coverage-card panel");
    add(card, node("h4", "", dimension.dimension_name));
    const table = node("div", "coverage-table");
    const tableHeading = node("div", "coverage-row coverage-heading");
    add(tableHeading, node("span", "", "Value"), node("span", "", "Tuples"), node("span", "", "Cases"));
    table.append(tableHeading);
    for (const value of dimension.values) {
      const row = node("button", "coverage-row coverage-action");
      row.type = "button";
      row.addEventListener("click", () => setCoverageFilter(dimension.dimension_name, value.value));
      add(row, node("span", "", humanize(value.value)), node("span", "", value.tuple_count), node("span", "", value.case_count));
      table.append(row);
    }
    if (dimension.omitted_tuple_count > 0) {
      const row = node("button", "coverage-row coverage-action omitted");
      row.type = "button";
      row.addEventListener("click", () => setCoverageFilter(dimension.dimension_name, "__omitted__"));
      add(row, node("span", "", "Omitted / not applicable"), node("span", "", dimension.omitted_tuple_count), node("span", "", dimension.omitted_case_count));
      table.append(row);
    }
    card.append(table);
    coverageGrid.append(card);
  }
  coverageSection.append(coverageGrid);

  add(content, intro, metrics, forms, coverageSection);
}

function renderDimensions() {
  const heading = node("section", "view-heading");
  add(heading, node("p", "eyebrow", "Coverage model"), node("h2", "", "Dimensions"), node("p", "lede", "Defined axes of meaningful user-input variation and their represented values."));
  content.append(heading);
  const search = state.filters.search.toLocaleLowerCase();
  const coverageById = new Map(state.dataset.coverage.map((item) => [item.dimension_id, item]));
  for (const dimension of state.dataset.dimensions) {
    if (search && !JSON.stringify(dimension).toLocaleLowerCase().includes(search)) continue;
    const coverage = coverageById.get(dimension.id);
    const card = node("article", "dimension-card panel");
    const title = node("div", "section-heading");
    const titleText = node("div", "");
    add(titleText, node("p", "eyebrow", dimension.id), node("h3", "", dimension.name));
    add(title, titleText, pill(`${coverage.values.reduce((sum, item) => sum + item.tuple_count, 0)} assignments`));
    add(card, title, node("p", "lede", dimension.definition));
    const facts = node("div", "two-column");
    add(facts, labelled("Applies when", dimension.applies_when), labelled("Why it matters", dimension.why_it_matters));
    card.append(facts);
    const values = node("div", "value-grid");
    for (const value of dimension.values) {
      const count = coverage.values.find((item) => item.value === value.value);
      const item = node("div", "value-card");
      add(
        item,
        node("strong", "", humanize(value.value)),
        pill(`${count.tuple_count} tuples · ${count.case_count} cases`, count.tuple_count === 0 ? "warning" : ""),
        node("p", "", value.definition || "No definition recorded."),
      );
      values.append(item);
    }
    card.append(values);
    if (Array.isArray(dimension.examples) && dimension.examples.length) {
      const examples = node("div", "examples");
      examples.append(node("h4", "", "Examples"));
      for (const example of dimension.examples) examples.append(node("p", "quote", example.query || JSON.stringify(example)));
      card.append(examples);
    }
    card.append(jsonDetails("Exact dimension record", dimension));
    content.append(card);
  }
}

function renderTuples(tuples, cases) {
  if (!tuples.some((item) => item.tuple_id === state.selectedTuple)) {
    state.selectedTuple = tuples[0]?.tuple_id || null;
  }
  const shell = node("div", "browser-shell");
  const rail = node("aside", "browser-rail");
  const railHeading = node("div", "rail-heading");
  add(railHeading, node("h2", "", "Tuples"), pill(tuples.length));
  rail.append(railHeading);
  if (!tuples.length) rail.append(node("p", "empty", "No tuples match the active filters."));
  for (const tupleItem of tuples) {
    const item = button(tupleItem.tuple_id, "rail-item", () => {
      state.selectedTuple = tupleItem.tuple_id;
      render();
    });
    if (tupleItem.tuple_id === state.selectedTuple) item.setAttribute("aria-current", "true");
    const purpose = node("span", "", tupleItem.record.purpose);
    const count = node("small", "", `${tupleItem.case_ids.length} cases`);
    add(item, purpose, count);
    rail.append(item);
  }
  const detail = node("section", "browser-detail");
  const selected = tuples.find((item) => item.tuple_id === state.selectedTuple);
  if (!selected) {
    detail.append(node("p", "empty", "Adjust or reset the filters to inspect tuples."));
  } else {
    renderTupleDetail(detail, selected, cases);
  }
  add(shell, rail, detail);
  content.append(shell);
}

function renderTupleDetail(parent, tupleItem, filteredCaseItems) {
  const record = tupleItem.record;
  const heading = node("div", "detail-heading");
  const title = node("div", "");
  add(title, node("p", "eyebrow", "Approved tuple"), node("h2", "", tupleItem.tuple_id));
  const actions = node("div", "detail-actions");
  add(actions, tupleHandoffControls(tupleItem), pill(`${tupleItem.case_ids.length} generated inputs`));
  add(heading, title, actions);
  add(parent, heading, node("p", "lede", record.purpose));

  const context = node("section", "two-column");
  add(context, labelled("Coverage basis", record.coverage_basis), labelled("Failure surface", record.failure_surface));
  parent.append(context);
  if (record.material_difference || record.nearest_related_tuple) {
    const relation = node("section", "panel compact");
    add(relation, labelled("Material difference", record.material_difference));
    if (record.nearest_related_tuple) {
      relation.append(button(`Open related tuple ${record.nearest_related_tuple}`, "text-button", () => {
        state.selectedTuple = record.nearest_related_tuple;
        render();
      }));
    }
    parent.append(relation);
  }

  const dimensions = node("section", "panel");
  const dimensionHeading = node("div", "section-heading");
  add(
    dimensionHeading,
    node("h3", "", "Dimension assignments"),
    node("p", "muted", "Select an assignment to see its dimension and value definitions."),
  );
  dimensions.append(dimensionHeading);
  const dimensionGrid = node("div", "dimension-pairs");
  for (const [name, value] of Object.entries(record.dimensions)) {
    dimensionGrid.append(dimensionAssignmentDetails(name, value));
  }
  dimensions.append(dimensionGrid);
  parent.append(dimensions);

  if (record.sequence_context) parent.append(jsonDetails("Declared sequence context", record.sequence_context, true));
  if (record.target_generation_constraint) parent.append(labelled("Generation constraint", record.target_generation_constraint));

  const generated = node("section", "panel");
  const generatedHeading = node("div", "section-heading");
  add(generatedHeading, node("h3", "", "Generated user inputs"), node("span", "muted", `${tupleItem.case_ids.length} total`));
  generated.append(generatedHeading);
  const rows = tupleItem.case_ids.map((caseId) => generatedInputRow(caseById(caseId)));
  const columns = varyingGeneratedInputColumns(
    [
      {
        key: "focalMessage",
        label: "Message under test",
        className: "generated-input-focal",
        width: "minmax(16rem, 3fr)",
        hideWhenConstant: false,
      },
      {
        key: "setupContext",
        label: "Setup context",
        className: "generated-input-context",
        width: "minmax(12rem, 2fr)",
        hideWhenConstant: true,
      },
      {
        key: "caseId",
        label: "Case",
        className: "generated-input-case",
        width: "minmax(6rem, 0.7fr)",
        hideWhenConstant: false,
      },
      {
        key: "interactionForm",
        label: "Interaction",
        className: "generated-input-form",
        width: "minmax(8rem, 1fr)",
        hideWhenConstant: true,
      },
    ],
    rows,
  );
  const inputTable = node("div", "generated-input-table");
  inputTable.style.setProperty("--generated-input-columns", columns.map((column) => column.width).join(" "));
  const inputTableHeading = node("div", "generated-input-heading");
  for (const column of columns) inputTableHeading.append(node("span", "", column.label));
  inputTable.append(inputTableHeading);
  const visibleIds = new Set(filteredCaseItems.map((item) => item.case_id));
  for (const row of rows) {
    const item = button("", `generated-input-row ${visibleIds.has(row.caseId) ? "" : "filtered-out"}`.trim(), () => {
      state.selectedCase = row.caseId;
      setView("cases");
    });
    item.setAttribute("aria-label", `Open case ${row.caseId}: ${row.focalMessage}`);
    for (const column of columns) {
      item.append(generatedInputCell(column.label, row[column.key], column.className));
    }
    inputTable.append(item);
  }
  generated.append(inputTable);
  parent.append(generated);
  parent.append(jsonDetails("Exact tuple record", record));
}

function tupleHandoffControls(tupleItem) {
  const controls = node("div", "handoff-controls");
  const format = node("select", "handoff-format");
  format.setAttribute("aria-label", "Handoff format");
  add(format, option("json", "JSON"), option("markdown", "Markdown"));
  const status = node("span", "handoff-status", "");
  status.setAttribute("role", "status");
  const copy = button("Copy handoff", "quiet-button handoff-copy", async () => {
    const selectedFormat = format.value;
    const originalLabel = copy.textContent;
    copy.disabled = true;
    copy.textContent = "Copying…";
    status.textContent = "";
    try {
      const handoff = buildTupleHandoff(tupleItem);
      const text = selectedFormat === "markdown"
        ? tupleHandoffMarkdown(handoff)
        : JSON.stringify(handoff, null, 2);
      await copyToClipboard(text);
      const formatLabel = selectedFormat === "json" ? "JSON" : "Markdown";
      copy.textContent = "Copied";
      status.textContent = `${formatLabel} handoff copied`;
      clientLog("handoff copied", `${tupleItem.tuple_id} · ${selectedFormat} · ${text.length} characters`);
    } catch (error) {
      copy.textContent = "Copy failed";
      status.textContent = errorMessage(error);
      console.error("[dataset-viewer] handoff copy failed", error);
    } finally {
      window.setTimeout(() => {
        copy.disabled = false;
        copy.textContent = originalLabel;
      }, 1800);
    }
  });
  add(controls, format, copy, status);
  return controls;
}

function buildTupleHandoff(tupleItem) {
  const generatedUserInputs = tupleItem.case_ids.map(
    (caseId) => caseById(caseId).example.user_messages,
  );
  const otherTuples = state.dataset.tuples
    .filter((item) => item.tuple_id !== tupleItem.tuple_id)
    .map((item) => ({
      tuple_id: item.tuple_id,
      record: item.record,
      generated_input_count: item.case_ids.length,
    }));

  return {
    handoff: {
      kind: "evaluation_dataset_tuple_rebuild_context",
      format_version: 1,
      task: `Rebuild or revise the generated user-input cases for tuple ${tupleItem.tuple_id}.`,
      guidance: [
        "Treat the dimension model and current tuple record as canonical source context.",
        "Preserve the current tuple's coverage intent while varying the wording and message sequence of its user inputs.",
        "Use the other tuples as comparison and exclusion context so rebuilt inputs do not drift into another tuple's coverage purpose.",
      ],
    },
    dataset: {
      name: state.dataset.dimension_set_name,
      version: state.dataset.dimension_set_version,
      purpose: state.dataset.purpose,
    },
    current_tuple: {
      tuple_id: tupleItem.tuple_id,
      record: tupleItem.record,
      generated_user_inputs: generatedUserInputs,
    },
    dimensions: state.dataset.dimensions,
    other_tuples: otherTuples,
  };
}

function tupleHandoffMarkdown(handoff) {
  const current = handoff.current_tuple;
  const lines = [
    `# Evaluation dataset handoff: ${current.tuple_id}`,
    "",
    handoff.handoff.task,
    "",
    "## How to use this context",
    "",
    ...handoff.handoff.guidance.map((item) => `- ${item}`),
    "",
    "## Dataset",
    "",
    `- Name: ${handoff.dataset.name}`,
    `- Version: ${handoff.dataset.version}`,
    `- Purpose: ${handoff.dataset.purpose}`,
    "",
    `## Current tuple: ${current.tuple_id}`,
    "",
    current.record.purpose || "No purpose recorded.",
    "",
    "### Exact tuple record",
    "",
    "```json",
    JSON.stringify(current.record, null, 2),
    "```",
    "",
    `### Generated user inputs (${current.generated_user_inputs.length})`,
    "",
    "```json",
    JSON.stringify(current.generated_user_inputs, null, 2),
    "```",
    "",
    "## Dimensions and values",
    "",
  ];

  for (const dimension of handoff.dimensions) {
    const currentAssignments = current.record.dimensions[dimension.name];
    const assigned = new Set(
      currentAssignments === undefined
        ? []
        : (Array.isArray(currentAssignments) ? currentAssignments : [currentAssignments]),
    );
    lines.push(
      `### ${dimension.name} (${dimension.id})`,
      "",
      dimension.definition || "No definition recorded.",
      "",
      `- Applies when: ${dimension.applies_when || "Not declared"}`,
      `- Why it matters: ${dimension.why_it_matters || "Not declared"}`,
      "- Values:",
      ...dimension.values.map((value) => {
        const marker = assigned.has(value.value) ? " **(assigned to current tuple)**" : "";
        return `  - \`${value.value}\`${marker}: ${value.definition || "No definition recorded."}`;
      }),
      "",
    );
  }

  lines.push("## Other tuples", "", "Use these as comparison and exclusion context.", "");
  for (const tupleItem of handoff.other_tuples) {
    const record = tupleItem.record;
    const assignments = Object.entries(record.dimensions)
      .map(([name, value]) => `${name}=${Array.isArray(value) ? value.join(" + ") : value}`)
      .join("; ");
    lines.push(
      `### ${tupleItem.tuple_id}`,
      "",
      `- Purpose: ${record.purpose || "Not declared"}`,
      `- Dimensions: ${assignments}`,
      `- Coverage basis: ${record.coverage_basis || "Not declared"}`,
      `- Failure surface: ${record.failure_surface || "Not declared"}`,
      `- Material difference: ${record.material_difference || "Not declared"}`,
      `- Nearest related tuple: ${record.nearest_related_tuple || "Not declared"}`,
      `- Generated inputs: ${tupleItem.generated_input_count}`,
      "",
    );
  }
  return lines.join("\n");
}

function dimensionAssignmentDetails(dimensionName, assigned) {
  const dimension = dimensionByName(dimensionName);
  const assignedValues = Array.isArray(assigned) ? assigned : [assigned];
  const details = node("details", "dimension-pair");
  const summary = node("summary", "dimension-pair-summary");
  add(
    summary,
    node("span", "field-label", dimensionName),
    node("strong", "", assignedValues.map(humanize).join(", ")),
  );
  summary.title = dimension?.definition || "Open assignment details";
  details.append(summary);

  const definitions = node("div", "dimension-pair-details");
  if (!dimension) {
    definitions.append(node("p", "muted", "No matching dimension definition was found."));
    details.append(definitions);
    return details;
  }

  definitions.append(labelled("Dimension definition", dimension.definition));
  for (const value of assignedValues) {
    const assignedValue = dimension.values.find((item) => item.value === value);
    definitions.append(
      labelled(
        `${humanize(value)} means`,
        assignedValue?.definition || "No value definition recorded.",
      ),
    );
  }
  definitions.append(dimensionValuesTable(dimension, assignedValues));
  definitions.append(labelled("Applies when", dimension.applies_when));
  definitions.append(labelled("Why it matters", dimension.why_it_matters));
  details.append(definitions);
  return details;
}

function dimensionValuesTable(dimension, assignedValues) {
  const section = node("section", "dimension-values-reference");
  section.append(node("h4", "", "All values in this dimension"));
  const assigned = new Set(assignedValues);

  const table = node("table", "dimension-values-table");
  const heading = node("tr", "");
  add(heading, node("th", "", "Value"), node("th", "", "Description"));
  const tableHead = node("thead", "");
  tableHead.append(heading);
  const tableBody = node("tbody", "");
  for (const value of dimension.values) {
    const isAssigned = assigned.has(value.value);
    const row = node("tr", isAssigned ? "assigned-value-row" : "");
    const valueCell = node("th", "");
    valueCell.scope = "row";
    valueCell.append(node("span", "dimension-value-name", humanize(value.value)));
    valueCell.append(node("code", "dimension-value-key", value.value));
    if (isAssigned) valueCell.append(node("span", "assigned-value-label", "Assigned"));
    add(row, valueCell, node("td", "", value.definition || "No value definition recorded."));
    tableBody.append(row);
  }
  add(table, tableHead, tableBody);
  section.append(table);
  return section;
}

function generatedInputRow(caseItem) {
  const focalIndex = caseItem.example.focal_message_index;
  const hasFixedFocalIndex = Number.isInteger(focalIndex);
  const focalMessage = hasFixedFocalIndex
    ? caseItem.example.user_messages[focalIndex]
    : caseItem.example.user_messages.at(-1);
  const setupMessages = hasFixedFocalIndex
    ? caseItem.example.user_messages.slice(0, focalIndex)
    : [];
  let setupContext = "Standalone input";
  if (setupMessages.length) setupContext = setupMessages.join(" → ");
  else if (caseItem.example.required_condition) setupContext = "Runtime-adaptive prelude";
  return {
    focalMessage,
    setupContext,
    caseId: caseItem.case_id,
    interactionForm: humanize(caseItem.interaction_form),
  };
}

function varyingGeneratedInputColumns(columns, rows) {
  return columns.filter(
    (column) => !column.hideWhenConstant || new Set(rows.map((row) => row[column.key])).size > 1,
  );
}

function generatedInputCell(label, value, className) {
  const cell = node("span", `generated-input-cell ${className}`, value);
  cell.dataset.label = label;
  cell.title = value;
  return cell;
}

function renderCases(cases) {
  if (!cases.some((item) => item.case_id === state.selectedCase)) {
    state.selectedCase = cases[0]?.case_id || null;
  }
  const shell = node("div", "browser-shell cases-browser");
  const rail = node("aside", "browser-rail");
  const railHeading = node("div", "rail-heading");
  add(railHeading, node("h2", "", "Cases"), pill(cases.length));
  rail.append(railHeading);
  if (!cases.length) rail.append(node("p", "empty", "No cases match the active filters."));
  for (const caseItem of cases) {
    const item = button(caseItem.case_id, "rail-item", () => {
      state.selectedCase = caseItem.case_id;
      render();
    });
    if (caseItem.case_id === state.selectedCase) item.setAttribute("aria-current", "true");
    const message = caseItem.example.user_messages.at(-1) || "";
    add(
      item,
      node("span", "", message),
      node("small", "", `${caseItem.tuple_id} · ${humanize(caseItem.interaction_form)}`),
    );
    rail.append(item);
  }
  const detail = node("section", "browser-detail");
  const selected = cases.find((item) => item.case_id === state.selectedCase);
  if (!selected) detail.append(node("p", "empty", "Adjust or reset the filters to inspect cases."));
  else renderCaseDetail(detail, selected);
  add(shell, rail, detail);
  content.append(shell);
}

function renderCaseDetail(parent, caseItem) {
  const tupleItem = tupleById(caseItem.tuple_id);
  const heading = node("div", "detail-heading");
  const title = node("div", "");
  add(title, node("p", "eyebrow", "Executable evaluation case"), node("h2", "", caseItem.case_id));
  add(heading, title, pill(humanize(caseItem.interaction_form), "accent"));
  add(parent, heading, node("p", "lede", tupleItem.record.purpose));

  const badges = node("div", "pill-row");
  badges.append(pill(`Tuple ${caseItem.tuple_id}`));
  for (const cohortId of caseItem.cohort_ids) badges.append(pill(`Case set ${cohortId}`));
  if (!caseItem.cohort_ids.length) badges.append(pill("No case-set membership", "subtle"));
  parent.append(badges);

  const conversation = node("section", "panel");
  add(conversation, node("h3", "", "Complete generated user input"));
  caseItem.example.user_messages.forEach((message, index) => {
    const messageCard = node("article", "message-card");
    const meta = node("div", "message-meta");
    add(meta, node("span", "field-label", `User message ${index + 1}`));
    if (isMessageUnderTest(caseItem, index)) meta.append(pill("Message under test", "accent"));
    add(messageCard, meta, node("p", "message-text", message));
    conversation.append(messageCard);
  });
  if (caseItem.example.required_condition) conversation.append(labelled("Required condition", caseItem.example.required_condition));
  if (caseItem.example.focal_user_behavior) conversation.append(labelled("Behavior under test", caseItem.example.focal_user_behavior));
  parent.append(conversation);

  parent.append(renderCaseGenerationContext(tupleItem));

  const prelude = node("section", "panel");
  add(prelude, node("h3", "", "Recorded prelude"));
  if (!caseItem.prelude.length) prelude.append(node("p", "muted", "No prelude is declared for this case."));
  caseItem.prelude.forEach((step, index) => {
    const row = node("div", "prelude-step");
    add(row, node("span", "step-number", index + 1), node("strong", "", humanize(step.kind)), node("code", "", step.content || step.action || "assert idle"));
    prelude.append(row);
  });
  parent.append(prelude);

  const fixture = node("section", "panel");
  const fixtureHeading = node("div", "section-heading");
  add(fixtureHeading, node("h3", "", "Recorded case fixture"), node("span", "muted", "Not merged with the shared fixture"));
  fixture.append(fixtureHeading);
  const accounts = caseItem.fixture.accounts || [];
  if (!accounts.length) fixture.append(node("p", "muted", "No case-specific accounts are declared."));
  for (const account of accounts) {
    const row = node("div", "account-row");
    add(
      row,
      node("strong", "", account.name),
      node("span", "muted", `${account.type} · ${account.currency}`),
      node("code", "", `${account.opening_balance_minor} minor units`),
    );
    fixture.append(row);
  }
  fixture.append(jsonDetails("Exact recorded fixture", caseItem.fixture));
  fixture.append(jsonDetails("Shared fixture source (separate)", state.dataset.shared_fixture));
  parent.append(fixture);

  parent.append(jsonDetails("Exact generated-input record", caseItem.example));
}

function isMessageUnderTest(caseItem, index) {
  const focalIndex = caseItem.example.focal_message_index;
  if (Number.isInteger(focalIndex)) return index === focalIndex;
  return Boolean(caseItem.example.required_condition)
    && index === caseItem.example.user_messages.length - 1;
}

function renderCaseGenerationContext(tupleItem) {
  const record = tupleItem.record;
  const context = node("section", "panel generation-context");
  const heading = node("div", "section-heading");
  const title = node("div", "");
  add(
    title,
    node("p", "eyebrow", "Generation context"),
    node("h3", "", `Generated from tuple ${tupleItem.tuple_id}`),
  );
  const openTuple = button(`Open full tuple ${tupleItem.tuple_id}`, "quiet-button", () => {
    state.selectedTuple = tupleItem.tuple_id;
    setView("tuples");
  });
  add(heading, title, openTuple);
  add(context, heading, node("p", "lede", record.purpose));

  const basis = node("div", "two-column");
  add(
    basis,
    labelled("Coverage basis", record.coverage_basis),
    labelled("Failure surface", record.failure_surface),
  );
  context.append(basis);

  const dimensionHeading = node("div", "generation-subheading");
  add(
    dimensionHeading,
    node("h4", "", "Assigned dimension definitions"),
    node(
      "p",
      "muted",
      "These are the dimension values that the generating tuple assigned to this input.",
    ),
  );
  context.append(dimensionHeading);

  const definitions = node("div", "assigned-dimensions");
  for (const [dimensionName, assigned] of Object.entries(record.dimensions)) {
    const dimension = dimensionByName(dimensionName);
    const card = node("article", "assigned-dimension");
    const cardHeading = node("div", "assigned-dimension-heading");
    add(cardHeading, node("strong", "", dimensionName));
    const assignedValues = Array.isArray(assigned) ? assigned : [assigned];
    for (const value of assignedValues) cardHeading.append(pill(humanize(value), "accent"));
    card.append(cardHeading);

    if (!dimension) {
      card.append(node("p", "muted", "No matching dimension definition was found."));
      definitions.append(card);
      continue;
    }

    card.append(node("p", "dimension-definition", dimension.definition));
    for (const value of assignedValues) {
      const assignedValue = dimension.values.find((item) => item.value === value);
      const valueDefinition = node("div", "assigned-value-definition");
      add(
        valueDefinition,
        node("span", "field-label", `${humanize(value)} means`),
        node("p", "", assignedValue?.definition || "No value definition recorded."),
      );
      card.append(valueDefinition);
    }
    card.append(labelled("Applies when", dimension.applies_when));
    definitions.append(card);
  }
  context.append(definitions);
  context.append(jsonDetails("Exact generating tuple record", record));
  return context;
}

function humanize(value) {
  return String(value ?? "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function populateValueFilter() {
  valueFilter.replaceChildren(option("", "All values"));
  const dimension = state.dataset.dimensions.find((item) => item.name === dimensionFilter.value);
  valueFilter.disabled = !dimension;
  if (!dimension) return;
  for (const value of dimension.values) valueFilter.append(option(value.value, humanize(value.value)));
  valueFilter.append(option("__omitted__", "Omitted / not applicable"));
}

function populateControls() {
  for (const dimension of state.dataset.dimensions) dimensionFilter.append(option(dimension.name, dimension.name));
  for (const form of Object.keys(state.dataset.totals.interaction_forms)) formFilter.append(option(form, humanize(form)));
  for (const cohort of state.dataset.cohorts) cohortFilter.append(option(cohort.cohort_id, cohort.cohort_id));
  for (const filename of state.dataset.source_files) sourceFile.append(option(filename, filename));

  for (const tab of document.querySelectorAll("[data-view]")) {
    tab.addEventListener("click", () => setView(tab.dataset.view));
  }
  searchFilter.addEventListener("input", () => {
    state.filters.search = searchFilter.value.trim();
    render();
  });
  dimensionFilter.addEventListener("change", () => {
    state.filters.dimension = dimensionFilter.value;
    state.filters.value = "";
    populateValueFilter();
    render();
  });
  valueFilter.addEventListener("change", () => {
    state.filters.value = valueFilter.value;
    render();
  });
  formFilter.addEventListener("change", () => {
    state.filters.form = formFilter.value;
    render();
  });
  cohortFilter.addEventListener("change", () => {
    state.filters.cohort = cohortFilter.value;
    render();
  });
  document.getElementById("reset-filters").addEventListener("click", () => {
    state.filters = {search: "", dimension: "", value: "", form: "", cohort: ""};
    searchFilter.value = "";
    dimensionFilter.value = "";
    valueFilter.value = "";
    formFilter.value = "";
    cohortFilter.value = "";
    populateValueFilter();
    render();
  });
  document.getElementById("source-open").addEventListener("click", () => {
    sourceDialog.showModal();
    loadSource();
  });
  sourceFile.addEventListener("change", loadSource);
}

async function loadSource() {
  const filename = sourceFile.value;
  if (!filename) return;
  sourceStatus.textContent = `Loading ${filename}…`;
  sourceJson.textContent = "";
  try {
    const response = await fetch(`/api/dataset/sources/${encodeURIComponent(filename)}`, {cache: "no-store"});
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    sourceStatus.textContent = filename;
    sourceJson.textContent = JSON.stringify(payload.document, null, 2);
  } catch (error) {
    sourceStatus.textContent = `Could not load source: ${error.message}`;
  }
}

function initializeTheme() {
  const toggle = document.getElementById("theme-toggle");
  const stored = localStorage.getItem("wallet-evals-dataset-theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = stored ? stored === "dark" : prefersDark;
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  toggle.setAttribute("aria-pressed", String(dark));
  toggle.textContent = dark ? "Light theme" : "Dark theme";
  toggle.addEventListener("click", () => {
    const nextDark = document.documentElement.dataset.theme !== "dark";
    document.documentElement.dataset.theme = nextDark ? "dark" : "light";
    localStorage.setItem("wallet-evals-dataset-theme", nextDark ? "dark" : "light");
    toggle.setAttribute("aria-pressed", String(nextDark));
    toggle.textContent = nextDark ? "Light theme" : "Dark theme";
  });
}

function showFileLaunchInstructions() {
  try {
    initializeTheme();
  } catch (error) {
    console.warn("[dataset-viewer] theme initialization failed", error);
  }
  const command = "uv run wallet_evals view-dataset";
  const link = node("a", "text-button", "Open http://127.0.0.1:8766");
  link.href = "http://127.0.0.1:8766";
  viewerStatus.textContent = "Launch the dataset viewer server to continue.";
  content.replaceChildren();
  const notice = node("section", "panel");
  add(
    notice,
    node("p", "eyebrow", "Server required"),
    node("h2", "", "This HTML file is not the running viewer"),
    node("p", "lede", "From the wallet-evals project, run:"),
    node("pre", "json-block", command),
    node("p", "muted", "Then use the local HTTP address printed in the terminal."),
    link,
  );
  content.append(notice);
  console.error(`[dataset-viewer] opened as a file; run: ${command}`);
}

async function initialize() {
  clientLog("boot", "Dataset viewer script started");
  try {
    try {
      initializeTheme();
      clientLog("theme", document.documentElement.dataset.theme);
    } catch (error) {
      console.warn("[dataset-viewer] theme initialization failed; using the light theme", error);
      document.documentElement.dataset.theme = "light";
    }
    viewerStatus.textContent = "Requesting validated dataset…";
    clientLog("request", "GET /api/dataset");
    const response = await fetch("/api/dataset", {cache: "no-store"});
    clientLog("response", `${response.status} · ${response.headers.get("content-length") || "unknown"} bytes`);
    viewerStatus.textContent = "Reading validated dataset…";
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    clientLog("parse", `${payload.totals.tuples} tuples · ${payload.totals.cases} cases`);
    viewerStatus.textContent = "Building coverage views…";
    state.dataset = payload;
    datasetPath.textContent = payload.dataset_directory;
    populateControls();
    render();
    clientLog("ready", "Coverage overview rendered");
  } catch (error) {
    showFatal(error, "initialization");
  }
}

if (window.location.protocol === "file:") {
  showFileLaunchInstructions();
} else {
  initialize().catch((error) => showFatal(error, "initialization promise"));
}
