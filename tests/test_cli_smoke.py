from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from wallet_evals import cli
from wallet_evals.case_sets import CaseSetError


class FakeCaseSource:
    case_ids = ("T001/E01", "T002/E01")
    case_set_id = "test-cohort"

    def __init__(self, path: Path) -> None:
        self.path = path


def _accept_path(_path: Path) -> None:
    pass


def _accept_ollama(_base_url: str, _model: str) -> None:
    pass


def _uv_location(_name: str) -> str:
    return "/tools/uv"


def test_cli_without_arguments_prints_help_and_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli.main([])

    assert code == 0
    output = capsys.readouterr().out
    assert "wallet_evals" in output
    assert "run" in output
    assert "view" in output
    assert "view-dataset" in output
    assert "workbench" in output
    assert "evaluate" in output


def test_cli_version_is_preserved(capsys: pytest.CaptureFixture[str]) -> None:
    code = cli.main(["--version"])

    assert code == 0
    assert capsys.readouterr().out.strip()


def test_run_requires_case_set() -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["run"])

    assert exc_info.value.code == 2


def test_run_parser_exposes_documented_defaults() -> None:
    args = cli.build_parser().parse_args(["run", "--case-set", "cases.json"])

    assert args.wallet_repo == cli.DEFAULT_WALLET_REPOSITORY
    assert args.model == cli.DEFAULT_MODEL
    assert args.ollama_base_url == cli.DEFAULT_OLLAMA_BASE_URL
    assert args.results_dir == cli.DEFAULT_RESULTS_DIRECTORY


def test_view_parser_exposes_documented_defaults() -> None:
    args = cli.build_parser().parse_args(["view"])

    assert args.results_dir == cli.DEFAULT_RESULTS_DIRECTORY
    assert args.port == cli.DEFAULT_VIEWER_PORT
    assert args.no_open is False


def test_view_dataset_parser_exposes_documented_defaults() -> None:
    args = cli.build_parser().parse_args(["view-dataset"])

    assert args.dataset_dir == cli.DEFAULT_DATASET_DIRECTORY
    assert args.port == cli.DEFAULT_DATASET_VIEWER_PORT
    assert args.no_open is False


def test_evaluate_parser_exposes_documented_default() -> None:
    args = cli.build_parser().parse_args(
        ["evaluate", "--plan", "plan.json", "--execution-result", "run.json"]
    )

    assert args.output_dir == cli.DEFAULT_EVALUATIONS_DIRECTORY


def test_evaluate_invokes_file_evaluation_with_resolved_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[tuple[Path, Path, Path]] = []

    def record_workbench(plan: Path, execution: Path, output: Path) -> object:
        calls.append((plan, execution, output))
        return SimpleNamespace(
            summary=SimpleNamespace(
                passed=2,
                case_count=3,
                failed=1,
                unable_to_judge=0,
            ),
            finding=SimpleNamespace(answer="One selected behavior gap was found."),
            artifact_path=output / "evaluation.json",
            report_path=output / "evaluation.md",
        )

    monkeypatch.setattr(cli, "run_workbench", record_workbench)
    plan = tmp_path / "plan.json"
    execution = tmp_path / "run.json"
    output = tmp_path / "evaluations"

    code = cli.main(
        [
            "evaluate",
            "--plan",
            str(plan),
            "--execution-result",
            str(execution),
            "--output-dir",
            str(output),
        ]
    )

    assert code == 0
    assert calls == [(plan.resolve(), execution.resolve(), output.resolve())]
    stdout = capsys.readouterr().out
    assert "2/3 passed, 1 failed" in stdout
    assert "One selected behavior gap was found." in stdout


def test_workbench_parser_exposes_component_defaults() -> None:
    args = cli.build_parser().parse_args(["workbench"])

    assert args.dataset_dir == cli.DEFAULT_DATASET_DIRECTORY
    assert args.wallet_repo == cli.DEFAULT_WALLET_REPOSITORY
    assert args.results_dir == cli.DEFAULT_RESULTS_DIRECTORY
    assert args.port == cli.DEFAULT_WORKBENCH_PORT
    assert args.dataset_viewer_port == cli.DEFAULT_DATASET_VIEWER_PORT
    assert args.trace_viewer_port == cli.DEFAULT_VIEWER_PORT
    assert args.model == cli.DEFAULT_MODEL


