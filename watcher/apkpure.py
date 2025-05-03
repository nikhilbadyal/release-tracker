import requests
from bs4 import BeautifulSoup

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher

status_200 = 200


class APKPureWatcher(Watcher):
    def __init__(self, user_agent: str | None = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)") -> None:
        self.headers = {
            "User-Agent": user_agent,
        }

    def fetch_latest_release(self, repo: str) -> ReleaseInfo:
        url = f"https://apkpure.net/p/{repo}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            msg = f"Failed to fetch the page: {e}"
            raise ValueError(msg) from e

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract the app name
        app_name_tag = soup.find("h1")
        app_name: str = app_name_tag.get_text(strip=True) if app_name_tag else "App name not found"

        # Extract the latest version
        version_label = soup.find("div", class_="title", string="Latest Version")
        version_value = version_label.find_next_sibling("div", class_="additional-info") if version_label else None
        latest_version = version_value.text.strip() if version_value else None

        if app_name and latest_version:
            asset = ReleaseAsset(
                name=app_name,
                download_url=url,
                api_url=url,
            )
            return ReleaseInfo(tag=latest_version, assets=[asset])

        msg = "Unable to find the app name or latest version on the page."
        raise ValueError(msg)
