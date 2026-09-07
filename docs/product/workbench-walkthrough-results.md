# Workbench Walkthrough Results

These walkthroughs were performed through the local Workbench, Wallet SUT, dataset viewer, and

trace viewer. They test the human evaluation flow, not production readiness.

## 1. Prepared cohort

1. Open the Workbench and choose `workbench-check-8`.
2. Review the eight selected cases together.
3. Run them with `qwen3.5:4b` and follow the active case and completed count.
4. Open the saved run and `T010/E01` in the trace viewer.

Result: eight traces were saved in declared order. The run retained `workbench-check-8` as its case

set identity, and the trace viewer opened the exact evidence artifact.

## 2. Focused developer probe

1. Search for `T010/E01` and `T011/E01`.
2. Select only those cases and run them as an ad hoc sample.
3. Compare their traces in the same saved run.

Result: `T010/E01` captured a public HTTP 502 while `T011/E01` produced a confirmation preview.

The overall run succeeded because both outcomes were captured as evidence. The 502 was SUT

behavior, not an execution failure.

## 3. Setup failure and retry

1. Select `T001/E01` and choose an unavailable model.
2. Observe the setup failure before case execution.
3. Keep the same selection, correct the model to `qwen3.5:4b`, and retry.
4. Open the successful trace.

Result: the failed attempt completed zero cases and created no result artifact. The corrected retry

saved one inspectable trace.

## 4. Reopen historical evidence

1. Stop the Workbench after a successful run.
2. Start it again with the same results directory.
3. Open the prior run from Saved runs without running Wallet again.

Result: the Workbench restarted idle and the prior artifact remained available through the trace

viewer.

## What playing the scenarios changed

- Selected cases are pinned together so a prepared cohort can be reviewed before execution.
- Prepared cohorts keep their source identity; edited selections become explicit ad hoc samples.
- Active, started, and completed cases are distinct, and full completion appears with success.
- Captured case-level errors are explained as evidence rather than implied run failures.

The prototype intentionally stops at selecting, running, recovering, and inspecting evidence.

Durable job management, multiple users, and automatic judgment remain outside this slice.
