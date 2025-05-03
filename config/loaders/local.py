from pathlib import Path
from typing import Any

import yaml

from .base import ConfigLoader


class LocalConfigLoader(ConfigLoader):
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        with self.path.open() as f:
            return yaml.safe_load(f)  # type: ignore[no-any-return]
