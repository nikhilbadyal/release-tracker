import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class WordPressPluginWatcher(Watcher):
    """
    Watcher for WordPress plugins from the official repository.

    Repo format: "plugin-slug" (e.g., "akismet", "contact-form-7")
    """

    def __init__(self, api_url: str = "https://api.wordpress.org/plugins/info/1.0") -> None:
        self.api_url = api_url

    def get_source_url(self, repo_id: str) -> str:
        """Generate the WordPress plugin URL."""
        return f"https://wordpress.org/plugins/{repo_id}/"

    def fetch_latest_release(self, plugin: str) -> ReleaseInfo:
        """
        Fetch the latest version from WordPress Plugin Directory.

        Args:
            plugin: WordPress plugin slug (e.g., "akismet")
        """
        params = {
            "action": "plugin_information",
            "slug": plugin,
            "fields": {
                "description": False,
                "installation": False,
                "faq": False,
                "screenshots": False,
                "changelog": False,
                "reviews": False,
                "sections": False,
                "tags": False,
                "versions": True,
                "donate_link": False,
                "banners": False,
                "icons": False,
                "active_installs": False,
                "short_description": False,
            },
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch WordPress plugin data for {plugin}: {e}"
            raise ValueError(msg) from e

        if "error" in data:
            msg = f"WordPress plugin '{plugin}' not found"
            raise ValueError(msg)

        version = data.get("version")
        if not version:
            msg = f"No version information found for WordPress plugin {plugin}"
            raise ValueError(msg)

        # WordPress plugins typically have a download link
        download_link = data.get("download_link", "")
        assets = []
        if download_link:
            assets.append(
                ReleaseAsset(
                    name=f"{plugin}-{version}.zip",
                    download_url=download_link,
                    api_url=download_link,
                ),
            )

        return ReleaseInfo(tag=version, assets=assets, source_url=self.get_source_url(plugin))


class WordPressThemeWatcher(Watcher):
    """
    Watcher for WordPress themes from the official repository.

    Repo format: "theme-slug" (e.g., "twentytwentyfour", "astra")
    """

    def __init__(self, api_url: str = "https://api.wordpress.org/themes/info/1.2/") -> None:
        self.api_url = api_url

    def get_source_url(self, theme_slug: str) -> str:
        """Generate the WordPress theme URL."""
        return f"https://wordpress.org/themes/{theme_slug}/"

    def fetch_latest_release(self, theme_slug: str) -> ReleaseInfo:
        """
        Fetch the latest version from WordPress Theme Directory.

        Args:
            theme_slug: WordPress theme slug (e.g., "twentytwentyfour")
        """
        params = {
            "action": "theme_information",
            "request[slug]": theme_slug,
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch WordPress theme data for {theme_slug}: {e}"
            raise ValueError(msg) from e

        version = data.get("version")
        download_link = data.get("download_link")

        if not version or not download_link:
            msg = f"Theme data for {theme_slug} missing version or download_link"
            raise ValueError(msg)

        asset = ReleaseAsset(
            name=f"{theme_slug}-{version}.zip",
            download_url=download_link,
            api_url=download_link,
        )

        return ReleaseInfo(tag=version, assets=[asset], source_url=self.get_source_url(theme_slug))
