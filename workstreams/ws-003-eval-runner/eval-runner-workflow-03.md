## Primary end-to-end workflow

**Principal actor:** Evaluation operator

**Trigger:** The operator starts an evaluation run after selecting one or more cases and the identified Wallet, model, and run configuration.

**Workflow:**

1. The runner prepares isolated Wallet state for each selected case.
2. It executes each case according to the case-defined participant actions.
3. During execution, it captures attributable, ordered evidence of the observable trajectory.
4. It associates each case trace with the execution identity and configuration that produced it.
5. It collects and durably saves the traces as one identifiable run result.

**Successful outcome:** A saved, identifiable run result containing the produced case traces and enough execution identity and configuration to interpret them later without rerunning Wallet.

The workflow ends when the evidence is saved. Correctness judgment, scoring, diagnosis, and publication are downstream and outside this workflow.

**Evidence:** [Evaluation Subsystem Product Frame](/Users/val/projects/ps/wallet-evals/docs/product/evaluation-subsystem-frame.md), [Product Spec](/Users/val/projects/ps/wallet-evals/docs/product/spec.md), and [Evaluation Runner Concepts](/Users/val/projects/ps/wallet-evals/docs/product/concepts.md).
