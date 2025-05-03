from abc import ABC, abstractmethod


class PersistenceBackend(ABC):
    @abstractmethod
    def get_last_release(self, repo: str) -> str | None:
        pass

    @abstractmethod
    def set_last_release(self, repo: str, tag: str) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up any resources."""
