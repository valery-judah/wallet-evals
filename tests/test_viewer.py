from __future__ import annotations

import http.client
import json
import os
import threading
from pathlib import Path
from typing import cast
from urllib.parse import quote

import pytest
from pydantic import JsonValue

from wallet_evals.runner import (
    CaseTrace,
    ExecutionContext,
    ParticipantAction,
    ParticipantActionTraceEvent,
    RunResult,
    WalletResponseTraceEvent,
)
from wallet_evals.viewer import (
    ArtifactNotFoundError,
    ArtifactValidationError,
    RunResultRepository,
    ViewerConfigurationError,
    create_viewer_server,
)
from wallet_evals.viewer.server import STATIC_DIRECTORY


def _run_result(run_id: str, *, case_id: str = "T001/E01") -> RunResult:
    context = ExecutionContext(
        wallet="wallet@abc123",
        model="model:1b",
        environment="local-in-process",
        settings={"case_set_id": "test-set", "isolation_mode": "fresh per case"},
    )
    trace = CaseTrace(
        run_id=run_id,
        case_execution_id=f"execution-{case_id.replace('/', '-')}",
        case_id=case_id,
        execution_context=context,
        case_context={
            "interaction_form": "standalone",
            "purpose": "Inspect a balance response.",
            "failure_surface": "Wallet could route incorrectly.",
            "dimensions": {"User Job": "wallet_state"},
        },
        starting_conditions={"balance_minor": 10000},
        events=(
            ParticipantActionTraceEvent(
                order=1,
                action=ParticipantAction(name="message", payload="Show my balance"),
            ),
            WalletResponseTraceEvent(
                order=2,
                response={"outcome": {"kind": "state_shown", "message": "Balance is 100"}},
            ),
        ),
    )
    return RunResult(run_id=run_id, execution_context=context, traces=(trace,))


def _write_artifact(directory: Path, filename: str, run_id: str) -> dict[str, JsonValue]:
    document: dict[str, JsonValue] = {
        "schema_version": "0.1",
        "run_result": _run_result(run_id).model_dump(mode="json"),
    }
    (directory / filename).write_text(json.dumps(document), encoding="utf-8")
    return document


def test_repository_lists_valid_and_invalid_artifacts_newest_first(tmp_path: Path) -> None:
    older_document = _write_artifact(tmp_path, "older.json", "run-older")
    newer_document = _write_artifact(tmp_path, "newer.json", "run-newer")
    del older_document, newer_document
    (tmp_path / "invalid.json").write_text('{"schema_version":"unknown"}', encoding="utf-8")
    os.utime(tmp_path / "older.json", ns=(1_000_000_000, 1_000_000_000))
    os.utime(tmp_path / "newer.json", ns=(3_000_000_000, 3_000_000_000))
    os.utime(tmp_path / "invalid.json", ns=(4_000_000_000, 4_000_000_000))

    summaries = RunResultRepository(tmp_path).list_artifacts()

    assert [summary.artifact_name for summary in summaries] == [
        "invalid.json",
        "newer.json",
        "older.json",
    ]
    assert summaries[0].valid is False
    assert summaries[0].error
    assert summaries[1].model_dump(mode="json") == {
        "artifact_name": "newer.json",
        "modified_at": "1970-01-01T00:00:03+00:00",
        "modified_ns": 3_000_000_000,
        "valid": True,
        "error": None,
        "run_id": "run-newer",
        "case_count": 1,
        "wallet": "wallet@abc123",
        "model": "model:1b",
        "case_set_id": "test-set",
    }


def test_repository_loads_exact_valid_document_and_confines_filenames(tmp_path: Path) -> None:
    document = _write_artifact(tmp_path, "run.json", "run-exact")
    repository = RunResultRepository(tmp_path)

    loaded = repository.load_artifact("run.json")

    assert loaded.document == document
    with pytest.raises(ArtifactNotFoundError):
        repository.load_artifact("../run.json")
    with pytest.raises(ArtifactNotFoundError):
        repository.load_artifact(str((tmp_path / "run.json").resolve()))


def test_repository_rejects_missing_directory_and_invalid_artifact(tmp_path: Path) -> None:
    with pytest.raises(ViewerConfigurationError, match="does not exist"):
        RunResultRepository(tmp_path / "missing")

    (tmp_path / "bad.json").write_text("not JSON", encoding="utf-8")
    with pytest.raises(ArtifactValidationError, match="valid JSON"):
        RunResultRepository(tmp_path).load_artifact("bad.json")


class RunningViewer:
    def __init__(self, results_directory: Path) -> None:
        self.server = create_viewer_server(RunResultRepository(results_directory), 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> RunningViewer:
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


def test_http_server_serves_assets_run_index_and_exact_artifact(tmp_path: Path) -> None:
    document = _write_artifact(tmp_path, "newest.json", "run-newest")
    _write_artifact(tmp_path, "older.json", "run-older")
    (tmp_path / "invalid.json").write_text("{}", encoding="utf-8")
    os.utime(tmp_path / "newest.json", ns=(5_000_000_000, 5_000_000_000))
    os.utime(tmp_path / "older.json", ns=(3_000_000_000, 3_000_000_000))
    os.utime(tmp_path / "invalid.json", ns=(4_000_000_000, 4_000_000_000))

    with RunningViewer(tmp_path) as viewer:
        status, content_type, content = viewer.get("/")
        assert status == 200
        assert content_type == "text/html; charset=utf-8"
        assert b"Trace viewer" in content

        status, content_type, content = viewer.get("/api/runs")
        index = cast(dict[str, object], json.loads(content))
        assert status == 200
        assert content_type == "application/json; charset=utf-8"
        assert index["default_artifact_name"] == "newest.json"
        assert len(cast(list[object], index["runs"])) == 3

        status, content_type, content = viewer.get(f"/api/runs/{quote('newest.json', safe='')}")
        artifact = cast(dict[str, object], json.loads(content))
        assert status == 200
        assert content_type == "application/json; charset=utf-8"
        assert artifact["document"] == document


def test_http_server_reports_unknown_invalid_and_unmatched_resources(tmp_path: Path) -> None:
    (tmp_path / "invalid.json").write_text("{}", encoding="utf-8")

    with RunningViewer(tmp_path) as viewer:
        assert viewer.get("/api/runs/missing.json")[0] == 404
        assert viewer.get("/api/runs/invalid.json")[0] == 422
        assert viewer.get("/api/runs/..%2Finvalid.json")[0] == 404
        assert viewer.get("/not-a-route")[0] == 404


def test_presentation_assets_label_evidence_and_avoid_html_injection_primitives() -> None:
    application = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
    page = (STATIC_DIRECTORY / "index.html").read_text(encoding="utf-8")
    styles = (STATIC_DIRECTORY / "styles.css").read_text(encoding="utf-8")

    for label in (
        "Participant action",
        "Wallet response",
        "Adaptive choice · cited participant-visible facts",
        "Observable change",
        "Complete captured response",
        "Derived response summary",
        "Execution provenance",
        "Raw trace evidence",
    ):
        assert label in application
    assert "Read only" in page
    assert 'id="theme-toggle"' in page
    assert 'data-theme="dark"' in styles
    assert "prefers-color-scheme: dark" in application
    assert "localStorage" in application
    assert "textContent" in application
    assert "createElement" in application
    assert "innerHTML" not in application
    assert "insertAdjacentHTML" not in application
