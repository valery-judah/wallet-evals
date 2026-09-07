# Reasoning Behind the Evaluation Workbench Frame
## Purpose of this document

This document records the reasoning process that led from the earlier evaluation-run, trace-viewer, and design-workbench concepts to the current **Evaluation Workbench Product Frame**.

It is not another product specification. Its purpose is to preserve:

- which conceptual problems we identified;
- which distinctions we introduced;
- which product boundaries we chose;
- which alternatives we rejected;
- how the evaluation methodology influenced the product frame; and
- which questions we intentionally left open.

The main outcome of the discussion was a shift from thinking about evaluation as a collection of tools and artifacts to thinking about it as a **question-centered investigation that produces trustworthy, scoped findings**.

## 1. Starting point: execution was being called evaluation

The first conceptual problem appeared in the term **evaluation run**.

The existing model used that term for:

```text
selected test-set cohort
    ↓
run the SUT
    ↓
collect traces
```

But at that point no one had yet decided whether the observed behaviour was acceptable.

The run produced evidence. It did not yet produce an evaluation.

That led to the first major distinction:

```text
Execution
    ↓ produces evidence
Judgment
    ↓ produces assessments
Evaluation
    ↓ produces results
```

This became the core semantic boundary for the rest of the work.

### Why the old terminology was misleading

Calling SUT execution an **evaluation run** compressed two different activities:

1. observing what the system did; and
2. deciding how that behaviour should be assessed.

This made it difficult to answer basic lifecycle questions:

- Has a completed run already been evaluated?
- Can the same trace be judged twice?
- Can two judges disagree?
- Can criteria change without changing the trace?
- What is the difference between a run result and an evaluation result?

The revised terminology therefore became:

```text
evaluation run  → execution run
run result      → execution result
```

A trace became explicitly historical evidence about what happened.

## 2. Judgment became a first-class concept

Once execution and evaluation were separated, the missing middle stage became obvious.

The useful primitive is not:

```text
trace → pass/fail
```

It is:

```text
trace
+
evaluation criterion
+
judge
    ↓
judgment
```

This was an important change because a pass/fail value has no meaning in isolation.

The same execution can:

- pass one criterion;
- fail another;
- receive different judgments from different judges;
- be judged again after an evaluator changes; or
- remain unable to support a judgment because evidence is insufficient.

The **judgment** therefore became an attributable artifact with its own lifecycle.

A judgment is tied to:

- the evidence target;
- the criterion;
- the judge;
- the judge configuration;
- the assessment; and
- supporting evidence or explanation.

Execution evidence remains unchanged when judgments change.

### Why this distinction matters

Without a first-class judgment object, the system would eventually have to place evaluator output inside traces or overwrite earlier verdicts.

That would mix historical evidence with later interpretation.

The new model preserves both.

## 3. Evaluation became the interpretation layer above judgments

Once judgment was explicit, **evaluation result** could be reserved for a later stage.

The resulting hierarchy became:

```text
Execution result
    ↓
Judgments
    ↓
Aggregation / comparison / interpretation
    ↓
Evaluation result
```

This clarified that a collection of pass/fail labels is still not automatically the answer to the motivating product question.

An evaluation result has meaning only within:

- a defined sample;
- a defined scope;
- the criteria applied;
- the analysis method; and
- the evaluation question being answered.

This distinction later became central to the Evaluation Workbench frame.

## 4. The execution subsystem was narrowed to one responsibility

The earlier **Evaluation Subsystem Product Frame** was then reconsidered.

Its actual responsibilities were:

- execute cases;
- capture traces;
- preserve provenance; and
- save the resulting evidence.

It explicitly did not judge correctness.

The product frame was therefore reframed around an **Evaluation Execution Subsystem**.

Its successful output became:

```text
Execution run
    ↓
Execution result
    └── case traces
```

The subsystem owns execution and evidence capture.

It does not own:

