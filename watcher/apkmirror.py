from typing import Any

import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class APKMirrorWatcher(Watcher):
    def __init__(self, config: dict[str, Any]) -> None:
        self.auth_token = config.get("auth_token", "YXBpLWFwa3VwZGF0ZXI6cm01cmNmcnVVakt5MDRzTXB5TVBKWFc4")
        self.user_agent = config.get("user_agent", "release-tracker")
        self.api_url = config.get("api_url", "https://www.apkmirror.com/wp-json/apkm/v1/app_exists/")

    def fetch_latest_release(self, repo_id: str) -> ReleaseInfo:
        headers = {
            "Authorization": f"Basic {self.auth_token}",
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
        }
        payload = {"pnames": [repo_id]}

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            print(f"❌ Error querying APKMirror for {repo_id}: {e}")
            raise

        apps = result.get("data", [])
        if not apps:
            print(f"ℹ️ No data found for {repo_id} on APKMirror.")
            msg = f"No data found for {repo_id} on APKMirror."
            raise ValueError(msg)

        app_info = apps[0]
        if not app_info.get("exists"):
            print(f"❌ App '{repo_id}' not found on APKMirror.")
            msg = f"App '{repo_id}' not found on APKMirror."
            raise ValueError(msg)

        release = app_info.get("release")
        if not release:
            print(f"ℹ️ App '{repo_id}' has no release info.")
            msg = f"App '{repo_id}' has no release info."
            raise ValueError(msg)

        version = release["version"]
        apks = app_info.get("apks", [])
        assets: list[ReleaseAsset] = []

        for apk in apks:
            apk_name = f"{repo_id}_{apk['version_code']}.apk"
            download_link = f"https://www.apkmirror.com{apk['link']}"
            assets.append(ReleaseAsset(name=apk_name, download_url=download_link, api_url=download_link))

        return ReleaseInfo(tag=version, assets=assets)
