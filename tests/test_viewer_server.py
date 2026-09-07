from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from wallet_evals.viewer import RunResultRepository, ViewerServerError
from wallet_evals.viewer import server as viewer_server


class ScriptedServer:
    server_address = (viewer_server.LOOPBACK_HOST, 9123)

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
) -> Callable[[RunResultRepository, int], ScriptedServer]:
    def factory(_repository: RunResultRepository, _port: int) -> ScriptedServer:
        return server

    return factory


def test_serve_viewer_opens_browser_and_closes_server(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    server = ScriptedServer(interrupt=True)
    opened: list[str] = []
    monkeypatch.setattr(viewer_server, "create_viewer_server", _return_server(server))

    viewer_server.serve_viewer(
        tmp_path,
        port=8765,
        open_browser=True,
        browser_open=lambda url: opened.append(url),
    )

    assert server.served and server.closed
    assert opened == ["http://127.0.0.1:9123"]
    output = capsys.readouterr().out
    assert "Trace viewer: http://127.0.0.1:9123" in output
    assert f"Results: {tmp_path.resolve()}" in output


def test_serve_viewer_no_open_and_browser_failure_are_nonfatal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    first = ScriptedServer()
    monkeypatch.setattr(viewer_server, "create_viewer_server", _return_server(first))
    viewer_server.serve_viewer(
        tmp_path,
        port=8765,
        open_browser=False,
        browser_open=lambda _url: (_ for _ in ()).throw(AssertionError("must not open")),
    )
    assert first.closed

    second = ScriptedServer()
    monkeypatch.setattr(viewer_server, "create_viewer_server", _return_server(second))

    def fail_to_open(_url: str) -> None:
        raise OSError("browser unavailable")

    viewer_server.serve_viewer(
        tmp_path,
        port=8765,
        open_browser=True,
        browser_open=fail_to_open,
    )
    assert second.served and second.closed


def test_create_server_wraps_bind_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def reject_bind(*_args: object, **_kwargs: object) -> None:
        raise OSError("address already in use")

    monkeypatch.setattr(viewer_server, "ViewerHTTPServer", reject_bind)

    with pytest.raises(ViewerServerError, match="address already in use"):
        viewer_server.create_viewer_server(viewer_server.RunResultRepository(tmp_path), 8765)


def test_serve_viewer_wraps_runtime_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    server = ScriptedServer(failure=OSError("socket failed"))
    monkeypatch.setattr(viewer_server, "create_viewer_server", _return_server(server))

    with pytest.raises(ViewerServerError, match="socket failed"):
        viewer_server.serve_viewer(tmp_path, port=8765, open_browser=False)

    assert server.closed
