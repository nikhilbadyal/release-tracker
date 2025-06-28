import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher

STATUS_OK = 200
STATUS_NOT_FOUND = 404


class PyPIWatcher(Watcher):
    """Watcher for PyPI package releases."""

    def __init__(self) -> None:
        """Initialize PyPI watcher. No authentication required for PyPI API."""

    def get_source_url(self, repo_id: str) -> str:
        """Generate the PyPI package URL."""
        return f"https://pypi.org/project/{repo_id}/"

    def fetch_latest_release(self, package: str) -> ReleaseInfo:
        """
        Fetch the latest release for a PyPI package.

        Args:
            package: The PyPI package name (e.g., 'requests', 'django')

        Returns
        -------
            ReleaseInfo with the latest version and available distribution files

        Raises
        ------
            ValueError: If package not found or API request fails
        """
        url = f"https://pypi.org/pypi/{package}/json"

        try:
            response = requests.get(url, timeout=10)
        except requests.RequestException as e:
            msg = f"Failed to fetch PyPI data for {package}: {e}"
            raise ValueError(msg) from e

        if response.status_code != STATUS_OK:
            if response.status_code == STATUS_NOT_FOUND:
                msg = f"Package '{package}' not found on PyPI"
            else:
                msg = f"Failed to fetch PyPI data for {package}: {response.status_code} - {response.text}"
            raise ValueError(msg)

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as e:
            msg = f"Invalid JSON response from PyPI for {package}: {e}"
            raise ValueError(msg) from e

        # Extract version from the 'info' section
        version = data.get("info", {}).get("version")
        if not version:
            msg = f"No version information found for {package}"
            raise ValueError(msg)

        # Extract assets from the 'urls' section (files for the latest version)
        assets: list[ReleaseAsset] = []
        for file_info in data.get("urls", []):
            filename = file_info.get("filename")
            download_url = file_info.get("url")

            if filename and download_url:
                # PyPI uses the same URL for both download and API access
                assets.append(
                    ReleaseAsset(
                        name=filename,
                        download_url=download_url,
                        api_url=download_url,
                    ),
                )

        return ReleaseInfo(tag=version, assets=assets, source_url=self.get_source_url(package))
