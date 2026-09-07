# Evaluation Design Workbench Product Frame
## Product outcome

The Evaluation Design Workbench helps a domain expert investigate and shape a defensible evaluation

design so the system under test (SUT) is exercised against product-important behavior and the

resulting evidence can answer a defined decision or knowledge need.

The workbench does not replace product judgment or domain expertise. It connects product intent,

coverage reasoning, evaluation artifacts, and exact source evidence so an expert can identify gaps,

select relevant context, and prepare grounded changes without reconstructing the evaluation from raw

files in every review.

The current dataset viewer is an implementation surface that provides some of these capabilities.

"Viewer" describes how that surface is delivered today. It is not the intended product category.

The product is an intent-led workbench composed of lenses over shared, validated evaluation sources.

## Product boundary

The workbench begins when a domain expert has a decision or knowledge need about the SUT and needs to

construct, inspect, or revise the evaluation coverage that could support it. The expert may begin

with a complete evaluation brief or with incomplete product and dataset sources whose gaps need to be

made explicit.

The workbench ends when the expert has either:

- established that the design is adequate for the stated evaluation question within a declared
  scope; or
- assembled a provenance-rich handoff describing what should be added, removed, clarified, or
  revised through an external authoring workflow.

The workbench supports evaluation design. It does not take ownership of the product decision that

motivated the evaluation, claim that a dataset is correct, or silently convert missing product

intent into evaluation requirements.

## Actors

- **Domain expert:** The primary user. Supplies product and domain judgment, investigates the design,
  identifies gaps or ambiguities, and decides what a handoff should ask an external workflow to
  change.
- **Evaluation engineer:** Maintains source contracts, validation, execution compatibility, and the
  external workflow that promotes reviewed changes into canonical evaluation artifacts.
- **Agent or repository workflow:** Consumes a grounded handoff and proposes or implements changes
  outside the workbench. It must preserve the handoff's sources, constraints, and unresolved
  questions.
- **Product owner or engineering team:** Uses the resulting evaluation design and later evidence to
  answer the decision or knowledge need. The workbench informs but does not make that decision.

## Primary job

When a domain expert needs to design or revise an evaluation for a SUT, help them connect the

evaluation question to product expectations, inspect how those expectations are represented in the

coverage model and cases, expose unsupported assumptions and gaps, and prepare an exact handoff for

the next revision.

The governing question for the first product slice is:

> Does this evaluation set exercise the product behavior and failure surfaces that matter for the
> stated evaluation question, and what should change if it does not?

## Operating model

```text
Evaluation brief
    ↓
Investigate through intent-specific lenses
    ↓
Capture findings, questions, notes, and selected evidence
    ↓
Assemble a lens-specific or cumulative handoff
    ↓
Revise canonical artifacts through an external workflow
    ↓
Reload and validate the changed design
```

This is a human-led loop. The workbench makes relationships and evidence easier to inspect. The

domain expert remains responsible for product meaning, and canonical changes remain subject to the

repository's normal review and validation process.

## Evaluation brief

A complete evaluation brief is the normative anchor for coverage construction. It is a versioned

source that identifies:

- the participant and their goal;
- the decision or knowledge need;
- the uncertainty that motivates evaluation;
- the evaluation question;
- the SUT and the evaluated boundary;
- applicable jobs, workflows, guarantees, invariants, critical failures, and unsupported behavior;
- coverage requirements and the evidence each requirement is intended to support;
- product, architecture, policy, research, or production sources; and
- unresolved product or evaluation questions.

This frame does not define a serialized evaluation-brief schema. A future source contract must do

that before the workbench can validate the brief as a runtime input.

If brief information is absent, the workbench must show the absence as a design gap. It may help an

expert collect source evidence and prepare a handoff to create or revise the brief, but it must not

infer product commitments from dataset frequency, tuple prose, or model-generated suggestions.

## Lenses

A lens is an intent-specific investigation over the same validated sources. It is not an independent

copy of the dataset. Lenses share source identity, filters, expert selections, and investigation

state while organizing evidence around the question the expert is trying to answer.

| Lens | Governing question | Intended result |
| --- | --- | --- |
| **Frame** | What are we evaluating, why, and against which product expectations? | A visible evaluation boundary, question, source basis, coverage requirements, and explicit gaps or open questions. |
| **Model** | Which dimensions and values represent meaningful behavioral variation? | A review of definitions, applicability, exclusions, missing distinctions, overlap, and connection to coverage requirements. |
| **Compose** | Which tuples exercise materially distinct purposes and failure surfaces? | A review of combinations, rationale, related tuples, omissions, duplication, and unrepresented interactions. |
| **Ground** | Are inputs, sequences, fixtures, and cases realistic and executable? | A review of the generated or observed input, message under test, interaction form, fixture and prelude fit, provenance, and exact case evidence. |
| **Balance** | Does the complete set adequately cover the intended scope? | A scoped account of represented, omitted, zero-coverage, overrepresented, redundant, baseline, difficult, and critical conditions. |
| **Handoff** | What evidence, gaps, questions, and exact records should guide the next revision? | A focused or cumulative packet that another agent or repository workflow can act on without losing provenance or constraints. |

