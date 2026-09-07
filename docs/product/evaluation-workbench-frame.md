# Evaluation Workbench Product Frame
## Product outcome

The **Evaluation Workbench** helps an expert conduct a traceable evaluation investigation from a defined decision or knowledge need through evaluation design, execution evidence, judgment, analysis, and scoped findings.

Its purpose is to help produce **trustworthy, scoped, and decision-relevant knowledge about AI Product and AI System behaviour**.

The primary outcome is:

> A defensible, traceable answer to one governing evaluation question, together with its scope, supporting evidence, uncertainty, limitations, and any proposed changes to reusable evaluation knowledge.

The Workbench does not make the product decision itself. It helps the expert establish what needs to be known, design an evaluation capable of answering the question, obtain and assess the required evidence, interpret the results within their scope, and identify how evaluation knowledge should improve.

## Product boundary

The Workbench begins when a participant has a **decision or knowledge need** about an AI Product or AI System and must reduce uncertainty about its behaviour.

Every investigation requires an **Evaluation Brief** and exactly one **governing evaluation question**.

The Workbench ends when the investigation has:

- a scoped finding that answers, or explicitly cannot answer, the governing question;
- attributable evidence, judgments, and analysis supporting that finding;
- explicit uncertainty, limitations, and unresolved gaps; and
- any handoffs proposing changes to evaluation knowledge or evaluation infrastructure.

The Workbench does not own:

- the product or organisational decision that motivated the evaluation;
- prioritisation of product work;
- root-cause diagnosis as an evaluation responsibility;
- implementation of product or system changes;
- canonical authoring of evaluation sources;
- SUT execution semantics; or
- automated evaluator implementation.

It may produce evidence that informs these activities.

## Evaluation in the broader system

Evaluation connects product expectations, observed system behaviour, and the participant's decision context.

```text
Product intent
    ↓
Expected behaviour ────────────────┐
                                   │
AI System + operating context      │
    ↓                              ├── Evaluation
Execution                          │
    ↓                              │
Observed behaviour ────────────────┤
                                   │
Decision / knowledge need          │
    ↓                              │
Uncertainty                        │
    ↓                              │
Evaluation question ───────────────┘
```

The Workbench operationalises this as an investigation:

```text
Evaluation Brief
    ↓
Evaluation design
    ↓
Execution evidence
    ↓
Judgments
    ↓
Measurements / comparisons / patterns
    ↓
Evaluation results
    ↓
Scoped finding
```

Evaluation is therefore broader than executing a test set or calculating a score.

## Primary object: Evaluation investigation

An **evaluation investigation** is the durable unit of work in the Workbench.

It exists to answer one governing evaluation question for a defined scope.

```text
Evaluation investigation
│
├── Evaluation Brief
├── Evaluation design
├── Execution requests and evidence
├── Judgments
├── Analysis
├── Evaluation results
├── Primary finding
└── Handoffs
```

An investigation may contain multiple execution runs, cohorts, judges, judgments, measurements, and intermediate results. They remain subordinate to the same governing question.

A materially different governing question creates a new investigation. Follow-up investigations may link to earlier investigations without changing their historical record.

## Evaluation Brief

Every investigation requires an **Evaluation Brief**. The brief is the normative anchor that establishes why the investigation exists and what it is intended to answer.

At the product-frame level, it identifies:

- the participant or stakeholder;
- the decision or knowledge need;
- the uncertainty motivating evaluation;
- the governing evaluation question;
- the SUT and evaluated boundary;
- applicable product intent and expected behaviour;
- intended evaluation scope;
- coverage requirements and intended evidence;
- relevant product, architecture, policy, research, production, or other sources; and
- unresolved product or evaluation questions.

The brief may expose incomplete or ambiguous information. Missing intent remains a visible gap. The Workbench may help investigate it and prepare a handoff, but it must not silently turn dataset frequency, trace behaviour, or model suggestions into product commitments.

## Workbench goals

The top-level goal is:

