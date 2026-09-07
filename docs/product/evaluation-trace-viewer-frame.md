# Evaluation Trace Viewer Product Frame
## Product outcome

The Evaluation Trace Viewer helps a domain expert inspect saved execution evidence, apply an explicit evaluation criterion, and record an attributable judgment without rerunning the system under test (SUT) or modifying the execution evidence.

The viewer sits at the judgment stage of the evaluation lifecycle:

```text
Execution
    ↓ produces evidence
Judgment
    ↓ produces assessments
Evaluation
    ↓ produces results
```

The viewer does not execute cases, replay the SUT, invent evaluation criteria, aggregate judgments into an evaluation result, or diagnose root cause.

Its successful outcome is a judgment that is attributable to:

* the execution evidence that was assessed;
* the evaluation criterion that was applied;
* the judge who produced the assessment; and
* the supporting evidence used to explain the judgment.

## Product boundary

The viewer begins when a saved execution result exists and a domain expert needs to assess one case execution from its case trace.

For the first product slice, the judgment target is one case execution as a whole.

The viewer ends when the expert has either:

* recorded a pass or fail judgment for that target; or
* recorded that the requested verdict cannot be produced from the available evidence or judgment context.

The viewer consumes execution results produced by the Evaluation Execution Subsystem. It does not call or replay the SUT, alter saved traces, or treat later judgments as changes to historical execution evidence.

A case trace is evidence about what happened during execution. A judgment is a later assessment of that evidence. The two remain separate artifacts.

## Governing question

> Given this case trace and this evaluation criterion, what judgment should be recorded, and what evidence supports it?

## Actors

* **Judge:** A domain expert assessing SUT behavior against an explicit evaluation criterion. An LLM-as-Judge (LaJ) or another automated judge may later consume the same evidence and judgment semantics without using the human viewer.
* **Operator:** An evaluation engineer who selects an execution configuration and produces saved execution results and case traces.
* **Beneficiary:** The product and engineering team that uses judgments and later evaluation results to understand SUT behavior or begin failure analysis.

## Primary job

When a domain expert needs to assess an executed evaluation case, help them connect the applicable criterion to the complete attributable execution evidence, inspect the behavior in context, and record a judgment whose basis can be understood later.

The normal review should make three things clear:

1. what case execution is being judged;
2. what evaluation criterion is being applied; and
3. which captured evidence supports the judgment.

## Primary workflow

```text
open execution result
    ↓
select case trace
    ↓
review judgment target and criterion
    ↓
review case execution as a whole
    ↓
inspect exact evidence as needed
    ↓
record judgment
```

The viewer reads execution evidence and creates a separate judgment artifact. It never edits the execution result or trace.

## Judgment model

The viewer keeps three layers distinct:

| Layer                  | Contents                                                                                             | Lifecycle                                                             |
| ---------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Execution evidence** | Execution result, case trace, ordered interaction, observations, errors, diagnostics, and provenance | Historical evidence produced by execution. Immutable from the viewer. |
| **Judgment context**   | Evidence target, evaluation criterion, judge identity, and relevant judge configuration              | Defines the assessment being requested.                               |
| **Judgment**           | Verdict or disposition, supporting evidence references, explanation, and judgment provenance         | Derived assessment stored separately from execution evidence.         |

This separation allows the same trace to be judged later under another criterion, by another judge, or under another judge configuration without rewriting the trace.

## Judgment target
### Whole case execution

The sole first-slice correctness target is one case execution interpreted from its attributable case trace.

The trace may contain:

* case context;
* ordered participant actions;
* complete SUT responses;
* response-adaptive choices;
* named observations;
* product-visible errors; and
* optional diagnostic evidence.

The expert records one judgment for the case execution as a whole.

Whole-case judgment is an MVP product choice. It does not define the only judgment target the broader evaluation system may ever support.

### Step outcome

A step outcome is the SUT's complete response to one identified trajectory step together with any observation attributable to that capture point.

A step outcome can be prominent in the viewer and cited as supporting evidence, but in the first slice it is evidence within the whole-case judgment target.

Its meaning may depend on earlier interaction context or later observable effects.

## Judgment outcome

For the first slice, the judgment uses a simple whole-case verdict:

* **pass**; or
* **fail**, with a short evidence-grounded note identifying the first observable failure.

