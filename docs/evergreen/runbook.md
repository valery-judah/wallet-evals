# Runbook

`make help` lists every command. This runbook says when to use each one. Pass extra CLI options
with `ARGS='...'`, for example `make eval-run ARGS='--model qwen3.5:4b'`.

## Command entry points

| Prefix | Owns | Doesn't own |
| --- | --- | --- |
| `setup-` | Dependency sync, the lock file, Git hooks, and `clean` | Running evaluations or pages |
| Checks: `fmt`, `fmt-check`, `lint`, `type`, `test`, `verify`, `secret-scan` | Formatting, lint, types, tests, and secret scans. Only `fmt` changes files | Calls to Wallet or Ollama |
| `eval-` | Runs that call Wallet and Ollama, and judging saved runs. Both write to `results/` | The dataset in `data/` and the viewers |
| `workbench-`, `dataset-`, `trace-` | The local pages, each in the foreground on its own port | Background process management |
| `build` | Source and wheel distributions in `dist/` | Publishing |

Make calls Poe tasks from `poe_tasks.toml` and the `wallet_evals` CLI. The old names `init`,
`sync`, `install-git-hooks`, and `check` still work as aliases.

## Setup

```bash
make setup
```

`make setup` syncs dependencies into `.venv` and points Git at `.githooks/`. The pre-commit hook
runs `make secret-scan-staged`.

## Validation

Run the full read-only check after code changes:

```bash
make verify
```

`make verify` runs `fmt-check`, `lint`, `type`, and `test` and stops at the first failure. Run one
step on its own with the target of the same name. Filter tests with `ARGS`:

```bash
make test ARGS='tests/test_runner.py'
make test ARGS='-k workbench'
```

`make fmt` formats code and fixes lint issues in place. `make secret-scan` checks every tracked
file for Gemini API keys.

## Run a case set against Wallet

Prerequisites:

- the Wallet repository is checked out at `../wallet`, or its path is passed with
  `ARGS='--wallet-repo PATH'`;
- Ollama is reachable at `http://127.0.0.1:11434`, or another endpoint is passed with
  `--ollama-base-url`; and
- the selected model is installed in Ollama. The default is `qwen3.5:9b`.

Run the ten-case cohort:

```bash
make eval-run
```

`CASE_SET` selects another case set:

```bash
make eval-run CASE_SET=data/dataset-1/<case-set>.json
```

The case-set file contains `schema_version`, `id`, `description`, and a unique list of case
identities. Its directory must contain the current dataset files:

```text
wallet_v1_case_fixtures.json
wallet_v1_evaluation_tuples_aligned.json
wallet_v1_examples_<tuple-id>.json
```

All selected fixtures, tuples, examples, and interaction forms are validated before Wallet starts.
Supported forms are standalone, fixed sequence, and the T020 adaptive sequence with a message, an
offered confirmation, an idle assertion, and the focal message.

Each case runs in a fresh in-memory Wallet. The command starts a managed worker,
`scripts/devex/run_wallet_cohort.py`, with the Wallet backend's own `uv` environment, so this
package doesn't depend on a Wallet source path.

CLI options, passed with `ARGS`:

```text
--wallet-repo PATH       default: ../wallet
--model NAME             default: qwen3.5:9b
--ollama-base-url URL    default: http://127.0.0.1:11434
--results-dir PATH       default: results/eval-runs
```

The command prints one progress line per case, such as `[3/10] T006/E01`. After the result is
saved, it prints:

```text
Run ID: <id>
Result: <absolute artifact path>
```

Exit status `0` means the complete result was saved. Status `2` means the arguments, dataset,
Wallet checkout, or Ollama check failed before the run. Status `1` means execution or saving
failed. A failed run doesn't save a partial result.

## Judge a saved run

```bash
make eval-judge \
  PLAN=data/evaluation-plans/workbench-check-8.plan.v1.json \
  RUN=results/eval-runs/<run-id>.json
```

The plan must match the saved run's case set exactly. The command applies the plan's
deterministic checks without running Wallet. It saves the evaluation as JSON and Markdown in
`results/evaluations/`; pass `ARGS='--output-dir PATH'` to save it somewhere else.

## Run the workbench

```bash
make workbench-run
```

