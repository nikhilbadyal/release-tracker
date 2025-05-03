from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path


class Notifier(ABC):
    @abstractmethod
    def send(self, title: str, body: str, attachments: Sequence[Path] = ()) -> bool:
        """Send a notification with a title, body, and optional file attachments."""