Pass/fail is the MVP judgment shape. The broader judgment concept may later support scores, labels, structured findings, or other criterion-specific outputs.

### Unable to judge

When the requested pass/fail assessment cannot be supported, the expert records an **unable-to-judge disposition**.

The record should identify the reason, such as:

* missing or incomplete execution evidence;
* ambiguous evidence attribution;
* missing or ambiguous evaluation criterion; or
* another explicit limitation that prevents the requested verdict.

Unable-to-judge describes the outcome of the judgment attempt. It is not a behavioral verdict about the SUT.

## Evidence roles

The viewer must keep these roles distinct:

| Evidence role             | Meaning                                                                       | Judgment use                                                       |
| ------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **Case context**          | Purpose, dimensions, interaction form, and initial conditions                 | Establishes what was exercised.                                    |
| **Evaluation criterion**  | Explicit behavior, property, requirement, or failure condition being assessed | Establishes the basis of the judgment.                             |
| **Participant action**    | Exact user message or typed action sent to the SUT                            | Establishes stimulus and interaction order.                        |
| **SUT response**          | Complete response exposed through the supported interaction contract          | Primary behavioral evidence, including product-visible errors.     |
| **Adaptive choice**       | Selected participant action and recorded participant-visible response facts   | Explains the execution path without becoming SUT behavior.         |
| **State observation**     | Read-only SUT fact named by subject, capture point, boundary, and source      | Establishes an attributable observable effect.                     |
| **Diagnostic attachment** | Step-linked runtime, model, log, or span record                               | Provides diagnostic context without replacing behavioral evidence. |
| **Judgment**              | Attributable assessment of the target under the criterion                     | Exists only after an explicit judgment action.                     |

## Judgment-facing trace model

The viewer consumes the storage-neutral execution and judgment semantics defined in `concepts.md`.

For a whole-case judgment, it must be able to recover:

* execution run, execution result, trace, case, SUT, model, and configuration identities;
* the judgment target;
* the applicable evaluation criterion and its identity;
* judge identity and relevant judge configuration;
* case intent, dimensions, interaction form, and declared initial conditions when recorded;
* ordered steps with stable identities, actor or role, action kind, exact input or typed action, complete SUT response, product error, and correlation identities;
* adaptive choices with the participant-visible response facts recorded as their basis;
* observations labelled by subject, capture point, observation boundary, exact value, and source;
* optional diagnostics attached to the relevant step; and
* exact evidence references used to support the recorded judgment.

Timestamps may order timestamped evidence for display. They do not establish identity, causality, evidence origin, or adaptive-choice basis.

Unsupported or unknown semantics remain visible as unknown. The viewer does not invent joins, observations, criteria, or expectations.

## Evidence presentation order

The default presentation should follow the judge's decision process instead of the storage layout or diagnostic volume:

1. judgment target and evaluation criterion;
2. case purpose, dimensions, and declared initial conditions;
3. ordered participant inputs or typed actions and complete SUT responses;
4. response-adaptive choices and their recorded participant-visible basis;
5. named observations at their recorded capture points;
6. execution, SUT, model, dataset-selection, and configuration provenance;
7. step-linked runtime events, model exchanges, logs, and spans; and
8. exact raw evidence and unresolved fields.

A response summary may be shown as a derived presentation aid. It is not a source record or judgment target. The expert must be able to inspect the complete captured response.

## Product capabilities

The viewer must enable a domain expert to:

* **Open execution evidence.** Load one saved execution result without calling the SUT and preserve its recorded identities.
* **Select a trace.** Navigate case executions using stable trace and case identity.
* **See the criterion.** Make the applicable evaluation criterion explicit before a verdict is recorded.
* **Review whole behavior.** Follow case context, ordered interaction, adaptive choices, observations, and product-visible errors as one case execution.
* **Inspect exact responses.** Show the complete captured SUT response alongside any derived summary.
* **Attribute observations.** Present what was observed, where it was observed, and after which step.
* **Separate evidence roles.** Label SUT behavior, participant actions, adaptive-choice evidence, judge-visible observations, and diagnostics by origin.
* **Inspect diagnostics on demand.** Attach runtime and model evidence to the relevant step when correlation identities support the join.
* **Record pass or fail.** Save a whole-case judgment and require an evidence-linked first-observable-failure note for failures.
* **Record unable to judge.** Preserve an explicit disposition and reason when the requested verdict cannot be supported.
* **Preserve judgment provenance.** Record the target, criterion, judge, relevant judge configuration, and evidence references needed to interpret the judgment.
* **Preserve execution evidence.** Store the judgment separately without editing the trace.
* **Track review progress.** Make completed, unable-to-judge, and remaining traces clear within the active review set.

