from __future__ import annotations

import json
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import monotonic
from typing import Any
from urllib.parse import urlsplit

from pydantic import ValidationError

from wallet_evals.dataset_viewer import (
    DatasetRepository,
    create_dataset_viewer_server,
)
from wallet_evals.viewer import (
    RunResultRepository,
    create_viewer_server,
)
from wallet_evals.workbench.orchestration import (
    WorkbenchBusyError,
    WorkbenchRunManager,
    WorkbenchRunRequest,
    WorkbenchRunRequestError,
)

LOOPBACK_HOST = "127.0.0.1"
STATIC_DIRECTORY = Path(__file__).with_name("static")
STATIC_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


class WorkbenchServerError(RuntimeError):
    """Raised when the local orchestration workbench cannot start or run."""


@dataclass(frozen=True)
class WorkbenchLinks:
    dataset_viewer_url: str
    trace_viewer_url: str


class WorkbenchHTTPServer(ThreadingHTTPServer):
    manager: WorkbenchRunManager
    dataset_repository: DatasetRepository
    run_repository: RunResultRepository
    links: WorkbenchLinks


def create_workbench_server(
    manager: WorkbenchRunManager,
    dataset_repository: DatasetRepository,
    run_repository: RunResultRepository,
    links: WorkbenchLinks,
    port: int,
) -> WorkbenchHTTPServer:
    handler = _handler_type(manager, dataset_repository, run_repository, links)
    try:
        server = WorkbenchHTTPServer((LOOPBACK_HOST, port), handler)
    except OSError as exc:
        raise WorkbenchServerError(
            f"cannot bind evaluation workbench to {LOOPBACK_HOST}:{port}: {exc}"
        ) from exc
    server.manager = manager
    server.dataset_repository = dataset_repository
    server.run_repository = run_repository
    server.links = links
    return server


def serve_workbench(
    dataset_directory: Path,
    wallet_repository: Path,
    results_directory: Path,
    *,
    model: str,
    ollama_base_url: str,
    port: int,
    dataset_viewer_port: int,
    trace_viewer_port: int,
    open_browser: bool,
    repository_root: Path,
    browser_open: Callable[[str], object] = webbrowser.open,
) -> None:
    dataset_repository = DatasetRepository(dataset_directory)
    resolved_results = results_directory.expanduser().resolve()
    resolved_results.mkdir(parents=True, exist_ok=True)
    run_repository = RunResultRepository(resolved_results)

    dataset_server = create_dataset_viewer_server(dataset_repository, dataset_viewer_port)
    try:
        trace_server = create_viewer_server(run_repository, trace_viewer_port)
    except Exception:
        dataset_server.server_close()
        raise
    dataset_url = f"http://{LOOPBACK_HOST}:{dataset_server.server_address[1]}"
    trace_url = f"http://{LOOPBACK_HOST}:{trace_server.server_address[1]}"
    manager = WorkbenchRunManager(
        dataset_repository,
        repository_root=repository_root,
        wallet_repository=wallet_repository,
        results_directory=resolved_results,
        ollama_base_url=ollama_base_url,
        default_model=model,
    )
    try:
        workbench_server = create_workbench_server(
            manager,
            dataset_repository,
            run_repository,
            WorkbenchLinks(dataset_viewer_url=dataset_url, trace_viewer_url=trace_url),
            port,
        )
    except Exception:
        dataset_server.server_close()
        trace_server.server_close()
        raise

    viewer_threads = (
        Thread(target=dataset_server.serve_forever, daemon=True),
        Thread(target=trace_server.serve_forever, daemon=True),
    )
    for thread in viewer_threads:
        thread.start()
    url = f"http://{LOOPBACK_HOST}:{workbench_server.server_address[1]}"
    print(f"Evaluation workbench: {url}", flush=True)
    print(f"Dataset viewer: {dataset_url}", flush=True)
    print(f"Trace viewer: {trace_url}", flush=True)
    if open_browser:
        try:
            browser_open(url)
        except Exception:
            pass
    try:
        workbench_server.serve_forever()
    except KeyboardInterrupt:
        pass
    except OSError as exc:
        raise WorkbenchServerError(f"evaluation workbench server failed: {exc}") from exc
    finally:
        workbench_server.server_close()
        dataset_server.shutdown()
        trace_server.shutdown()
        dataset_server.server_close()
        trace_server.server_close()


