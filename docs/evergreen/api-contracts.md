# API Contracts

The runner exposes a Python library API from `wallet_evals.runner`; the workbench exposes plan and

completed-evaluation models plus `evaluate_execution` and `run_workbench` from

`wallet_evals.workbench`. All domain models reject unknown fields and are frozen after validation.

Arbitrary payloads, response bodies, starting conditions, and settings must be JSON-compatible

values.

## Command-line operation

```text
wallet_evals run --case-set PATH
  [--wallet-repo PATH]
  [--model NAME]
  [--ollama-base-url URL]
  [--results-dir PATH]
```

`--case-set` is the only required option. It identifies a JSON document with

`schema_version`, `id`, `description`, and unique case identities. Companion fixture, tuple, and

per-tuple example files are resolved from the same directory. `--run-config` is intentionally

unused and reserved for a future document that can identify the SUT, model, environment, and

output settings together.

With no arguments the command prints help and succeeds. `--version` remains available. A run

returns status `0` only after saving a complete result, `2` for arguments, configuration, or

preflight failures, and `1` for execution or persistence failures.

The read-only dataset viewer command is:

```text
wallet_evals view-dataset
  [--dataset-dir PATH]
  [--port PORT]
  [--no-open]
```

It defaults to `data/dataset-1`, loopback port `8766`, and opening the default browser. Startup

loads and validates the entire co-located dataset. A missing or invalid dataset is a configuration

failure with status `2`; a server bind or runtime failure returns `1`. Ctrl-C closes the server

successfully, and browser-opening failure is non-fatal.

The dataset-viewer HTTP surface is read-only:

- `GET /api/dataset` returns the joined dataset metadata, totals, coverage, dimensions, tuples,
  executable cases, optional case sets, shared fixture, and source filenames.
- `GET /api/dataset/sources/<encoded-filename>` returns the exact validated JSON document for a
  discovered source filename.

Unknown, absolute, or traversal source names return `404`. There are no editing, approval,

case-set export, execution, or verdict routes.

The local viewer command is:

```text
wallet_evals view
  [--results-dir PATH]
  [--port PORT]
  [--no-open]
```

It defaults to `results/eval-runs`, loopback port `8765`, and opening the default browser. A

missing result directory is a configuration failure with status `2`; a server bind or runtime

failure returns `1`. Ctrl-C closes the server successfully. Browser-opening failure is non-fatal

because the URL is printed.

The viewer HTTP surface is read-only:

- `GET /api/runs` returns ordered artifact summaries, validation status, and the newest valid
  default artifact name.
- `GET /api/runs/<encoded-filename>` returns the exact validated artifact document and local
  file metadata.

Artifact names must match a discovered `*.json` filename in the configured directory. Invalid

artifacts appear in the index but return `422` when loaded. Missing or unmatched names return

`404`. There are no mutation routes or review-record interfaces in this version.

The local orchestration workbench command is:

```text
wallet_evals workbench
  [--dataset-dir PATH]
  [--wallet-repo PATH]
  [--model NAME]
  [--ollama-base-url URL]
  [--results-dir PATH]
  [--port PORT]
  [--dataset-viewer-port PORT]
  [--trace-viewer-port PORT]
  [--no-open]
```

It starts one page for case selection, Wallet execution, run status, and viewer handoffs. The

dataset and trace viewers remain separate read-only servers. The Workbench accepts one active run

at a time and retains generated ad hoc case sets outside the canonical dataset.

The optional deterministic evaluation command is:

```text
wallet_evals evaluate
  --plan PATH
  --execution-result PATH
  [--output-dir PATH]
```

The default output directory is `results/evaluations`. The plan must use schema `0.1` and contain

an `evaluation_plan` with a stable identity, Evaluation Brief, case-set identity, and ordered case

definitions. Each case definition has one criterion and one or more checks. Supported check kinds

are `outcome_sequence`, `response_json_equals`, `no_http_error`, and

`observable_change_count`.

The command requires the execution artifact's recorded case-set identity and complete ordered case

list to exactly match the plan. It returns `0` after saving a JSON evaluation artifact and Markdown

report, `2` for an invalid or mismatched plan or execution, and `1` for an unexpected persistence

failure. Each file is completed atomically, and existing artifacts for the same plan and run are

not overwritten.

## Run operation

