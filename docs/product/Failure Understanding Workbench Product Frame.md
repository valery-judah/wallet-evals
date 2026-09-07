# Failure Understanding Workbench Product Frame
## Product outcome

The Failure Understanding Workbench helps domain experts inspect execution evidence, decide whether observed SUT behavior passed or failed, and preserve concise evidence-grounded failure observations that can support later failure analysis.

The first product slice is deliberately narrow:

```text
execution result
    ↓
case trace
    ↓ domain-expert review
pass

or

fail
    + short first-observable-failure note
    + evidence reference
```

This review is the entry point to failure understanding. It does not require a predefined failure taxonomy, a formal evaluation criterion, or a complete explanation of root cause.

The expert may judge the trace using applicable product knowledge, domain expertise, case context, requirements, policies, and other legitimate knowledge available to them.

Later failure-understanding work may compare failure observations across traces, develop recurring codes and categories, build a failure model, operationalise selected failure modes, and aggregate measurements. Those activities are outside the first product slice and may initially happen in other tools.

The current trace viewer is an implementation surface that provides evidence for this product direction. "Viewer" describes the current interface. **Failure Understanding Workbench** describes the broader product responsibility.

## Product boundary

The workbench begins when an attributable execution result exists and a domain expert needs to inspect one or more case traces.

For the first product slice, the unit of review is one case execution evidenced by one saved case trace.

The workbench ends the first-phase review when the expert records either:

- **pass**; or
- **fail**, with a short description of the first observable failure and a reference to the supporting trace evidence.

If the trace does not contain enough attributable evidence for the expert to make a pass/fail judgment, the workbench may record that the review could not be completed and why.

The workbench does not execute or replay the SUT, alter saved traces, infer missing evidence, or determine correctness on the expert's behalf.

## Position in the evaluation lifecycle

```text
Evaluation Design Workbench
    ↓ defines evaluation intent and cases
Evaluation Execution Subsystem
    ↓ produces execution results and case traces
Failure Understanding Workbench
    ↓ produces expert reviews and failure observations
Later analysis / operationalisation / measurement
    ↓ may produce failure models, labels, and evaluation results
```

The Failure Understanding Workbench owns expert interpretation of observed behavior. It does not own SUT execution or evaluation-design construction.

The first product slice stops before cross-trace synthesis and measurement.

## Governing question

For the first product slice:

> Looking at this complete case execution, did the SUT behavior pass or fail, and if it failed, what is the first observable problem in the trace?

For later failure-understanding work:

> Across the failures we have observed, what recurring failure patterns exist, how do they differ, and what evidence is required to recognize them consistently?

The second question defines the longer-term product direction. It is not a requirement for the first implementation.

## Actors

- **Domain expert:** The primary user. Reviews SUT behavior using their product and domain knowledge, records pass/fail, and describes observed failures in concrete terms.
- **Evaluation engineer:** Maintains execution, trace, identity, and review contracts so evidence can be inspected and later analysis can retain provenance.
- **Failure analyst:** May be the same domain expert or another analyst. Compares observations across traces and develops deeper failure structure in later phases.
- **Product or engineering team:** Uses reviewed failures, later failure models, and measurements to understand SUT behavior and guide improvement.

An LLM may later assist with organizing observations, suggesting groupings, or applying operationalised failure modes. Such assistance does not replace domain-expert interpretation of ambiguous product or domain behavior.

## First-phase operating model

```text
Open an execution result
    ↓
Select a case trace
    ↓
Review the case execution as a whole
    ↓
Inspect complete evidence as needed
    ↓
Record pass or fail
    ↓
If fail:
    record first observable failure
    + evidence reference
```

The normal task is deliberately small. The expert should not have to create a taxonomy, choose a failure category, assign severity, identify root cause, or exhaustively annotate every downstream symptom before recording a failed review.

## Review unit
### Case execution evidenced by a trace

The first product slice reviews one case execution as a whole using the attributable evidence in its saved case trace.

The trace may contain:

- case purpose and context;
- participant actions or typed actions;
- complete SUT responses;
- response-adaptive choices;
- named observations;
- product-visible errors;
- execution and configuration provenance; and
- optional diagnostic evidence.

The meaning of a response may depend on earlier interaction context or later observable effects. The default review therefore follows the whole trajectory instead of judging an isolated response string.

