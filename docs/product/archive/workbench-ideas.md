# Evaluation Design Workbench Experiment Ideas
## Status and purpose

This document is an unvalidated experiment backlog for the

[Evaluation Design Workbench](product-frame.md). It is not a feature backlog, delivery plan, or

commitment to change the current dataset viewer.

Each experiment tests one product assumption with the smallest useful trial. Promote an idea into

product scope only after recording what a domain expert did, what evidence the trial produced, and

which decision that evidence supports.

All experiments preserve the workbench boundary:

- canonical evaluation sources remain immutable inside the workbench;
- source facts, deterministic findings, expert notes, and proposed changes stay distinguishable;
- construction happens through explicit handoffs to an external workflow;
- SUT execution and trace judgment remain separate; and
- missing product intent remains a visible gap rather than an invitation to invent it.

## Suggested order

| Wave | Experiment | Primary assumption | Effort | Existing capability reused |
| --- | --- | --- | --- | --- |
| 1 | 1. Evaluation brief sufficiency | A compact brief can anchor coverage review. | Low, manual | Dataset purpose, exact sources, source references, and open questions. |
| 1 | 2. Artifact tabs versus intent lenses | Intent-led lenses reduce reconstruction and navigation work. | Low, manual or paper prototype | Existing Overview, Statistics, Dimensions, Tuples, and Cases views. |
| 1 | 3. Requirement-to-case traceability map | Traceability reveals gaps that raw counts cannot. | Medium, derived table | Stable dimension, tuple, and case identities plus coverage counts. |
| 1 | 4. Tuple handoff A/B test | Layered context produces safer agent-assisted revisions. | Low, manual | Current JSON and Markdown tuple handoffs. |
| 2 | 5. Open-question impact map | Product ambiguity becomes actionable when linked to affected artifacts. | Low, data or UI spike | Existing open product questions and exact-source inspection. |
| 2 | 6. Evidence basket and local workspace | Experts benefit from retaining selected evidence and notes across lenses. | Medium, UI spike | Identity navigation, filters, clipboard support, and browser-local theme state. |
| 2 | 7. Risk-aware Balance lens | Coverage needs rationale, risk, and uncertainty, not only counts. | Medium, data and UI spike | Statistics, filters, omitted values, zero coverage, and cohorts. |
| 2 | 8. Grounding review checklist | A focused review catches case-quality defects before execution. | Low, manual or UI spike | Complete cases, tuple provenance, fixtures, preludes, and message sequences. |
| 3 | 9. External revision loop | Guided handoffs can support construction without direct editing. | High, integration probe | Handoff copy, startup validation, exact records, and viewer reload. |
| 3 | 10. Trace-to-design feedback handoff | Trace findings can inform coverage without merging the two viewers. | Medium, manual integration probe | Stable case identity and the separate trace viewer. |

Wave numbers express dependency and learning order, not delivery commitments. Stop or revise an idea

when its stop signal appears. Do not advance it merely because a prototype was built.

## Wave 1: test the product model manually
### 1. Evaluation brief sufficiency

**Status:** Unvalidated

**Lenses:** Frame, Model, Balance

**Hypothesis:** A concise, source-linked evaluation brief gives a domain expert enough normative

context to assess why coverage exists and what is missing without repeatedly reconstructing product

intent from specifications, architecture documents, and tuple prose.

**Smallest useful trial:** Draft one human-readable Wallet evaluation brief from existing product and

architecture sources. Include the participant goal, decision or knowledge need, uncertainty,

evaluation question, SUT boundary, applicable jobs and guarantees, critical failures, coverage

requirements, source references, exclusions, and open questions. Treat the draft as disposable and

non-canonical.

**Domain-expert task:** Use only the draft brief and the current viewer to explain the coverage intent

of a small but varied selection: one baseline tuple, one ambiguous tuple, one contextual sequence,

one compound request, and one repeat or cancellation case. Identify coverage that appears unsupported

and product questions that block a conclusion.

**Evidence to collect:**

