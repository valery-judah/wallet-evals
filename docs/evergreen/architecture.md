# Architecture

`EvaluationRunner` owns evidence production from identity establishment through durable result

saving. The local Workbench coordinates a person's movement across dataset selection, the runner,

and the read-only viewers without taking over their responsibilities. An optional file-based

evaluator consumes one saved result after execution.

## Repository shape

```text
src/wallet_evals/runner/
  models.py       validated domain values and evidence records
  ports.py        external capability protocols
  service.py      serial run and case orchestration
  persistence.py  durable JSON file result store
  errors.py       runner contract failures
src/wallet_evals/case_sets.py
                  complete current-dataset validation, joins, and action-plan mapping
src/wallet_evals/dataset_viewer/
                  coverage projection, loopback HTTP server, and packaged browser assets
src/wallet_evals/viewer/
                  validated result discovery, loopback HTTP server, and packaged browser assets
src/wallet_evals/workbench/
                  local orchestration page plus optional deterministic judgment
scripts/devex/run_wallet_cohort.py
                  managed worker loaded in the sibling Wallet backend environment
```

The public CLI performs repository, dataset, and Ollama preflight in the wallet-evals

environment. It then launches the managed worker through the sibling Wallet backend's `uv`

environment. This keeps Wallet a runtime boundary and avoids a non-portable source dependency

in wallet-evals.

`tests/test_runner.py` exercises the component through in-memory adapters and the concrete file

store. Dataset and command contracts are covered in `tests/test_case_sets.py` and

`tests/test_cli_smoke.py`. Dataset-viewer repository, coverage, HTTP, launch, and presentation

contracts are covered by `tests/test_dataset_viewer.py` and `tests/test_dataset_viewer_server.py`.

Trace-viewer contracts are covered by `tests/test_viewer.py` and `tests/test_viewer_server.py`.

Workbench plan, judgment, scope, persistence, and report contracts are covered by

`tests/test_workbench.py`.

## Runtime flow

1. `EvaluationRunner.run` establishes a run identity, resolves every selected case, checks that
   adaptive execution is available when needed, and creates all case-execution identities.
2. The runner processes cases serially. For each case it asks `WalletExecutionFactory` for fresh
   state carrying the case starting conditions and governing execution context.
3. It supplies the declared standalone or fixed actions. For adaptive cases it supplies the
   initial action, then asks `AdaptiveActionSelector` for bounded later actions using only the
   declared role context and facts exposed in the preceding Wallet response.
4. It snapshots each participant action followed by the Wallet observations in the order the
   Wallet adapter exposed them. Complete responses and observable changes remain distinct event
   types.
5. It closes each case-scoped Wallet execution, assembles the traces into one `RunResult`, and
   calls `RunResultStore.save` exactly once.
6. It returns a saved-result identity only if persistence succeeds and identifies the same run.

Run-level context, case definitions, actions, observations, and adaptive facts are copied at

capture boundaries. This keeps later adapter mutation from changing already captured evidence.

## External capabilities

| Port | Required behavior |
| --- | --- |
| `CaseDefinitionSource` | Resolve the authoritative definition for the requested case identity. |
| `WalletExecutionFactory` | Create fresh, controllable state for one `CaseExecution`, reflecting its starting conditions and isolated from other executions. |
| `WalletExecution` | Perform one participant action, expose complete responses and relevant changes in occurrence order, and release case-scoped state. |
| `AdaptiveActionSelector` | Optionally choose the next adaptive action within the declared names and case-specific bounds, cite facts from the preceding visible response, or stop. |
| `RunResultStore` | Durably retain the complete result and return the identity of that artifact. |
| `IdentityGenerator` | Produce one run identity and distinct case-execution identities before capture. |

Fresh-state and durability guarantees belong to their adapters. A successful return from

`bootstrap` means starting conditions and isolation have been established. A successful return

from `save` means the complete result survives the Wallet runtime.

## Failure behavior

The baseline has no retry or partial-result policy. A lookup, bootstrap, interaction, adaptive

