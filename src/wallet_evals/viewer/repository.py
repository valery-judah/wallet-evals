from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

from wallet_evals.runner import RunResult


class ViewerConfigurationError(ValueError):
    """Raised when the local viewer cannot use its configured result directory."""


class ArtifactNotFoundError(LookupError):
    """Raised when a requested artifact is not in the configured result directory."""


class ArtifactValidationError(ValueError):
    """Raised when a discovered artifact is not a valid run-result document."""


class RunResultEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["0.1"]
    run_result: RunResult


class RunArtifactSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_name: str
    modified_at: str
    modified_ns: int
    valid: bool
    error: str | None = None
    run_id: str | None = None
    case_count: int | None = None
    wallet: str | None = None
    model: str | None = None
    case_set_id: JsonValue = None


class LoadedRunArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_name: str
    modified_at: str
    document: dict[str, JsonValue]


class RunResultRepository:
    """Discover and validate immutable local run-result artifacts."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory.expanduser().resolve()
        if not self.directory.is_dir():
            raise ViewerConfigurationError(
                f"results directory does not exist or is not a directory: {self.directory}"
            )

    def list_artifacts(self) -> tuple[RunArtifactSummary, ...]:
        summaries = [self._summarize(path) for path in self._artifact_paths()]
        return tuple(
            sorted(
                summaries,
                key=lambda summary: (-summary.modified_ns, summary.artifact_name),
            )
        )

    def load_artifact(self, artifact_name: str) -> LoadedRunArtifact:
        path = self._resolve_artifact(artifact_name)
        payload, _ = self._load_validated(path)
        return LoadedRunArtifact(
            artifact_name=path.name,
            modified_at=_modified_at(path),
            document=payload,
        )

    def _artifact_paths(self) -> tuple[Path, ...]:
        return tuple(path for path in self.directory.glob("*.json") if path.is_file())

    def _resolve_artifact(self, artifact_name: str) -> Path:
        if not artifact_name or artifact_name not in {path.name for path in self._artifact_paths()}:
            raise ArtifactNotFoundError(f"run artifact not found: {artifact_name}")
        return self.directory / artifact_name

    def _summarize(self, path: Path) -> RunArtifactSummary:
        stat = path.stat()
        try:
            _, envelope = self._load_validated(path)
        except ArtifactValidationError as exc:
            return RunArtifactSummary(
                artifact_name=path.name,
                modified_at=_modified_at(path),
                modified_ns=stat.st_mtime_ns,
                valid=False,
                error=str(exc),
            )
        context = envelope.run_result.execution_context
        return RunArtifactSummary(
            artifact_name=path.name,
            modified_at=_modified_at(path),
            modified_ns=stat.st_mtime_ns,
            valid=True,
            run_id=envelope.run_result.run_id,
            case_count=len(envelope.run_result.traces),
            wallet=context.wallet,
            model=context.model,
            case_set_id=context.settings.get("case_set_id"),
        )

    @staticmethod
    def _load_validated(path: Path) -> tuple[dict[str, JsonValue], RunResultEnvelope]:
        try:
            parsed: object = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ArtifactValidationError(f"cannot read valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ArtifactValidationError("artifact root must be a JSON object")
        parsed_mapping = cast(dict[object, object], parsed)
        if not all(isinstance(key, str) for key in parsed_mapping):
            raise ArtifactValidationError("artifact root must be a JSON object")
        payload = cast(dict[str, JsonValue], parsed)
        try:
            envelope = RunResultEnvelope.model_validate(payload)
        except ValidationError as exc:
            raise ArtifactValidationError(str(exc)) from exc
        return payload, envelope


def _modified_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()


__all__ = [
    "ArtifactNotFoundError",
    "ArtifactValidationError",
    "LoadedRunArtifact",
    "RunArtifactSummary",
    "RunResultRepository",
    "ViewerConfigurationError",
]