- which brief fields the expert actually uses;
- which missing facts force them back to source documents;
- which tuple or case decisions cannot be traced to the brief;
- whether the brief exposes uncertainty rather than hiding it; and
- time spent reconstructing context outside the brief.

**Success signal:** The expert can explain the selected coverage, identify genuine gaps, and state

remaining uncertainty without relying on unreferenced product knowledge.

**Stop or revise signal:** The brief becomes a long restatement of all source documents, or the

expert still needs to reconstruct the product boundary before judging most coverage choices.

**Decision informed:** The minimum useful content and structure of a future versioned evaluation

brief.

**Prerequisites:** One Wallet domain expert and access to the current product, architecture, and

dataset sources.

**Existing capability reused:** Dataset purpose, tuple coverage basis, failure surfaces, source

materials, open questions, and exact-source inspection.

### 2. Artifact tabs versus intent lenses

**Status:** Unvalidated

**Lenses:** Frame, Model, Compose, Ground, Balance, Handoff

**Hypothesis:** Organizing the same evidence around expert questions reduces backtracking and makes

the expected result of each investigation clearer than artifact-type navigation alone.

**Smallest useful trial:** Create a paper, document, or lightweight clickable wrapper with six lens

prompts. Do not change the underlying dataset views. For each prompt, point to the existing view or

views that contain the needed evidence.

**Domain-expert task:** Complete two comparable coverage-review exercises: one starting from the

current artifact tabs and one following the lens prompts. Ask the expert to locate a coverage gap,

inspect the affected tuple and cases, and prepare a revision handoff.

**Evidence to collect:**

- where the expert expects to find each kind of evidence;
- navigation errors, backtracking, and repeated context reconstruction;
- whether lens names and governing questions are understood without explanation;
- which lenses require evidence from several existing views; and
- whether the expert can describe the intended output of each lens.

**Success signal:** The lens path reduces avoidable navigation and the expert can predict what each

lens is for and when its investigation is complete.

**Stop or revise signal:** Lens labels feel more abstract than the artifacts, produce more context

switching, or obscure direct access to dimensions, tuples, and cases.

**Decision informed:** Whether one workbench shell should organize navigation by intent, and which

lens names or boundaries need revision.

**Prerequisites:** The current viewer and two comparable review tasks that do not reuse the same

answer.

**Existing capability reused:** All current views, shared filters, tuple-to-case navigation, and

exact evidence.

### 3. Requirement-to-case traceability map

**Status:** Unvalidated

**Lenses:** Frame, Model, Compose, Ground, Balance

**Hypothesis:** An explicit path from coverage requirement to dimension, tuple, and executable case

reveals unsupported cases and uncovered requirements that dimension-value totals cannot show.

**Smallest useful trial:** Select three materially different coverage requirements from the draft

brief. Build a derived table mapping each requirement to relevant dimensions and values, tuples, and

case identities. Include an explicit reason for every relationship and allow an `unmapped` result.

**Domain-expert task:** Review the map in both directions: start from each requirement to inspect its

evidence, then start from selected tuples and cases to identify the requirement they support.

**Evidence to collect:**

- requirements with no credible tuple or case coverage;
- tuples or cases with no traceable requirement;
- relationships that depend on unstated expert interpretation;
- dimensions that are descriptive but do not change a failure surface; and
- whether the map changes the expert's priorities beyond what raw counts suggested.

**Success signal:** The map identifies actionable omissions, unsupported coverage, or unclear

relationships that the expert agrees are materially important.

**Stop or revise signal:** Most relationships require subjective inference because the brief or

tuple rationale is too vague, or the map merely repeats existing counts without changing a decision.

**Decision informed:** Whether traceability should become a source contract, a derived workbench

projection, or both.

**Prerequisites:** A draft evaluation brief with at least three reviewed coverage requirements.

**Existing capability reused:** Stable dimension, tuple, and case identities, tuple rationales, and

coverage totals.

### 4. Tuple handoff A/B test

**Status:** Unvalidated

**Lenses:** Compose, Ground, Handoff

**Hypothesis:** A layered handoff grounded in the evaluation question and selected evidence helps an

