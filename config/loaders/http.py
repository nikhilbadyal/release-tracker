from typing import Any

import requests
import yaml

from .base import ConfigLoader


class HTTPConfigLoader(ConfigLoader):
    def __init__(self, url: str) -> None:
        self.url = url

    def load(self) -> dict[str, Any]:
        resp = requests.get(self.url, timeout=10)
        resp.raise_for_status()
        return yaml.safe_load(resp.text)  # type: ignore[no-any-return]
