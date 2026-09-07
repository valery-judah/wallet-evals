# Evaluation Execution Subsystem Product Frame

The evaluation execution subsystem provides attributable evidence of how an identified version and configuration of the system under test (SUT) behaved when exercised against a selected cohort of evaluation cases.

It owns **execution and evidence capture**. It does not own correctness judgment or the final evaluation result.

Within the broader evaluation system:

```text
Execution
    ↓ produces evidence
Judgment
    ↓ produces assessments
Evaluation
    ↓ produces results
```

This subsystem implements the execution stage.

Its successful outcome is a durable **execution result** containing the case traces produced by an execution run together with the run identity, SUT identity, configuration, and provenance needed to interpret those traces later.

## Product outcome

Domain experts and automated judges need stable execution evidence so they can assess SUT behavior without rerunning the system or reconstructing the conditions under which a trace was produced.

The execution subsystem therefore:

- executes a selected cohort of evaluation cases against an identified SUT configuration;
- isolates case executions so one case does not unintentionally determine another;
- captures attributable evidence about each case trajectory as a case trace; and
- saves those traces and their run-level provenance as an execution result.

A completed execution run establishes what evidence was captured about what the SUT did. It does not establish whether that behavior was correct.

## Primary workflow

```text
select evaluation cases and execution configuration
    ↓
execute cases in isolation
    ↓
capture case traces
    ↓
save execution result
```

At run scope:

```text
Selected test-set cohort
    ↓
Execution run
    ↓
Execution result
  ├── case trace A
  ├── case trace B
  └── case trace C
```

The saved execution result is the handoff from execution to downstream judgment.

## Core concepts owned by this subsystem
### Execution run

An **execution run** is one execution of a selected cohort of evaluation cases against a specific version and configuration of the SUT.

The run records enough identity and configuration information to tie every case execution and trace to the conditions that produced it.

### Case execution

A **case execution** is one occurrence of exercising one evaluation case against a specific SUT setup.

The participant actions, SUT responses, and relevant resulting state changes form the case trajectory that occurs during execution.

### Case trace

A **case trace** is the evidence captured about a case trajectory.

It records observable execution evidence together with enough identity, ordering, and provenance to support later review and judgment. A trace is historical evidence about what was observed. It does not contain a behavioral verdict merely because it was produced for evaluation purposes.

### Execution result

An **execution result** is the durable, attributable output of one execution run.

It contains the case traces produced by the run together with run-level identity, configuration, and provenance information.

The execution result is evidence produced by execution. Later judgments and evaluation results derive from that evidence but do not modify it.

## Proposed MVP boundary
### Included

- Targeted execution of one or more evaluation cases against an identified SUT and model/configuration.
- Selection of a cohort of cases for an execution run.
- Isolation between case executions.
- Capture of attributable case traces.
- Preservation of the execution identity, SUT identity, configuration, and provenance needed to interpret each trace.
- Durable saving of the execution result and its traces as files.
- Stable identities that allow downstream judgment artifacts to refer back to the evidence they assessed.

### Explicitly excluded or deferred

- Evaluation criteria authoring or management.
- Correctness judgment by a domain expert, LLM-as-Judge (LaJ), or other judge.
- Judge execution, judge orchestration, or judge configuration management.
- Scoring, aggregation, adjudication, thresholds, and release gating.
- Production of evaluation results.
- Runner-generated judgeability or evidence-sufficiency decisions.
- Identification or classification of failures, error analysis, and root-cause diagnosis.
- A required trace viewer, judgment UI, or publication workflow.
- Production-scale orchestration, parallel execution, and generalized multi-agent simulation.
- Historical analytics and cross-run reporting.
- A permanent serialized trace schema or tracing implementation.

## Downstream judgment boundary

Judgment begins after execution evidence exists.

A **judge** is an attributable evaluator, such as a domain expert or LLM-as-Judge, that applies an **evaluation criterion** to identified execution evidence and produces a **judgment**.

Conceptually:

```text
Case trace + evaluation criterion + judge
                    ↓
                 judgment
```

A judgment may contain a pass/fail verdict, score, label, structured findings, or other criterion-specific assessment. It must remain attributable to the evidence, criterion, judge, and relevant judge configuration that produced it.

Multiple judgments may exist for the same case trace and criterion. Judges may disagree, and judging may be repeated under a different judge version or configuration. These later activities do not rewrite the saved case trace or execution result.

One or more judgments may then be aggregated or interpreted for a defined evaluation question and scope to produce an **evaluation result**.

```text
Execution result
    ↓ consumed by
Judges applying evaluation criteria
    ↓
Judgments
    ↓ aggregate / interpret
Evaluation result
```

The execution subsystem stops at the execution result. Judgment and evaluation consume its evidence through stable identities and provenance.

## Terminology rationale

Earlier versions called SUT execution an **evaluation run** and the saved trace collection a **run result**.

That terminology was workable while the subsystem was described only as a runner, but it becomes misleading once judgment and evaluation are explicit stages.

**Evaluation run** implied that completing SUT execution completed an evaluation. In practice, execution only produces evidence; no evaluation criterion has yet been applied and no judgment has been produced.

**Run result** also left the word `result` ambiguous. The saved trace collection is the result of execution, while an **evaluation result** is a later interpretation or aggregation of judgments. Calling the first artifact an **execution result** makes the lifecycle explicit.

The current terminology therefore assigns one responsibility to each stage:

| Stage | Governing question | Primary output |
| --- | --- | --- |
| **Execution** | What did the SUT do? | Case traces and execution result |
| **Judgment** | How does this evidence compare with this criterion? | Judgments |
| **Evaluation** | What do these judgments imply for the evaluation question and scope? | Evaluation result |

The subsystem described by this product frame owns the first row.
