import json
from pathlib import Path
from typing import Any

from persistence.base import PersistenceBackend


class FileBackend(PersistenceBackend):
    def __init__(self, file_path: str = "release_tracker.json") -> None:
        self.file_path = file_path
        self.data: dict[str, Any] = {}
        self._load_data()

    def _load_data(self) -> None:
        if Path(self.file_path).exists():
            with Path(self.file_path).open() as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def _save_data(self) -> None:
        with Path(self.file_path).open("w") as f:
            json.dump(self.data, f)

    def get_last_release(self, repo: str) -> str | None:
        return self.data.get(repo)

    def set_last_release(self, repo: str, tag: str) -> None:
        self.data[repo] = tag
        self._save_data()

    def close(self) -> None:
        # I don't need to do anything here since the data is saved automatically
        pass