### Step outcome

A step outcome is the SUT's complete response to one identified trajectory step together with observations attributable to that point.

A step outcome can be highlighted and cited by the expert. In the first product slice it remains evidence within the whole-case review rather than an independent pass/fail target.

## Review outcome
### Pass

A **pass** records the domain expert's judgment that the observed case execution is acceptable under the applicable product and domain understanding available to the expert.

The MVP does not require the expert to formalize all of that knowledge into a separate criterion object.

### Fail

A **fail** records the domain expert's judgment that the observed case execution contains unacceptable behavior.

A failed review also records:

- a short, concrete description of the **first observable failure**; and
- a reference to the trace evidence supporting that observation.

The note should describe what was observed before trying to explain the internal cause.

Examples of the intended note shape include:

```text
Executed the transfer without user confirmation.
```

```text
Dropped the user's previously stated replacement preference.
```

```text
Claimed a property feature that is absent from the available data.
```

These are observations grounded in behavior. They are not required to belong to a predefined failure taxonomy.

### Review cannot be completed

Sometimes the expert may be unable to decide pass/fail because necessary evidence is missing, ambiguous, or cannot be attributed reliably.

The workbench should preserve that state and its reason rather than force a verdict.

This is a review-state outcome. It is not a behavioral verdict about the SUT.

## Judgment basis

The first product slice does not require a formal evaluation criterion to exist before a domain expert can review a trace.

The expert's judgment basis may include:

- domain expertise;
- product knowledge;
- case intent and expectations;
- explicit requirements or guarantees;
- product or policy documents;
- knowledge of supported and unsupported behavior; and
- other relevant context available to the expert.

Some of this basis may be explicit in the evaluation artifacts. Some may remain knowledge held by the expert.

The workbench should show relevant recorded context when it exists and preserve source identity when it is available. It should not invent or formalize missing product knowledge on the expert's behalf.

A future measurement workflow may require explicit operational criteria for consistent labeling. That is a later stage of failure understanding.

## Evidence roles

The workbench keeps evidence and expert interpretation separate.

| Role | Meaning | Use |
| --- | --- | --- |
| **Case context** | Purpose, dimensions, interaction form, initial conditions, and recorded expectations | Helps the expert understand what situation was exercised. |
| **Participant action** | Exact user message or typed action sent to the SUT | Establishes stimulus and interaction order. |
| **SUT response** | Complete response exposed through the supported interaction contract | Primary behavioral evidence. |
| **Adaptive choice** | Selected participant action and recorded participant-visible facts used as its basis | Explains the execution path. |
| **State observation** | Read-only SUT fact named by subject, capture point, boundary, and source | Establishes an attributable observable effect. |
| **Diagnostic attachment** | Step-linked runtime, model, log, or span record | Provides supporting diagnostic context. |
| **Expert review** | Pass/fail or incomplete-review state recorded by the domain expert | Records the expert's judgment of the case execution. |
| **Failure observation** | Short evidence-grounded description of the first observable failure | Seeds later failure-understanding analysis. |

Execution evidence remains historical evidence. Expert reviews and failure observations are derived artifacts and do not modify the trace.

## Evidence presentation

The default presentation should help the expert understand the execution before exposing diagnostic volume.

For the first product slice, the normal review order is:

1. case purpose, dimensions, initial conditions, and recorded expectations;
2. ordered participant actions or typed actions and complete SUT responses;
3. response-adaptive choices and the recorded response facts used as their basis;
4. named observations at their recorded capture points;
5. execution, SUT, model, dataset-selection, and configuration provenance;
6. step-linked runtime events, model exchanges, logs, and spans; and
7. exact raw evidence and unresolved fields.

A response summary may be shown as a navigation aid, but the expert must be able to inspect the complete captured response.

The workbench should make evidence origin clear so participant behavior, SUT behavior, observations, and apparatus diagnostics are not confused.

## Product capabilities: first slice

The first Failure Understanding Workbench should enable a domain expert to:

