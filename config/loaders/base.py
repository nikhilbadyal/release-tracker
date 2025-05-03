from abc import ABC, abstractmethod
from typing import Any


class ConfigLoader(ABC):
    @abstractmethod
    def load(self) -> dict[str, Any]: ...