```python
EvaluationRunner.run(request: RunRequest) -> SavedRunResultIdentity
```

`RunRequest` contains:

- `case_ids`: one or more unique selected case identities;
- `execution_context.wallet`: the identified Wallet;
- `execution_context.model`: the identified model;
- `execution_context.environment`: the identified environment; and
- `execution_context.settings`: other relevant JSON-compatible settings.

The call succeeds only after a complete `RunResult` has been saved. The return value contains

the same `run_id` and an adapter-defined `artifact_id` for the durable result.

## Case definitions and action plans

`CaseDefinition` contains `case_id`, `starting_conditions`, `case_context`, and one discriminated

action plan:

- `StandaloneActionPlan`: exactly one declared action;
- `FixedSequenceActionPlan`: one or more actions whose order is fixed before execution; or
- `ResponseAdaptiveActionPlan`: an initial action, private role context, allowed action names,
  case-specific selection bounds, and an inclusive maximum action count.

A `ParticipantAction` has a non-empty `name` and an optional JSON-compatible `payload`.

## Wallet exercise contract

```python
WalletExecutionFactory.bootstrap(execution: CaseExecution) -> WalletExecution
WalletExecution.perform(action: ParticipantAction) -> InteractionResult
WalletExecution.close() -> None
```

`CaseExecution` includes the run identity, case-execution identity, full selected case definition,

and effective execution context. Each `bootstrap` call must return fresh state for only that

execution.

`InteractionResult.observations` is a non-empty ordered sequence containing at least one

`WalletResponseObservation`. A response observation preserves the complete JSON-compatible

Wallet response and may expose named `ParticipantVisibleFact` values. An

`ObservableChangeObservation` preserves a subject, capture point, and JSON-compatible value.

The tuple order is the occurrence order the trace will preserve.

## Adaptive selection contract

```python
AdaptiveActionSelector.select_next(
    request: AdaptiveSelectionRequest,
) -> AdaptiveChoice | None
```

The request contains the private role context, allowed action names, case-specific selection

bounds, prior actions, and facts from the preceding interaction. `None` ends the sequence. A

choice must use an allowed action name and cite at least one fact that appeared in that preceding

response. The runner validates both conditions and the maximum action count before sending the

action. The selector adapter is responsible for applying any case-specific bounds carried in

`selection_bounds`. Only the chosen action and cited visible facts enter the trace; private role

context and selection bounds do not.

## Trace and result contract

Every `CaseTrace` contains:

- run, case-execution, and case identities;
- the effective execution context;
- case context and starting conditions; and
- events numbered contiguously from one.

Event kinds are `participant_action`, `wallet_response`, and `observable_change`. Adaptive

participant-action events also carry their visible factual basis. `RunResult` contains one or

more traces, requires distinct case-execution identities, and requires every trace to carry the

same run identity and execution context as the result.

## File artifact `0.1`

`JsonFileRunResultStore` writes `<percent-encoded-run-id>.json` with this envelope:

```json
{
  "schema_version": "0.1",
  "run_result": {}
}
```

`run_result` is the JSON representation of `RunResult`. Version `0.1` is an implementation

format for the MVP and makes no forward- or backward-compatibility guarantee.

The workbench writes `<plan-id>--<run-id>.evaluation.json` with this envelope:

```json
{
  "schema_version": "0.1",
  "completed_evaluation": {}
}
```

The completed evaluation snapshots the plan, execution provenance, judge identity, case judgments,

summary, and scoped finding. The companion `<plan-id>--<run-id>.md` is a derived readable report.

Neither file changes the source execution artifact.

## Errors

Model validation failures use Pydantic `ValidationError`. Capability failures propagate from

their adapters. Runner contract failures derive from `EvaluationRunnerError`, including missing

adaptive selection, case-definition identity mismatch, identity collision, out-of-bounds

adaptive choice, and persistence identity mismatch. No failure returns a successful saved-result

identity.

For the managed local Wallet adapter, public Wallet failures such as an HTTP 502 response are

captured as response evidence. They do not by themselves fail the run. Adapter, runner, and

persistence failures do fail the run and prevent a partial save.

Workbench plan or scope failures use `WorkbenchConfigurationError`. An absent response or JSON

path during an otherwise valid evaluation is recorded as an unable-to-judge check assessment, not

raised as a configuration error and never treated as a pass.
