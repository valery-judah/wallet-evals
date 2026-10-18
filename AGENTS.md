# Agent Contract

wallet-evals runs synthetic cases against Wallet, saves the evidence as run results, and shows
that evidence in local read-only viewers. The workbench page connects case selection, one Wallet
run, and the viewers. Wallet is a sibling checkout at `../wallet`, and runs use a local Ollama
model.

## Canonical sources

### Repository and infrastructure
- `README.md` - project overview and quick start
- `docs/README.md` - docs index
- `docs/evergreen/runbook.md` - commands, local workflows, and adapter rules
- `data/` - the current dataset, case sets, and evaluation plans

### Product and architecture
- `docs/product/spec.md` - current product base
- `docs/product/concepts.md` - evaluation system language
- `docs/product/evaluation-workbench-frame.md` - current workbench product frame
- `docs/evergreen/mvp.md` - stable product scope
- `docs/evergreen/architecture.md` - components, runtime flow, and repository shape
- `docs/evergreen/api-contracts.md` - CLI, library, and artifact contracts

`docs/evergreen/` is canonical and wins when sources disagree. `docs/product/` holds product work
in progress. `workstreams/` and `docs/product/archive/` are history only.

## Commands
- Use `make <target>` for repository workflows and `make help` for the current catalog. Pass extra CLI options with `ARGS='...'`.
- Make calls Poe for Python checks and the `wallet_evals` CLI for evaluation commands. If no target exists, use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, `pipenv`, `npm`, or `npx`.
- `make eval-run` starts Wallet and calls local Ollama. It needs `../wallet` and the model installed.
- `workbench-run`, `dataset-view`, and `trace-view` stay in the foreground. Run them as background processes and pass `ARGS='--no-open'` so they don't open a browser.

## Validation
- Code change: `make verify`.
- Change to the runner, the case-set loader, or the Wallet worker: also run `make eval-run` when Wallet and Ollama are available.
- Docs-only change: check that the commands and links you changed exist.

## Scratch scripts
- Put temporary, exploratory, and devex scripts in `scripts/devex/`. `scripts/devex/run_wallet_cohort.py` is the managed Wallet worker, so don't treat it as scratch.