> **W0. Help an expert produce trustworthy evaluation knowledge for a defined decision or knowledge need.**

```text
W0. Produce trustworthy evaluation knowledge for a defined need
│
├── W1. Frame what needs to be known
├── W2. Design how relevant behaviour will be observed
├── W3. Judge observed behaviour
├── W4. Turn judgments into scoped findings
├── W5. Develop reusable evaluation knowledge
└── W6. Preserve trust in the evaluation process
```

### W1. Frame what needs to be known

Connect the participant's goal and uncertainty to one governing evaluation question and the relevant product and SUT boundary.

```text
Participant
    ↓
Goal
    ↓
Decision or knowledge need
    ↓
Uncertainty
    ↓
Governing evaluation question
```

Governing question:

> **What do we need to learn, about which behaviour, and why?**

### W2. Design how relevant behaviour will be observed

Translate the evaluation question and applicable product expectations into an evaluable design.

```text
Evaluation question
    ↓
Product expectations
    ↓
Coverage requirements
    ↓
Behaviour dimensions and conditions
    ↓
Cases and cohorts
    ↓
Required execution evidence
    ↓
Evaluation criteria
```

Governing question:

> **What must we exercise and observe for the evaluation question to be answerable?**

The Workbench does not independently invent product intent. Product and domain owners remain responsible for underlying commitments.

### W3. Judge observed behaviour

Apply explicit evaluation criteria to attributable execution evidence.

```text
Execution evidence
    +
Evaluation criterion
    +
Judge
    ↓
Judgment
```

Judges may include code-based checks, reference-based evaluators, model-based judges, domain experts, and other explicitly defined mechanisms.

The Workbench may trigger automated evaluators and provide a human judgment surface. It does not own automated evaluator implementation.

Governing question:

> **Given this criterion and this evidence, what judgment is supported?**

### W4. Turn judgments into scoped findings

Individual judgments do not by themselves answer the governing question. The Workbench helps interpret judgments within the evaluated sample and scope.

```text
Judgments
    ↓
Counts / rates / comparisons / patterns
    ↓
Scope + uncertainty + limitations
    ↓
Evaluation result
    ↓
Scoped finding
```

The sample determines the meaning of the result. A challenge cohort, regression suite, representative sample, and controlled comparison support different claims.

Governing question:

> **What can we validly conclude from these judgments within this evaluated scope?**

### W5. Develop reusable evaluation knowledge

Evaluation should improve the team's ability to evaluate future behaviour.

The Workbench may identify proposed changes to:

- evaluation briefs;
- coverage requirements;
- dimensions and conditions;
- cases and cohorts;
- representative examples;
- criteria and rubrics;
- evaluators;
- trusted judgments or labels;
- failure or quality models;
- regression suites;
- decision rules; and
- evidence requirements.

Canonical changes happen through an external authoring or repository workflow:

```text
Investigation finding
    ↓
Proposed evaluation-knowledge change
    ↓
Provenance-rich handoff
    ↓
External authoring / repository workflow
    ↓
Review and validation
    ↓
Updated canonical sources
    ↓
Reload into Workbench
```

Governing question:

> **What did this investigation teach us that should change our reusable evaluation knowledge?**

### W6. Preserve trust in the evaluation process

The Workbench must make the basis and limits of a finding inspectable.

```text
Decision / knowledge need
    ↓
Evaluation question
    ↓
Product expectation
    ↓
Coverage requirement / criterion
    ↓
Case / cohort
    ↓
Execution
    ↓
Trace evidence
    ↓
Judgment
    ↓
Measurement / comparison
    ↓
Evaluation result
    ↓
Finding
```

Missing links, evidence gaps, disagreement, and unknowns remain visible.

Findings should also be routed to the appropriate learning loop:

```text
Observed product failure
    → Product Improvement Loop

New or poorly fitting behaviour
    → Evaluation Knowledge Loop

Unclear criterion or evaluator disagreement
    → Evaluation Knowledge Loop

Missing or inaccessible evidence
    → Evaluation Infrastructure Loop
```

