from typing import Any

import requests
from bs4 import BeautifulSoup

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class FdroidWatcher(Watcher):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        if not config:
            config = {}
        self.base_url: str = config.get("base_url", "https://f-droid.org/en/packages/")
        self.repo_url: str = config.get("repo_url", "https://f-droid.org/repo/")
        self.user_agent: str = config.get("user_agent", "release-tracker")

    def get_source_url(self, repo_id: str) -> str:
        """Generate the F-Droid package URL."""
        return f"https://f-droid.org/en/packages/{repo_id}/"

    def fetch_latest_release(self, repo_id: str) -> ReleaseInfo:
        package_url: str = f"{self.base_url}{repo_id}/"
        headers: dict[str, str] = {"User-Agent": self.user_agent}

        try:
            response = requests.get(package_url, headers=headers, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Error fetching F-Droid page for {repo_id}: {e}")
            raise

        soup = BeautifulSoup(response.text, "lxml")
        latest_section = soup.find("li", id="latest")
        if not latest_section:
            msg = f"No 'latest' section found for {repo_id} on F-Droid."
            raise ValueError(msg)

        # Extract version info
        header = latest_section.find("a")
        if not header:
            msg = f"No version header found in F-Droid page for {repo_id}."
            raise ValueError(msg)
        latest_version = header.get("name", "unknown")

        container = latest_section.find("p", class_="package-version-download")
        if not container:
            msg = "No download container found"
            raise ValueError(msg)

        # Now find the 'Download APK' link inside that
        apk_link = container.find("a", string=lambda s: s and "Download APK" in s)
        if not apk_link:
            msg = "Download APK link not found"
            raise ValueError(msg)

        download_url = apk_link.get("href")

        asset = ReleaseAsset(
            name=repo_id,
            download_url=download_url,
            api_url=package_url,
        )
        return ReleaseInfo(tag=latest_version, assets=[asset], source_url=self.get_source_url(repo_id))
