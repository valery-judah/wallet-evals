# Evaluation System Concepts

This document defines the shared product language for executing an evaluation set, capturing evidence, judging that evidence, and producing evaluation results. It describes conceptual semantics, not a serialized schema, file layout, tracing implementation, judge implementation, or runtime architecture.

## Conceptual boundary

The system separates three stages that have different responsibilities and produce different artifacts:

```text
Execution
    ↓ produces evidence
Judgment
    ↓ produces assessments
Evaluation
    ↓ produces results
```

**Execution** asks what the SUT did under a defined case and configuration.

**Judgment** asks how captured behavior should be assessed against a defined evaluation criterion.

**Evaluation** uses judgments to answer a defined evaluation question for a declared scope.

This separation is important because execution evidence is historical evidence about what happened, while judgments and evaluation results are derived interpretations of that evidence. A trace remains the same even if it is judged later, judged by multiple judges, or judged under revised criteria.

## Evaluation case

An **evaluation case** defines one bounded situation in which Wallet behavior is exercised.

## Execution run

An **execution run** is one execution of a selected cohort of evaluation cases against a specific version and configuration of the SUT.

During the run, each selected case is set up and executed, and the execution system captures evidence of what happens. It also records the SUT, model, environment, and other relevant settings so every case execution and trace can be tied back to the configuration that produced it.

The output of an execution run is an execution result containing the captured case traces and run-level provenance. The execution run does not decide whether the SUT behaved correctly.

## Case execution

A **case execution** is a single run of an evaluation case against a specific Wallet setup.

The runner prepares the case's starting conditions and then runs the interaction with Wallet. The participant actions, Wallet responses, and resulting changes make up the case's actual trajectory.

The case determines how participant actions are supplied during execution.

### Standalone

A **standalone** case contains a single participant action.

```text
participant action
    ↓
Wallet response
```

No later participant action needs to be determined.

### Fixed sequence

A **fixed-sequence** case defines all participant actions before execution begins.

```text
action 1 → Wallet response 1
    ↓
action 2 → Wallet response 2
    ↓
action 3 → Wallet response 3
```

Wallet's responses are captured as evidence, but they do not determine which participant action comes next. The runner follows the sequence declared by the case.

For example, a case may define:

```text
1. "Show my recent transactions."
2. "Open transaction X."
3. "Show its details."
```

All three actions are known before Wallet is exercised.

Fixed sequences are appropriate when the intended participant behavior is known in advance and remains valid regardless of the specific form of Wallet's intermediate responses.

### Response-adaptive sequence

A **response-adaptive** case is used when a later participant action cannot be determined correctly until Wallet has responded.

```text
action 1
    ↓
Wallet response 1
    ↓
participant observes response
    ↓
select next action
    ↓
action 2
    ↓
Wallet response 2
```

The participant selects the next action from the Wallet behavior visible to it during execution, subject to the role, allowed actions, and other bounds declared by the case.

For example:

```text
Participant:
"Transfer $20 to Alice."

Wallet:
"Transfer prepared."
offered_actions = ["confirm", "cancel"]

Participant:
confirm
```

If Wallet instead asks the participant to select an account, `confirm` may no longer be a valid next action. The next step therefore cannot safely be encoded before execution.

Response-adaptive execution is needed when predefining the next action would assume the Wallet behavior that the case is intended to evaluate. The current product frame makes this the defining reason for adaptive execution.

The adaptive participant may use declared private role context and participant-visible Wallet responses to choose among allowed actions. The trace records the action actually selected and the participant-visible response facts used as its basis, but does not record private reasoning.

### Relationship to trajectory and trace

The **case execution** is the actual occurrence of exercising the case.

The actions taken, Wallet responses, and resulting state changes form the execution's **case trajectory**.

The runner captures attributable evidence about that trajectory as the **case trace**.

```text
evaluation case
    ↓
case execution
    ↓
case trajectory occurs
    ↓
runner captures evidence
    ↓
case trace
```

## Case trajectory

A **case trajectory** is what actually happens during a case execution, in the order it happens.

It includes the participant's actions, Wallet's responses, and any changes in Wallet or its environment that affect the course or outcome of the case.

The trajectory exists whether or not the evaluation system captures all of it. The runner only sees and records the parts of the execution that are observable through the available interfaces and instrumentation.

## Case trace

A **case trace** is the evidence the execution system captures about what happened during a case trajectory.

The trace records the observable parts of the execution, together with enough context to understand where that evidence came from and in what order events occurred.

It does not contain the trajectory itself or claim to capture everything that happened. It is recorded evidence available for later judgment, review, failure understanding, and diagnosis.

A case trace does not contain a behavioral verdict merely because it was produced for evaluation purposes.

## Execution result

An **execution result** is the durable, attributable output of one execution run.

It contains the case traces produced by the run together with run-level identity, configuration, and provenance information.

An execution result is evidence about SUT execution. It does not include a runner-generated behavioral verdict.

