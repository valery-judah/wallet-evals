# wallet-evals

Evidence-preserving evaluation runner and local workbench for Wallet behavior. The workbench gives
one human workflow for choosing cases, running Wallet, and opening the resulting evidence in the
existing read-only viewers.

The project uses a clean command model:

- `uv` manages environments and dependencies.
- `uv run poe <task>` runs Python developer workflows.
- `make <target>` is reserved for repo setup wrappers.

## Requirements
- Python 3.11+
- `uv`
- A Wallet checkout beside this repository, at `../wallet` by default
- Ollama running locally with `qwen3.5:9b`, unless command options select another endpoint or model

## Initialize The Repo
```bash
make init
uv run poe verify
```

## Run

```bash
uv run wallet_evals run \
  --case-set data/dataset-1/harness-check-10.v1.json
```

The case-set JSON selects case identities. Its directory must also contain:

```text
wallet_v1_case_fixtures.json
wallet_v1_evaluation_tuples_aligned.json
wallet_v1_examples_<tuple-id>.json
```

The command validates the complete selection before starting Wallet, then runs every case in a
fresh in-memory Wallet dependency graph. It launches the managed worker with the sibling
Wallet backend's `uv` environment, so this package does not depend on a local Wallet source
path.

Defaults are `../wallet`, `qwen3.5:9b`, `http://127.0.0.1:11434`, and
`results/eval-runs`. Override them with `--wallet-repo`, `--model`, `--ollama-base-url`, and
`--results-dir`. Progress is printed as `[3/10] T006/E01`. A successful run ends with its run
ID and the absolute JSON artifact path. Exit status is `0` after a complete artifact is saved,
`2` for invalid input or failed preflight, and `1` for execution or persistence failure. No
partial artifact is saved.

## Use the workbench

```bash
uv run wallet_evals workbench \
  --wallet-repo ../wallet \
  --model qwen3.5:4b
```

The page supports the main exploratory journey:

1. start from a prepared case set or select individual cases;
2. choose a local model and run Wallet;
3. watch progress or correct a setup failure; and
4. open the saved run or a specific case in the trace viewer.

The dataset and trace viewers remain separate, read-only components. The workbench only connects
their handoffs and keeps one active local run in memory.

An optional deterministic evaluation can be applied when a saved run exactly matches a plan:

```bash
uv run wallet_evals evaluate \
  --plan data/evaluation-plans/workbench-check-8.plan.v1.json \
  --execution-result results/eval-runs/<run-id>.json
```

## Review dataset coverage

```bash
uv run wallet_evals view-dataset \
  --dataset-dir data/dataset-1
```

The command validates and joins the complete dataset before opening a read-only viewer at
`http://127.0.0.1:8766`. Dataset identity, purpose, case sets, and source context appear in the
Overview tab. Totals and dimension-value coverage have a dedicated Statistics tab. The remaining
tabs support filtered review of dimension definitions, approved tuples, generated user inputs,
executable fixtures and preludes, case-set membership, and exact source JSON. A tuple can also be
copied as JSON or Markdown handoff context, with the dimension model, its generated inputs, and
the other tuple definitions. Use `--port` to select another loopback port or `--no-open` to print
the URL without opening a browser.

Open the printed `http://127.0.0.1:<port>` address. Opening the packaged `index.html` directly as
a `file://` URL cannot reach the dataset API and displays launch instructions instead.

Invalid files or cross-file relationships prevent startup. The viewer does not edit the dataset,
record approvals, export case sets, execute Wallet, or record verdicts.

## View saved traces

```bash
uv run wallet_evals view \
  --results-dir results/eval-runs
```

The command starts a read-only viewer at `http://127.0.0.1:8765` and opens it in the default
browser. It lists valid and invalid `*.json` artifacts, validates schema `0.1` run results, and
shows case context, ordered actions and responses, adaptive evidence, observations, provenance,
and exact captured JSON. Use `--port` to select another loopback port or `--no-open` to print the
URL without opening a browser.

The viewer does not call Wallet, edit artifacts, or record judgments. Stop it with Ctrl-C.

## Command Model
Use Poe for Python work:

```bash
uv run poe fmt
uv run poe fmt-check
uv run poe lint
uv run poe type
uv run poe test
uv run poe verify
uv run poe run
uv run poe build
uv run poe clean
```

Use `make` for repo setup wrappers:

```bash
make help
make init
make install-git-hooks
```

## Secret Scanning

This repo includes a local Gemini API key scan for strings that match the format-aware
`AIza[A-Za-z0-9_-]{35}` pattern. Version 1 scans only Gemini-style keys, has no allowlist, and
keeps CI `gitleaks` checks as separate defense in depth.

Run a repo-wide audit of tracked files:

```bash
uv run poe secret-scan
```

Install the repo-managed pre-commit hook:

```bash
make install-git-hooks
```

After installation, each commit scans staged added lines only. It does not scan unchanged old
lines, full git history, or non-staged working tree changes.

## Dependencies
- Add a runtime dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`
- Sync lockfile + env: `uv sync --group dev`

## Project layout
```text
docs/
scripts/
src/wallet_evals/
  case_sets.py
  dataset_viewer/
  runner/
  viewer/
  workbench/
tests/
poe_tasks.toml
```

## Configuration
- Packaging and tooling: `pyproject.toml`
- Python task catalog: `poe_tasks.toml`
- Canonical docs scaffold: `docs/`

## Contributing
See `CONTRIBUTING.md`.

## Security
See `SECURITY.md`.

## License
Add a `LICENSE` file (MIT/Apache-2.0/BSD-3-Clause/etc.) and update this section.
