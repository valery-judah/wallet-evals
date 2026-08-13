# Evaluation Runner Concepts

This document defines the shared product language for the evaluation running system. It describes execution and evidence semantics, not a serialized schema, file layout, tracing implementation, or runtime architecture.

## Evaluation case

An **evaluation case** defines one bounded situation in which Wallet behavior is exercised.

## Evaluation run

An evaluation run is a single execution of a selected test set against a specific version and configuration of the SUT.

During the run, each selected case is set up and executed, and the evaluation system captures evidence of what happens. It also records the SUT, model, environment, and other relevant settings so every case execution and trace can be tied back to the configuration that produced it.

The output of the run is a set of case traces that can be reviewed and judged later. The run itself does not decide whether the SUT behaved correctly.


## Case execution

A case execution is a single run of an evaluation case against a specific Wallet setup.

The runner prepares the case’s starting conditions and then runs the interaction with Wallet. The participant actions, Wallet responses, and resulting changes make up the case’s actual trajectory.

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

A case trajectory is what actually happens during a case execution, in the order it happens.
It includes the participant's actions, Wallet's responses, and any changes in Wallet or its environment that affect the course or outcome of the case.
The trajectory exists whether or not the evaluation system captures all of it. The runner only sees and records the parts of the execution that are observable through the available interfaces and instrumentation.

## Case trace

A **case trace** is the evidence the evaluation system captures about what happened during a case trajectory.

The trace records the observable parts of the execution, together with enough context to understand where that evidence came from and in what order events occurred.

It does not contain the trajectory itself or claim to capture everything that happened. It is the recorded evidence available for later review and judgment.

## Run result

A **run result** is the durable, attributable collection of evidence produced by one evaluation run.

It contains the traces produced by the run together with run-level identity and configuration information.

A run result does not include a runner-generated behavioral verdict.

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
Run result
    ↓ consume downstream
Judgment / failure understanding / diagnosis
```