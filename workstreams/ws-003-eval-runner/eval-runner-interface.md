# Evaluation runner interface requirements

These requirements identify only the domain interactions that must cross the evaluation runner boundary. They do not define internal responsibility-to-responsibility interfaces, component allocation, APIs, schemas, protocols, or deployment.

## `IR-1` — Operate an evaluation run

* **External party:** Evaluation operator
* **Purpose:** Start a run for selected evaluation cases under an identified Wallet, model, environment, and other relevant run settings, and identify the saved result when the run completes.
* **Information crossing the boundary:** Selected case identities; execution configuration; saved run-result identity.
* **Responsibilities served:** `R-1`, `R-7`
* **Workflow:** `WF-1`, `OUTCOME`

## `IR-2` — Bootstrap a case execution

* **External parties or capabilities:** Source of the selected evaluation-case definition; controllable Wallet and relevant environment state.
* **Purpose:** Establish one distinguishable case execution from its case-defined starting conditions and participant-action declaration, under the run's governing execution context and isolated from other case executions.
* **Information crossing the boundary:** Case definition; starting conditions; participant-action mode and bounds; execution context; controllable Wallet conditions.
* **Required result:** The case execution is ready to run from its defined, isolated starting conditions.
* **Responsibilities served:** `R-1`, `R-2`, `R-3`
* **Workflow:** `WF-1`, entry to `WF-2`

## `IR-3` — Exercise Wallet

* **External systems:** Identified Wallet and model under the governing execution context.
* **Purpose:** Supply case-valid participant actions and observe the Wallet behavior that forms the case trajectory.
* **Information crossing the boundary:** Participant actions; complete Wallet responses; relevant resulting Wallet or environment changes; participant-visible response facts required for response-adaptive action selection.
* **Required result:** Observable trajectory evidence is available in distinguishable occurrence order.
* **Responsibilities served:** `R-3`, `R-4`, `R-5`
* **Workflow:** `WF-2`, `WF-3`

## `IR-4` — Persist the run result

* **External capability:** Persistence destination.
* **Purpose:** Durably retain the complete identifiable run result independently of the Wallet execution runtime.
* **Information crossing the boundary:** Run identity and execution context; every produced attributable case trace.
* **Required result:** The saved run result remains available for later interpretation without rerunning Wallet.
* **Responsibilities served:** `R-7`
* **Workflow:** `WF-5`, `OUTCOME`

## Minimum blockers

None.
