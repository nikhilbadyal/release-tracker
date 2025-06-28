import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher

status_200 = 200


class GitHubWatcher(Watcher):
    def __init__(self, token: str | None = None) -> None:
        self.headers = {"Authorization": f"token {token}"} if token else {}

    def get_source_url(self, repo_id: str) -> str:
        """Generate the GitHub repository URL."""
        return f"https://github.com/{repo_id}"

    def fetch_latest_release(self, repo: str) -> ReleaseInfo:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        r = requests.get(url, headers=self.headers, timeout=10)
        if r.status_code != status_200:
            msg = f"Failed to fetch latest release for {repo}: {r.status_code} - {r.text}"
            raise ValueError(
                msg,
            )

        data = r.json()
        assets = [
            ReleaseAsset(
                name=asset["name"],
                download_url=asset["browser_download_url"],
                api_url=asset["url"],
            )
            for asset in data.get("assets", [])
        ]
        return ReleaseInfo(tag=data["tag_name"], assets=assets, source_url=self.get_source_url(repo))
