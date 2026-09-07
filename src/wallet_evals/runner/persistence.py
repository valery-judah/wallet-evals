from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from urllib.parse import quote

from wallet_evals.runner.models import RunResult, SavedRunResultIdentity


class JsonFileRunResultStore:
    """Save each complete run result as one human-inspectable JSON file."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def save(self, result: RunResult) -> SavedRunResultIdentity:
        self._directory.mkdir(parents=True, exist_ok=True)
        filename = f"{quote(result.run_id, safe='')}.json"
        destination = self._directory / filename
        if destination.exists():
            raise FileExistsError(f"run result already exists: {destination}")

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._directory,
                prefix=f".{filename}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(
                    {
                        "schema_version": "0.1",
                        "run_result": result.model_dump(mode="json"),
                    },
                    temporary_file,
                    ensure_ascii=False,
                    indent=2,
                )
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.link(temporary_path, destination)
            temporary_path.unlink()
            temporary_path = None
            directory_fd = os.open(self._directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        return SavedRunResultIdentity(
            run_id=result.run_id,
            artifact_id=str(destination.resolve()),
        )
