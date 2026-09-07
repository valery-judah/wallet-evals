from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

from wallet_evals import __version__
from wallet_evals.case_sets import CaseSetError, DatasetCaseSource
from wallet_evals.dataset_viewer import DatasetViewerServerError, serve_dataset_viewer
from wallet_evals.viewer import ViewerConfigurationError, ViewerServerError, serve_viewer
from wallet_evals.workbench import (
    WorkbenchConfigurationError,
    WorkbenchExecutionError,
    WorkbenchServerError,
    run_workbench,
    serve_workbench,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WALLET_REPOSITORY = REPOSITORY_ROOT.parent / "wallet"
DEFAULT_RESULTS_DIRECTORY = REPOSITORY_ROOT / "results/eval-runs"
DEFAULT_DATASET_DIRECTORY = REPOSITORY_ROOT / "data/dataset-1"
DEFAULT_EVALUATIONS_DIRECTORY = REPOSITORY_ROOT / "results/evaluations"
LOCAL_WALLET_WORKER = REPOSITORY_ROOT / "scripts/devex/run_wallet_cohort.py"
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_VIEWER_PORT = 8765
DEFAULT_DATASET_VIEWER_PORT = 8766
DEFAULT_WORKBENCH_PORT = 8764


class RunConfigurationError(ValueError):
    """Raised when a local run cannot be established from operator inputs."""


class RunExecutionError(RuntimeError):
    """Raised when the configured run cannot be launched."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wallet_evals",
        description="Run Wallet evaluation cases and save attributable traces.",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser(
        "run",
        help="Run a selected case set against the managed local Wallet SUT.",
    )
    run_parser.add_argument(
        "--case-set",
        type=Path,
        required=True,
        help="JSON file selecting the evaluation case identities to run.",
    )
    run_parser.add_argument(
        "--wallet-repo",
        type=Path,
        default=DEFAULT_WALLET_REPOSITORY,
        help=f"Wallet repository checkout (default: {DEFAULT_WALLET_REPOSITORY}).",
    )
    run_parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model used by Wallet (default: {DEFAULT_MODEL}).",
    )
    run_parser.add_argument(
        "--ollama-base-url",
        default=DEFAULT_OLLAMA_BASE_URL,
        help=f"Ollama HTTP base URL (default: {DEFAULT_OLLAMA_BASE_URL}).",
    )
    run_parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIRECTORY,
        help=f"Run-result destination (default: {DEFAULT_RESULTS_DIRECTORY}).",
    )
    view_parser = subparsers.add_parser(
        "view",
        help="Inspect saved run-result traces in a local read-only browser viewer.",
    )
    view_parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIRECTORY,
        help=f"Saved run-result directory (default: {DEFAULT_RESULTS_DIRECTORY}).",
    )
    view_parser.add_argument(
        "--port",
        type=_viewer_port,
        default=DEFAULT_VIEWER_PORT,
        help=f"Loopback HTTP port (default: {DEFAULT_VIEWER_PORT}).",
    )
    view_parser.add_argument(
        "--no-open",
        action="store_true",
        help="Print the viewer URL without opening the default browser.",
    )
    dataset_view_parser = subparsers.add_parser(
        "view-dataset",
        help="Inspect dataset coverage, tuples, generated inputs, and executable cases.",
    )
    dataset_view_parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=DEFAULT_DATASET_DIRECTORY,
        help=f"Evaluation dataset directory (default: {DEFAULT_DATASET_DIRECTORY}).",
    )
    dataset_view_parser.add_argument(
        "--port",
        type=_viewer_port,
        default=DEFAULT_DATASET_VIEWER_PORT,
        help=f"Loopback HTTP port (default: {DEFAULT_DATASET_VIEWER_PORT}).",
    )
    dataset_view_parser.add_argument(
        "--no-open",
        action="store_true",
        help="Print the viewer URL without opening the default browser.",
    )
    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Judge one saved execution against a scoped evaluation plan.",
    )
    evaluate_parser.add_argument(
        "--plan",
        type=Path,
        required=True,
        help="Immutable evaluation plan with a brief, criteria, and case checks.",
    )
    evaluate_parser.add_argument(
        "--execution-result",
        type=Path,
        required=True,
        help="Saved execution-result JSON artifact to evaluate.",
    )
    evaluate_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_EVALUATIONS_DIRECTORY,
        help=f"Completed evaluation destination (default: {DEFAULT_EVALUATIONS_DIRECTORY}).",
    )
    workbench_parser = subparsers.add_parser(
        "workbench",
        help="Open the local case-selection, Wallet-run, and evidence-review workbench.",
    )
    workbench_parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=DEFAULT_DATASET_DIRECTORY,
        help=f"Evaluation dataset directory (default: {DEFAULT_DATASET_DIRECTORY}).",
    )
    workbench_parser.add_argument(
        "--wallet-repo",
        type=Path,
        default=DEFAULT_WALLET_REPOSITORY,
        help=f"Wallet repository checkout (default: {DEFAULT_WALLET_REPOSITORY}).",
    )
    workbench_parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Initial Ollama model shown in the workbench (default: {DEFAULT_MODEL}).",
    )
    workbench_parser.add_argument(
        "--ollama-base-url",
        default=DEFAULT_OLLAMA_BASE_URL,
        help=f"Ollama HTTP base URL used for runs (default: {DEFAULT_OLLAMA_BASE_URL}).",
    )
    workbench_parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIRECTORY,
        help=f"Run-result destination (default: {DEFAULT_RESULTS_DIRECTORY}).",
    )
    workbench_parser.add_argument(
        "--port",
        type=_viewer_port,
        default=DEFAULT_WORKBENCH_PORT,
        help=f"Workbench loopback port (default: {DEFAULT_WORKBENCH_PORT}).",
    )
    workbench_parser.add_argument(
        "--dataset-viewer-port",
        type=_viewer_port,
        default=DEFAULT_DATASET_VIEWER_PORT,
        help=f"Dataset-viewer loopback port (default: {DEFAULT_DATASET_VIEWER_PORT}).",
    )
    workbench_parser.add_argument(
        "--trace-viewer-port",
        type=_viewer_port,
        default=DEFAULT_VIEWER_PORT,
        help=f"Trace-viewer loopback port (default: {DEFAULT_VIEWER_PORT}).",
    )
    workbench_parser.add_argument(
        "--no-open",
        action="store_true",
        help="Print the workbench URL without opening the default browser.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(arguments)
    if args.version:
        print(__version__)
        return 0
    if args.command is None:
        parser.print_help()
        return 0

    try:
        if args.command == "view":
            return _view_results(args)
        if args.command == "view-dataset":
            return _view_dataset(args)
        if args.command == "workbench":
            return _open_workbench(args)
        if args.command == "evaluate":
            return _run_evaluation(args)
        return _run_local_wallet(args)
    except (
        CaseSetError,
        RunConfigurationError,
        ViewerConfigurationError,
        WorkbenchConfigurationError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (
        DatasetViewerServerError,
        RunExecutionError,
        ViewerServerError,
        WorkbenchExecutionError,
        WorkbenchServerError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _view_results(args: argparse.Namespace) -> int:
    results_directory = _resolve_path(args.results_dir)
    port = args.port
    if not isinstance(port, int):
        raise RunConfigurationError("viewer port has an invalid value")
    serve_viewer(results_directory, port=port, open_browser=not args.no_open)
    return 0


def _view_dataset(args: argparse.Namespace) -> int:
    dataset_directory = _resolve_path(args.dataset_dir)
    port = args.port
    if not isinstance(port, int):
        raise RunConfigurationError("viewer port has an invalid value")
    serve_dataset_viewer(dataset_directory, port=port, open_browser=not args.no_open)
    return 0


def _run_evaluation(args: argparse.Namespace) -> int:
    saved = run_workbench(
        _resolve_path(args.plan),
        _resolve_path(args.execution_result),
        _resolve_path(args.output_dir),
    )
    print(
        f"Evaluation: {saved.summary.passed}/{saved.summary.case_count} passed, "
        f"{saved.summary.failed} failed, "
        f"{saved.summary.unable_to_judge} unable to judge",
        flush=True,
    )
    print(f"Finding: {saved.finding.answer}", flush=True)
    print(f"Artifact: {saved.artifact_path}", flush=True)
    print(f"Report: {saved.report_path}", flush=True)
    return 0


def _open_workbench(args: argparse.Namespace) -> int:
    model = _nonblank(args.model, label="model")
    ollama_base_url = _normalize_http_base_url(args.ollama_base_url)
    ports = (args.port, args.dataset_viewer_port, args.trace_viewer_port)
    if any(not isinstance(port, int) for port in ports):
        raise RunConfigurationError("workbench port has an invalid value")
    workbench_port, dataset_viewer_port, trace_viewer_port = cast(tuple[int, int, int], ports)
    serve_workbench(
        _resolve_path(args.dataset_dir),
        _resolve_path(args.wallet_repo),
        _resolve_path(args.results_dir),
        model=model,
        ollama_base_url=ollama_base_url,
        port=workbench_port,
        dataset_viewer_port=dataset_viewer_port,
        trace_viewer_port=trace_viewer_port,
        open_browser=not args.no_open,
        repository_root=REPOSITORY_ROOT,
    )
    return 0


def _run_local_wallet(args: argparse.Namespace) -> int:
    case_set_path = _resolve_path(args.case_set)
    wallet_repository = _resolve_path(args.wallet_repo)
    results_directory = _resolve_path(args.results_dir)
    model = _nonblank(args.model, label="model")
    ollama_base_url = _normalize_http_base_url(args.ollama_base_url)

    source = DatasetCaseSource(case_set_path)
    _validate_local_wallet_checkout(wallet_repository)
    _validate_worker()
    uv = shutil.which("uv")
    if uv is None:
        raise RunConfigurationError("uv is not installed or is not available on PATH")
    _validate_ollama(ollama_base_url, model)

    print(
        f"Running {len(source.case_ids)} case(s) from {source.case_set_id} against local Wallet.",
        flush=True,
    )
    environment = os.environ.copy()
    environment.pop("VIRTUAL_ENV", None)
    source_root = str(REPOSITORY_ROOT / "src")
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root
        if not existing_pythonpath
        else os.pathsep.join((source_root, existing_pythonpath))
    )
    command = [
        uv,
        "--directory",
        str(wallet_repository / "backend"),
        "run",
        "python",
        str(LOCAL_WALLET_WORKER),
        "--case-set",
        str(case_set_path),
        "--wallet-repo",
        str(wallet_repository),
        "--model",
        model,
        "--ollama-base-url",
        ollama_base_url,
        "--results-dir",
        str(results_directory),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=False,
        )
    except OSError as exc:
        raise RunExecutionError(f"cannot launch the managed Wallet worker: {exc}") from exc
    return completed.returncode


def _validate_local_wallet_checkout(repository: Path) -> None:
    backend_project = repository / "backend/pyproject.toml"
    if not backend_project.is_file():
        raise RunConfigurationError(
            f"Wallet checkout must contain backend/pyproject.toml: {repository}"
        )
    if not (repository / ".git").exists():
        raise RunConfigurationError(f"Wallet checkout is not a Git worktree: {repository}")


def _validate_worker() -> None:
    if not LOCAL_WALLET_WORKER.is_file():
        raise RunConfigurationError(f"managed Wallet worker is missing: {LOCAL_WALLET_WORKER}")


def _validate_ollama(base_url: str, model: str) -> None:
    endpoint = f"{base_url}/api/tags"
    try:
        with urlopen(endpoint, timeout=5) as response:  # noqa: S310 - URL is operator supplied.
            payload: object = json.load(response)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RunConfigurationError(f"cannot reach Ollama at {base_url}: {exc}") from exc
    available_names: set[str] = set()
    if isinstance(payload, dict):
        models = cast(dict[str, object], payload).get("models")
        if isinstance(models, list):
            for item in cast(list[object], models):
                if not isinstance(item, dict):
                    continue
                name = cast(dict[str, object], item).get("name")
                if isinstance(name, str):
                    available_names.add(name)
    if model not in available_names:
        available = ", ".join(sorted(available_names))
        raise RunConfigurationError(
            f"Ollama model {model!r} is not installed; available models: {available or 'none'}"
        )


def _normalize_http_base_url(value: object) -> str:
    normalized = _nonblank(value, label="Ollama base URL").rstrip("/")
    parsed = urlsplit(normalized)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname is None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise RunConfigurationError("Ollama base URL must be a full HTTP URL without a path")
    return normalized


def _resolve_path(value: object) -> Path:
    if not isinstance(value, Path):
        raise RunConfigurationError("path argument has an invalid value")
    return value.expanduser().resolve()


def _nonblank(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunConfigurationError(f"{label} must not be blank")
    return value.strip()


def _viewer_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


if __name__ == "__main__":
    raise SystemExit(main())
