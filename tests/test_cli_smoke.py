from __future__ import annotations

import pytest

from wallet_evals.cli import main


def test_cli_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    code = main([])
    assert code == 0
    out = capsys.readouterr().out
    assert "wallet_evals" in out


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--version"])
    assert code == 0
    out = capsys.readouterr().out.strip()
    assert out