def test_workbench_opens_orchestration_surface_with_component_links(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def record_workbench(
        dataset_directory: Path,
        wallet_repository: Path,
        results_directory: Path,
        **options: object,
    ) -> None:
        calls.append(
            {
                "dataset": dataset_directory,
                "wallet": wallet_repository,
                "results": results_directory,
                **options,
            }
        )

    monkeypatch.setattr(cli, "serve_workbench", record_workbench)
    dataset = tmp_path / "dataset"
    wallet = tmp_path / "wallet"
    results = tmp_path / "results"

    code = cli.main(
        [
            "workbench",
            "--dataset-dir",
            str(dataset),
            "--wallet-repo",
            str(wallet),
            "--results-dir",
            str(results),
            "--model",
            "model-test:1b",
            "--port",
            "9010",
            "--dataset-viewer-port",
            "9011",
            "--trace-viewer-port",
            "9012",
            "--no-open",
        ]
    )

    assert code == 0
    assert calls == [
        {
            "dataset": dataset.resolve(),
            "wallet": wallet.resolve(),
            "results": results.resolve(),
            "model": "model-test:1b",
            "ollama_base_url": cli.DEFAULT_OLLAMA_BASE_URL,
            "port": 9010,
            "dataset_viewer_port": 9011,
            "trace_viewer_port": 9012,
            "open_browser": False,
            "repository_root": cli.REPOSITORY_ROOT,
        }
    ]


@pytest.mark.parametrize("command", ["view", "view-dataset"])
@pytest.mark.parametrize("port", ["0", "65536", "not-a-port"])
def test_view_rejects_invalid_port(command: str, port: str) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([command, "--port", port])

    assert exc_info.value.code == 2


def test_view_invokes_server_with_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[Path, int, bool]] = []

    def record_viewer(results_directory: Path, *, port: int, open_browser: bool) -> None:
        calls.append((results_directory, port, open_browser))

    monkeypatch.setattr(cli, "serve_viewer", record_viewer)

    code = cli.main(
        [
            "view",
            "--results-dir",
            str(tmp_path),
            "--port",
            "9123",
            "--no-open",
        ]
    )

    assert code == 0
    assert calls == [(tmp_path.resolve(), 9123, False)]


def test_view_dataset_invokes_server_with_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[Path, int, bool]] = []

    def record_viewer(dataset_directory: Path, *, port: int, open_browser: bool) -> None:
        calls.append((dataset_directory, port, open_browser))

    monkeypatch.setattr(cli, "serve_dataset_viewer", record_viewer)

    code = cli.main(
        [
            "view-dataset",
            "--dataset-dir",
            str(tmp_path),
            "--port",
            "9124",
            "--no-open",
        ]
    )

    assert code == 0
    assert calls == [(tmp_path.resolve(), 9124, False)]


