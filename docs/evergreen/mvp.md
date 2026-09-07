# MVP

The MVP lets a local evaluation operator choose cases, run them against Wallet, and inspect the saved evidence as one lightweight workflow. Execution, evidence viewing, and optional deterministic judgment remain separate components.

## Included

- Standalone, fixed-sequence, and bounded response-adaptive action plans.
- A distinct run identity and case-execution identity established before evidence capture.
- A fresh Wallet execution requested for every selected case.
- Complete Wallet responses, participant actions, and named observable changes captured in
  occurrence order.
- The participant-visible facts used for each adaptive choice, without the selector's private
  role context or reasoning.
- Case context, starting conditions, and effective Wallet, model, environment, and settings
  preserved with each trace.
- Serial collection of completed traces into one run result.
- Durable, human-inspectable JSON file storage through the provided local result store.
- A case-set driven local command that validates the current dataset layout, starts a managed
  sibling Wallet worker, runs against local Ollama, and reports the saved artifact.
- A concrete current-dataset adapter and a fresh in-memory local Wallet adapter for developer
  evaluation runs.
- A loopback-only, read-only dataset viewer that validates the complete current dataset and shows
  dataset context, dedicated coverage statistics, tuples, generated inputs, executable fixtures
  and preludes, case-set membership, exact sources, and copyable tuple handoff context.
- A loopback-only, read-only browser viewer for validated `0.1` run artifacts, including case
  context, ordered evidence, adaptive basis, observations, provenance, and exact JSON.
- A loopback-only Workbench page that composes case selection, one active Wallet run, progress,
  recoverable setup errors, saved runs, and links into both viewers.
- Prepared case-set selection and ad hoc ordered case selection without editing the canonical
  dataset.
- A file-based deterministic evaluator that validates an immutable Evaluation Brief, exact case-set
  scope, per-case criteria, and deterministic observable checks.
- Pass, fail, and unable-to-judge case judgments with check-level expected values, observations,
  and trace event references.
- An aggregate summary and scoped primary finding saved as both validated JSON and Markdown.

## Integration boundary

The reusable runner keeps case definitions, Wallet execution, adaptive selection, and storage behind ports. The repository also provides one developer integration for the current JSON dataset layout and a sibling Wallet checkout. Other deployments can supply different adapters without changing the runner.

## Excluded

- Human judgment, model-based judging, criterion authoring, adjudication, diagnosis, and release
  gating.
- Parallel or production-scale orchestration.
- Retry, resume, skip, or partial-result workflows.
- A permanent case-file or trace-file compatibility promise.
- A general run-configuration file that selects the SUT, model, environment, and output policy.
- Remote, production, or non-Wallet execution adapters.
- Interactive review assignment, progress persistence, and editing of completed evaluations.
- Dataset editing, approval state, case-set export, and execution controls in the dataset viewer.
- Cross-run comparison, filtering, replay, rerun controls, and artifact editing.
