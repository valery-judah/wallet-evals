from __future__ import annotations

import json
from collections.abc import Iterable
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
from typing import cast

from wallet_evals.dataset_viewer import DatasetRepository
from wallet_evals.viewer import RunResultRepository
from wallet_evals.workbench.orchestration import RunningProcess, WorkbenchRunManager
from wallet_evals.workbench.server import WorkbenchLinks, create_workbench_server

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIRECTORY = REPOSITORY_ROOT / "data/dataset-1"
STATIC_DIRECTORY = REPOSITORY_ROOT / "src/wallet_evals/workbench/static"


class ImmediateProcess:
    @property
    def stdout(self) -> Iterable[str]:
        return iter(("Error: model unavailable\n",))

    def wait(self) -> int:
        return 2


def _factory(command: list[str], *, cwd: Path) -> RunningProcess:
    del command, cwd
    return ImmediateProcess()


def _request(
    connection: HTTPConnection,
    method: str,
    path: str,
    payload: object | None = None,
) -> tuple[int, str, object]:
    body = None if payload is None else json.dumps(payload)
    connection.request(
        method,
        path,
        body=body,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    response = connection.getresponse()
    content_type = response.getheader("Content-Type", "")
    text = response.read().decode("utf-8")
    parsed: object = json.loads(text) if "application/json" in content_type else text
    return response.status, content_type, parsed


def test_workbench_http_composes_selection_run_and_viewer_handoffs(tmp_path: Path) -> None:
    dataset = DatasetRepository(DATASET_DIRECTORY)
    results = tmp_path / "eval-runs"
    results.mkdir()
    run_repository = RunResultRepository(results)
    manager = WorkbenchRunManager(
        dataset,
        repository_root=REPOSITORY_ROOT,
        wallet_repository=REPOSITORY_ROOT / "wallet-sut",
        results_directory=results,
        ollama_base_url="http://127.0.0.1:11434",
        default_model="model-default",
        process_factory=_factory,
    )
    server = create_workbench_server(
        manager,
        dataset,
        run_repository,
        WorkbenchLinks(
            dataset_viewer_url="http://127.0.0.1:9101",
            trace_viewer_url="http://127.0.0.1:9102",
        ),
        0,
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    try:
        status, _, body = _request(connection, "GET", "/api/workbench")
        snapshot = cast(dict[str, object], body)
        dataset_payload = cast(dict[str, object], snapshot["dataset"])
        links = cast(dict[str, object], snapshot["links"])

        assert status == 200
        assert dataset_payload["case_count"] == 440
        assert len(cast(list[object], dataset_payload["cohorts"])) == 2
        assert links["dataset_viewer"] == "http://127.0.0.1:9101"
        assert links["trace_viewer"] == "http://127.0.0.1:9102"

        status, content_type, page = _request(connection, "GET", "/")
        assert status == 200
        assert "text/html" in content_type
        assert "Select cases" in cast(str, page)
        assert "Run Wallet" in cast(str, page)

        status, _, script = _request(connection, "GET", "/app.js")
        assert status == 200
        assert "payload.cohort_id = state.selectedCohortId" in cast(str, script)

        cohort = dataset.bundle.cohorts["workbench-check-8"]
        status, _, response = _request(
            connection,
            "POST",
            "/api/run",
            {
                "case_ids": list(cohort.cases),
                "model": "missing",
                "cohort_id": cohort.id,
            },
        )
        assert status == 202
        prepared_run = cast(dict[str, object], cast(dict[str, object], response)["run"])
        assert prepared_run["selection_id"] == "workbench-check-8"
        assert prepared_run["cohort_id"] == "workbench-check-8"
        assert manager.wait(5).status == "failed"

        status, _, response = _request(
            connection,
            "POST",
            "/api/run",
            {
                "case_ids": ["T001/E01"],
                "model": "model-default",
                "cohort_id": cohort.id,
            },
        )
        assert status == 400
        assert "exactly match cohort" in cast(str, cast(dict[str, object], response)["error"])

        status, _, response = _request(
            connection,
            "POST",
            "/api/run",
            {"case_ids": ["T010/E01"], "model": "missing"},
        )
        assert status == 202
        assert cast(dict[str, object], cast(dict[str, object], response)["run"])["status"] in {
            "running",
            "failed",
        }
        ad_hoc_run = cast(dict[str, object], cast(dict[str, object], response)["run"])
        assert cast(str, ad_hoc_run["selection_id"]).startswith("workbench-ad-hoc-")
        assert ad_hoc_run["cohort_id"] is None
        assert manager.wait(5).status == "failed"

        status, _, response = _request(
            connection,
            "POST",
            "/api/run",
            {"case_ids": ["not/a-case"], "model": "model-default"},
        )
        assert status == 400
        assert "not in the loaded dataset" in cast(str, cast(dict[str, object], response)["error"])
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(5)


def test_workbench_pins_selected_matches_ahead_of_the_case_list_limit() -> None:
    application = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")

    assert "const selectedMatches = matching.filter" in application
    assert "...selectedMatches" in application
    assert "80 - selectedMatches.length" in application
    assert "Selected cases appear first." in application
    assert "Case-level errors in the technical output are captured evidence." in application