- **Open execution evidence.** Load one saved execution result without calling the SUT.
- **Select a trace.** Navigate case executions using stable case and trace identities.
- **Understand the case.** See relevant case purpose, interaction form, initial conditions, and recorded expectations.
- **Review the whole trajectory.** Follow participant actions, SUT responses, adaptive choices, observations, and product-visible errors in order.
- **Inspect complete responses.** Move from a readable presentation to the complete captured response.
- **Attribute observations.** See what was observed, where it was observed, and after which step.
- **Inspect diagnostics on demand.** Open runtime and model evidence when recorded identities support the join.
- **Record pass.** Save one expert pass judgment for the case execution.
- **Record fail.** Save one expert fail judgment with a short first-observable-failure note and evidence reference.
- **Record incomplete review.** Preserve why pass/fail could not be established from the available evidence.
- **Preserve provenance.** Keep expert identity, execution identity, trace identity, and evidence references attached to the review.
- **Track review progress.** Distinguish reviewed, incomplete, and remaining traces in the active review set.
- **Export or copy failure observations.** Make the failure notes and their source identities usable in later analysis outside the workbench.

## Proposed first product slice
### Included

- Local inspection of one saved execution result at a time.
- Whole-case review of each selected case trace.
- Complete interaction evidence as the primary review surface.
- Stable execution, trace, case, SUT, model, and configuration provenance.
- Domain-expert pass/fail review.
- Short first-observable-failure note for failed cases.
- Evidence reference for the failure observation.
- Explicit incomplete-review state when pass/fail cannot be supported.
- Separate persistence of expert review artifacts and execution evidence.
- Basic progress through a review cohort.
- Copy/export of reviewed failures with enough identity to continue analysis elsewhere.

### Explicitly excluded or deferred

- SUT execution, replay, rerun, or execution configuration controls.
- Evaluation case authoring or evaluation-design editing.
- Requirement that expert knowledge be formalized into explicit criteria before review.
- Automatic grading or LLM-as-Judge execution.
- Predefined failure-taxonomy selection during first-pass review.
- Required severity, impact, confidence, root-cause, or remediation fields.
- Exhaustive annotation of every failure symptom in a trace.
- Per-step correctness verdicts or partial credit.
- Cross-trace focused coding and category development inside the first slice.
- Failure-mode taxonomy editing inside the first slice.
- Operationalisation of failure modes into stable labeling criteria.
- Bulk application of failure-mode labels.
- Aggregation, frequency analysis, metrics, dashboards, thresholds, or release gating.
- Root-cause diagnosis or decisions about which product or system change to make.
- Multi-expert assignment, blind review, disagreement handling, or adjudication.
- Cross-run or cross-model comparison.
- A permanent UI framework, tracing vendor, storage format, or deployment model.

## Relationship to failure understanding

The first product slice implements the earliest practical part of failure understanding: inspect traces, separate acceptable from unacceptable executions, and preserve concrete observations about failures.

It intentionally stays close to the evidence.

```text
case traces
    ↓
domain-expert pass/fail review
    ↓
concrete first-failure observations
```

These observations can later become inputs to deeper analysis:

```text
failure observations
    ↓
initial coding
    ↓
constant comparison
    ↓
focused coding
    ↓
candidate categories
    ↓
integrated failure model
```

That later analysis should remain iterative. Analysts may merge similar observations, split broad groups, preserve ambiguous incidents, compare unsuccessful and successful cases, and revise earlier interpretations as new evidence appears.

The workbench does not need to implement all of those stages at once.

## Later phases
### Phase 2: Cross-trace analysis

A later version may help analysts bring reviewed failures together and compare them across traces.

Possible capabilities include:

- collect failure observations across cohorts or runs;
- compare incidents side by side;
- add or revise concrete initial codes;
- find related observations without forcing a taxonomy;
- preserve alternative interpretations and unresolved incidents;
- attach analytical memos;
- use successful or contradictory cases to test proposed groupings; and
- maintain links from every analytical statement back to source traces.

This work may initially be performed in external applications. The first-slice review artifact should therefore retain enough provenance to support that workflow.

### Phase 3: Failure-model development

A later version may support focused coding and category development:

- synthesize recurring initial codes;
- propose candidate categories;
- merge or split categories;
- preserve representative and contradictory incidents;
- define application-specific failure modes;
- record boundaries and examples; and
- maintain traceability from failure modes to observations and traces.

LLMs may assist with organization or candidate grouping. Their suggestions remain analytical aids subject to review against complete traces and domain knowledge.

### Phase 4: Operationalisation and measurement