Governing question:

> **Why should this finding be trusted, what exactly does it cover, and what remains unknown?**

## Operating model

The Workbench is organised around the investigation rather than around individual artifacts.

```text
Evaluation Brief
    ↓
Frame question and scope
    ↓
Inspect / design coverage
    ↓
Select cases, cohorts, criteria, and methods
    ↓
Request execution
    ↓
Consume execution results
    ↓
Apply automated and / or human judgment
    ↓
Measure / compare / interpret
    ↓
Produce scoped finding
    ↓
Identify evaluation-learning opportunities
    ↓
Prepare external handoffs
    ↓
Complete investigation
```

This is a dependency model, not a mandatory linear wizard. New evidence may require revisiting coverage, criteria, evaluators, or evidence requirements before the investigation can be completed.

## Orchestration and subsystem ownership

The Workbench coordinates evaluation activity while specialised subsystems retain their own responsibilities.

### Execution

The Workbench may select a cohort and SUT configuration, request an execution run, inspect status, and consume the resulting execution evidence.

The **Evaluation Execution Subsystem** owns case execution, isolation, SUT interaction, evidence capture, trace production, and execution-result provenance.

```text
Evaluation Workbench
    ↓ execution request
Evaluation Execution Subsystem
    ↓
Execution result
    ↓
Evaluation Workbench
```

### Automated judges

The Workbench may select criteria and approved evaluators, request automated judgment, inspect results, and surface disagreement.

The evaluator or judge subsystem owns implementation of the automated evaluation mechanism.

```text
Evaluation Workbench
    ↓ judgment request
Automated evaluator / judge
    ↓
Judgment
    ↓
Evaluation Workbench
```

### Human judgment

Human judgment may happen directly inside the Workbench through a trace-review surface. The existing Evaluation Trace Viewer is an early judgment-facing implementation surface.

## Evaluation results and findings

The Workbench keeps several levels of output distinct.

### Judgment

A **judgment** is one attributable assessment of defined evidence under a defined evaluation criterion.

### Measurement

A **measurement** aggregates or summarises judgments over a defined sample or scope, such as pass rate, criterion counts, cohort-level rates, agreement, or regression counts.

### Evaluation result

An **evaluation result** is a derived result that uses judgments, measurements, comparisons, or another declared analysis to answer part of the governing evaluation question for an explicit scope.

An investigation may contain multiple evaluation results.

### Finding

A **finding** interprets evaluation results and evidence in relation to the governing evaluation question.

The completed investigation has one primary finding or explicit answer state. It must state:

- what was evaluated;
- which scope the claim covers;
- which evidence and results support it;
- material uncertainty or disagreement;
- known evidence gaps;
- relevant limitations; and
- what remains unknown.

A completed investigation may conclude that the evidence is insufficient to answer the question.

## Information and ownership model

The Workbench keeps three information classes separate.

| Layer | Contents | Authority and lifecycle |
| --- | --- | --- |
| **Canonical evaluation sources** | Evaluation briefs, product sources, coverage requirements, dimensions, cases, cohorts, criteria, evaluator definitions, trusted labels, and other versioned evaluation knowledge | Externally authored, reviewed, validated, and immutable from the Workbench |
| **Investigation workspace** | Selections, execution references, judgments, notes, derived analysis, comparisons, findings, questions, and investigation state | Working state associated with one investigation |
| **Handoffs** | Source identities, evidence, findings, proposed changes, constraints, unresolved questions, and acceptance checks | Explicit proposals for an external authoring or engineering workflow |

Derived analysis must remain distinguishable from source facts and expert input. A handoff proposes work; it does not become canonical merely because the Workbench produced it.

## Investigation lifecycle

An evaluation investigation has three high-level states:

```text
Draft
    ↓
Active
    ↓
Completed
```

**Draft:** the investigation and Evaluation Brief are being established.

