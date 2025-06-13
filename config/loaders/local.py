from pathlib import Path
from typing import Any

import yaml

from .base import ConfigLoader


class LocalConfigLoader(ConfigLoader):
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            msg = f"Config file not found: {self.path}"
            raise FileNotFoundError(msg)

        try:
            with self.path.open() as f:
                config = yaml.safe_load(f)
                if config is None:
                    msg = f"Config file is empty or contains only whitespace: {self.path}"
                    raise ValueError(msg)
                return config  # type: ignore[no-any-return]
        except yaml.YAMLError as e:
            msg = f"Invalid YAML in config file {self.path}: {e}"
            raise ValueError(msg) from e