- criteria;
- judges;
- judgments;
- aggregation; or
- evaluation findings.

This was the first important product-boundary rule that carried into the later Workbench design:

> A product may orchestrate another subsystem without absorbing that subsystem's semantic responsibility.
## 5. The trace viewer was recognised as a judgment surface

The next question was the **Evaluation Trace Viewer**.

The original viewer framing said that the user:

- opens saved traces;
- reviews the execution;
- applies an evaluation basis; and
- records pass/fail or not-judgeable.

That means its real job is judgment, even though its implementation is called a viewer.

For a time we considered renaming the future product to **Judgment Workbench**.

That was conceptually clean, but we decided not to force the rename into the current product framing.

The resulting approach was:

- keep **Evaluation Trace Viewer** as the current product/surface name;
- rewrite its frame using the new execution/judgment/evaluation concepts; and
- treat it as the current human-facing implementation of the judgment stage.

This preserved continuity with the existing product while fixing its semantics.

### Whole-case judgment was kept as an MVP choice

The current viewer judges one case execution as a whole.

We explicitly avoided turning that into a universal evaluation rule.

The broader concept allows a judgment to target other defined evidence scopes in the future.

So:

```text
whole case execution
```

is a first-slice product constraint, not the definition of judgment itself.

### "Not judgeable" was also reframed

A further distinction was introduced:

```text
pass / fail
```

are behavioural verdicts.

```text
unable to judge
```

describes the outcome of a judgment attempt.

It may arise because:

- evidence is incomplete;
- evidence cannot be attributed;
- the criterion is ambiguous; or
- another explicit limitation prevents the requested assessment.

This avoids treating lack of evidence as a property of the SUT's behaviour.

## 6. The Evaluation Design Workbench remained a separate product responsibility

A future **Evaluation Design Workbench** already existed as a product concept.

Its responsibility is evaluation design and coverage construction:

- product intent;
- evaluation questions;
- coverage requirements;
- dimensions;
- cases;
- cohorts;
- design gaps; and
- revision handoffs.

We considered whether trace judgment should simply become another lens inside that product.

We rejected that for the current conceptual model.

Design and judgment answer different governing questions.

Evaluation design asks:

> Does this evaluation design exercise the behaviour needed to answer the evaluation question?

Judgment asks:

> Given this evidence and criterion, what assessment is supported?

Keeping those responsibilities distinct reduced the risk of building one vague product that owned every evaluation activity.

This distinction later became useful when defining the larger Evaluation Workbench as an investigation-level product that can coordinate specialist capabilities without erasing their boundaries.

## 7. We then moved from individual products to the whole evaluation problem

At this point the system contained several clear pieces:

```text
Evaluation Design Workbench
    ↓
Evaluation Execution Subsystem
    ↓
Evaluation Trace Viewer / human judgment
    ↓
Evaluation results
```

The next question was no longer how to rename a component.

It was:

> What should the overall Evaluation Workbench exist to accomplish?

Instead of starting from the existing viewers or a proposed set of UI lenses, we returned to the evaluation methodology.

This changed the framing substantially.

## 8. Evaluation goals became the source of the Workbench design

The methodology defines evaluation as a practice that connects:

- product intent;
- observed behaviour;
- judgment;
- reusable evaluation knowledge; and
- product decisions.

It also gives the evaluation system a top-level goal:

> Provide trustworthy, scoped, and decision-relevant knowledge about AI Product and AI System behaviour.

We used that as the basis for the Workbench instead of deriving the product from current implementation surfaces.

The resulting Workbench goal tree became:

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

This was an important methodological decision.

The Workbench should be shaped by the knowledge work evaluation requires, not by which files or artifacts currently have viewers.

## 9. We chose to include findings, not stop at judgments

One boundary needed an explicit decision.

Should the Workbench stop after individual judgments?

We decided **no**.

A set of judgments still does not answer an evaluation question.

