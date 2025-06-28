from urllib.parse import quote

import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher

status_okay = 200


class GitLabWatcher(Watcher):
    def __init__(self, token: str | None = None, base_url: str = "https://gitlab.com/api/v4") -> None:
        self.base_url = base_url
        self.headers = {"PRIVATE-TOKEN": token} if token else {}

    def get_source_url(self, repo_id: str) -> str:
        """Generate the GitLab repository URL."""
        gitlab_base = self.base_url[:-7] if self.base_url.endswith("/api/v4") else "https://gitlab.com"
        return f"{gitlab_base}/{repo_id}"

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

        # Add source code assets (zip, tar.gz, tar.bz2, tar)
        for source in latest.get("assets", {}).get("sources", []):
            name = f"{repo.split('/')[-1]}-{tag_name}.{source['format']}"
            download_url = source["url"]
            assets.append(ReleaseAsset(name=name, download_url=download_url, api_url=download_url))

        # Add custom asset links
        for link in latest.get("assets", {}).get("links", []):
            name = link["name"]
            download_url = link["url"]

            # If there's a direct_asset_url, use that for better download experience
            if link.get("direct_asset_url"):
                download_url = link["direct_asset_url"]

            # Use the original link URL as api_url for reference
            api_url = link["url"]
            assets.append(ReleaseAsset(name=name, download_url=download_url, api_url=api_url))

        return ReleaseInfo(tag=tag_name, assets=assets, source_url=self.get_source_url(repo))