**Active:** the investigation may evolve through design, execution, judgment, analysis, and refinement.

**Completed:** the investigation has a primary finding or an explicit insufficient-evidence conclusion for its governing question.

A completed investigation is a frozen historical record. Its meaning remains tied to the exact brief, evaluated SUT and configurations, cases and cohorts, execution evidence, criteria, judge and evaluator versions, analysis rules, results, finding, uncertainty, and limitations used at completion.

A materially new governing question or materially changed scope creates a new investigation.

## Relationship to the evaluation learning loops
### Product Improvement Loop

The Workbench supplies findings about product and system behaviour. It does not own causal diagnosis, prioritisation, product changes, acceptable trade-offs, or release decisions.

### Evaluation Knowledge Loop

The Workbench is an investigation surface for discovering and refining coverage, criteria, quality and failure concepts, evaluators, examples, labels, datasets, measurements, and evaluation rules. Canonical changes are promoted externally.

### Evaluation Infrastructure Loop

The Workbench may expose missing evidence, inaccessible evidence, broken attribution, inefficient review, evaluator execution limitations, or missing provenance. Infrastructure changes remain external.

## Relationship to current products

The Evaluation Workbench is a future investigation-level product direction.

### Evaluation Design Workbench

Provides framing and evaluation-design capabilities: evaluation question and boundary, product expectations, coverage requirements, dimensions, cases, cohorts, design gaps, and design handoffs.

### Evaluation Execution Subsystem

Remains a separate producer of attributable execution evidence. It executes selected cases and returns execution results and traces.

### Evaluation Trace Viewer

Provides the current human judgment-facing surface. It helps a domain expert inspect a case trace under an evaluation criterion and record an attributable judgment.

### Evaluation Workbench

Coordinates these capabilities around one evaluation investigation. This does not require every capability to be implemented in one process, service, page, or codebase.

## Product capabilities

At the product-frame level, the Evaluation Workbench should enable an expert to:

- create or open an evaluation investigation;
- establish and inspect its Evaluation Brief;
- understand the governing question and evaluated scope;
- inspect relevant product expectations and source evidence;
- inspect and shape coverage requirements, cases, cohorts, and criteria;
- identify evaluation-design gaps and unsupported assumptions;
- request execution against an identified SUT configuration;
- inspect execution results and traces;
- request automated evaluators;
- perform human judgment when required;
- inspect and compare judgments;
- identify disagreement, ambiguity, and unable-to-judge cases;
- measure and compare behaviour across defined scopes;
- inspect uncertainty and evidence gaps;
- produce evaluation results and a scoped primary finding;
- identify proposed evaluation-knowledge changes;
- prepare provenance-rich external handoffs;
- preserve traceability across the investigation; and
- complete and retain the investigation as a historical record.

## Trust and ownership boundaries

- Product and domain owners define product intent.
- The Workbench does not invent product commitments.
- Canonical evaluation sources establish source identity and provenance.
- Execution results and traces remain historical execution evidence.
- Judgments remain derived, attributable assessments and do not rewrite traces.
- Measurements retain the sample and scope that give them meaning.
- Findings retain links to the results, judgments, evidence, criteria, and evaluation question that support them.
- Expert notes remain investigation state unless promoted through an external reviewed workflow.
- Missing product intent remains missing.
- Missing evidence remains missing.
- Unsupported joins remain unsupported.
- Evaluator disagreement remains visible until resolved or explicitly accepted.
- Later knowledge does not silently rewrite completed investigations.
- A failed judgment does not establish root cause.
- A finding informs a product decision but does not make it.

## Explicitly excluded or deferred

The Workbench product frame does not imply ownership of:

- direct editing or approval of canonical evaluation sources;
- direct editing of product specifications;
- SUT implementation or product changes;
- execution-runtime implementation;
- automated evaluator implementation;
- causal root-cause diagnosis as an evaluation responsibility;
- product prioritisation;
- release approval or risk acceptance;
- hidden model reasoning;
- unsupported inference of product intent;
- silent relabeling of historical evidence;
- silent recomputation of completed investigations under new definitions; or
- a particular UI, navigation pattern, lens taxonomy, storage model, or deployment architecture.

