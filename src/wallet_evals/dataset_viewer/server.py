from __future__ import annotations

import json
import webbrowser
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import unquote, urlsplit

from wallet_evals.dataset_viewer.repository import (
    DatasetRepository,
    DatasetSourceNotFoundError,
)

LOOPBACK_HOST = "127.0.0.1"
STATIC_DIRECTORY = Path(__file__).with_name("static")
STATIC_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


class DatasetViewerServerError(RuntimeError):
    """Raised when the local dataset viewer cannot start or run."""


class DatasetViewerHTTPServer(ThreadingHTTPServer):
    repository: DatasetRepository


def create_dataset_viewer_server(
    repository: DatasetRepository,
    port: int,
) -> DatasetViewerHTTPServer:
    handler = _handler_type(repository)
    try:
        server = DatasetViewerHTTPServer((LOOPBACK_HOST, port), handler)
    except OSError as exc:
        raise DatasetViewerServerError(
            f"cannot bind dataset viewer to {LOOPBACK_HOST}:{port}: {exc}"
        ) from exc
    server.repository = repository
    return server


def serve_dataset_viewer(
    dataset_directory: Path,
    *,
    port: int,
    open_browser: bool,
    browser_open: Callable[[str], object] = webbrowser.open,
) -> None:
    print(f"Dataset viewer load: validating {dataset_directory.expanduser().resolve()}", flush=True)
    repository = DatasetRepository(dataset_directory)
    totals = repository.snapshot().totals
    print(
        "Dataset viewer load: validated "
        f"{totals.dimensions} dimensions, {totals.tuples} tuples, "
        f"{totals.cases} cases, and {totals.cohorts} case sets",
        flush=True,
    )
    server = create_dataset_viewer_server(repository, port)
    actual_port = server.server_address[1]
    url = f"http://{LOOPBACK_HOST}:{actual_port}"
    print(f"Dataset viewer: {url}", flush=True)
    print(f"Dataset: {repository.directory}", flush=True)
    if open_browser:
        try:
            browser_open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except OSError as exc:
        raise DatasetViewerServerError(f"dataset viewer server failed: {exc}") from exc
    finally:
        server.server_close()


def _handler_type(repository: DatasetRepository) -> type[BaseHTTPRequestHandler]:
    class DatasetViewerRequestHandler(BaseHTTPRequestHandler):
        server_version = "wallet-evals-dataset-viewer"
        request_started = 0.0

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract.
            self.request_started = monotonic()
            route = urlsplit(self.path).path
            if route == "/api/dataset":
                self._send_json(
                    HTTPStatus.OK,
                    repository.snapshot().model_dump(mode="json"),
                )
                return
            if route.startswith("/api/dataset/sources/"):
                filename = unquote(route.removeprefix("/api/dataset/sources/"))
                try:
                    source = repository.load_source(filename)
                except DatasetSourceNotFoundError as exc:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                else:
                    self._send_json(HTTPStatus.OK, source.model_dump(mode="json"))
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
                    {"error": "viewer asset is unavailable"},
                )
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self._write_content(content)

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
                route = urlsplit(self.path).path
                print(
                    f"Dataset viewer HTTP: client disconnected while reading {route}",
                    flush=True,
                )

        def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
            del size
            elapsed_ms = (monotonic() - self.request_started) * 1000
            route = urlsplit(self.path).path
            print(
                f"Dataset viewer HTTP: {self.command} {route} -> {code} ({elapsed_ms:.1f} ms)",
                flush=True,
            )

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    return DatasetViewerRequestHandler


__all__ = [
    "LOOPBACK_HOST",
    "STATIC_DIRECTORY",
    "DatasetViewerServerError",
    "create_dataset_viewer_server",
    "serve_dataset_viewer",
]