## Evaluation criterion

An **evaluation criterion** defines the basis on which captured behavior is judged.

A criterion states the behavior, property, requirement, or failure condition that a judge should assess from the available evidence. The criterion is part of the judgment context; it is not inferred from the trace merely because a case exercised related behavior.

Different criteria may be applied to the same case trace.

## Judge

A **judge** is an attributable evaluator that applies an evaluation criterion to captured evidence and produces a judgment.

A judge may be a domain expert, an LLM-as-Judge (LaJ), or another explicitly defined evaluation mechanism. Judge identity and relevant configuration must be attributable so a judgment can be understood and reproduced as far as the judging mechanism allows.

Judges consume execution evidence. They do not modify the case trace that records what happened.

## Judgment

A **judgment** is one attributable assessment produced by one judge for a defined evidence target under a defined evaluation criterion.

The evidence target will normally be a case trace or an explicitly identified part of the evidence associated with that case execution.

A judgment records the assessment produced by the judge, such as a pass/fail verdict, score, or label, together with enough identity and provenance to establish:

- which evidence was judged;
- which criterion was applied;
- which judge and judge configuration produced the assessment; and
- any recorded supporting evidence, explanation, or structured findings that are part of the judge's output.

A judgment is derived from execution evidence. It is not part of the execution evidence itself.

Multiple judgments may exist for the same trace and criterion. For example, a domain expert and an LLM-as-Judge may disagree. Preserving the judgments separately allows disagreement, review, reruns of judging, and later adjudication without rewriting the trace.

## Evaluation result

An **evaluation result** is a derived result that uses one or more judgments to answer an evaluation question for a defined scope.

Depending on that scope, an evaluation result may contain case-level outcomes, criterion-level outcomes, aggregate metrics, cohort summaries, or another explicit interpretation of the judgments. The aggregation or interpretation rule must be attributable rather than implicit.

An evaluation result retains links to the judgments and execution evidence from which it was derived.

Failure understanding and root-cause diagnosis may consume the same traces, judgments, and evaluation results, but they are separate activities. A failed judgment identifies that observed behavior did not satisfy a criterion; it does not by itself establish why the SUT behaved that way.

## Conceptual relationships

```text
Evaluation case
    ↓ instantiate
Case execution
    ↓ unfolds as
Case trajectory
    ↓ capture
Case trace
    ↓ collect
Execution result
    ↓ judge against criterion
Judgment
    ↓ aggregate / interpret for evaluation question
Evaluation result
    ↓ may inform
Failure understanding / diagnosis / product decision
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
          ↓
    one or more judges
          ↓
       judgments
          ↓
 aggregation / interpretation
          ↓
    evaluation result
```

The short form is:

```text
Execution produces evidence.
Judges produce judgments.
Evaluation produces results.
```

## Terminology rationale and evolution
### Previous model

The earlier terminology used **evaluation run** for SUT execution and **run result** for the collected traces and run metadata:

```text
Evaluation run
    ↓
Case traces
    ↓
Run result
    ↓
Judgment happens later
```

That model was internally sufficient while the document described only the runner. It becomes misleading once judging is modeled as a first-class part of the evaluation system.

There are four problems with the previous terminology.

First, **evaluation run** names an execution-only operation as evaluation. The operation exercises the SUT and captures evidence, but no criterion has yet been applied and no assessment has been produced. Calling that stage an evaluation makes it unclear whether a completed run means the system has merely produced traces or has already determined correctness.

Second, **run result** uses `result` for evidence that still requires judgment. This creates an ambiguous distinction once the system also needs an actual evaluation result. A trace collection is the result of execution, while an evaluation result is a derived answer based on judgments. Qualifying the first as **execution result** makes the lifecycle explicit.

Third, the previous model placed judgment only as an unspecified downstream consumer. That makes it difficult to represent the identity and lifecycle of assessments themselves. Once domain experts and LLM-as-Judge evaluators can inspect the same trace, the system needs a first-class **judgment** object so disagreement, repeated judging, judge-version changes, and adjudication can be represented without changing execution evidence.

Fourth, the previous model did not make the evaluation criterion explicit in the relationship between trace and verdict. A pass/fail value has meaning only relative to what was being assessed. The same trace may pass one criterion and fail another. Modeling the criterion as judgment context prevents a trace from being treated as intrinsically passing or failing.

### Current model

The current terminology assigns each stage a distinct responsibility and output:

| Stage | Governing question | Primary output |
| --- | --- | --- |
| **Execution** | What did the SUT do? | Case traces and execution result |
| **Judgment** | How does this evidence compare with this criterion? | Judgments |
| **Evaluation** | What do these judgments imply for the evaluation question and scope? | Evaluation result |

This model preserves the evidence boundary: execution artifacts record what happened; judgments record attributable assessments of that evidence; evaluation results record attributable interpretation or aggregation of judgments.