The Workbench therefore owns the reasoning layer that turns judgments into:

- measurements;
- comparisons;
- patterns;
- scoped evaluation results; and
- a finding that answers the governing question.

Conceptually:

```text
Judgments
    ↓
Measurements / comparisons / patterns
    ↓
Evaluation results
    ↓
Scoped finding
```

This made the Workbench an actual evaluation product rather than a combined design-and-review tool.

## 10. We chose external canonical authoring

The methodology treats evaluation knowledge as reusable and evolving:

- cases;
- coverage;
- criteria;
- evaluators;
- failure models;
- examples;
- labels;
- regression suites; and
- decision rules.

The question was whether the Workbench should directly modify these canonical artifacts.

We chose the **external authoring model**.

The Workbench may discover that evaluation knowledge should change, but it produces a handoff:

```text
Investigation finding
    ↓
Proposed knowledge change
    ↓
Provenance-rich handoff
    ↓
External authoring / repository workflow
    ↓
Review + validation
    ↓
Updated canonical sources
```

This preserved a useful trust boundary already present in the Design Workbench:

- canonical sources are source truth;
- investigation state is working state;
- handoffs propose changes;
- promotion to canonical status happens elsewhere.

This also avoids turning every exploratory finding into an implicit dataset or rubric mutation.

## 11. We chose orchestration without ownership

Another boundary question was whether the Workbench should merely inspect results created elsewhere or actively initiate evaluation activity.

We chose to let it **trigger and orchestrate**:

- execution runs;
- automated judges; and
- human review workflows.

But the Workbench does not own the internal semantics of those subsystems.

For example:

```text
Evaluation Workbench
    ↓ request
Execution Subsystem
    ↓
Execution result
```

and:

```text
Evaluation Workbench
    ↓ request
Automated evaluator
    ↓
Judgment
```

This gives the user an end-to-end investigation experience without collapsing all runtime responsibilities into one product.

## 12. The primary object became the evaluation investigation

This was the most important product-design choice after the execution/judgment split.

We considered two organizing models:

### Artifact-centered

```text
datasets
runs
traces
judgments
charts
```

### Investigation-centered

```text
decision / knowledge need
    ↓
uncertainty
    ↓
evaluation question
    ↓
design
    ↓
evidence
    ↓
judgments
    ↓
analysis
    ↓
finding
```

We chose the second.

The primary Workbench object is therefore an **evaluation investigation**.

Artifacts exist inside the investigation because they help answer its question.

This prevents the future product from becoming a collection of disconnected artifact viewers.

## 13. One investigation has one governing evaluation question

We then fixed the cardinality:

> One investigation has exactly one governing evaluation question.

Supporting subquestions may exist, but they remain subordinate to that question.

The reason is scope coherence.

One governing question gives the investigation:

- one reason to exist;
- one meaning for its evidence;
- one completion condition; and
- one primary finding.

If another question becomes independently important, it becomes another linked investigation.

## 14. The Evaluation Brief became mandatory

We decided every investigation should require an **Evaluation Brief**.

The brief is the normative anchor for:

- why the evaluation exists;
- the decision or knowledge need;
- the uncertainty;
- the governing question;
- the SUT boundary;
- applicable product expectations;
- evaluation scope;
- coverage requirements;
- intended evidence;
- sources; and
- unresolved questions.

The important rule is:

> The brief may be incomplete, but it may not be implicit.

Missing information is visible as a gap.

The Workbench may help investigate the gap, but it should not silently invent product intent.

We intentionally did not yet specify the minimum schema or exact validation rules for the brief. That is a later design question.

## 15. Completed investigations became immutable historical records

We then decided that an investigation should have a lifecycle:

```text
Draft
    ↓
Active
    ↓
Completed
```

A completed investigation is frozen.

Its finding remains tied to the exact:

- Evaluation Brief version;
- SUT and configurations;
- cases and cohorts;
- evidence;
- criteria;
- judge versions;
- analysis rules;
- results;
- uncertainty; and
- limitations

