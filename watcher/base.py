from abc import ABC, abstractmethod


class ReleaseAsset:
    def __init__(self, name: str, download_url: str, api_url: str) -> None:
        self.name = name
        self.download_url = download_url
        self.api_url = api_url


class ReleaseInfo:
    def __init__(self, tag: str, assets: list[ReleaseAsset], source_url: str | None = None) -> None:
        self.tag = tag
        self.assets = assets
        self.source_url = source_url


class Watcher(ABC):
    @abstractmethod
    def fetch_latest_release(self, repo: str) -> ReleaseInfo:
        pass

    @abstractmethod
    def get_source_url(self, repo_id: str) -> str:
        """Generate the source URL for a repository."""