Lens names are stable product concepts. A particular UI may implement them as tabs, routes, panels,

or another navigation structure without changing their purpose.

## Information layers

The workbench keeps three information layers separate.

| Layer | Contents | Authority and lifecycle |
| --- | --- | --- |
| **Canonical sources** | Versioned evaluation brief, dimensions, tuples, inputs, cases, fixtures, cohorts, and exact source documents. | Source evidence. Validated on load and never mutated by the workbench. |
| **Investigation workspace** | Browser-local selections, notes, questions, and lens findings. | Expert working state. Separate from source facts and not an approval or dataset revision. |
| **Handoffs** | Selected source identities and records, expert notes, derived findings, constraints, unresolved questions, requested changes, and acceptance checks. | Explicit output for an external workflow. A handoff proposes work but does not alter or approve canonical artifacts. |

Browser-local workspace state is the intended persistence boundary for the first workbench slice. It

must be keyed to the relevant evaluation-brief and dataset identities so a changed source set cannot

silently inherit stale findings. The expert must be able to clear the workspace and explicitly copy

or export its handoffs.

## Findings and handoffs

Each lens can produce a focused handoff. The workbench can also compose selected lens outputs into

one cumulative evaluation-design handoff.

A handoff must distinguish:

- facts copied from validated sources;
- coverage counts or relationships derived deterministically from those sources;
- notes and questions entered by the domain expert;
- gaps or inconsistencies identified through a declared workbench rule;
- proposed changes requested by the expert; and
- unresolved matters that require product, domain, or engineering judgment.

Every source-derived claim must retain sufficient identity to locate the source record. A handoff

must include the evaluation question and relevant constraints so an agent cannot treat a local edit

as an unconstrained request to regenerate the dataset.

The external workflow may propose changes, but the expert reviews them and the repository validates

them. After promotion, the workbench reloads the canonical sources and recomputes every lens from the

new validated state.

## Relationship to current implementation

The current read-only dataset viewer provides evidence for several planned lenses:

| Current capability | Workbench interpretation |
| --- | --- |
| Dataset purpose and validated source context | Partial Frame evidence, without a first-class evaluation brief or traceable coverage requirements. |
| Dimension definitions, values, applicability, and examples | Model lens. |
| Tuple purpose, coverage basis, failure surface, relationships, and generated inputs | Compose lens. |
| Complete cases, interaction forms, fixtures, preludes, and exact records | Ground lens. |
| Coverage statistics, omitted dimensions, filters, and cohorts | Balance lens. |
| Copyable tuple context | An early, tuple-scoped Handoff capability. |

This mapping is product interpretation, not a statement that the workbench has already been

implemented. The current CLI, HTTP API, browser routes, source layout, and read-only dataset viewer

remain the canonical MVP behavior until a later implementation plan changes them.

## Relationship to execution and trace evidence

The first slice focuses on coverage construction. SUT execution, trace review, and correctness

judgment remain separate product stages.

The existing trace viewer remains separate. Stable case and execution identities provide the future

bridge: later evidence-feedback handoffs may identify which case was executed, what source-recorded

behavior or finding motivates a design revision, and which coverage artifact may need review. They

must not mutate traces or infer unsupported causal relationships.

Trace integration is deferred. The workbench must not claim that a designed case produced useful

evidence merely because it is present or executable.

## Trust and ownership boundaries

- Product and domain owners define product intent. The workbench does not invent jobs, guarantees,
  critical failures, acceptable trade-offs, or release criteria.
- Canonical source records establish identity and provenance. Labels and ordering conveniences do not
  establish relationships that the sources do not declare.
- Deterministic joins and coverage calculations are derived findings and must remain distinguishable
  from source facts.
- Expert notes are investigation state. They do not become source truth or approval merely because
  they appear beside validated evidence.
- Handoffs are proposed work. They do not become canonical until an external workflow implements,
  reviews, and validates the change.
- Missing intent, ambiguous requirements, unsupported joins, and absent evidence remain visible as
  gaps. The workbench does not normalize them into plausible-looking defaults.
- The workbench displays only validated, source-recorded evidence and explicit expert input. It never
  requests, infers, or exposes hidden model reasoning.