selection, capture, or save failure propagates to the operator. An opened Wallet execution is

closed in all cases. The runner does not call persistence unless every selected case produced a

complete trace, and it never returns a saved identity after a failed save.

An undesirable Wallet response is evidence, not a runner error, as long as the Wallet adapter

can return it as a complete ordered observation.

## Managed local Wallet adapter

The current operator command creates a fresh Wallet `AppContainer` for every case and seeds the

case's declared accounts into its in-memory repositories. Participant actions use Wallet's

public conversation request and response models. The adapter captures the complete public

response, the participant-visible facts used by an adaptive step, and ledger snapshots whenever

accounts or transactions change. Wallet processing exceptions handled publicly as HTTP 502 are

converted to the same public status and body and retained as trace evidence.

Execution provenance includes the case-set identity and absolute path, Wallet Git revision and

dirty-state flag, model, Ollama endpoint, selected case count, and the fresh-per-case isolation

mode.

## Local dataset viewer

The dataset viewer uses the same whole-dataset loader as `DatasetCaseSource`. Startup validates

the dimension set, tuple version and count, dimension assignments, per-tuple example files,

fixture coverage, interaction declarations, and optional case-set references before any coverage

is presented. This prevents partial joins from producing misleading counts.

The repository projects the validated source documents into dimensions, tuples, executable cases,

case sets, and per-dimension tuple and case counts. Multi-valued tuple assignments contribute once

to every assigned value. Omitted dimensions remain an explicit not-applicable display category

rather than being normalized into an invented value.

A standard-library HTTP server binds to loopback and serves the composed dataset, confined exact

source-file reads, and packaged HTML, CSS, and JavaScript. The browser provides overview,

statistics, dimension, tuple, and case views with shared search and filters. Dataset identity and

source context remain in Overview; totals and dimension-value coverage are isolated in

Statistics. The tuple view composes a clipboard-only JSON or Markdown handoff from the loaded

snapshot. It includes the full dimension model, the selected tuple and its generated inputs, and

the remaining tuple records as comparison context. Recorded case fixtures and the shared fixture

remain separate because the current source format does not declare general merge semantics. The

server has no write, export, approval, execution, or verdict routes.

## Local persistence

`JsonFileRunResultStore` writes one provisional `0.1` JSON document per run. It writes and syncs

a temporary file, atomically links the complete file into the destination without overwriting an

existing run, and then syncs the destination directory. The format is inspectable but is not yet

a permanent compatibility contract.

## Smallest evaluation workbench

The Workbench is a small loopback orchestration server. It projects the validated dataset into a

searchable selection surface, launches the existing managed Wallet command for one ordered

selection, tracks its progress, lists saved runs, and produces deep links into the trace viewer.

It starts the dataset and trace viewers as sibling read-only servers.

An ad hoc selection is staged as a retained generated case set beside links to the validated

dataset companions. This lets the existing runner consume it without modifying the canonical

dataset. The Workbench keeps one active attempt in memory; restart, collaboration, and durable job

management are intentionally outside this prototype.

The optional deterministic evaluator remains a separate saved-run consumer. It can be used only

when an execution exactly matches its plan and does not change the orchestration workflow.

## Local trace viewer

The viewer is a separate read-only consumer of saved `0.1` artifacts. Its repository lists

`*.json` files and validates every selectable envelope through the same `RunResult` model used

by the runner. Invalid files remain visible with their error. Artifact retrieval uses only

filenames discovered inside the configured result directory, preventing request paths from

escaping that directory.

A standard-library HTTP server binds to loopback and serves two read-only JSON routes plus

packaged HTML, CSS, and JavaScript. The browser derives concise response summaries for display

but labels them as derived and retains the complete response, participant-visible facts, and

raw trace. Artifact values enter the page only through DOM text nodes.

The viewer has no Wallet dependency, execution control, review persistence, or write route. It

orders the local run list by file modification time for navigation only and uses recorded run,

case-execution, case, and event identities for evidence attribution.
