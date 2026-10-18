# wallet-evals

wallet-evals runs synthetic cases against Wallet and saves what Wallet did as run results. Local
read-only viewers show the dataset and the saved evidence, and the workbench page connects case
selection, a Wallet run, and both viewers in one workflow.

## Requirements
- Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)
- A Wallet checkout beside this repository, at `../wallet` by default
- [Ollama](https://ollama.com/) running locally with `qwen3.5:9b`, unless you pick another model

## Quick start

```bash
make setup
make verify
```

Run the ten-case cohort against Wallet and open the saved evidence:

```bash
ollama pull qwen3.5:9b
make eval-run
make trace-view
```

Or do the same from the workbench page, which also opens the dataset and trace viewers:

```bash
make workbench-run
```

The workbench and viewers stay in the foreground; stop them with Ctrl-C. Pass CLI options with
`ARGS`, for example `make eval-run ARGS='--model qwen3.5:4b'`.

`make help` lists every command. The [runbook](docs/evergreen/runbook.md) explains when to use
each one, the CLI options, and the exit statuses.

## What each command does
- `make eval-run` validates the whole case set, then runs each case in a fresh in-memory Wallet
  through a managed worker in Wallet's own `uv` environment. It saves one JSON run result in
  `results/eval-runs/` and prints its path. A failed run saves nothing.
- `make eval-judge PLAN=... RUN=...` checks a saved run against an evaluation plan in
  `data/evaluation-plans/` and saves a JSON and Markdown evaluation in `results/evaluations/`.
- `make dataset-view` validates `data/dataset-1` and shows its coverage, tuples, generated inputs,
  fixtures, and case sets on `http://127.0.0.1:8766`.
- `make trace-view` lists saved run results and shows each case's actions, Wallet responses,
  observations, and provenance on `http://127.0.0.1:8765`.
- `make workbench-run` serves the workbench on `http://127.0.0.1:8764`.

The viewers never edit files, run Wallet, or record judgments.

## Secret scanning
`make secret-scan` checks tracked files for strings that match the Gemini API key format
`AIza[A-Za-z0-9_-]{35}`. `make setup` installs a pre-commit hook that runs
`make secret-scan-staged`, which checks only the lines added in staged changes.

## Repository layout

```text
src/wallet_evals/   CLI, runner, case-set loader, workbench, and both viewers
scripts/devex/      Managed Wallet worker and devex scripts
data/               Dataset, case sets, and evaluation plans
results/            Saved run results and evaluations (ignored by Git)
docs/               Docs index in docs/README.md
workstreams/        Design history of past workstreams
Makefile            Command catalog
poe_tasks.toml      Python tasks that Make calls
```

## Docs
- [Docs index](docs/README.md)
- [Runbook](docs/evergreen/runbook.md): commands and local workflows
- [MVP](docs/evergreen/mvp.md), [architecture](docs/evergreen/architecture.md), and
  [API contracts](docs/evergreen/api-contracts.md)
- [Product spec](docs/product/spec.md) and [concepts](docs/product/concepts.md)

## Configuration
- Packaging and tools: `pyproject.toml`
- Python tasks: `poe_tasks.toml`
- Add a dependency with `uv add <package>`, or `uv add --dev <package>` for a dev dependency.
  Then run `make setup-sync`.

## Contributing
See `CONTRIBUTING.md`.

## Security
See `SECURITY.md`.

## License
MIT. See `LICENSE`.