def _handler_type(
    manager: WorkbenchRunManager,
    dataset_repository: DatasetRepository,
    run_repository: RunResultRepository,
    links: WorkbenchLinks,
) -> type[BaseHTTPRequestHandler]:
    class WorkbenchRequestHandler(BaseHTTPRequestHandler):
        server_version = "wallet-evals-workbench"
        request_started = 0.0

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract.
            self.request_started = monotonic()
            route = urlsplit(self.path).path
            if route == "/api/workbench":
                self._send_json(
                    HTTPStatus.OK,
                    _workbench_snapshot(manager, dataset_repository, run_repository, links),
                )
                return
            if route == "/api/run":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "run": manager.snapshot().model_dump(mode="json"),
                        "saved_runs": _saved_runs(run_repository),
                    },
                )
                return
            static = STATIC_ROUTES.get(route)
            if static is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "resource not found"})
                return
            filename, content_type = static
            try:
                content = (STATIC_DIRECTORY / filename).read_bytes()
            except OSError:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "workbench asset is unavailable"},
                )
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self._write_content(content)

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract.
            self.request_started = monotonic()
            route = urlsplit(self.path).path
            if route != "/api/run":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "resource not found"})
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload: object = json.loads(self.rfile.read(content_length))
                request = WorkbenchRunRequest.model_validate(payload)
                state = manager.start(request)
            except (ValueError, json.JSONDecodeError, ValidationError) as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            except WorkbenchRunRequestError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            except WorkbenchBusyError as exc:
                self._send_json(HTTPStatus.CONFLICT, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.ACCEPTED, {"run": state.model_dump(mode="json")})

        def _send_json(self, status: HTTPStatus, payload: Any) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self._write_content(content)

        def _write_content(self, content: bytes) -> None:
            try:
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
            del size
            elapsed_ms = (monotonic() - self.request_started) * 1000
            route = urlsplit(self.path).path
            print(
                f"Workbench HTTP: {self.command} {route} -> {code} ({elapsed_ms:.1f} ms)",
                flush=True,
            )

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    return WorkbenchRequestHandler


def _workbench_snapshot(
    manager: WorkbenchRunManager,
    dataset_repository: DatasetRepository,
    run_repository: RunResultRepository,
    links: WorkbenchLinks,
) -> dict[str, object]:
    snapshot = dataset_repository.snapshot()
    cases = [
        {
            "case_id": case.case_id,
            "tuple_id": case.tuple_id,
            "interaction_form": case.interaction_form,
            "messages": case.example.get("user_messages", []),
            "cohort_ids": list(case.cohort_ids),
        }
        for case in snapshot.cases
    ]
    cohorts = [
        {
            "cohort_id": cohort.cohort_id,
            "description": cohort.description,
            "case_ids": list(cohort.case_ids),
        }
        for cohort in snapshot.cohorts
    ]
    return {
        "dataset": {
            "directory": snapshot.dataset_directory,
            "name": snapshot.dimension_set_name,
            "case_count": snapshot.totals.cases,
            "cases": cases,
            "cohorts": cohorts,
        },
        "defaults": {
            "model": manager.default_model,
            "wallet_repository": str(manager.wallet_repository),
        },
        "links": {
            "dataset_viewer": links.dataset_viewer_url,
            "trace_viewer": links.trace_viewer_url,
        },
        "run": manager.snapshot().model_dump(mode="json"),
        "saved_runs": _saved_runs(run_repository),
    }


def _saved_runs(repository: RunResultRepository) -> list[dict[str, Any]]:
    return [summary.model_dump(mode="json") for summary in repository.list_artifacts()]


__all__ = [
    "LOOPBACK_HOST",
    "STATIC_DIRECTORY",
    "WorkbenchHTTPServer",
    "WorkbenchLinks",
    "WorkbenchServerError",
    "create_workbench_server",
    "serve_workbench",
]
