# Evaluation Runner Ontology Analysis
## Purpose

This document refines the conceptual ontology of the evaluation runner and aligns its terminology with established usage in agent frameworks, dialogue systems, reinforcement learning, and observability systems.

The goal is to define the main product concepts and their boundaries. This is a conceptual model, not a serialized schema, tracing implementation, or runtime architecture.

The existing concepts document already establishes the central distinction:

* an **evaluation case** describes a bounded situation to exercise;
* a **case execution** is one actual execution of that case;
* a **case trajectory** is what actually happens;
* a **case trace** is the evidence captured about what happened;
* a **run result** collects the traces and run-level context.

The resulting ontology should preserve these distinctions while introducing lower-level terms only where they clarify the model.

## Core ontology

The primary conceptual chain is:

```text
Evaluation case
    ↓ instantiate
Case execution
    ↓ unfolds as
Case trajectory
    ↓ observed and captured as
Case trace
    ↓ collected into
Run result
```

This matches the relationship already defined in the concepts document.

An **evaluation run** sits around this chain and coordinates the execution of a selected set of cases against one SUT version and configuration.

The ontology therefore has two related layers:

```text
Behavioral semantics

Evaluation case
    ↓
Case execution
    ↓
Case trajectory

Evidence semantics

Case trajectory
    ↓ observation
Case trace
    ↓
Run result
```

This separation is important. The trajectory represents behavior that occurred. The trace represents available evidence about that behavior.

## Evaluation case

An **evaluation case** defines one bounded situation in which Wallet behavior is exercised.

The case is declarative. It establishes starting conditions, participant behavior or bounds on that behavior, and the situation being evaluated.

A case can currently use one of three interaction forms:

* standalone;
* fixed sequence;
* response-adaptive sequence.

These describe how participant actions are determined during execution. They are properties or modes of an evaluation case rather than peer concepts to trajectory or trace.

## Evaluation run

An **evaluation run** is one execution of a selected test set against a specific SUT version and configuration. It provides the shared execution and configuration context for the case executions belonging to that run.

The term should remain **evaluation run**, even though some external frameworks use `run` at a much smaller granularity.

For example, LangSmith defines a run as an individual unit of agent work and groups runs into a trace. In OpenTelemetry terms, LangSmith describes such a run as comparable to a span.

That usage conflicts with the established product meaning of evaluation run. Within this ontology, bare `run` should therefore be avoided where the level is unclear. **Evaluation run** is the canonical term.

## Case execution

A **case execution** is one actual occurrence of exercising an evaluation case against a specific Wallet setup.

It is the occurrence from which both the trajectory and trace arise.

The distinction is:

```text
case       = specification
execution  = occurrence
trajectory = behavior that occurred
trace      = evidence recorded about it
```

This distinction should remain central to the model.

## Case trajectory

A **case trajectory** is the ordered behavior that actually occurs during a case execution.

It includes participant actions, Wallet responses, and relevant changes in Wallet or its environment. The trajectory exists independently of whether the evaluation system observes or records every part of it.

`Trajectory` has useful precedent in agent systems. LangSmith defines a trajectory as an ordered representation of the path an agent took and distinguishes it from the nested execution detail contained in traces.

The exact LangSmith representation differs from this ontology: LangSmith derives a trajectory from recorded traces, while the evaluation runner defines trajectory as the behavior itself. The shared semantic idea is the **ordered behavioral path**.

The evaluation runner should retain its stronger distinction between actual trajectory and recorded trace.

## Turn

A **turn** should be introduced as a subordinate behavioral concept.

A turn represents one participant interaction cycle:

```text
participant action
    ↓
Wallet processing
    ↓
Wallet response
```

This fits the structure already present in standalone and sequential cases, although the existing document does not currently name that structure as a turn.

`Turn` is established dialogue-system terminology. LangSmith defines a turn as one user message together with everything the agent does in response, and represents a multi-turn session as a sequence of such interactions. OpenAI's Agents SDK similarly instruments model turns as `turn_span` operations.

The proposed relationship is:

```text
Case trajectory
    ├── Turn 1
    │   ├── participant action
    │   ├── Wallet response
    │   └── relevant state changes
    │
    ├── Turn 2
    │   └── ...
    │
    └── Turn N
```

A standalone case normally produces one turn. Fixed and response-adaptive sequences can produce multiple turns.

A turn belongs to the **behavioral ontology**. It should not be defined as a tracing primitive.

## Case trace

A **case trace** is the attributable evidence captured about a case trajectory.

It records observable parts of execution and enough context to establish their source and ordering. It does not claim to contain the trajectory itself or everything that happened.

This meaning aligns well with established observability terminology.

OpenTelemetry models a trace as a set of related spans representing an operation. OpenAI's Agents SDK likewise defines a trace as one end-to-end workflow operation composed of spans.

The evaluation runner adds an important semantic constraint: the case trace is **evidence about the case trajectory**.

## Span

A **span** should be introduced as a subordinate trace concept.

A span represents one observable operation with a beginning and end inside a case trace.

```text
Case trace
    ├── span
    │   ├── child span
    │   └── child span
    ├── span
    └── span
```

This is the strongest cross-framework convention considered here.

OpenTelemetry defines a span as a unit of work or operation and the fundamental building block of a trace. Spans can form parent-child relationships and contain timestamps, attributes, events, links, and status.

OpenAI's Agents SDK follows the same structure: traces contain spans, and spans represent timed operations such as agent execution, model generations, tool calls, guardrails, handoffs, and turns.

LlamaIndex also exports workflow steps, LLM calls, and custom operations as OpenTelemetry spans, including nested span relationships.