The workbench serves `http://127.0.0.1:8764` and starts the dataset and trace viewers next to it.
Start from a prepared case set or pick cases, run Wallet, then open the saved evidence. If setup
fails, fix the model or local service and retry with the same selection. Pick another model with
`ARGS='--model qwen3.5:4b'`.

Workflow checks to try:

- run the prepared eight-case cohort and inspect one difficult trace;
- select only two related cases for a focused developer check;
- choose a missing model, see the setup failure, then retry; and
- reopen an older saved run without rerunning Wallet.

These scenarios test the evaluation workflow and the links between pages. They don't measure
Wallet's production quality.

## Inspect dataset coverage

```bash
make dataset-view
```

`DATASET` selects another dataset directory; the default is `data/dataset-1`. The viewer listens
only on `127.0.0.1`, uses port `8766`, prints the URL and the absolute dataset directory, and opens
the default browser. Pass `ARGS='--port PORT'` for another port or `ARGS='--no-open'` to skip the
browser. Stop it with Ctrl-C.

Use the printed `http://127.0.0.1:<port>` URL. Opening the packaged HTML file directly as a
`file://` page can't reach the dataset API and shows launch instructions instead.

Startup validates every dimension, tuple, generated-input file, case fixture, interaction form,
and case set before the browser opens. An invalid file or broken reference between files stops
startup.

- **Overview** shows dataset identity, purpose, case sets, and source context.
- **Statistics** shows tuple and executable-case counts for every declared dimension value, and
  lists omitted dimensions separately. A tuple with several values counts toward each one.
- The other tabs show dimension definitions, tuple purpose and failure context, generated message
  sequences with the message under test marked, fixtures, preludes, case-set membership, and the
  exact source JSON. Search and filters apply across tuples and cases. Recorded case fixtures and
  the shared fixture are shown separately.

In a tuple, choose JSON or Markdown and use **Copy handoff** to copy its dimension definitions,
tuple record, generated user inputs, and the other tuple records, for use in another chat.

The viewer never writes dataset files, exports a case set, runs Wallet, records approvals, or
records a verdict.

## Inspect saved run results

```bash
make trace-view
```

`RESULTS` selects another result directory; the default is `results/eval-runs`. The viewer
listens only on `127.0.0.1`, uses port `8765`, prints the URL and the absolute result directory,
and opens the default browser. `--port` and `--no-open` work as for the dataset viewer. Stop it
with Ctrl-C.

Every `*.json` file in the directory is listed. Schema `0.1` files that validate as `RunResult`
can be opened. Invalid files show their validation error and can't be selected. The newest valid
file by modification time opens first; modification time only orders the list and says nothing
about run identity or execution order.

The case view shows:

- purpose, failure surface, dimensions, and starting conditions;
- participant actions, complete Wallet responses, the facts behind each adaptive choice, and
  observations, in recorded event order;
- labelled response summaries, with the exact response and visible facts underneath; and
- run, case-execution, Wallet, model, environment, settings, and raw trace evidence.

The viewer never calls Wallet or writes to the result directory. It doesn't record pass, fail, or
not-judgeable reviews.

## Integrating the runner

Construct `EvaluationRunner` with:

1. a `CaseDefinitionSource` that returns the exact requested case identity;
2. a `WalletExecutionFactory` that creates fresh isolated state from the supplied
   `CaseExecution`;
3. a `RunResultStore`, normally `JsonFileRunResultStore(Path(...))` for local use;
4. an `AdaptiveActionSelector` if any selected case is response-adaptive; and
5. optionally, a custom `IdentityGenerator` for controlled environments or tests.

Then pass a validated `RunRequest` to `run`. Treat the returned `artifact_id` as the result of a
successful run. If the call raises, the runner didn't save a complete run result.

The default identity generator uses UUIDs. The local file store creates its directory when
needed, refuses to replace an existing result identity, and returns an absolute artifact path.

## Adapter checklist

- `bootstrap` must not reuse mutable Wallet or environment state across cases.
- `perform` must return observations in occurrence order and include the complete Wallet
  response, even when that response shows wrong behavior.
- Participant-visible facts must include only facts the participant actually saw.
- `close` must release the state owned by that case execution.
- `save` must not return until the whole result is durably saved and must identify the same run
  it received.

## Package

```bash
make build
```

`make build` writes source and wheel distributions to `dist/`. `make clean` removes caches and
generated local files.