## Proposed MVP boundary
### Included

* Local inspection of one saved execution result at a time.
* Stable whole-case judgment identity.
* One active domain-expert judgment per selected case trace in the initial workflow.
* Explicit evaluation criterion in the judgment context.
* Case context, ordered interaction, adaptive choices, and named observations in the main review path.
* Complete SUT response inspection with derived summaries clearly labelled.
* Optional on-demand runtime, model, log, span, and raw-source inspection.
* Visible execution, SUT, model, dataset-selection, and configuration provenance.
* Pass and fail verdicts.
* Unable-to-judge disposition with an explicit reason.
* Required evidence-linked first-observable-failure note for failed judgments.
* Separate persistence of judgment artifacts and execution evidence.
* Basic review progress for completed, unable-to-judge, and remaining traces.

### Explicitly excluded or deferred

* Case authoring or dataset editing.
* Evaluation criterion authoring or silent inference of missing criteria.
* SUT execution, replay, rerun, or execution configuration controls.
* Editing, repairing, enriching, or resealing execution evidence.
* Automated judge execution in the first human-review slice.
* Numeric scoring or other criterion-specific judgment forms beyond the MVP verdict contract.
* Independent per-step correctness verdicts.
* Partial credit, multi-label failure annotation, and exhaustive failure-symptom enumeration.
* Multiple simultaneous judgments for one target.
* Multi-expert assignment, blind review, disagreement resolution, and adjudication.
* Aggregation of judgments into evaluation results.
* Thresholds and release gating.
* Root-cause analysis, failure taxonomy development, refactoring, and regression design inside the viewer.
* Cross-run or cross-model comparison, historical dashboards, and trend analysis.
* A particular UI framework, tracing vendor, storage layout, or deployment model.
* Remote publication, collaboration, and administrative access control.

## Trust and decision boundary

* Saved case traces and execution results are the source of execution evidence. The viewer does not call, replay, enrich, or mutate the SUT or captured records.
* Recorded execution, trace, case, step, request, observation, diagnostic, criterion, judge, and source identities establish attribution and joins.
* Timestamps determine display order only.
* SUT responses, participant actions, adaptive-choice evidence, judge-visible observations, hidden model content, and apparatus diagnostics are labelled by origin.
* Product-visible SUT errors remain behavioral evidence. Reset, isolation, capture, correlation, and teardown problems remain apparatus facts.
* A judgment is a derived artifact. It does not correct or rewrite the trace.
* Pass/fail has meaning only under an identified evaluation criterion.
* The viewer does not invent a criterion from case prose, dataset frequency, model suggestions, or observed behavior.
* Failure judgment and root-cause diagnosis remain separate activities.
* The local MVP assumes synthetic evaluation data. Remote or non-synthetic review requires a separate access and privacy boundary.

## Evidence status
### Observed

The disposable harness branch and its current viewer provide evidence about the product problem. They are not a production implementation, migration target, supported input format, or source of compatibility commitments.

Observed behavior includes:

* one local saved execution artifact can be inspected without calling the live SUT;
* case records, end-of-case observations, runtime events, model exchanges, and distributed spans can be joined using recorded case and trace identities;
* timestamps are useful for ordering evidence but do not establish identity;
* the current primary view can hide material information when it presents a derived response preview instead of the complete structured response;
* the meaning of a response may depend on earlier interaction context;
* fixed and response-adaptive cases expose different execution evidence;
* participant-visible product errors can be valid behavioral evidence even when diagnostics also classify an event as an error; and
* domain experts are the intended initial judges under a working pass/fail contract.

A disposable inspection of selected cases produced two useful examples:

* a friendly response preview appeared correct while the complete structured response contained behavior that changed the judgment; and
* a response that appeared wrong in isolation was consistent with the earlier interaction and product contract when the complete trajectory was reviewed.

These observations support whole-case review and complete-response inspection. They do not establish a permanent artifact format or minimum capture policy.

### Inferred