- The workbench never modifies execution evidence or uses later findings to rewrite what a trace
  recorded.

## First product slice

The proposed first slice is one local Evaluation Design Workbench shell centered on coverage

construction. It includes:

- the six lenses defined in this frame;
- a versioned evaluation brief as the intended product-intent anchor;
- validated, immutable evaluation dataset sources;
- shared filters and identity-based navigation across lenses;
- browser-local notes and evidence selections kept separate from sources;
- lens-specific and cumulative guided handoffs; and
- explicit validation and reload after an external revision.

This is an intended product boundary, not a claim about the current implementation. Runtime

interfaces, source schemas, migrations, and UI behavior require separate design and delivery work.

## Explicitly excluded or deferred

- Direct editing or approval of canonical evaluation sources.
- Server-side persistence of investigation state.
- SUT execution, replay, rerun, or execution configuration controls.
- Correctness verdicts, evaluator execution, scoring, aggregation, or release gating.
- Root-cause diagnosis or decisions about which product or system change to make.
- Automatic invention of product expectations, coverage requirements, dimensions, or cases.
- Hidden model reasoning or evaluation-only private reasoning.
- Sampling, clustering, or cohort creation inside the first slice.
- Unified trace review, judgment, or evidence repair.
- Multi-user collaboration, assignment, adjudication, and access control.
- A permanent evaluation-brief, handoff, dataset, or workspace serialization contract.

## Success criteria

The product direction is successful when a domain expert can:

- state the evaluation question and evaluated SUT boundary before interpreting coverage;
- trace important dimensions, tuples, and cases to a coverage requirement and product source, or
  identify that the traceability is missing;
- identify meaningful gaps, overlaps, omissions, duplication, unrealistic cases, and unresolved
  product questions without reading every raw file independently;
- move from a readable projection to exact source evidence without losing record identity;
- distinguish source facts, deterministic findings, expert notes, and proposed changes;
- assemble a focused or cumulative handoff without manually reconstructing context in another tool;
- keep canonical artifacts unchanged during investigation; and
- reload externally revised sources and see the lenses recomputed from the validated result.

The workbench does not establish evaluation quality merely by making artifacts easier to inspect.

Success still depends on sound product sources, domain-expert review, realistic cases, appropriate

execution, adequate evidence capture, and later judgment.

## Evidence status
### Observed

- The current dataset can be validated and joined into dimensions, tuples, generated inputs,
  executable cases, fixtures, cohorts, coverage counts, and exact source records.
- Current sources preserve useful local intent such as dataset purpose, dimension rationale, tuple
  coverage basis, tuple purpose, failure surfaces, source-material references, exclusions, and open
  product questions.
- The current dataset viewer makes those artifacts easier to inspect and can produce copyable
  tuple-scoped context without editing the dataset.
- The current trace viewer is a separate read-only consumer of saved execution evidence.

### Inferred

- Artifact-oriented views are useful evidence surfaces but do not by themselves lead the expert from
  a decision need to a defensible evaluation design.
- Intent-specific lenses can reduce reconstruction work by keeping the governing question, relevant
  evidence, and expected investigation result together.
- A versioned evaluation brief is needed to make coverage traceable to explicit product intent rather
  than relying on tuple prose or source frequency.
- Guided handoffs can support construction while retaining a read-only trust boundary for canonical
  sources.

### Unknown

- The minimum evaluation-brief content that remains useful across products and SUT types.
- Which lens findings experts use in practice and which become distracting or redundant.
- How much browser-local investigation state experts need before they require a portable or shared
  workspace.
- Which source excerpts and acceptance checks make a handoff reliable for agent-assisted revision.
- How experts distinguish true coverage gaps from deliberate exclusions or risk-based allocation.
- Which trace findings should feed back into coverage design and what identity contract that bridge
  requires.

## Learning agenda

1. Review the six lenses against a complete Wallet coverage-design task and record where the expert
   still has to reconstruct context manually.
2. Draft an evaluation brief from existing Wallet product and architecture sources, then test whether
   it is sufficient to evaluate the current dimensions, tuples, and cases without inventing intent.
3. Compare lens-specific and cumulative handoffs on real revision tasks and check whether an external
   agent preserves source constraints and record identity.
4. Observe how experts use notes and selections across interruptions before choosing any persistence
   beyond browser-local state.
5. Use executed case findings to prototype an identity-based evidence-feedback handoff without
   merging the trace viewer or changing saved evidence.
6. Promote only validated product decisions into the evergreen MVP, architecture, API contracts, and
   runbook when corresponding runtime behavior is ready to be supported.