## Success criteria

The product direction is successful when an expert can begin with a defined decision or knowledge need and produce a defensible evaluation finding without manually reconstructing the relationship among product intent, evaluation design, execution evidence, judgments, measurements, and analysis.

For a completed investigation, the expert should be able to answer:

- Why did this evaluation exist?
- What was the governing evaluation question?
- What product behaviour and SUT boundary were evaluated?
- Which product expectations applied?
- What evaluation design and sample were used?
- What system versions and configurations were executed?
- What evidence was captured?
- Which criteria and judges were applied?
- What judgments were produced?
- What measurements or comparisons were derived?
- What is the scoped answer to the evaluation question?
- What uncertainty or limitations apply?
- What remains unknown?
- What should change in reusable evaluation knowledge?
- Which sources and evidence support each material claim?

## Evidence status
### Observed

Current evaluation artifacts and product surfaces already support parts of the intended Workbench model:

- evaluation datasets can represent dimensions, cases, fixtures, cohorts, and coverage information;
- source records preserve local evaluation intent such as rationale, purpose, exclusions, failure surfaces, and product questions;
- saved execution results and traces preserve attributable evidence about case trajectories;
- human trace review benefits from complete interaction context rather than isolated final responses;
- judgments need to remain separate from execution evidence; and
- evaluation design, execution, and trace review currently exist as separate stages and surfaces.

### Inferred

The Workbench framing assumes:

- the evaluation investigation is a better primary organising object than datasets, runs, traces, or judgments individually;
- one governing question gives an investigation a coherent scope and completion condition;
- experts benefit from maintaining context across design, execution, judgment, and analysis;
- the Workbench can orchestrate execution and automated judges while leaving their implementation ownership separate;
- findings are stronger when measurements, scope, evidence, uncertainty, and product expectations remain connected;
- evaluation knowledge should change through explicit handoffs rather than silent mutation of canonical artifacts; and
- completed investigations should remain historical records when evaluation knowledge evolves.

### Unknown

Important open questions include:

- the minimum Evaluation Brief content required before an investigation can proceed;
- which investigation state needs durable persistence or collaboration;
- which expert jobs require integrated Workbench surfaces and which are better served by linked specialist tools;
- which analysis operations experts repeatedly use across evaluation question types;
- how automated and human judgments should be reviewed together;
- how evaluator disagreement and adjudication should work;
- how findings should be represented across current-state, regression, comparison, production, and release investigations; and
- which future navigation model best supports the investigation without recreating disconnected artifact viewers.

## Learning agenda

1. **Investigation as the primary object.** Test whether one governing question can organise representative evaluation tasks across design, execution, judgment, analysis, and findings.
2. **Evaluation Brief as the anchor.** Test whether experts can interpret coverage, evidence, judgments, and findings from a versioned brief without reconstructing intent from unrelated sources.
3. **Cross-stage continuity.** Observe where experts lose context when moving from design to execution evidence, traces to judgments, and judgments to analysis.
4. **Finding construction.** Test how experts move from judgments and measurements to a scoped answer, including uncertainty and insufficient-evidence outcomes.
5. **Evaluation-knowledge feedback.** Follow failed, ambiguous, and poorly fitting cases through evaluation-design revision and identify what an external handoff must preserve.
6. **Infrastructure feedback.** Identify which evidence and tooling gaps can be recognised during an investigation and converted into useful infrastructure handoffs.
7. **Workbench versus specialist tools.** Determine which activities require one shared investigation environment and which can remain specialised surfaces connected through stable identity and context.
8. **Navigation and lenses.** Derive navigation only after observing repeated expert jobs. Validate whether the existing lens concepts remain useful, need to expand, or should be replaced by another investigation-oriented model.
