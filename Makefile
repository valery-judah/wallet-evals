.DEFAULT_GOAL := help

# Make is the single entry point for repository workflows. Python workflows call
# Poe tasks in poe_tasks.toml, and evaluation commands call the wallet_evals CLI.
# Target names start with the part of the system they act on: setup-, eval-,
# workbench-, dataset-, trace-. Checks (fmt, lint, type, test, verify) keep short
# names. Pass extra CLI options with ARGS='...'.

UV := uv
POE := $(UV) run poe
CLI := $(UV) run wallet_evals
ARGS ?=

CASE_SET ?= data/dataset-1/harness-check-10.v1.json
DATASET ?= data/dataset-1
RESULTS ?= results/eval-runs
PLAN ?=
RUN ?=

SETUP_TARGETS := setup setup-sync setup-lock setup-hooks clean
CHECK_TARGETS := verify fmt fmt-check lint type test secret-scan secret-scan-staged
EVAL_TARGETS := eval-run eval-judge
VIEW_TARGETS := workbench-run dataset-view trace-view
PACKAGE_TARGETS := build
ALIAS_TARGETS := init sync install-git-hooks check

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target> [ARGS='<extra CLI options>']"
	@echo ""
	@print_section() { \
		title="$$1"; \
		targets="$$2"; \
		echo "$$title:"; \
		for target in $$targets; do \
			awk -v target="$$target" 'BEGIN {FS = ":.*## "} $$0 ~ ("^" target ":.*## ") {printf "  %-20s %s\n", target, $$2; exit}' $(MAKEFILE_LIST); \
		done; \
		echo ""; \
	}; \
	print_section "Setup" "$(SETUP_TARGETS)"; \
	print_section "Checks (read-only except fmt)" "$(CHECK_TARGETS)"; \
	print_section "Evaluation (writes results/)" "$(EVAL_TARGETS)"; \
	print_section "Local pages (foreground, stop with Ctrl-C)" "$(VIEW_TARGETS)"; \
	print_section "Package" "$(PACKAGE_TARGETS)"; \
	print_section "Aliases for old names (use the new names)" "$(ALIAS_TARGETS)"

.PHONY: ensure-uv
ensure-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Error: 'uv' is not installed or not on PATH."; \
		echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 127; \
	}

# --- Setup ---

.PHONY: setup
setup: setup-sync setup-hooks ## Sync dependencies and configure Git hooks

.PHONY: setup-sync
setup-sync: ensure-uv ## Sync dependencies from uv.lock into the local .venv
	$(UV) sync --group dev

.PHONY: setup-lock
setup-lock: ensure-uv ## Generate or refresh uv.lock (writes tracked files)
	$(UV) lock

.PHONY: setup-hooks
setup-hooks: ## Configure Git to use the hooks in .githooks/
	@if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
		git config core.hooksPath .githooks; \
	else \
		echo "Not in a git repository. Skipping git hooks setup."; \
	fi

.PHONY: clean
clean: ensure-uv ## Remove caches and generated local artifacts
	$(POE) clean

# --- Checks ---

.PHONY: verify
verify: setup-sync ## Run format check, lint, types, and tests
	$(POE) verify

.PHONY: fmt
fmt: ensure-uv ## Format code and auto-fix lint issues (writes files)
	$(POE) fmt

.PHONY: fmt-check
fmt-check: ensure-uv ## Check formatting without changing files
	$(POE) fmt-check

.PHONY: lint
lint: ensure-uv ## Run lint checks
	$(POE) lint

.PHONY: type
type: ensure-uv ## Run strict type checks
	$(POE) type

.PHONY: test
test: setup-sync ## Run tests (ARGS='-k <expr>' to filter)
	$(POE) test $(ARGS)

.PHONY: secret-scan
secret-scan: ensure-uv ## Scan tracked files for leaked Gemini API keys
	$(POE) secret-scan

.PHONY: secret-scan-staged
secret-scan-staged: ensure-uv ## Scan staged added lines for leaked Gemini API keys (used by the pre-commit hook)
	$(POE) secret-scan-staged

# --- Evaluation ---

.PHONY: eval-run
eval-run: setup-sync ## Run a case set against Wallet and local Ollama, then save a run result (CASE_SET=<path>)
	$(CLI) run --case-set $(CASE_SET) $(ARGS)

.PHONY: eval-judge
eval-judge: setup-sync ## Judge a saved run against an evaluation plan without running Wallet (PLAN=<path> RUN=<path>)
	@test -n "$(PLAN)" -a -n "$(RUN)" || { \
		echo "Usage: make eval-judge PLAN=<plan.json> RUN=<results/eval-runs/<run-id>.json>"; \
		exit 2; \
	}
	$(CLI) evaluate --plan $(PLAN) --execution-result $(RUN) $(ARGS)

# --- Local pages ---

.PHONY: workbench-run
workbench-run: setup-sync ## Run the workbench on http://127.0.0.1:8764 with both viewers (foreground)
	$(CLI) workbench $(ARGS)

.PHONY: dataset-view
dataset-view: setup-sync ## Run the read-only dataset viewer on http://127.0.0.1:8766 (DATASET=<dir>, foreground)
	$(CLI) view-dataset --dataset-dir $(DATASET) $(ARGS)

.PHONY: trace-view
trace-view: setup-sync ## Run the read-only trace viewer on http://127.0.0.1:8765 (RESULTS=<dir>, foreground)
	$(CLI) view --results-dir $(RESULTS) $(ARGS)

# --- Package ---

.PHONY: build
build: ensure-uv ## Build source and wheel distributions into dist/
	$(POE) build

# --- Aliases for old names ---

.PHONY: $(ALIAS_TARGETS)
init: setup ## Alias for setup
sync: setup-sync ## Alias for setup-sync
install-git-hooks: setup-hooks ## Alias for setup-hooks
check: verify ## Alias for verify