agent revise cases with less intent drift than the current tuple-scoped context alone.

**Smallest useful trial:** Prepare two handoffs for the same tuple revision. Use the current copied

tuple handoff as the baseline. Extend the second with the evaluation-question identity, relevant

coverage requirement, selected source excerpts, expert notes, explicit constraints, unresolved

questions, requested changes, and acceptance checks.

**Domain-expert task:** Give each handoff to a fresh agent session and request a proposed revision.

Review both proposals without allowing either agent to inspect unlisted repository context.

**Evidence to collect:**

- preservation of tuple purpose, failure surface, dimensions, and interaction form;
- unintended drift into another tuple's coverage;
- invented product assumptions;
- realism and variation of proposed inputs;
- corrective turns required before the proposal is acceptable; and
- handoff size and information the agent did not use.

**Success signal:** The layered handoff produces a materially safer proposal with fewer corrections

while retaining exact provenance and a manageable amount of context.

**Stop or revise signal:** Both handoffs perform equivalently, or the layered version adds volume

without improving constraint preservation or review effort.

**Decision informed:** The minimum content of lens-specific and cumulative workbench handoffs.

**Prerequisites:** One reviewed tuple revision task, acceptance checks agreed before the trial, and

two isolated agent sessions.

**Existing capability reused:** Current tuple handoff generation in JSON or Markdown.

## Wave 2: test focused workbench capabilities
### 5. Open-question impact map

**Status:** Unvalidated

**Lenses:** Frame, Model, Compose, Handoff

**Hypothesis:** Product ambiguity becomes actionable when each open question is connected to the

coverage artifacts and decisions it can invalidate.

**Smallest useful trial:** Derive a temporary impact table from existing open product questions. For

each question, record the source, affected dimensions, tuples and cases, the reason for the impact,

the responsible decision owner, and a possible clarification handoff. Do not fabricate links when

the impact is unknown.

**Domain-expert task:** Select one open question, inspect every proposed impact, remove unsupported

links, add missing links, and prepare a focused clarification handoff.

**Evidence to collect:**

- how many proposed relationships survive expert review;
- artifacts whose validity genuinely depends on the unresolved question;
- questions that are too broad to support a focused handoff;
- missing ownership or source evidence; and
- whether the map changes which ambiguity the expert addresses first.

**Success signal:** The expert can identify a bounded set of affected artifacts and prepare a

source-grounded clarification request without treating the ambiguity as resolved.

**Stop or revise signal:** Impact relationships are mostly speculative, or the map creates false

confidence by making broad questions look mechanically traceable.

**Decision informed:** Whether open questions deserve a first-class Frame projection and how impact

relationships should be established.

**Prerequisites:** Existing source questions and one expert able to judge their product impact.

**Existing capability reused:** `open_product_questions`, source-material records, tuple rationales,

identity navigation, and exact-source inspection.

### 6. Evidence basket and local workspace

**Status:** Unvalidated

**Lenses:** All lenses, especially Handoff

**Hypothesis:** Experts need a lightweight way to retain selected evidence, notes, and questions

across lenses and interruptions before assembling a handoff.

**Smallest useful trial:** Prototype a browser-local evidence basket. Let the expert select a few

dimensions, tuples, cases, source excerpts, and findings; add a note to each; close and reopen the

page; clear the workspace; and simulate a changed dataset identity that marks the saved workspace as

stale.

**Domain-expert task:** Investigate one cross-lens coverage concern, collect the relevant evidence,

pause the review, resume it, and produce a focused handoff from the retained selection.

**Evidence to collect:**

- evidence the expert chooses to retain and later removes;
- whether notes are attached at the right granularity;
- time and navigation needed to resume the investigation;
- confusion between local notes and canonical source facts;
- behavior when the source identity changes; and
- privacy or control concerns about browser-local retention.

**Success signal:** The expert resumes without rediscovering the evidence, understands which content

is local, and does not reuse stale findings against changed sources.

**Stop or revise signal:** Experts rarely revisit selections, local state is mistaken for source

truth, or stale-state handling causes more work than reconstructing the investigation.

