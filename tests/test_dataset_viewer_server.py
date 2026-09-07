from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import cast
from urllib.parse import quote

import pytest

from wallet_evals.dataset_viewer import DatasetRepository, DatasetViewerServerError
from wallet_evals.dataset_viewer import server as dataset_server
from wallet_evals.dataset_viewer.server import STATIC_DIRECTORY

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIRECTORY = REPOSITORY_ROOT / "data/dataset-1"


class RunningDatasetViewer:
    def __init__(self) -> None:
        self.server = dataset_server.create_dataset_viewer_server(
            DatasetRepository(DATASET_DIRECTORY),
            0,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> RunningDatasetViewer:
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        del args
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def get(self, path: str) -> tuple[int, str, bytes]:
        address = cast(tuple[str, int], self.server.server_address)
        connection = http.client.HTTPConnection(address[0], address[1], timeout=2)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            return response.status, response.getheader("Content-Type", ""), response.read()
        finally:
            connection.close()


def test_http_server_serves_assets_composed_dataset_and_exact_sources(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with RunningDatasetViewer() as viewer:
        status, content_type, content = viewer.get("/")
        assert status == 200
        assert content_type == "text/html; charset=utf-8"
        assert b"Dataset viewer" in content

        status, content_type, content = viewer.get("/api/dataset")
        dataset = cast(dict[str, object], json.loads(content))
        assert status == 200
        assert content_type == "application/json; charset=utf-8"
        totals = cast(dict[str, object], dataset["totals"])
        assert totals["cases"] == 440
        assert len(cast(list[object], dataset["coverage"])) == 8

        filename = "wallet_v1_examples_T001.json"
        status, content_type, content = viewer.get(
            f"/api/dataset/sources/{quote(filename, safe='')}"
        )
        source = cast(dict[str, object], json.loads(content))
        assert status == 200
        assert content_type == "application/json; charset=utf-8"
        document = cast(dict[str, object], source["document"])
        assert document["tuple_id"] == "T001"

    request_log = capsys.readouterr().out
    assert "Dataset viewer HTTP: GET / -> 200" in request_log
    assert "Dataset viewer HTTP: GET /api/dataset -> 200" in request_log
    assert "Dataset viewer HTTP: GET /api/dataset/sources/" in request_log


def test_http_server_rejects_unknown_traversal_and_unmatched_resources() -> None:
    with RunningDatasetViewer() as viewer:
        assert viewer.get("/api/dataset/sources/missing.json")[0] == 404
        assert viewer.get("/api/dataset/sources/..%2Fwallet_v1_case_fixtures.json")[0] == 404
        assert viewer.get("/not-a-route")[0] == 404


def test_presentation_assets_cover_review_workflow_and_dom_safety() -> None:
    application = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
    page = (STATIC_DIRECTORY / "index.html").read_text(encoding="utf-8")
    styles = (STATIC_DIRECTORY / "styles.css").read_text(encoding="utf-8")

    for label in (
        "Coverage overview",
        "Dataset overview",
        "Dataset statistics",
        "Dimensions",
        "Generated user inputs",
        "Executable evaluation case",
        "Complete generated user input",
        "Recorded case fixture",
        "Shared fixture source (separate)",
        "Exact tuple record",
        "Generation context",
        "Assigned dimension definitions",
        "Exact generating tuple record",
        "Open full tuple",
        "Message under test",
        "Behavior under test",
        "Setup context",
        "Runtime-adaptive prelude",
        "Select an assignment to see its dimension and value definitions.",
        "Dimension definition",
        "All values in this dimension",
        "Assigned",
        "Description",
        "Why it matters",
        "Copy handoff",
        "Handoff format",
        "evaluation_dataset_tuple_rebuild_context",
        "Dimensions and values",
        "assigned to current tuple",
        "Other tuples",
    ):
        assert label in application
    assert "Read only" in page
    assert 'data-view="overview"' in page
    assert 'data-view="statistics"' in page
    assert 'data-view="dimensions"' in page
    assert 'data-view="tuples"' in page
    assert 'data-view="cases"' in page
    assert 'id="theme-toggle"' in page
    assert 'href="styles.css"' in page
    assert 'src="app.js"' in page
    assert 'data-theme="dark"' in styles
    assert "prefers-color-scheme: dark" in application
    assert "localStorage" in application
    assert 'clientLog("boot"' in application
    assert 'clientLog("request"' in application
    assert 'clientLog("response"' in application
    assert 'clientLog("ready"' in application
    assert "unhandledrejection" in application
    assert 'window.location.protocol === "file:"' in application
    assert "This HTML file is not the running viewer" in application
    assert "uv run wallet_evals view-dataset" in application
    assert "textContent" in application
    assert "createElement" in application
    assert "innerHTML" not in application
    assert "insertAdjacentHTML" not in application
    assert "dimension.definition" in application
    assert "assignedValue?.definition" in application
    assert "assigned-dimensions" in styles
    assert "generated-input-table" in styles
    assert "Inspect executable case" not in application
    assert "varyingGeneratedInputColumns" in application
    assert "hideWhenConstant: true" in application
    assert "--generated-input-columns" in styles
    assert "dimensionAssignmentDetails" in application
    assert "dimensionValuesTable" in application
    assert "dimension-pair-summary" in styles
    assert "dimension-values-table" in styles
    assert "handoff-controls" in styles
    assert "clipboard-fallback" in styles
    assert "navigator.clipboard.writeText" in application
    assert 'document.execCommand("copy")' in application
    assert "buildTupleHandoff" in application
    assert "tupleHandoffMarkdown" in application
    assert "caseById(caseId).example.user_messages" in application
    assert application.index("current_tuple:") < application.index(
        "dimensions: state.dataset.dimensions"
    )
    assert "Focal user input" not in application
    assert "Focal message" not in application
    assert "Focal user behavior" not in application


class ScriptedServer:
    server_address = (dataset_server.LOOPBACK_HOST, 9124)

    def __init__(self, *, interrupt: bool = False, failure: OSError | None = None) -> None:
        self.interrupt = interrupt
        self.failure = failure
        self.served = False
        self.closed = False

    def serve_forever(self) -> None:
        self.served = True
        if self.interrupt:
            raise KeyboardInterrupt
        if self.failure is not None:
            raise self.failure

    def server_close(self) -> None:
        self.closed = True


def _return_server(
    server: ScriptedServer,
) -> Callable[[DatasetRepository, int], ScriptedServer]:
    def factory(_repository: DatasetRepository, _port: int) -> ScriptedServer:
        return server

    return factory


def test_serve_dataset_viewer_opens_browser_prints_paths_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = ScriptedServer(interrupt=True)
    opened: list[str] = []
    monkeypatch.setattr(
        dataset_server,
        "create_dataset_viewer_server",
        _return_server(server),
    )

    dataset_server.serve_dataset_viewer(
        DATASET_DIRECTORY,
        port=8766,
        open_browser=True,
        browser_open=lambda url: opened.append(url),
    )

    assert server.served and server.closed
    assert opened == ["http://127.0.0.1:9124"]
    output = capsys.readouterr().out
    assert "Dataset viewer load: validating" in output
    assert "Dataset viewer load: validated 8 dimensions, 22 tuples, 440 cases" in output
    assert "Dataset viewer: http://127.0.0.1:9124" in output
    assert f"Dataset: {DATASET_DIRECTORY.resolve()}" in output


def test_create_dataset_server_wraps_bind_and_runtime_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_bind(*_args: object, **_kwargs: object) -> None:
        raise OSError("address already in use")

    monkeypatch.setattr(dataset_server, "DatasetViewerHTTPServer", reject_bind)
    with pytest.raises(DatasetViewerServerError, match="address already in use"):
        dataset_server.create_dataset_viewer_server(
            DatasetRepository(DATASET_DIRECTORY),
            8766,
        )

    scripted = ScriptedServer(failure=OSError("socket failed"))
    monkeypatch.setattr(
        dataset_server,
        "create_dataset_viewer_server",
        _return_server(scripted),
    )
    with pytest.raises(DatasetViewerServerError, match="socket failed"):
        dataset_server.serve_dataset_viewer(
            DATASET_DIRECTORY,
            port=8766,
            open_browser=False,
        )
    assert scripted.closed