The canonical conceptual name should therefore be **span**. `Trace span` may be useful in APIs or schemas when disambiguation is necessary, but it does not need to be a separate ontology term.

## Event

**Event** is useful as a lower-level concept, but it should not be part of the minimal core ontology yet.

The term has broad established usage with different meanings.

OpenTelemetry allows timestamped events to be attached to spans. Rasa represents a conversation as a sequence of events covering user messages, bot responses, actions, state changes, session transitions, and other occurrences.

This makes `event` suitable for representing a discrete observed occurrence, for example:

```text
span
    ├── event: request sent
    ├── event: tool output received
    └── event: state changed
```

However, `event` is sufficiently generic that introducing it without a concrete need could blur the distinction between actual behavior and recorded evidence.

If introduced, **trace event** should mean a recorded point-in-time occurrence attached to trace evidence. Actual participant actions, Wallet responses, and state changes should continue to be described as parts of the trajectory.

## Step

**Step should not be a core ontology concept.**

The term is established but heavily overloaded.

In reinforcement-learning environments, a step is one environment transition caused by an agent action. Gymnasium's `step(action)` advances the environment and produces the next observation and related outcome information.

LlamaIndex uses workflow steps as executable workflow units and exports those steps as spans for observability.

Other workflow systems use `step` for their own scheduler or graph execution semantics.

As a result, an unqualified `step` could mean:

```text
interaction step
workflow step
agent step
environment step
runner step
trace step
```

These are different concepts.

Where a subsystem genuinely has steps, the term should be qualified by that subsystem. It should not sit beside `turn`, `trajectory`, or `span` in the shared product ontology.

## Trajectory and trace

The most important boundary in the ontology is between **trajectory** and **trace**.

```text
CASE TRAJECTORY                        CASE TRACE

what happened                          what was captured

behavioral reality                     attributable evidence

participant actions                    recorded inputs
Wallet responses                       recorded outputs
state/environment changes              spans
other causally relevant behavior       trace events
                                       timing
                                       metadata
```

A trajectory may contain behavior that instrumentation cannot observe.

A trace may contain instrumentation metadata that is not itself part of Wallet behavior.

Therefore:

```text
trajectory ≠ trace
```

A trace is evidence about a trajectory.

This is already explicit in the current concepts document and should remain a defining property of the ontology.

## Turn and span

`Turn` and `span` also represent different dimensions.

A **turn** is a semantic unit of interaction.

A **span** is an observability unit representing an operation.

They can correspond in simple cases, but the ontology should not require a one-to-one mapping.

For example:

```text
Turn
│
├── participant action
│
└── Wallet response
     │
     └── represented in trace by
         ├── model span
         ├── tool span
         │   ├── database span
         │   └── API span
         └── generation span
```

One turn can produce many spans. A span can also represent work outside a participant-facing turn, such as case setup or cleanup.

## Resulting ontology

The recommended behavioral ontology is:

```text
Evaluation run
    │
    ├── Case execution
    │     │
    │     ├── Evaluation case
    │     │     defines/bounds
    │     │
    │     └── Case trajectory
    │           │
    │           ├── Turn
    │           │    ├── participant action
    │           │    ├── Wallet response
    │           │    └── relevant state changes
    │           │
    │           └── ...
    │
    └── ...
```

The corresponding evidence ontology is:

```text
Case execution
    │
    └── Case trajectory
          │
          │ observed through available instrumentation
          ↓
        Case trace
          │
          ├── Span
          │    ├── child Span
          │    └── trace Event
          │
          └── Span

Evaluation run
    │
    └── Case traces + run identity/configuration
          ↓
      Run result
```

The complete conceptual flow is:

```text
Evaluation case
    ↓ instantiated as
Case execution
    ↓ unfolds as
Case trajectory
    ↓ consists of
Turn(s)
    ↓ observed and captured as
Case trace
    ↓ structured using
Span(s) [and optionally trace events]
    ↓ collected with run context into
Run result
    ↓ consumed by
Judgment / failure understanding / diagnosis
```

## Recommended canonical vocabulary

The main shared concepts should be:

| Term                | Role                                                         |
| ------------------- | ------------------------------------------------------------ |
| **Evaluation case** | Definition of the bounded evaluation situation               |
| **Evaluation run**  | Execution of a selected set of cases under one configuration |
| **Case execution**  | One occurrence of exercising one case                        |
| **Case trajectory** | Actual ordered behavior during the execution                 |
| **Turn**            | One participant-Wallet interaction cycle within a trajectory |
| **Case trace**      | Captured evidence about a trajectory                         |
| **Span**            | Observable operation within a trace                          |
| **Run result**      | Durable collection of traces and run-level context           |

`Trace event` can be added when the trace representation requires discrete point-in-time observations.

`Step` should remain outside the shared ontology unless qualified for a specific subsystem.

## Naming principles

The ontology should follow four rules.

First, **behavior and evidence remain separate**. `Trajectory` describes behavior; `trace`, `span`, and trace events describe captured evidence.

Second, **interaction semantics and instrumentation semantics remain separate**. `Turn` describes the interaction. `Span` describes observable operations used to record it.

Third, **existing product terms take precedence where external frameworks use the same word differently**. In particular, `evaluation run` retains its current meaning even though frameworks such as LangSmith use `run` for a smaller execution unit.

Fourth, **generic terms should be qualified when their meaning depends on a subsystem**. This especially applies to `step` and `event`.

The resulting vocabulary gives the evaluation runner a small conceptual core while remaining compatible with terminology used in dialogue systems, agent evaluation, and standard observability tooling.
