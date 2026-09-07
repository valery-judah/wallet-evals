from __future__ import annotations


class EvaluationRunnerError(RuntimeError):
    """Base error raised when the runner cannot satisfy its evidence contract."""


class CaseDefinitionIdentityError(EvaluationRunnerError):
    """Raised when a case source returns a definition for a different identity."""


class IdentityCollisionError(EvaluationRunnerError):
    """Raised before capture when generated execution identities are not distinct."""


class MissingAdaptiveSelectorError(EvaluationRunnerError):
    """Raised before execution when an adaptive case has no selector capability."""


class AdaptiveChoiceViolationError(EvaluationRunnerError):
    """Raised when an adaptive choice exceeds the case-declared evidence or action bounds."""


class PersistenceContractError(EvaluationRunnerError):
    """Raised when persistence identifies a different run than the one saved."""
