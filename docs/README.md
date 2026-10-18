# Docs

`evergreen/` is canonical and wins when sources disagree. `product/` holds product work in
progress. `../workstreams/` and `product/archive/` record design history and are not kept up to
date.

## Repository and infrastructure
- `evergreen/runbook.md`: commands, local workflows, and adapter rules
- `../data/`: the current dataset, case sets, and evaluation plans

## Product
- `product/spec.md`: current product base
- `product/concepts.md`: evaluation system language
- `product/ontology.md`: how the runner's terms line up with agent, dialogue, and observability terms
- `product/evaluation-workbench-frame.md`: current workbench product frame
- `product/evaluation-workbench-reasoning.md`: how the workbench frame was reached from the earlier frames
- `product/evaluation-subsystem-frame.md`: execution and evidence capture frame
- `product/evaluation-trace-viewer-frame.md`: trace viewer and judgment frame
- `product/Failure Understanding Workbench Product Frame.md`: expert review of failures in saved traces
- `product/workbench-workflow-scenarios.md` and `product/workbench-walkthrough-results.md`: workbench workflow scenarios and their results

## Architecture
- `evergreen/mvp.md`: stable product scope
- `evergreen/architecture.md`: components, runtime flow, and repository shape
- `evergreen/api-contracts.md`: CLI, library, and artifact contracts

## History
- `../workstreams/`: design history of past workstreams
- `product/archive/`: earlier product exploration