Once selected failure modes are stable enough for repeated application, later workflows may:

- define operational criteria;
- label traces consistently;
- re-annotate historical traces when definitions change;
- quantify recurring failures;
- compare runs or system versions;
- identify regression patterns; and
- produce evaluation-level measurements or results.

This is a different activity from open-ended failure discovery. The product should preserve that boundary so the failure model is not narrowed prematurely to whatever is easiest to count.

## Relationship to other products
### Evaluation Design Workbench

The Evaluation Design Workbench asks whether the evaluation design exercises the behavior and failure surfaces needed to answer an evaluation question.

The Failure Understanding Workbench starts after cases have been executed. It asks whether observed SUT behavior passed or failed and, for failures, what happened.

A reviewed failure may later motivate changes to evaluation coverage. Such feedback should preserve case, trace, and source identity. The Failure Understanding Workbench does not directly edit canonical evaluation-design artifacts.

### Evaluation Execution Subsystem

The Evaluation Execution Subsystem produces execution results and case traces.

The Failure Understanding Workbench consumes those artifacts as immutable historical evidence. It does not repair, enrich, or rewrite them.

### Later evaluation and measurement

Failure understanding may eventually produce operational failure modes and labels that can be measured across cohorts and system versions.

Those measurements may contribute to evaluation results. The first Failure Understanding Workbench slice does not aggregate pass/fail reviews into a release decision or quality score.

## Trust and ownership boundaries

- Domain experts decide whether observed behavior is acceptable using applicable product and domain knowledge.
- The workbench supports that decision with attributable evidence and context. It does not decide correctness for the expert.
- Expert knowledge does not have to be fully serialized before a review can occur.
- When an explicit requirement, policy, case expectation, or other source is available, the workbench should preserve its identity rather than converting it into an unattributed summary.
- Saved execution results and traces remain the source of execution evidence.
- Expert reviews and failure observations are separate derived artifacts.
- A failed review records an observed problem. It does not establish root cause.
- The earliest observable failure may be upstream of many later symptoms. The workbench should not require exhaustive downstream annotation in the first pass.
- Runtime, model, log, and span data provide diagnostics. They do not replace participant-visible behavior or attributable state observations.
- Product-visible SUT errors remain behavioral evidence. Reset, capture, correlation, isolation, or teardown problems remain apparatus facts.
- Unsupported or missing semantics remain visible as unknown.
- Later automated analysis may propose interpretations or groupings, but those proposals must remain distinguishable from expert observations and source evidence.

## Evidence status
### Observed

The current disposable viewer and harness provide evidence about the first-phase review problem:

- a domain expert can inspect one saved execution result without calling the live SUT;
- case records, observations, runtime events, model exchanges, and distributed spans can be joined through recorded identities;
- timestamps can order evidence but should not establish identity;
- a derived response preview can conceal material behavior present in the complete structured response;
- the meaning of an isolated response can change when earlier interaction context is considered;
- fixed and response-adaptive cases expose different execution evidence;
- product-visible errors can be behavioral evidence even when diagnostics also classify an event as an error; and
- the existing working review contract is pass/fail with a short note and evidence location for the first observable failure.

The failure-understanding method also establishes that early analysis should stay close to trace incidents, use concrete descriptions, avoid forcing incidents into a predefined taxonomy, and distinguish the first observable failure from inferred root cause.

### Inferred

- The first useful product outcome is a reliable set of pass/fail expert reviews with concrete failure observations linked to source evidence.
- Requiring full classification during this first pass would add work before the failure structure is known.
- Whole-case review is the appropriate first-slice unit because the meaning of an individual response may depend on trajectory context.
- Complete SUT responses and attributable observations should dominate the default review path.
- Failure observations should be portable because deeper coding may initially occur in other tools.
- Later analytical structures should retain traceability back to the original review and execution evidence.
- Cross-trace synthesis and measurement are distinct phases and can be added after the first review workflow is useful.

### Unknown

- Which recorded case context experts actually need beyond the trace and their own domain knowledge.
- When experts need explicit product or policy sources visible alongside a trace.
- Whether the first slice needs structured fields beyond pass/fail, failure note, and evidence reference.
- How often incomplete reviews occur and which reasons need structured representation.
- Which export or handoff format best supports deeper coding in external tools.
- At what review volume cross-trace comparison becomes necessary inside the workbench.
- Which deeper-analysis operations are best kept in specialized external applications.
- When multiple experts, disagreement handling, or adjudication become necessary.
- Which failure modes eventually require operational criteria and repeated labeling.
- Which aggregate results are useful for product decisions after a failure model exists.

