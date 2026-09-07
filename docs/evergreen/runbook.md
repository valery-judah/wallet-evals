# Runbook
## Setup

```bash
make init
```

Use `uv` for every Python workflow in this repository.

## Validation

Run the full read-only verification suite after code changes:

```bash
uv run poe verify
```

Run the runner and viewer contract tests while iterating:

```bash
uv run pytest tests/test_runner.py tests/test_case_sets.py tests/test_dataset_viewer.py \
  tests/test_dataset_viewer_server.py tests/test_viewer.py tests/test_viewer_server.py \
  tests/test_workbench.py tests/test_cli_smoke.py
```

Formatting and individual checks are available through `uv run poe fmt`, `fmt-check`, `lint`,

`type`, and `test`. Use `uv run poe --help` for the current task catalog and `make help` for local

setup wrappers.

## Run the local ten-case cohort

Prerequisites:

- the Wallet repository is checked out beside this repository at `../wallet`, or its path is
  supplied with `--wallet-repo`;
- Ollama is reachable at `http://127.0.0.1:11434`, or another endpoint is supplied with
  `--ollama-base-url`; and
- the selected model is installed in Ollama. The default is `qwen3.5:9b`.

Run:

```bash
uv run wallet_evals run \
  --case-set data/dataset-1/harness-check-10.v1.json
```

The case-set file contains `schema_version`, `id`, `description`, and a unique list of case

identities. Its directory must contain the current dataset companions:

```text
wallet_v1_case_fixtures.json
wallet_v1_evaluation_tuples_aligned.json
wallet_v1_examples_<tuple-id>.json
```

All selected fixtures, tuples, examples, and interaction forms are validated before Wallet is

started. Supported forms are standalone, fixed sequence, and the T020 adaptive sequence with a

message, an offered confirmation, an idle assertion, and the focal message.

Optional overrides:

```text
--wallet-repo PATH       default: ../wallet
--model NAME             default: qwen3.5:9b
--ollama-base-url URL    default: http://127.0.0.1:11434
--results-dir PATH       default: results/eval-runs
```

The command prints one progress line per case. After a successful atomic save it prints:

```text
Run ID: <id>
Result: <absolute artifact path>
```

Exit status `0` means the complete artifact was saved. Status `2` means arguments, dataset,

Wallet checkout, or Ollama preflight were invalid. Status `1` means execution or persistence

failed. A failed run does not save a partial result.

## Run the smallest evaluation workbench

```bash
uv run wallet_evals workbench \
  --wallet-repo wallet-sut \
  --model qwen3.5:4b
```

The page opens the dataset and trace viewers alongside the Workbench. Start from a prepared case

set or hand-pick cases, run Wallet, then open the saved evidence. If setup fails, correct the model

or local service and retry with the same selection.

Useful workflow probes are:

- run the prepared eight-case cohort and inspect one difficult trace;
- select only two related cases for a focused developer check;
- choose a missing model, observe the preflight failure, then retry; and
- reopen an older saved run without rerunning Wallet.

These are scenarios for testing the evaluation workflow and handoffs, not claims about production

quality.

## Inspect dataset coverage

Launch the local read-only dataset viewer:

```bash
uv run wallet_evals view-dataset \
  --dataset-dir data/dataset-1
```

The viewer binds only to `127.0.0.1`, uses port `8766` by default, prints the local URL and

absolute dataset directory, and opens the default browser. Use `--port PORT` to choose another

port and `--no-open` for a headless session. Stop the server with Ctrl-C.

Use the printed `http://127.0.0.1:<port>` URL. Do not open the packaged HTML file directly; a

`file://` page cannot reach the validated dataset API and will show server-launch instructions.

Startup validates every dimension, tuple, generated-input file, case fixture, interaction form,

and optional case set before the browser opens. Invalid or incomplete joins prevent startup. The

Statistics tab reports tuple and executable-case counts for every declared dimension value and

shows omitted dimensions separately. Multi-valued tuples contribute to each assigned value. The

Overview tab keeps dataset identity, purpose, case sets, and validated source context separate

from those counts.

The remaining views provide dimension definitions, tuple purpose and failure context, complete

generated message sequences, message-under-test markers, fixtures, preludes, case-set membership,

and exact source JSON. In a tuple, choose JSON or Markdown and use **Copy handoff** to copy its

dimension definitions, exact tuple record, generated user inputs, and the other tuple records for

comparison in another chat. Search and filters apply across tuple and case review. Recorded case

fixtures and the shared fixture are shown separately rather than implicitly merged.

The viewer never writes dataset files, exports a case set, runs Wallet, records approval state, or

records a verdict.

## Inspect saved run results

Launch the local read-only trace viewer:

```bash
uv run wallet_evals view \
  --results-dir results/eval-runs
```

The viewer binds only to `127.0.0.1`, uses port `8765` by default, prints the local URL and

absolute result directory, and opens the default browser. Use `--port PORT` to choose another

port and `--no-open` for a headless session. Stop the server with Ctrl-C.

Every `*.json` file remains visible in the run browser. Schema `0.1` artifacts that validate as

`RunResult` can be opened. Invalid artifacts show their validation error and cannot be selected.

The newest valid artifact by file modification time opens initially; modification time is only

a local navigation convenience, not run identity or execution ordering.

The main case view presents:

- purpose, failure surface, dimensions, and starting conditions;
- participant actions, complete Wallet responses, adaptive factual basis, and observations in
  recorded event order;
- clearly labelled derived response summaries with the exact response and visible facts
  available underneath; and
- run, case-execution, Wallet, model, environment, settings, and raw trace evidence.

The viewer never calls Wallet or writes to the result directory. Pass, fail, and not-judgeable

review records are not part of this inspection-only version.

## Integrating the runner

Construct `EvaluationRunner` with:

1. a `CaseDefinitionSource` that returns the exact requested case identity;
2. a `WalletExecutionFactory` that creates fresh isolated state from the supplied
   `CaseExecution`;
3. a `RunResultStore`, normally `JsonFileRunResultStore(Path(...))` for local use;
4. an `AdaptiveActionSelector` if any selected case is response-adaptive; and
5. optionally, a custom `IdentityGenerator` for controlled environments or tests.

Then pass a validated `RunRequest` to `run`. Treat the returned `artifact_id` as the successful

operation result. If the call raises, no complete run result was established by the runner.

The default identity generator uses UUIDs. The local file store creates its destination

directory when needed, refuses to replace an existing result identity, and returns an absolute

artifact path.

## Adapter checklist

- `bootstrap` must not reuse mutable Wallet or environment state across cases.
- `perform` must return observations in occurrence order and include the complete Wallet
  response, even when that response is undesirable behavior.
- Participant-visible facts must include only facts actually available to the participant.
- `close` must release the state owned by that case execution.
- `save` must not return until the whole result is durably retained and must identify the same
  run it received.
