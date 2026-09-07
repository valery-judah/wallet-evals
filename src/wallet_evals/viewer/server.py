from __future__ import annotations

import json
import webbrowser
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from wallet_evals.viewer.repository import (
    ArtifactNotFoundError,
    ArtifactValidationError,
    RunResultRepository,
)

LOOPBACK_HOST = "127.0.0.1"
STATIC_DIRECTORY = Path(__file__).with_name("static")
STATIC_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


class ViewerServerError(RuntimeError):
    """Raised when the local viewer server cannot start or run."""


class ViewerHTTPServer(ThreadingHTTPServer):
    repository: RunResultRepository


def create_viewer_server(repository: RunResultRepository, port: int) -> ViewerHTTPServer:
    handler = _handler_type(repository)
    try:
        server = ViewerHTTPServer((LOOPBACK_HOST, port), handler)
    except OSError as exc:
        raise ViewerServerError(
            f"cannot bind trace viewer to {LOOPBACK_HOST}:{port}: {exc}"
        ) from exc
    server.repository = repository
    return server


def serve_viewer(
    results_directory: Path,
    *,
    port: int,
    open_browser: bool,
    browser_open: Callable[[str], object] = webbrowser.open,
) -> None:
    repository = RunResultRepository(results_directory)
    server = create_viewer_server(repository, port)
    actual_port = server.server_address[1]
    url = f"http://{LOOPBACK_HOST}:{actual_port}"
    print(f"Trace viewer: {url}", flush=True)
    print(f"Results: {repository.directory}", flush=True)
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
        raise ViewerServerError(f"trace viewer server failed: {exc}") from exc
    finally:
        server.server_close()


def _handler_type(repository: RunResultRepository) -> type[BaseHTTPRequestHandler]:
    class ViewerRequestHandler(BaseHTTPRequestHandler):
        server_version = "wallet-evals-viewer"

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract.
            route = urlsplit(self.path).path
            if route == "/api/runs":
                summaries = repository.list_artifacts()
                default_artifact = next(
                    (summary.artifact_name for summary in summaries if summary.valid),
                    None,
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "results_directory": str(repository.directory),
                        "default_artifact_name": default_artifact,
                        "runs": [summary.model_dump(mode="json") for summary in summaries],
                    },
                )
                return
            if route.startswith("/api/runs/"):
                artifact_name = unquote(route.removeprefix("/api/runs/"))
                try:
                    artifact = repository.load_artifact(artifact_name)
                except ArtifactNotFoundError as exc:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                except ArtifactValidationError as exc:
                    self._send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})
                else:
                    self._send_json(HTTPStatus.OK, artifact.model_dump(mode="json"))
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
            self.wfile.write(content)

        def _send_json(self, status: HTTPStatus, payload: Any) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    return ViewerRequestHandler


__all__ = [
    "LOOPBACK_HOST",
    "STATIC_DIRECTORY",
    "ViewerServerError",
    "create_viewer_server",
    "serve_viewer",
]
