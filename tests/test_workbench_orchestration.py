from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from threading import Event

import pytest

from wallet_evals.case_sets import DatasetCaseSource
from wallet_evals.dataset_viewer import DatasetRepository
from wallet_evals.workbench.orchestration import (
    RunningProcess,
    WorkbenchRunManager,
    WorkbenchRunRequest,
    WorkbenchRunRequestError,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIRECTORY = REPOSITORY_ROOT / "data/dataset-1"


class FakeProcess:
    def __init__(self, lines: Iterable[str], return_code: int) -> None:
        self._lines = tuple(lines)
        self._return_code = return_code

    @property
    def stdout(self) -> Iterable[str]:
        return iter(self._lines)

    def wait(self) -> int:
        return self._return_code


class RecordingProcessFactory:
    def __init__(self, process: RunningProcess) -> None:
        self.process = process
        self.calls: list[tuple[list[str], Path]] = []

    def __call__(self, command: list[str], *, cwd: Path) -> RunningProcess:
        self.calls.append((command, cwd))
        return self.process


class PausingSuccessfulProcess:
    def __init__(self, artifact: Path) -> None:
        self.artifact = artifact
        self.first_recorded = Event()
        self.second_recorded = Event()
        self.release_first = Event()
        self.release_second = Event()

    @property
    def stdout(self) -> Iterable[str]:
        yield "[1/2] T002/E01\n"
        self.first_recorded.set()
        if not self.release_first.wait(5):
            raise TimeoutError("test did not release the first case")
        yield "[2/2] T008/E01\n"
        self.second_recorded.set()
        if not self.release_second.wait(5):
            raise TimeoutError("test did not release the second case")
        yield "Run ID: run-a\n"
        yield f"Result: {self.artifact}\n"

    def wait(self) -> int:
        return 0


class PausingAfterResultProcess:
    def __init__(self, artifact: Path) -> None:
        self.artifact = artifact
        self.wait_started = Event()
        self.release_wait = Event()

    @property
    def stdout(self) -> Iterable[str]:
        yield "[1/1] T002/E01\n"
        yield f"Result: {self.artifact}\n"

    def wait(self) -> int:
        self.wait_started.set()
        if not self.release_wait.wait(5):
            raise TimeoutError("test did not release process wait")
        return 0


def _manager(
    tmp_path: Path,
    process: RunningProcess,
) -> tuple[WorkbenchRunManager, RecordingProcessFactory]:
    factory = RecordingProcessFactory(process)
    manager = WorkbenchRunManager(
        DatasetRepository(DATASET_DIRECTORY),
        repository_root=REPOSITORY_ROOT,
        wallet_repository=REPOSITORY_ROOT / "wallet-sut",
        results_directory=tmp_path / "eval-runs",
        ollama_base_url="http://127.0.0.1:11434",
        default_model="model-default",
        process_factory=factory,
    )
    return manager, factory


def test_selected_cases_are_staged_run_and_linked_to_the_saved_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "eval-runs/run-a.json"
    process = FakeProcess(
        (
            "Running 2 case(s) from selection\n",
            "[1/2] T002/E01\n",
            "[2/2] T008/E01\n",
            "Run ID: run-a\n",
            f"Result: {artifact}\n",
        ),
        0,
    )
    manager, factory = _manager(tmp_path, process)

    started = manager.start(WorkbenchRunRequest(case_ids=("T002/E01", "T008/E01"), model="model-a"))
    finished = manager.wait(5)

    assert started.status == "running"
    assert finished.status == "succeeded"
    assert finished.completed_cases == 2
    assert finished.total_cases == 2
    assert finished.artifact_path == str(artifact)
    assert finished.artifact_name == "run-a.json"
    command, cwd = factory.calls[0]
    assert cwd == REPOSITORY_ROOT
    assert command[0:4] == [command[0], "-m", "wallet_evals.cli", "run"]
    case_set_path = Path(command[command.index("--case-set") + 1])
    document = json.loads(case_set_path.read_text(encoding="utf-8"))
    assert document["cases"] == ["T002/E01", "T008/E01"]
    assert document["id"].startswith("workbench-ad-hoc-")
    assert finished.selection_id == document["id"]
    assert finished.cohort_id is None
    source = DatasetCaseSource(case_set_path)
    assert source.case_ids == ("T002/E01", "T008/E01")


def test_prepared_cohort_identity_is_recorded_in_staged_case_set(tmp_path: Path) -> None:
    artifact = tmp_path / "eval-runs/run-cohort.json"
    process = FakeProcess((f"Result: {artifact}\n",), 0)
    manager, factory = _manager(tmp_path, process)
    cohort = manager.dataset_repository.bundle.cohorts["workbench-check-8"]

    started = manager.start(
        WorkbenchRunRequest(
            case_ids=cohort.cases,
            model="model-a",
            cohort_id=cohort.id,
        )
    )
    finished = manager.wait(5)

    assert started.selection_id == "workbench-check-8"
    assert started.cohort_id == "workbench-check-8"
    assert finished.status == "succeeded"
    command, _ = factory.calls[0]
    case_set_path = Path(command[command.index("--case-set") + 1])
    document = json.loads(case_set_path.read_text(encoding="utf-8"))
    assert document["id"] == "workbench-check-8"
    assert document["cases"] == list(cohort.cases)


def test_supplied_cohort_must_match_selected_cases_and_order(tmp_path: Path) -> None:
    manager, factory = _manager(tmp_path, FakeProcess((), 0))
    cohort = manager.dataset_repository.bundle.cohorts["workbench-check-8"]

    with pytest.raises(WorkbenchRunRequestError, match="exactly match cohort"):
        manager.start(
            WorkbenchRunRequest(
                case_ids=tuple(reversed(cohort.cases)),
                model="model-a",
                cohort_id=cohort.id,
            )
        )

    assert manager.snapshot().status == "idle"
    assert factory.calls == []


def test_case_start_output_does_not_overstate_completed_cases(tmp_path: Path) -> None:
    process = PausingSuccessfulProcess(tmp_path / "eval-runs/run-a.json")
    manager, _ = _manager(tmp_path, process)

    manager.start(WorkbenchRunRequest(case_ids=("T002/E01", "T008/E01"), model="model-a"))

    assert process.first_recorded.wait(5)
    first = manager.snapshot()
    assert first.status == "running"
    assert first.started_cases == 1
    assert first.completed_cases == 0
    assert first.active_case_id == "T002/E01"

    process.release_first.set()
    assert process.second_recorded.wait(5)
    second = manager.snapshot()
    assert second.status == "running"
    assert second.started_cases == 2
    assert second.completed_cases == 1
    assert second.active_case_id == "T008/E01"

    process.release_second.set()
    finished = manager.wait(5)
    assert finished.status == "succeeded"
    assert finished.started_cases == 2
    assert finished.completed_cases == 2
    assert finished.active_case_id is None


def test_result_is_published_atomically_with_success_after_process_exit(tmp_path: Path) -> None:
    artifact = tmp_path / "eval-runs/run-a.json"
    process = PausingAfterResultProcess(artifact)
    manager, _ = _manager(tmp_path, process)

    manager.start(WorkbenchRunRequest(case_ids=("T002/E01",), model="model-a"))

    assert process.wait_started.wait(5)
    still_running = manager.snapshot()
    assert still_running.status == "running"
    assert still_running.started_cases == 1
    assert still_running.completed_cases == 0
    assert still_running.active_case_id == "T002/E01"
    assert still_running.artifact_path is None
    assert still_running.artifact_name is None
    assert f"Result: {artifact}" in still_running.output

    process.release_wait.set()
    finished = manager.wait(5)
    assert finished.status == "succeeded"
    assert finished.completed_cases == 1
    assert finished.active_case_id is None
    assert finished.artifact_path == str(artifact)
    assert finished.artifact_name == "run-a.json"


def test_preflight_failure_is_visible_and_selection_can_be_retried(tmp_path: Path) -> None:
    manager, _ = _manager(
        tmp_path,
        FakeProcess(("Error: Ollama model 'missing' is not installed\n",), 2),
    )
    request = WorkbenchRunRequest(case_ids=("T010/E01",), model="missing")

    first = manager.start(request)
    failed = manager.wait(5)

    assert first.case_ids == ("T010/E01",)
    assert failed.status == "failed"
    assert failed.error == "Ollama model 'missing' is not installed"
    assert failed.artifact_path is None

    retried = manager.start(request)
    assert retried.status == "running"
    assert retried.case_ids == first.case_ids
    assert manager.wait(5).status == "failed"


def test_unknown_case_selection_is_rejected_before_start(tmp_path: Path) -> None:
    manager, factory = _manager(tmp_path, FakeProcess((), 0))

    with pytest.raises(WorkbenchRunRequestError, match="not in the loaded dataset"):
        manager.start(WorkbenchRunRequest(case_ids=("unknown/E01",), model="model-a"))

    assert manager.snapshot().status == "idle"
    assert factory.calls == []
