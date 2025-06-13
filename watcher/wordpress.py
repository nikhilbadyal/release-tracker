import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class WordPressWatcher(Watcher):
    """
    Watcher for WordPress plugins from the official repository.

    Repo format: "plugin-slug" (e.g., "akismet", "contact-form-7")
    """

    def __init__(self, api_url: str = "https://api.wordpress.org/plugins/info/1.2") -> None:
        self.api_url = api_url

    def fetch_latest_release(self, plugin_slug: str) -> ReleaseInfo:
        """
        Fetch the latest version from WordPress Plugin Directory.

        Args:
            plugin_slug: WordPress plugin slug (e.g., "akismet")
        """
        # WordPress API parameters
        params = {
            "action": "plugin_information",
            "request[slug]": plugin_slug,
            "request[fields][versions]": "1",
            "request[fields][download_link]": "1",
            "request[fields][homepage]": "1",
            "request[fields][tags]": "1",
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            plugin_data = response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch WordPress plugin {plugin_slug}: {e}"
            raise ValueError(msg) from e

        # Check if plugin exists
        if "error" in plugin_data:
            msg = f"WordPress plugin {plugin_slug} not found: {plugin_data.get('error', 'Unknown error')}"
            raise ValueError(msg)

        # Extract plugin information
        latest_version = plugin_data.get("version")
        if not latest_version:
            msg = f"No version information found for WordPress plugin {plugin_slug}"
            raise ValueError(msg)

        plugin_data.get("name", plugin_slug)
        download_link = plugin_data.get("download_link", "")
        homepage = plugin_data.get("homepage", "")

        # Create assets
        assets = []

        # Main plugin download
        if download_link:
            assets.append(
                ReleaseAsset(
                    name=f"{plugin_slug}.{latest_version}.zip",
                    download_url=download_link,
                    api_url=download_link,
                ),
            )

        # Plugin page on WordPress.org
        plugin_page_url = f"https://wordpress.org/plugins/{plugin_slug}/"
        assets.append(
            ReleaseAsset(
                name="WordPress Plugin Page",
                download_url=plugin_page_url,
                api_url=plugin_page_url,
            ),
        )

        # Homepage if different from plugin page
        if homepage and homepage != plugin_page_url:
            assets.append(
                ReleaseAsset(
                    name="Plugin Homepage",
                    download_url=homepage,
                    api_url=homepage,
                ),
            )

        # Development version if available
        svn_url = f"https://plugins.svn.wordpress.org/{plugin_slug}/trunk/"
        assets.append(
            ReleaseAsset(
                name="Development Version (SVN)",
                download_url=svn_url,
                api_url=svn_url,
            ),
        )

        # Historical versions if available
        versions = plugin_data.get("versions", {})
        if isinstance(versions, dict) and len(versions) > 1:
            # Add link to all versions
            versions_url = f"https://wordpress.org/plugins/{plugin_slug}/advanced/"
            assets.append(
                ReleaseAsset(
                    name="All Versions",
                    download_url=versions_url,
                    api_url=versions_url,
                ),
            )

        return ReleaseInfo(tag=latest_version, assets=assets)
