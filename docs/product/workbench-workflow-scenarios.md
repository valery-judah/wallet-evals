# Workbench Workflow Scenarios

These scenarios test how a person moves through the evaluation components. They are not Wallet

behavior test cases and are not a production-readiness checklist.

The enacted results are recorded in

[Workbench Walkthrough Results](workbench-walkthrough-results.md).

## 1. Prepared cohort to evidence

An evaluation engineer selects the prepared eight-case cohort, chooses a local model, runs Wallet,

watches progress, and opens the saved run in the trace viewer.

The workflow succeeds when case intent is visible before execution, the run produces one saved

artifact, and the trace viewer opens that exact artifact.

## 2. Focused developer probe

A Wallet developer searches for two related ambiguity cases, selects only those cases, runs them as

an ad hoc cohort, and opens the resulting traces without changing the canonical dataset.

This was exercised with `T010/E01` and `T011/E01`. The Workbench staged the selection, captured both

traces, and exposed the run through the trace viewer.

## 3. Setup failure and retry

An operator selects one case but chooses a model that is not installed. The run stops during

preflight, no execution artifact appears, and the selection remains available. The operator fixes

the model and retries.

This was exercised with `T001/E01`: the missing-model attempt failed with a useful setup message,

and the retry with `qwen3.5:4b` produced one saved trace.

## 4. Behavior failure is still inspectable evidence

Wallet returns undesirable behavior, such as a captured public error, but the runner still

completes because the evidence boundary worked. The operator can open that trace rather than seeing

the attempt mislabeled as an infrastructure failure.

The focused ambiguity run exercised this distinction: Wallet behavior included a public processing

failure while the two-case execution itself completed and remained inspectable.

## 5. Reopen historical evidence

A reviewer opens the Workbench after earlier runs exist, chooses a saved run, and enters the trace

viewer without rerunning Wallet. Historical evidence stays separate from the current case selection

and any new attempt.
