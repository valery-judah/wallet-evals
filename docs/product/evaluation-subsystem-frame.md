# Evaluation Subsystem Product Frame

Domain experts and automated judges need attributable evidence of how an identified version of the SUT behaved when exercised against a selected set of evaluation cases, without having to rerun the system.

The evaluation subsystem executes those cases under a recorded configuration and produces saved case traces: captured evidence about the trajectories that occurred during execution.

Its successful outcome is an identifiable run result containing the traces produced by the run and the execution identity needed to interpret them.

The subsystem does not judge whether the observed behavior was correct.

## Primary workflow

`select cases and execution configuration → execute cases in isolation → capture case traces → save the run result`

## Proposed MVP boundary

### Included

* Targeted execution of one or more evaluation cases against an identified SUT and model/configuration.
* Isolation between case executions.
* Capture of attributable case traces.
* Preservation of the execution identity and configuration needed to interpret each trace.
* Durable saving of the run result and its traces as files.

### Explicitly excluded or deferred

* Correctness judgment, scoring, aggregation, thresholds, and release gating.
* Runner-generated judgeability or evidence-sufficiency decisions.
* Identification or classification of failures, error analysis, and root-cause diagnosis.
* A required judge, viewer, or publication workflow.
* Production-scale orchestration, parallel execution, and generalized multi-agent simulation.
* Historical analytics and cross-run reporting.
* A permanent serialized trace schema or tracing implementation.

## Downstream judgment boundary

A saved case trace is attributable evidence about one case execution and the trajectory that occurred.

A downstream domain expert or automated judge may evaluate that behavior from the trace against an applicable evaluation basis and record:

* **pass**; or
* **fail**, with a short evidence-grounded note identifying the first observable failure.

The verdict and failure note are downstream judgment artifacts. They are not produced by the evaluation runner and do not alter the saved trace.
