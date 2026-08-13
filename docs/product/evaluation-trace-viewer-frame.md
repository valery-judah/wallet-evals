# Evaluation Trace Viewer Product Frame

## Product boundary

The Evaluation Trace Viewer begins when a domain expert opens saved evaluation run
results and selects a case trace. It ends when the expert records one pass or fail
verdict for the case execution evidenced by that trace, or records that the case
execution is not judgeable from the trace.

The viewer consumes evidence produced by the
[evaluation subsystem](evaluation-subsystem-frame.md). It does not execute or replay
a case, call Wallet, alter the saved trace, or decide correctness on the expert's
behalf.

“Trace” means the attributable evidence captured about a case trajectory, not only
distributed spans. The primary object is the ordered Wallet behavior described in
[Product Concepts](concepts.md). Runtime events, model exchanges, logs, and spans
are supporting attachments.

## Status of implementation evidence

The disposable harness branch, its viewer, and its adaptive experiment are evidence
about the product problem. They are not a production implementation, migration
target, supported input format, or source of compatibility commitments.

Nothing in that branch is presumed to survive: not its schemas, filenames,
commands, status strings, container topology, tracing layout, dependencies, server,
or browser interface. Future design may discard it completely.

## Evidence status

### Observed

- The example viewer opens one local run result and presents captured cases without
  calling the live Wallet SUT.
- It joins case records, end-of-case observations, runtime events, model exchanges,
  and distributed spans using recorded case and trace identities. Timestamps order
  evidence but do not establish identity.
- The example's primary case view shows a request and derived answer. Separate views
  expose the fuller interaction, structured exchanges, observations, model
  activity, case definition, and raw evidence.
- The fixed and adaptive experiments use different case shapes. Fixed cases use
  phased steps and end observations; adaptive cases use participant steps, choice
  basis, role adherence, and repeated observations.
- A participant-visible Wallet error can be valid behavioral evidence even when a
  transport or span also calls it an error. Reset, isolation, capture, and
  correlation records describe the evaluation apparatus instead.
- Domain experts are the intended initial judges. The working verdict contract is
  pass or fail, with a short note and evidence location for the first observable
  failure.

#### Disposable 20-case inspection

An exploratory inspection of 20 selected cases showed two important judgment
problems. It was a learning exercise, not domain-expert adjudication or a Wallet
quality estimate.

- One friendly response preview appeared correct while the complete structured
  Wallet response assigned a user-provided category as a merchant. The preview was
  insufficient evidence.
- Another response appeared wrong in isolation, but the earlier interaction showed
  that a transaction task remained active and the product contract prohibited
  switching capabilities. The complete trajectory changed the interpretation.

These examples support whole-case judgment from a trace and capture of complete responses.
They do not establish a permanent artifact format or minimum observation policy.

### Inferred

- The viewer's primary value is reducing the work required for a domain expert to
  reach and explain one attributable whole-case judgment from a trace.
- Case intent, ordered participant actions, complete Wallet responses, adaptive
  choices, and named observations should dominate the normal review path.
- A response summary is a useful display projection but is not a judgment unit or
  source record.
- Observations need explicit subjects and capture points so the expert does not
  attribute a later effect to the wrong step.
- Verdicts should be separate artifacts keyed to the saved trace. Recording
  a verdict must not alter execution evidence.
- Diagnostics should be available on demand and attached to their originating
  steps rather than mixed into the participant-visible interaction.

### Unknown

- Which explicit expectations, evaluation policy, or expert knowledge must be
  visible for consistent judgment.
- Which observation subjects and capture points are necessary for representative
  cases.
- The minimum diagnostic evidence needed after the ordered interaction and named
  observations are available.
- Which private participant context or evaluation-only model content a judge may
  inspect and how access should be explained.
- Whether later review needs multiple experts, blind review, disagreement handling,
  or adjudication.
- Which decisions require repeated samples, comparisons, or aggregate results.

## Intent

### Actors and situation

- **Judge:** a domain expert assessing Wallet behavior against product and domain
  expectations. An automated judge may later consume the same trace and
  verdict semantics without using the human interface.
- **Operator:** an evaluation engineer who selects a run configuration and produces
  saved case traces.
- **Beneficiary:** the product and engineering team using verdicts to assess Wallet
  behavior or begin failure analysis.

The need arises after a case trace has been saved but the underlying execution
cannot be judged reliably from an isolated response string or raw diagnostics alone.

### Job and intended outcome

The expert's job is to inspect one case execution through its saved trace, apply the
visible evaluation basis, and record whether Wallet behavior passed or failed as a
whole.

The intended outcome is one review record identifying the run, trace, case execution,
evaluation basis, judge, verdict, and, for a failure, a short first-observable-
failure note linked to the relevant trace evidence. When the trace cannot support a
verdict, the expert records a not-judgeable disposition.