## Learning agenda
### First-pass review contract

- **Question:** Are pass/fail, a short first-observable-failure note, and an evidence reference sufficient for useful first-pass domain-expert review?
- **Decision affected:** minimum review artifact and first implementation scope.
- **Evidence needed:** have domain experts review a representative cohort and record what additional information they need at judgment time.

### Failure-note usefulness

- **Question:** Do concrete first-observable-failure notes provide enough material for later coding and comparison?
- **Decision affected:** note guidance, export contract, and whether additional structured fields are needed.
- **Evidence needed:** take a set of reviewed failures into a separate coding exercise and record which context analysts must reconstruct.

### Review evidence sufficiency

- **Question:** Which trace evidence must be prominent for experts to judge representative standalone, multi-step, adaptive, and product-error cases?
- **Decision affected:** default evidence presentation and upstream capture requirements.
- **Evidence needed:** observe expert reviews while recording which evidence surfaces they consult before deciding pass/fail.

### External-analysis handoff

- **Question:** What must a reviewed failure carry so deeper coding can happen reliably in another application?
- **Decision affected:** export shape and provenance contract.
- **Evidence needed:** move reviewed failures through a real external coding workflow and identify lost context, broken links, or manual reconstruction.

### Cross-trace workbench threshold

- **Question:** At what point does moving failure observations between tools create enough friction to justify comparison and coding capabilities inside the workbench?
- **Decision affected:** timing and scope of Phase 2.
- **Evidence needed:** perform several real coding rounds externally and record repeated navigation, joining, comparison, and provenance work.

## Terminology rationale and evolution

Earlier versions framed this product as the **Evaluation Trace Viewer**, and a later draft reframed it as a **Judgment Workbench**.

The trace-viewer name described the interface but under-described the expert's work. The domain expert does more than read a trace: they decide whether the observed behavior passed or failed and record why a failure is visible in the evidence.

The Judgment Workbench framing captured that first decision more accurately, but it made the pass/fail artifact appear to be the product's final purpose.

The broader workflow is failure understanding.

The initial pass/fail review is useful because it separates acceptable executions from failures and produces concrete observations tied to evidence. Those observations then support deeper analytical work across traces. The failure-understanding method may later develop focused codes, categories, failure modes, operational labels, and measurements.

The product name therefore reflects the longer-lived problem space while allowing a deliberately small first implementation.

```text
First slice:
trace → pass/fail → first observable failure

Later:
failure observations → coding → comparison → failure model

Later still:
failure model → operational labels → measurement
```

This sequence also preserves the distinction between an observed failure and an inferred explanation. The first pass records what the trace demonstrates. Deeper analysis may later investigate patterns, conditions, mechanisms, and causes.

## Relationship to current implementation

The current trace viewer remains useful implementation evidence for the first Failure Understanding Workbench slice.

| Current capability | Failure Understanding Workbench interpretation |
| --- | --- |
| Open one saved run result | Open one execution result |
| Select a trace | Select one whole-case review target |
| Case/interaction view | Primary behavior review |
| Response preview and full response | Readable projection plus exact source evidence |
| Observations and diagnostics | Supporting attributable evidence |
| Pass/fail/not-judgeable controls | Early expert review capture |
| Failure note | First observable failure observation |
| Review progress | First-pass review workflow |

This mapping is a product interpretation. Existing schemas, filenames, commands, statuses, trace layouts, dependencies, server behavior, and browser structure are not compatibility commitments.

## Evidence sources

- `concepts.md` defines shared execution, trace, judgment, and evaluation concepts.
- The Evaluation Execution Subsystem Product Frame defines the execution producer boundary.
- `evaluation-trace-viewer-frame.md` records current viewer evidence and the initial domain-expert review contract.
- `20-error-analysis.md` defines the failure-understanding method, including first-observable-failure analysis, initial coding, focused coding, category development, failure-model construction, operationalisation, and measurement.
- `workbench-product-frame.md` defines the separate Evaluation Design Workbench and its coverage-design boundary.

:::