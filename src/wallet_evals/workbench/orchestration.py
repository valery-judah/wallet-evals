from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock, Thread
from typing import Annotated, Literal, Protocol, TypeAlias, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from wallet_evals.dataset_viewer import DatasetRepository

NonEmptyString: TypeAlias = Annotated[str, Field(min_length=1)]
CASE_STARTED_PATTERN = re.compile(r"^\[(\d+)/(\d+)\]\s+(.+)$")


class WorkbenchOrchestrationError(RuntimeError):
    """Base error for the local orchestration prototype."""


class WorkbenchBusyError(WorkbenchOrchestrationError):
    """Raised when a second run is requested while one is active."""


class WorkbenchRunRequestError(WorkbenchOrchestrationError):
    """Raised when the selected cases cannot be run."""


class OrchestrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class WorkbenchRunRequest(OrchestrationModel):
    case_ids: tuple[NonEmptyString, ...] = Field(min_length=1)
    model: NonEmptyString
    cohort_id: NonEmptyString | None = None

    @field_validator("case_ids")
    @classmethod
    def case_ids_are_unique(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("selected case identities must be unique")
        return case_ids

    @field_validator("model")
    @classmethod
    def model_is_not_blank(cls, model: str) -> str:
        if not model.strip():
            raise ValueError("model must not be blank")
        return model.strip()

    @field_validator("cohort_id")
    @classmethod
    def cohort_id_is_not_blank(cls, cohort_id: str | None) -> str | None:
        if cohort_id is None:
            return None
        if not cohort_id.strip():
            raise ValueError("cohort identity must not be blank")
        return cohort_id.strip()


class WorkbenchRunState(OrchestrationModel):
    status: Literal["idle", "running", "succeeded", "failed"] = "idle"
    request_id: str | None = None
    selection_id: str | None = None
    cohort_id: str | None = None
    case_ids: tuple[str, ...] = ()
    model: str | None = None
    started_cases: int = 0
    completed_cases: int = 0
    total_cases: int = 0
    active_case_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    artifact_path: str | None = None
    artifact_name: str | None = None
    error: str | None = None
    output: tuple[str, ...] = ()


class RunningProcess(Protocol):
    @property
    def stdout(self) -> Iterable[str] | None: ...

    def wait(self) -> int: ...


class ProcessFactory(Protocol):
    def __call__(self, command: list[str], *, cwd: Path) -> RunningProcess: ...


class _LocalProcess:
    def __init__(self, process: subprocess.Popen[str]) -> None:
        self._process = process

    @property
    def stdout(self) -> Iterable[str] | None:
        return cast(Iterable[str] | None, self._process.stdout)

    def wait(self) -> int:
        return self._process.wait()


def _start_process(command: list[str], *, cwd: Path) -> RunningProcess:
    process = subprocess.Popen(  # noqa: S603 - command uses local validated inputs.
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    return _LocalProcess(process)


class WorkbenchRunManager:
    """Run one selected local Wallet cohort at a time and expose lightweight status."""

    def __init__(
        self,
        dataset_repository: DatasetRepository,
        *,
        repository_root: Path,
        wallet_repository: Path,
        results_directory: Path,
        ollama_base_url: str,
        default_model: str,
        process_factory: ProcessFactory = _start_process,
    ) -> None:
        self.dataset_repository = dataset_repository
        self.repository_root = repository_root.expanduser().resolve()
        self.wallet_repository = wallet_repository.expanduser().resolve()
        self.results_directory = results_directory.expanduser().resolve()
        self.ollama_base_url = ollama_base_url
        self.default_model = default_model
        self._process_factory = process_factory
        self._lock = Lock()
        self._state = WorkbenchRunState()
        self._thread: Thread | None = None
        self._case_ids = set(dataset_repository.bundle.case_ids)
        self._cohorts = {
            cohort_id: cohort.cases
            for cohort_id, cohort in dataset_repository.bundle.cohorts.items()
        }

    def snapshot(self) -> WorkbenchRunState:
        with self._lock:
            return self._state.model_copy(deep=True)

    def start(self, request: WorkbenchRunRequest) -> WorkbenchRunState:
        unknown = tuple(case_id for case_id in request.case_ids if case_id not in self._case_ids)
        if unknown:
            raise WorkbenchRunRequestError(
                f"selected cases are not in the loaded dataset: {', '.join(unknown)}"
            )
        if request.cohort_id is not None:
            cohort_cases = self._cohorts.get(request.cohort_id)
            if cohort_cases is None:
                raise WorkbenchRunRequestError(
                    f"selected cohort is not in the loaded dataset: {request.cohort_id}"
                )
            if request.case_ids != cohort_cases:
                raise WorkbenchRunRequestError(
                    "selected cases must exactly match cohort "
                    f"{request.cohort_id} in declared order"
                )
        with self._lock:
            if self._state.status == "running":
                raise WorkbenchBusyError("a Wallet run is already active")
            request_id = str(uuid4())
            staging_id = f"workbench-selection-{request_id}"
            selection_id = request.cohort_id or f"workbench-ad-hoc-{request_id}"
            self._state = WorkbenchRunState(
                status="running",
                request_id=request_id,
                selection_id=selection_id,
                cohort_id=request.cohort_id,
                case_ids=request.case_ids,
                model=request.model.strip(),
                total_cases=len(request.case_ids),
                started_at=datetime.now(UTC).isoformat(),
            )
            thread = Thread(
                target=self._execute,
                args=(staging_id, selection_id, request),
                daemon=True,
            )
            self._thread = thread
            thread.start()
            return self._state.model_copy(deep=True)

    def wait(self, timeout: float | None = None) -> WorkbenchRunState:
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout)
        return self.snapshot()

    def _execute(
        self,
        staging_id: str,
        selection_id: str,
        request: WorkbenchRunRequest,
    ) -> None:
        try:
            case_set_path = self._prepare_selection(
                staging_id,
                selection_id,
                request.case_ids,
                request.cohort_id,
            )
            command = [
                sys.executable,
                "-m",
                "wallet_evals.cli",
                "run",
                "--case-set",
                str(case_set_path),
                "--wallet-repo",
                str(self.wallet_repository),
                "--model",
                request.model.strip(),
                "--ollama-base-url",
                self.ollama_base_url,
                "--results-dir",
                str(self.results_directory),
            ]
            process = self._process_factory(command, cwd=self.repository_root)
            if process.stdout is None:
                raise RuntimeError("Wallet runner did not expose progress output")
            artifact_path: str | None = None
            for raw_line in process.stdout:
                line = raw_line.rstrip()
                if line:
                    self._record_output(line)
                    if line.startswith("Result: "):
                        artifact_path = line.removeprefix("Result: ").strip()
            return_code = process.wait()
            state = self.snapshot()
            if return_code == 0 and artifact_path is not None:
                self._finish(status="succeeded", artifact_path=artifact_path)
            else:
                error = next(
                    (line.removeprefix("Error: ") for line in reversed(state.output) if line),
                    f"Wallet runner exited with status {return_code}",
                )
                self._finish(status="failed", error=error)
        except Exception as exc:
            self._finish(status="failed", error=str(exc))

    def _prepare_selection(
        self,
        staging_id: str,
        selection_id: str,
        case_ids: tuple[str, ...],
        cohort_id: str | None,
    ) -> Path:
        selection_directory = (
            self.results_directory.parent / "workbench" / "selections" / staging_id
        )
        selection_directory.mkdir(parents=True, exist_ok=False)
        cohort_filenames = set(self.dataset_repository.bundle.cohort_filenames.values())
        for filename in self.dataset_repository.bundle.source_documents:
            if filename in cohort_filenames:
                continue
            source = self.dataset_repository.directory / filename
            (selection_directory / filename).symlink_to(source)
        case_set_path = selection_directory / "selection.v1.json"
        case_set_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "id": selection_id,
                    "description": (
                        f"Prepared cohort {cohort_id} selected in the local evaluation workbench."
                        if cohort_id is not None
                        else "Ad hoc case selection created by the local evaluation workbench."
                    ),
                    "cases": list(case_ids),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return case_set_path

    def _record_output(self, line: str) -> None:
        with self._lock:
            output = (*self._state.output, line)
            started = self._state.started_cases
            completed = self._state.completed_cases
            total = self._state.total_cases
            active_case_id = self._state.active_case_id
            match = CASE_STARTED_PATTERN.match(line)
            if match is not None:
                started = int(match.group(1))
                total = int(match.group(2))
                active_case_id = match.group(3).strip()
                completed = max(completed, started - 1)
            self._state = self._state.model_copy(
                update={
                    "output": output,
                    "started_cases": started,
                    "completed_cases": completed,
                    "total_cases": total,
                    "active_case_id": active_case_id,
                }
            )

    def _finish(
        self,
        *,
        status: Literal["succeeded", "failed"],
        error: str | None = None,
        artifact_path: str | None = None,
    ) -> None:
        with self._lock:
            update: dict[str, object] = {
                "status": status,
                "error": error,
                "active_case_id": None,
                "finished_at": datetime.now(UTC).isoformat(),
            }
            if status == "succeeded":
                if artifact_path is None:
                    raise RuntimeError("a successful Wallet run must publish an artifact")
                update.update(
                    {
                        "completed_cases": self._state.total_cases,
                        "artifact_path": artifact_path,
                        "artifact_name": Path(artifact_path).name,
                    }
                )
            self._state = self._state.model_copy(update=update)


__all__ = [
    "ProcessFactory",
    "RunningProcess",
    "WorkbenchBusyError",
    "WorkbenchOrchestrationError",
    "WorkbenchRunManager",
    "WorkbenchRunRequest",
    "WorkbenchRunRequestError",
    "WorkbenchRunState",
]