## Core experience

The primary workflow is:

`open saved run results → select a case trace → review the case execution as a whole → record pass/fail or not judgeable → if failed, link the first observable failure`

The viewer must let the expert:

- understand case purpose, dimensions, initial conditions, and expectations;
- follow every participant message or typed action and Wallet response in order;
- distinguish Wallet behavior from participant choices, read-only observations,
  and runner diagnostics;
- see the Wallet response facts used for a response-adaptive choice;
- relate an observation to its subject and capture point;
- move from a human-readable presentation to exact captured evidence;
- resume a review set with judged, not-judgeable, and remaining traces clear.

## Judgment unit

### Case execution evidenced by a trace

The sole v1 correctness unit is one case execution interpreted from the attributable
evidence in its saved trace. The trace includes case context, ordered participant
actions, complete Wallet responses, response-adaptive choices, named observations,
Wallet errors, and optional diagnostic evidence.

The expert assigns one verdict to the case execution as a whole. The viewer does not
produce per-step verdicts, partial credit, numeric scores, or a rollup from local
step judgments.

### Step outcome

A step outcome is Wallet's complete response to one identified trajectory step plus
any observation that can be attributed to that capture point. It may include
structured content, offered actions, conversation status, transport status, or a
Wallet product error.

A step outcome can be prominent in the viewer and cited by a failure note, but it
is evidence within the trace rather than an independent verdict target. Its meaning
may depend on earlier interactions or later observable effects.

## Evidence roles

The viewer must keep these roles distinct:

| Evidence role | Meaning | Judgment use |
| --- | --- | --- |
| Case context | Purpose, dimensions, interaction form, initial conditions, expectations | Establishes what the expert is judging and on what basis. |
| Participant action | Exact user message or typed action sent to Wallet | Establishes the stimulus and interaction order. |
| Wallet response | Complete response exposed through the supported interaction contract | Primary behavioral evidence, including product errors. |
| Adaptive choice | Selected participant action and cited participant-visible response facts | Explains the trial path without becoming Wallet behavior. |
| State observation | Read-only Wallet fact named by subject, capture point, boundary, and source | Establishes an attributable observable effect. |
| Diagnostic attachment | Step-linked runtime, model, log, or span record | Explains internals without replacing public behavior. |
| Verdict | The expert's pass, fail, or not-judgeable review record | Exists only after an explicit judgment action. |

## Judgment-facing trace model

The viewer consumes the storage-neutral semantic contract defined in
[Product Concepts](concepts.md). It must recover:

- run, trace, case, dataset selection, Wallet, model, and configuration
  identities;
- case intent, dimensions, interaction form, declared initial conditions, and
  applicable expectations;
- ordered steps with stable identities, actor or role, action kind, exact input or
  typed action, complete Wallet response, product error, and correlation identities;
- adaptive choices with their cited participant-visible response facts;
- observations labelled by subject, capture point, observation boundary, exact
  value, and source;
- optional diagnostic records attached to the relevant step.

The viewer may order timestamped records for display but must not infer identity,
causality, evidence origin, or adaptive-choice basis. Unsupported or unknown
semantics must remain visible rather than being normalized into invented facts.

## Evidence presentation order

The default presentation follows the expert's decision rather than the storage
layout or diagnostic volume:

1. case purpose, dimensions, declared initial conditions, and expectations;
2. ordered participant inputs or typed actions and complete Wallet responses;
3. response-adaptive choices and the response facts cited as their basis;
4. named observations at their recorded capture points;
5. run, Wallet, model, dataset-selection, and configuration identity;
6. step-linked runtime events, model exchanges, logs, and spans; and
7. exact raw evidence and unresolved fields.

Presentation order does not imply that every verdict requires every optional
diagnostic layer.

## Product capabilities

The viewer must enable a domain expert to:

- **Open saved results.** Load one run result without calling Wallet and preserve
  its recorded identities.
- **Select a trace.** Navigate cases using stable trace and case identity,
  not response text or latest timestamp.
- **Review whole behavior.** Follow the case context, ordered interaction, adaptive
  choices, observations, and errors as one case execution.
- **Inspect exact responses.** Show Wallet's complete captured response alongside
  any derived summary.
- **Attribute observations.** Present what was observed, where it was observed, and
  after which step.
- **Separate evidence roles.** Label participant-visible Wallet behavior,
  judge-visible observations, participant choices, and diagnostics by origin.
- **Inspect diagnostics on demand.** Attach runtime and model evidence to the
  relevant step when correlation identities support the join.
- **Withhold a verdict.** Record not judgeable when the trace does not support a
  verdict or its evidence cannot be attributed.
- **Record one verdict.** Save pass or fail for the case execution, with a
  short evidence-linked first-failure note when it fails.
- **Preserve execution evidence.** Store the verdict separately without editing the
  trace.