that existed when it was completed.

This prevents historical findings from silently changing meaning when:

- criteria evolve;
- labels are revised;
- datasets change;
- new evidence appears; or
- product expectations change.

New work creates a new linked investigation.

## 16. The Workbench became an investigation environment, not a single monolithic subsystem

The final frame therefore does not imply that all evaluation capabilities must live in one service, application, or codebase.

The Workbench is a **product-level investigation environment**.

It can coordinate specialised capabilities:

```text
Evaluation Workbench
│
├── Design capabilities
│
├── Execution orchestration
│       ↓
│   Execution Subsystem
│
├── Human judgment
│       ↓
│   Trace review surface
│
├── Automated judgment orchestration
│       ↓
│   Evaluators / judges
│
├── Analysis and evaluation results
│
├── Findings
│
└── Handoffs
        ↓
    External authoring / engineering workflows
```

The investigation is the shared context across them.

## 17. Information ownership became a Workbench-wide principle

The earlier Design Workbench had already distinguished three information layers.

We generalized them across the full Evaluation Workbench:

| Layer | Meaning |
| --- | --- |
| **Canonical evaluation sources** | Reviewed, versioned evaluation knowledge and product sources |
| **Investigation workspace** | Evidence references, judgments, analysis, notes, findings, selections, and active investigation state |
| **Handoffs** | Explicit proposals for external changes |

This gives the product a consistent rule:

> Investigation work may derive knowledge and propose changes without silently changing source truth.
## 18. Trust and traceability became a first-class product goal

The Workbench should preserve the chain from motivation to conclusion:

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

This chain is not merely provenance metadata.

It determines whether the final claim is defensible.

The Workbench must therefore preserve:

- version identity;
- scope;
- evidence provenance;
- evaluator provenance;
- uncertainty;
- disagreement;
- missing links;
- unsupported joins; and
- known limitations.

A clean-looking result is not sufficient if the evidence chain is weak.

## 19. The three evaluation learning loops influenced the boundaries

The methodology describes three connected loops:

### Product Improvement Loop

Changes the product or system.

The Workbench supplies evidence to it but does not own:

- prioritisation;
- root-cause diagnosis;
- implementation;
- product trade-offs; or
- release decisions.

### Evaluation Knowledge Loop

Changes the team's reusable understanding of how to evaluate the product.

The Workbench participates heavily here by discovering:

- coverage gaps;
- new quality or failure patterns;
- ambiguous criteria;
- evaluator problems;
- missing cases; and
- relabeling needs.

Canonical changes still happen externally.

### Evaluation Infrastructure Loop

Changes how evidence is captured and evaluation work is performed.

The Workbench may reveal:

- missing trace evidence;
- poor attribution;
- inaccessible evidence;
- inefficient review;
- missing evaluator capabilities; or
- insufficient provenance.

These become infrastructure handoffs.

This routing prevents every evaluation finding from being treated as a product bug.

## 20. We intentionally did not design the Workbench around lenses yet

The earlier Evaluation Design Workbench proposed a toolbox of lenses.

When moving to the whole Evaluation Workbench, we deliberately stopped short of extending that lens taxonomy.

The reason was methodological:

> Navigation should be derived from repeated expert jobs after the product responsibilities and investigation model are clear.

Starting with lenses risks preserving artifact-oriented structure under new names.

The current Workbench frame therefore defines:

- goals;
- boundaries;
- investigation lifecycle;
- information ownership;
- subsystem relationships;
- outputs;
- trust requirements; and
- product capabilities.

The future navigation model remains open.

The existing lenses may survive, expand, merge, or be replaced.

That should be decided from usage evidence rather than from conceptual symmetry.

## 21. Current product decomposition

The resulting conceptual product family is:

### Evaluation Design Workbench

Focused on evaluation framing, coverage, cases, cohorts, criteria, and design revision.