* The viewer's primary value is reducing the work needed to produce an attributable judgment from complete execution evidence.
* Judgment context should make the criterion explicit instead of relying on an implicit or reconstructed evaluation basis.
* Case intent, ordered participant actions, complete SUT responses, adaptive choices, and named observations should dominate the normal review path.
* Derived response summaries can help navigation but cannot replace exact captured evidence.
* Observations need explicit subjects and capture points to avoid attribution errors.
* Judgments should be separate artifacts keyed to immutable execution evidence.
* Diagnostics should remain available on demand and attached to their originating steps.
* Unable-to-judge is better represented as the outcome of a judgment attempt than as a correctness verdict.

### Unknown

* Which criterion representation gives domain experts enough context for consistent judgment.
* Which observation subjects and capture points are necessary for representative cases.
* The minimum diagnostic evidence needed after complete interaction evidence and named observations are available.
* Which private participant context or evaluation-only model content a judge may inspect and how access should be explained.
* When judgment targets smaller than a whole case execution are necessary.
* Which judgment forms beyond pass/fail are needed for representative evaluation criteria.
* How later multi-judge review should represent disagreement, repeated judging, and adjudication.
* Which decisions require repeated samples, comparisons, or aggregate evaluation results.

## Learning agenda
### Judgment criterion

* **Question:** What criterion information must be visible for a domain expert to produce a consistent whole-case judgment?
* **Decision affected:** criterion contract, judgment context, default presentation, and future LaJ compatibility.
* **Blocking status:** not blocking exploratory review; blocking a stable repeatable judgment contract.
* **Evidence needed:** representative experts judge a targeted cohort while recording which criterion information they use and where ambiguity prevents a verdict.

### Observation sufficiency

* **Question:** Which observation subjects and capture points are necessary for representative whole-case judgments without ambiguous attribution?
* **Decision affected:** upstream case definitions, execution capture behavior, viewer defaults, and future serialized contracts.
* **Blocking status:** not blocking full-evidence prototypes; blocking a permanent minimum observation contract.
* **Evidence needed:** review standalone, multi-step, adaptive, and product-error runs while recording which observations affect judgments.

### Minimum diagnostic evidence

* **Question:** What diagnostic material can be removed from the normal review path once complete responses and named observations are available?
* **Decision affected:** default presentation, capture cost, and artifact size.
* **Blocking status:** not blocking full-evidence review; blocking a thinner permanent diagnostic contract.
* **Evidence needed:** compare judgment and explanation quality with systematically reduced step-linked diagnostics.

### Judgment target

* **Question:** When is whole-case judgment sufficient, and when does an evaluation criterion require another evidence target?
* **Decision affected:** judgment identity, viewer navigation, criterion contract, and future automated judging.
* **Blocking status:** not blocking the first whole-case slice.
* **Evidence needed:** classify representative criteria by the evidence target needed to assess them without losing required context.

### Review continuity

* **Question:** What review-set size and interruption pattern require durable progress, filtering, or resume behavior?
* **Decision affected:** local persistence and navigation design.
* **Blocking status:** not blocking single-session review.
* **Evidence needed:** observe experts reviewing targeted cohorts of increasing size.

## Terminology rationale

Earlier versions used **evaluation run** for SUT execution, **run result** for the saved execution evidence, and **verdict** as the primary downstream artifact.

The current product concepts separate the lifecycle:

* SUT execution is an **execution run**;
* its durable evidence is an **execution result**;
* a judge applies an **evaluation criterion** to identified execution evidence;
* the judge produces a **judgment**; and
* later aggregation or interpretation of judgments produces an **evaluation result**.

For the first viewer slice, `pass` and `fail` remain verdict values inside the judgment.

Likewise, **not judgeable** becomes an **unable-to-judge disposition**. It records that the requested pass/fail verdict could not be produced under the available evidence or criterion context.

The short form is:

```text
Execution produces evidence.
Judges produce judgments.
Evaluation produces results.
```

The Evaluation Trace Viewer supports the middle stage for a human domain expert.

## Evidence sources

* `concepts.md` defines the shared execution, judgment, and evaluation language.
* The Evaluation Execution Subsystem Product Frame defines the producer boundary.
* The current trace viewer and disposable harness provide implementation evidence for the review workflow without establishing a permanent interface or storage contract.
