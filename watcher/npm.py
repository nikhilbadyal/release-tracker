import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class NPMWatcher(Watcher):
    """
    Watcher for NPM packages.

    Repo format: "package-name" or "@scope/package-name"
    """

    def __init__(self, registry_url: str = "https://registry.npmjs.org") -> None:
        self.registry_url = registry_url.rstrip("/")

    def fetch_latest_release(self, package_name: str) -> ReleaseInfo:
        """
        Fetch the latest version from NPM registry.

        Args:
            package_name: NPM package name (e.g., "express" or "@types/node")
        """
        # Handle scoped packages - URL encode the @ symbol
        if package_name.startswith("@"):
            package_name = package_name.replace("@", "%40")

        package_url = f"{self.registry_url}/{package_name}"

        try:
            response = requests.get(package_url, timeout=10)
            response.raise_for_status()
            package_data = response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch NPM package {package_name}: {e}"
            raise ValueError(msg) from e

        # Get the latest version info
        latest_version = package_data.get("dist-tags", {}).get("latest")
        if not latest_version:
            msg = f"No latest version found for NPM package {package_name}"
            raise ValueError(msg)

        versions = package_data.get("versions", {})
        version_info = versions.get(latest_version)
        if not version_info:
            msg = f"Version info not found for {package_name}@{latest_version}"
            raise ValueError(msg)

        # Get distribution info
        dist_info = version_info.get("dist", {})
        tarball_url = dist_info.get("tarball", "")
        dist_info.get("shasum", "")

        # Package metadata
        package_display_name = package_data.get("name", package_name)
        homepage = package_data.get("homepage", "")
        repository = package_data.get("repository", {})

        # Create assets
        assets = []

        # Tarball asset
        if tarball_url:
            assets.append(
                ReleaseAsset(
                    name=f"{package_display_name}-{latest_version}.tgz",
                    download_url=tarball_url,
                    api_url=package_url,
                ),
            )

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

        return ReleaseInfo(tag=latest_version, assets=assets)
