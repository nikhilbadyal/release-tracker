import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class NPMWatcher(Watcher):
    """
    Watcher for NPM packages.

    Repo format: "package-name" or "@scope/package-name"
    """

    def __init__(self, registry_url: str = "https://registry.npmjs.org") -> None:
        self.registry_url = registry_url.rstrip("/")

    def get_source_url(self, repo_id: str) -> str:
        """Generate the NPM package URL."""
        return f"https://www.npmjs.com/package/{repo_id}"

    def fetch_latest_release(self, package: str) -> ReleaseInfo:
        """
        Fetch the latest version from NPM registry.

        Args:
            package_name: NPM package name (e.g., "express" or "@types/node")
        """
        # Handle scoped packages - URL encode the @ symbol
        if package.startswith("@"):
            package = package.replace("@", "%40")

        url = f"{self.registry_url}/{package}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch NPM data for {package}: {e}"
            raise ValueError(msg) from e

        # Get the latest version
        latest_version = data.get("dist-tags", {}).get("latest")
        if not latest_version:
            msg = f"No latest version found for {package}"
            raise ValueError(msg)

        # Get version-specific data
        version_data = data.get("versions", {}).get(latest_version, {})
        if not version_data:
            msg = f"No data found for version {latest_version} of {package}"
            raise ValueError(msg)

        # Create assets from the dist information
        assets: list[ReleaseAsset] = []
        dist = version_data.get("dist", {})
        if dist.get("tarball"):
            tarball_name = f"{package}-{latest_version}.tgz"
            assets.append(
                ReleaseAsset(
                    name=tarball_name,
                    download_url=dist["tarball"],
                    api_url=dist["tarball"],
                ),
            )

        # Package metadata
        data.get("name", package)
        homepage = data.get("homepage", "")
        repository = data.get("repository", {})

        # If there's a repository URL, include it as an asset
        if isinstance(repository, dict) and repository.get("url"):
            repo_url = repository["url"]
            # Clean up common git URL formats
            repo_url = repo_url.removeprefix("git+")
            repo_url = repo_url.removesuffix(".git")

            assets.append(
                ReleaseAsset(
                    name="Source Code",
                    download_url=repo_url,
                    api_url=repo_url,
                ),
            )

        # Homepage as asset if available
        if homepage and homepage != repo_url:
            assets.append(
                ReleaseAsset(
                    name="Homepage",
                    download_url=homepage,
                    api_url=homepage,
                ),
            )

        return ReleaseInfo(tag=latest_version, assets=assets, source_url=self.get_source_url(package))
