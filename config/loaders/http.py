from typing import Any

import requests
import yaml
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .base import ConfigLoader


class HTTPConfigLoader(ConfigLoader):
    def __init__(self, url: str) -> None:
        self.url = url

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def load(self) -> dict[str, Any]:
        try:
            resp = requests.get(self.url, timeout=10)
            resp.raise_for_status()

            if not resp.text.strip():
                msg = f"Empty response from config URL: {self.url}"
                raise ValueError(msg)

            config = yaml.safe_load(resp.text)
            if config is None:
                msg = f"Config from URL contains only whitespace or is empty: {self.url}"
                raise ValueError(msg)
        except yaml.YAMLError as e:
            msg = f"Invalid YAML from config URL {self.url}: {e}"
            raise ValueError(msg) from e
        except requests.RequestException as e:
            msg = f"Failed to fetch config from {self.url}: {e}"
            raise ConnectionError(msg) from e
        else:
            return config  # type: ignore[no-any-return]