## Proposed MVP boundary

### Included

- Local inspection of one saved evaluation run at a time.
- The shared storage-neutral trace semantics for standalone, fixed-sequence,
  typed-action, response-adaptive, and Wallet-error cases.
- Stable whole-case judgment identity and one verdict per trace.
- Case context, ordered interaction, adaptive choices, and named observations in
  the main review path.
- Complete Wallet response inspection with derived summaries clearly labelled.
- Optional on-demand runtime, model, log, span, and raw-source inspection.
- Visible run, Wallet, model, dataset-selection, and configuration provenance.
- Pass, fail, and not-judgeable review records.
- A required short note and evidence location for the first observable failure.
- Basic review progress for judged, not-judgeable, and remaining traces.

### Explicitly excluded or deferred

- Case authoring, dataset editing, SUT execution, replay, and rerun controls.
- Reconstruction or invention of observations, participant choices, or causal
  joins that were not captured upstream.
- An independent verdict for a step outcome.
- Compatibility with disposable harness schemas, commands, or viewer behavior.
- Automatic grading, numeric scoring, aggregation, thresholds, and release gating.
- Partial credit, per-step sub-verdicts, multi-label failure annotation, and
  exhaustive failure-symptom enumeration.
- Root-cause analysis, failure taxonomy development, refactoring, and regression
  design inside the viewer.
- Cross-run or cross-model comparison, historical dashboards, and trend analysis.
- Multi-expert assignment, blind review, disagreement resolution, and adjudication.
- Editing, repairing, enriching, or resealing execution evidence.
- A particular UI framework, tracing vendor, storage layout, or deployment model.
- Remote publication, collaboration, and administrative access control.

## Trust and decision boundary

- Saved case traces are the source of execution evidence. The viewer does
  not call, replay, enrich, or mutate Wallet or the captured records.
- Recorded run, trace, case, step, request, observation, diagnostic, and source
  identities establish joins. Timestamps determine display order only.
- Wallet responses, participant actions, adaptive-choice evidence, judge-visible
  observations, hidden model content, and apparatus diagnostics are labelled by
  origin.
- Wallet product errors remain behavioral evidence. Reset, isolation, capture,
  correlation, and teardown problems remain apparatus facts.
- A verdict is a new judgment artifact, not a correction to the trace.
- The viewer does not invent a rubric. The visible judgment basis comes from the
  case, an attached evaluation policy, or explicit domain expertise.
- An automated judge may later read the same trace and emit the same verdict
  contract without using this interface.
- The local MVP assumes synthetic evaluation data. Remote or non-synthetic review
  requires a new access and privacy boundary.

## Learning agenda

### Observation sufficiency

- **Question:** Which observation subjects and capture points are necessary for a
  domain expert to judge representative trajectories without ambiguous attribution?
- **Decision affected:** upstream case definitions, capture behavior, viewer defaults,
  and the future serialized contract.
- **Blocking status:** not blocking full-evidence prototypes; blocking a permanent
  minimum observation contract.
- **Evidence needed:** review standalone, multi-step, adaptive, and Wallet-error
  runs while recording which named observations the expert uses.

### Judgment basis

- **Question:** Which case expectations, product policies, or domain knowledge must
  be visible for consistent whole-case judgments from traces?
- **Decision affected:** case authoring, review presentation, and automated-judge
  compatibility.
- **Blocking status:** not blocking exploratory expert review; blocking a stable
  repeatable judgment contract.
- **Evidence needed:** representative experts judge a targeted cohort and record the
  basis used and first observable failure for each failed case execution.

### Minimum diagnostic evidence

- **Question:** What diagnostic material can be removed once complete responses and
  named observations are available?
- **Decision affected:** default presentation, capture cost, and artifact size.
- **Blocking status:** not blocking full-evidence review; blocking a thinner
  permanent diagnostic contract.
- **Evidence needed:** compare judgment and explanation quality with systematically
  reduced step-linked diagnostics.

### Review continuity

- **Question:** What review-set size and interruption pattern require durable
  progress, filtering, or resume behavior?
- **Decision affected:** local persistence and navigation design.
- **Blocking status:** not blocking single-session review.
- **Evidence needed:** observe experts reviewing targeted cohorts of increasing
  size.

## Evidence sources

- [Product Spec](spec.md) and [Product Concepts](concepts.md) define the shared
  runner-viewer contract.
- [Evaluation Subsystem Product Frame](evaluation-subsystem-frame.md) defines the
  producer boundary.
- [Evaluation tuples](../../data/dataset-1/wallet_v1_evaluation_tuples_aligned.json),
  [fixed-sequence examples](../../data/dataset-1/wallet_v1_examples_T018.json), and
  [adaptive-candidate examples](../../data/dataset-1/wallet_v1_examples_T020.json)
  provide current case material for trajectory walkthroughs.
