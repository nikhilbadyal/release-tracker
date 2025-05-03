from urllib.parse import quote

import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher

status_okay = 200


class GitLabWatcher(Watcher):
    def __init__(self, token: str | None = None, base_url: str = "https://gitlab.com/api/v4") -> None:
        self.base_url = base_url
        self.headers = {"PRIVATE-TOKEN": token} if token else {}

    def fetch_latest_release(self, repo: str) -> ReleaseInfo:
        # GitLab repo format: namespace/project
        encoded_repo = quote(repo, safe="")
        url = f"{self.base_url}/projects/{encoded_repo}/releases"

        resp = requests.get(url, headers=self.headers, timeout=10)
        if resp.status_code != status_okay:
            msg = f"Failed to fetch releases for {repo}: {resp.status_code} - {resp.text}"
            raise ValueError(msg)

        releases = resp.json()
        if not releases:
            msg = f"No releases found for {repo}."
            raise ValueError(msg)

        latest = releases[0]
        tag_name = latest["tag_name"]
        assets: list[ReleaseAsset] = []

        for link in latest.get("assets", {}).get("links", []):
            name = link["name"]
            download_url = link["url"]
            # GitLab doesn't provide an API URL for direct asset downloading like GitHub
            assets.append(ReleaseAsset(name=name, download_url=download_url, api_url=download_url))

        return ReleaseInfo(tag=tag_name, assets=assets)