### Evaluation Execution Subsystem

Focused on running the SUT and producing attributable execution evidence.

### Evaluation Trace Viewer

The current human-facing judgment surface for inspecting execution evidence and recording judgments.

### Automated evaluators / judges

Specialised mechanisms that apply criteria and produce judgments.

### Evaluation Workbench

The future investigation-level product that coordinates these capabilities around one governing evaluation question and carries the work through scoped findings and learning handoffs.

This relationship is conceptual.

It does not require one deployment, one repository, or one UI.

## 22. The final product model

The resulting model can be summarized as:

```text
Participant
    ↓
Decision / knowledge need
    ↓
Uncertainty
    ↓
Evaluation Brief
    ↓
ONE governing evaluation question
    ↓
Evaluation investigation
    │
    ├── Design relevant evaluation coverage
    │
    ├── Request execution
    │       ↓
    │   Execution evidence
    │
    ├── Apply human / automated judgment
    │       ↓
    │   Judgments
    │
    ├── Measure / compare / interpret
    │       ↓
    │   Evaluation results
    │
    ├── Produce scoped finding
    │
    └── Identify evaluation-learning changes
            ↓
        External handoffs
```

The completed investigation becomes an immutable historical record.

Its finding informs a product decision but does not make that decision.

## 23. Main design principles that emerged

The discussion produced a small set of principles that should remain stable even if the UI and implementation change.

### Separate observation from interpretation

Execution records what happened.

Judgment assesses what happened.

Evaluation interprets judgments for a defined question and scope.

### Organize around questions, not artifacts

Runs, traces, criteria, and judgments are evidence and tools inside an investigation.

They are not the reason the product exists.

### Preserve explicit scope

Every measurement and finding is meaningful only under the sample, system configuration, criteria, and question that produced it.

### Keep canonical knowledge externally governed

The Workbench can investigate, derive, and propose.

Canonical evaluation knowledge changes through explicit reviewed workflows.

### Orchestrate specialised systems without absorbing their responsibilities

The Workbench may initiate execution and automated judging while preserving clear subsystem ownership.

### Treat uncertainty as a valid result

An investigation may complete with insufficient evidence.

An unable-to-judge case is not a pass.

A missing product commitment is not an inferred criterion.

### Preserve history

Completed investigations, execution evidence, and previous judgments remain attributable historical records.

Later learning creates new artifacts instead of silently rewriting the old ones.

### Let navigation follow work

Lenses, pages, tabs, and other UI structures should be derived after observing how experts actually conduct investigations.

## 24. Questions intentionally deferred

The frame leaves several decisions open by design.

They include:

- the exact Evaluation Brief schema;
- the minimum brief content required to begin execution;
- the persistence model for active investigations;
- multi-user collaboration;
- assignment and adjudication;
- the exact analysis toolkit;
- evaluator registry and configuration UX;
- how human and automated judgments are reconciled;
- when sub-case judgment targets are required;
- investigation lineage semantics;
- canonical handoff schemas;
- exact integration with repository workflows;
- online and production evaluation workflows;
- release-gating behavior;
- navigation and lens taxonomy; and
- implementation architecture.

These questions should be answered after the product frame is validated against representative evaluation investigations.

## 25. How to use this reasoning going forward

The current Evaluation Workbench frame should be treated as a product hypothesis grounded in the evaluation methodology and the conceptual distinctions developed during this discussion.

Future design work should be checked against three questions:

1. **Does this help answer the governing evaluation question?**
2. **Does it preserve the boundary between source evidence, derived judgment, analysis, and product decision?**
3. **Does it improve the ability to produce and reuse trustworthy evaluation knowledge?**

If a proposed feature cannot be connected to one of those responsibilities, it may belong in a specialist subsystem or another product loop.

The next design phase should therefore validate the investigation model through real evaluation tasks before committing to a permanent lens or navigation structure.