def test_view_missing_directory_returns_configuration_exit_code(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli.main(["view", "--results-dir", str(tmp_path / "missing"), "--no-open"])

    assert code == 2
    assert "results directory does not exist" in capsys.readouterr().err


def test_view_server_failure_returns_execution_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def reject_server(_directory: Path, *, port: int, open_browser: bool) -> None:
        del port, open_browser
        raise cli.ViewerServerError("address already in use")

    monkeypatch.setattr(cli, "serve_viewer", reject_server)

    code = cli.main(["view", "--results-dir", str(tmp_path)])

    assert code == 1
    assert "address already in use" in capsys.readouterr().err


def test_view_dataset_invalid_directory_returns_configuration_exit_code(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli.main(["view-dataset", "--dataset-dir", str(tmp_path / "missing"), "--no-open"])

    assert code == 2
    assert "dataset directory does not exist" in capsys.readouterr().err


def test_view_dataset_server_failure_returns_execution_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def reject_server(_directory: Path, *, port: int, open_browser: bool) -> None:
        del port, open_browser
        raise cli.DatasetViewerServerError("address already in use")

    monkeypatch.setattr(cli, "serve_dataset_viewer", reject_server)

    code = cli.main(["view-dataset", "--dataset-dir", str(tmp_path)])

    assert code == 1
    assert "address already in use" in capsys.readouterr().err


def test_run_preflights_and_invokes_wallet_worker_with_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_set = tmp_path / "inputs/cases.json"
    wallet_repository = tmp_path / "wallet-checkout"
    results_directory = tmp_path / "artifacts"
    invocations: list[tuple[list[str], Path, dict[str, str], bool]] = []
    ollama_checks: list[tuple[str, str]] = []

    monkeypatch.setattr(cli, "DatasetCaseSource", FakeCaseSource)
    monkeypatch.setattr(cli, "_validate_local_wallet_checkout", _accept_path)
    monkeypatch.setattr(cli, "_validate_worker", lambda: None)
    monkeypatch.setattr(cli.shutil, "which", _uv_location)

    def record_ollama_check(base_url: str, model: str) -> None:
        ollama_checks.append((base_url, model))

    monkeypatch.setattr(cli, "_validate_ollama", record_ollama_check)

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        invocations.append((command, cwd, env, check))
        print("Run ID: run-test")
        print(f"Result: {results_directory.resolve() / 'run-test.json'}")
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(
        [
            "run",
            "--case-set",
            str(case_set),
            "--wallet-repo",
            str(wallet_repository),
            "--model",
            "model-test:1b",
            "--ollama-base-url",
            "http://localhost:9999/",
            "--results-dir",
            str(results_directory),
        ]
    )

    assert code == 0
    assert ollama_checks == [("http://localhost:9999", "model-test:1b")]
    assert len(invocations) == 1
    command, cwd, environment, check = invocations[0]
    assert command == [
        "/tools/uv",
        "--directory",
        str(wallet_repository.resolve() / "backend"),
        "run",
        "python",
        str(cli.LOCAL_WALLET_WORKER),
        "--case-set",
        str(case_set.resolve()),
        "--wallet-repo",
        str(wallet_repository.resolve()),
        "--model",
        "model-test:1b",
        "--ollama-base-url",
        "http://localhost:9999",
        "--results-dir",
        str(results_directory.resolve()),
    ]
    assert cwd == cli.REPOSITORY_ROOT
    assert check is False
    assert environment["PYTHONPATH"].split(os.pathsep)[0] == str(cli.REPOSITORY_ROOT / "src")
    output = capsys.readouterr().out
    assert "Running 2 case(s) from test-cohort" in output
    assert "Run ID: run-test" in output
    assert f"Result: {results_directory.resolve() / 'run-test.json'}" in output


def test_worker_failure_exit_code_is_preserved(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cli, "DatasetCaseSource", FakeCaseSource)
    monkeypatch.setattr(cli, "_validate_local_wallet_checkout", _accept_path)
    monkeypatch.setattr(cli, "_validate_worker", lambda: None)
    monkeypatch.setattr(cli, "_validate_ollama", _accept_ollama)
    monkeypatch.setattr(cli.shutil, "which", _uv_location)

    def fail_worker(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, check
        return subprocess.CompletedProcess(command, returncode=1)

    monkeypatch.setattr(cli.subprocess, "run", fail_worker)

    assert cli.main(["run", "--case-set", str(tmp_path / "cases.json")]) == 1


def test_invalid_dataset_returns_configuration_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def reject_dataset(_path: Path) -> FakeCaseSource:
        raise CaseSetError("duplicate case identity")

    monkeypatch.setattr(cli, "DatasetCaseSource", reject_dataset)

    code = cli.main(["run", "--case-set", str(tmp_path / "cases.json")])

    assert code == 2
    assert "duplicate case identity" in capsys.readouterr().err


def test_failed_ollama_preflight_returns_configuration_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "DatasetCaseSource", FakeCaseSource)
    monkeypatch.setattr(cli, "_validate_local_wallet_checkout", _accept_path)
    monkeypatch.setattr(cli, "_validate_worker", lambda: None)
    monkeypatch.setattr(cli.shutil, "which", _uv_location)

    def reject_ollama(_base_url: str, _model: str) -> None:
        raise cli.RunConfigurationError("model is not installed")

    monkeypatch.setattr(cli, "_validate_ollama", reject_ollama)

    code = cli.main(["run", "--case-set", str(tmp_path / "cases.json")])

    assert code == 2
    assert "model is not installed" in capsys.readouterr().err


def test_launch_failure_returns_execution_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "DatasetCaseSource", FakeCaseSource)
    monkeypatch.setattr(cli, "_validate_local_wallet_checkout", _accept_path)
    monkeypatch.setattr(cli, "_validate_worker", lambda: None)
    monkeypatch.setattr(cli, "_validate_ollama", _accept_ollama)
    monkeypatch.setattr(cli.shutil, "which", _uv_location)

    def fail_to_launch(*_args: object, **_kwargs: object) -> None:
        raise OSError("process unavailable")

    monkeypatch.setattr(cli.subprocess, "run", fail_to_launch)

    code = cli.main(["run", "--case-set", str(tmp_path / "cases.json")])

    assert code == 1
    assert "cannot launch" in capsys.readouterr().err
