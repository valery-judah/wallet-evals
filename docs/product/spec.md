# Product Spec

## Product outcome

Wallet evaluation turns a chosen configuration of synthetic cases into saved,
inspectable case traces. Those traces preserve evidence of what was exercised,
what Wallet exposed in order, and which execution produced the evidence so a
domain expert can judge the behavior without rerunning Wallet.

Evidence capture and correctness judgment are separate product stages. Successful
execution or capture does not imply that Wallet behaved correctly.

## Evaluation runner

An evaluation operator selects a case set and the Wallet, model, and run
configuration to exercise. The runner:

1. executes each selected case in isolated Wallet state;
2. captures an attributable trace of each case execution;
3. collects the case traces; and
4. saves identifiable run results for later inspection.

Input validation is supporting behavior rather than the runner's primary value
path. The runner does not grade Wallet behavior, decide whether a trace is
judgeable, or hand evidence to a particular judge.

See the [Evaluation Subsystem Product Frame](evaluation-subsystem-frame.md) for the
producer boundary and MVP detail.

## Evaluation trace viewer

A domain expert opens saved run results and judges one case execution as a whole
from its saved trace. The viewer presents case intent, ordered interactions,
adaptive choices, named observations, and linked diagnostics while preserving
their evidence roles.

The expert records pass or fail, or records that the case execution is not
judgeable from its trace. A verdict is a separate artifact and never changes the
saved trace.

See the [Evaluation Trace Viewer Product Frame](evaluation-trace-viewer-frame.md) for
the consumer boundary and judgment workflow.

## Shared trace contract

The runner and viewer share a storage-neutral semantic contract for case context,
execution identity, ordered steps, adaptive evidence, named observations,
and diagnostic references. The contract does not yet choose an exact serialized
schema, storage layout, observation schedule, or compatibility policy.

See [Product Concepts](concepts.md) for the shared vocabulary and evidence model.

## Current product decisions

- One case execution, interpreted through its attributable trace, is the v1
  correctness judgment unit.
- Wallet's complete response is preserved; display summaries are derived views.
- Observations are named by subject and capture point rather than stored as one
  timeless final-state value.
- Adaptive choices cite participant-visible response facts without preserving
  private reasoning.
- Runtime and model diagnostics are optional, step-linked supporting evidence.
