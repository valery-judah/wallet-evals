## Outcome-driven derivation

1. The outcome requires one saved, identifiable result. The system must therefore identify the run, collect its produced traces, and durably preserve them as one result.
2. The result must be interpretable without rerunning Wallet. The system must preserve the execution identity and relevant configuration that governed each trace.
3. Each trace must be attributable to the execution that produced it. The system must establish and preserve the relationship among the selected case, its execution, the run, and its configuration.
4. A trace is evidence of an actual case trajectory. The system must execute every selected case from its defined starting conditions, in Wallet state isolated from other case executions.
5. The trajectory depends on case-defined participant behavior. The system must supply actions according to the case’s declared mode and bounds, including response-adaptive selection from participant-visible Wallet behavior.
6. Later interpretation depends on evidence of what occurred and in what order. The system must capture the observable participant actions, complete Wallet responses, and relevant resulting changes in distinguishable occurrence order.
7. Response-adaptive behavior cannot be understood from actions alone. For those cases, the system must also preserve the selected actions and the participant-visible response facts on which selection was based, while excluding private reasoning.

## Minimal complete system responsibilities

**R-1 — Establish execution identity and governing context**  
Establish an identifiable evaluation run from the selected cases and identified Wallet, model, environment, and other relevant run settings, and make each case execution distinguishable as a member of that run before capturing its evidence.

**R-2 — Prepare each case in isolated starting conditions**  
For every selected case, prepare controllable Wallet conditions that reflect the case-defined starting conditions and remain isolated from every other case execution.

**R-3 — Conduct the case-defined interaction**  
Exercise each selected case against the identified Wallet and model by supplying participant actions according to the case’s declared action mode, role, allowed actions, and other bounds. For response-adaptive cases, determine later actions from participant-visible Wallet behavior within those bounds.

**R-4 — Capture an attributable ordered case trace**  
Capture evidence of each observable trajectory in distinguishable occurrence order, including participant actions, Wallet’s complete responses, and relevant resulting changes, while retaining the originating case-execution identity.

**R-5 — Preserve adaptive-choice evidence**  
For every response-adaptive case, preserve the action actually selected and the participant-visible response facts used as its basis, without preserving private participant reasoning.

**R-6 — Associate traces with their producing execution context**  
Associate every produced trace with its originating case execution, run identity, and the Wallet, model, environment, and other relevant settings that governed that execution.

**R-7 — Assemble and durably save the run result**  
Collect all traces produced by the run and durably save them, together with the run-level identity and execution context needed for later interpretation, as one identifiable result retained independently of the Wallet execution runtime.

These responsibilities stop at evidence preservation. They do not include correctness judgment, judgeability decisions, scoring, diagnosis, publication, or alteration of traces through downstream verdicts.

## Derived inputs

- `eval-runner-workflow-03.md`, providing the primary workflow, actor, trigger, transitions, outcome, and boundary
- `eval-runner-conditions.md`, providing the necessary behavioral conditions and their supported workflow transitions

## Authoritative basis

- `docs/product/evaluation-subsystem-frame.md`, “Primary workflow,” “Proposed MVP boundary,” and “Downstream judgment boundary”
- `docs/product/spec.md`, “Product outcome,” “Evaluation runner,” and “Current product decisions”
- `docs/product/concepts.md`, “Evaluation run,” “Case execution,” “Case trajectory,” “Case trace,” and “Run result”
