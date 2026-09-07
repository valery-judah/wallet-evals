from __future__ import annotations

from typing import Protocol

from wallet_evals.runner.models import (
    AdaptiveChoice,
    AdaptiveSelectionRequest,
    CaseDefinition,
    CaseExecution,
    InteractionResult,
    ParticipantAction,
    RunResult,
    SavedRunResultIdentity,
)


class CaseDefinitionSource(Protocol):
    def get(self, case_id: str) -> CaseDefinition:
        """Return the authoritative definition for a selected case."""
        ...


class WalletExecution(Protocol):
    def perform(self, action: ParticipantAction) -> InteractionResult:
        """Perform an action and return observations in occurrence order."""
        ...

    def close(self) -> None:
        """Release the state owned by this case execution."""
        ...


class WalletExecutionFactory(Protocol):
    def bootstrap(self, execution: CaseExecution) -> WalletExecution:
        """Return fresh state reflecting this case's declared starting conditions."""
        ...


class AdaptiveActionSelector(Protocol):
    def select_next(self, request: AdaptiveSelectionRequest) -> AdaptiveChoice | None:
        """Choose a bounded next action, or stop the adaptive sequence."""
        ...


class RunResultStore(Protocol):
    def save(self, result: RunResult) -> SavedRunResultIdentity:
        """Durably save the complete result and identify the retained artifact."""
        ...


class IdentityGenerator(Protocol):
    def new_run_id(self) -> str:
        """Create a new evaluation run identity."""
        ...

    def new_case_execution_id(self, run_id: str, case_id: str) -> str:
        """Create a new identity for a case execution within a run."""
        ...