**Decision informed:** Whether browser-local workspace state is justified and which records, notes,

version keys, reset controls, and export behavior it needs.

**Prerequisites:** A disposable UI spike and two source-identity states.

**Existing capability reused:** Stable identities, current selections and filters, clipboard support,

and the established browser-local theme preference.

### 7. Risk-aware Balance lens

**Status:** Unvalidated

**Lenses:** Frame, Balance

**Hypothesis:** Domain experts make better coverage decisions when counts are interpreted through

product importance, failure severity, uncertainty, and deliberate exclusions rather than an implied

goal of uniform representation.

**Smallest useful trial:** Choose several coverage requirements and annotate them with source-backed,

ordinal descriptions of importance, failure consequence, uncertainty, and intentional exclusions.

Place those descriptions beside the current tuple and case counts. Avoid a composite numeric score.

**Domain-expert task:** Prioritize three coverage changes using raw statistics first, then repeat the

task with the risk-aware context. Explain every change in priority.

**Evidence to collect:**

- decisions that change and the source-grounded reason;
- zero or low coverage that is deliberate rather than deficient;
- high counts that lack product justification;
- categories that experts cannot assess from available sources; and
- whether ordinal labels create disagreement or false precision.

**Success signal:** The added context helps the expert distinguish a real gap from intentional

allocation and produces a more defensible revision priority.

**Stop or revise signal:** The annotations merely restate opinion, encourage pseudo-scoring, or do

not change interpretation beyond the raw coverage table.

**Decision informed:** Which normative context the Balance lens needs and whether it belongs in the

evaluation brief or a separate allocation model.

**Prerequisites:** A reviewed draft brief and source evidence for the selected requirements.

**Existing capability reused:** Dimension-value statistics, omitted and zero-coverage rows, cohorts,

and shared filters.

### 8. Grounding review checklist

**Status:** Unvalidated

**Lenses:** Ground, Handoff

**Hypothesis:** A short, evidence-oriented checklist helps experts detect case-construction defects

before execution without turning review into mechanical approval.

**Smallest useful trial:** Apply a provisional checklist to ten varied cases spanning standalone,

fixed-sequence, and adaptive forms. Review realism, meaningful variation, hidden tuple leakage,

message-under-test clarity, sequence coherence, fixture and prelude fit, executability, provenance,

and near-duplication.

**Domain-expert task:** Review each case from its complete generated input and context, record only

observable concerns, and create one handoff for the highest-value revision.

**Evidence to collect:**

- defects found that validation does not catch;
- checklist items that require unavailable product context;
- repeated findings across cases;
- disagreement between reviewers when a second expert is available;
- review time and signs of checkbox fatigue; and
- whether findings translate into bounded changes.

**Success signal:** The checklist finds materially important, reproducible defects and helps create a

focused handoff without hiding expert uncertainty.

**Stop or revise signal:** Findings are mostly stylistic, checklist results vary without explainable

domain reasons, or review effort exceeds the value of defects found.

**Decision informed:** Which Ground-lens prompts and findings are useful enough to standardize.

**Prerequisites:** Ten representative cases and, when possible, two independent domain reviewers for

a small overlap sample.

**Existing capability reused:** Complete message sequences, message-under-test marking, tuple context,

fixtures, preludes, interaction forms, and exact case JSON.

## Wave 3: test the workbench loops
### 9. External revision loop

**Status:** Unvalidated

**Lenses:** Compose, Ground, Balance, Handoff

**Hypothesis:** A domain expert can construct evaluation changes safely through a guided external

workflow while the workbench remains read-only.

**Smallest useful trial:** Select one bounded tuple or case revision. Assemble a cumulative handoff,

give it to an agent or repository workflow in a disposable branch, review the proposed patch, run the

existing dataset validation, reload the viewer, and compare the affected lenses before and after.

**Domain-expert task:** Define the change and acceptance checks, inspect the proposal, reject invented

assumptions, approve or revise it through the normal repository workflow, and confirm whether the

reloaded design now answers the original gap.

**Evidence to collect:**

- source identity and constraints preserved through the handoff;
- corrections required before validation succeeds;
- unexpected changes outside the requested scope;
- whether coverage projections update as expected;
- treatment of old browser-local notes after source identity changes; and
- total expert effort across handoff, review, validation, and reload.

**Success signal:** A bounded, validated revision completes without direct workbench writes, preserves

provenance, and resolves the stated design gap without collateral coverage drift.

**Stop or revise signal:** The external workflow repeatedly loses source constraints, the expert must

reconstruct most context manually, or the before-and-after views cannot explain the result.

**Decision informed:** Whether the guided-handoff boundary is viable as the construction model and

what validation or comparison support it needs.

**Prerequisites:** A successful handoff trial, an isolated revision branch, existing dataset

validation, and a reviewed acceptance check.

**Existing capability reused:** Tuple handoff, exact records, startup validation, coverage projection,

and reload of changed canonical sources.

### 10. Trace-to-design feedback handoff

**Status:** Unvalidated

**Lenses:** Frame, Compose, Ground, Balance, Handoff

**Hypothesis:** A small, identity-based feedback packet can carry a source-recorded execution finding

back into coverage review without merging trace inspection, judgment, or root-cause analysis into the

workbench.

**Smallest useful trial:** Choose one saved case trace and one domain-expert finding already supported

by visible evidence. Manually create a packet containing run, case-execution, case, and tuple

identities; the cited trace evidence; the observed finding; the coverage assumption to review; and

explicit uncertainty. Do not include a root-cause claim or proposed SUT fix.

**Domain-expert task:** Start from the feedback packet, locate the corresponding design artifacts,

and decide whether to revise a requirement, dimension, tuple, case, fixture, allocation, or nothing.

Prepare a design handoff only if the evidence supports one.

**Evidence to collect:**

- whether identities locate the intended artifacts without heuristic joins;
- additional trace context needed to interpret the finding;
- pressure to turn the packet into a verdict or diagnosis;
- cases where observed behavior does not justify a coverage change;
- uncertainty preserved through the review; and
- whether the packet yields a bounded design question.

**Success signal:** The expert reaches the right design context, preserves the evidence boundary, and

either creates a grounded revision handoff or explicitly decides that no coverage change follows.

**Stop or revise signal:** Identity cannot support the join, the packet omits evidence needed for

interpretation, or reviewers routinely infer causality or rewrite the trace.

**Decision informed:** The minimum identity and evidence contract for a future trace-feedback bridge.

**Prerequisites:** One validated saved run, one evidence-linked expert finding, and stable case and

tuple identity.

**Existing capability reused:** The separate trace viewer, saved run evidence, case identity, tuple

provenance, and exact-source inspection.

## Promotion rules

- Record a result before changing the product frame, source contract, or implementation roadmap.
- Prefer the smallest trial that can disprove the assumption. A polished prototype is not evidence
  that the underlying job exists.
- Do not combine several untested ideas in one trial when the result would not identify which idea
  helped.
- Treat a success signal as evidence to continue, not automatic approval to implement.
- When a stop signal appears, retire the idea or change the assumption before building more.
- Preserve negative and inconclusive results. They are product knowledge and prevent repeated work.
- Keep experiment artifacts disposable unless a separate review promotes them into a supported
  source or interface.

## Experiment result template

```markdown
# Workbench experiment result: <experiment ID and title>

- Status: completed | stopped | inconclusive
- Date:
- Participant role and relevant domain experience:
- Facilitator or observer:
- Source identities and versions:
- Prototype or setup:
- Task performed:

## Observations

### Source facts used

### Deterministic findings shown by the prototype

### Participant notes and behavior

### Proposed changes or follow-up questions

## Signals

- Success signals observed:
- Stop or revise signals observed:
- Unexpected evidence:

## Decision

- Promote | iterate | stop | gather more evidence
- Decision informed:
- Rationale and limitations:

## Follow-up

- Owner:
- Next action:
- Related artifacts:
```

Do not record private model reasoning in an experiment result. Link exact source evidence by stable

identity, and label facilitator interpretation separately from participant statements.
