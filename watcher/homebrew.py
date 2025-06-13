import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class HomebrewWatcher(Watcher):
    """
    Watcher for Homebrew formulas.

    Repo format: "formula-name" or "tap/formula-name" (e.g., "git", "homebrew/cask/docker")
    """

    def __init__(self, api_url: str = "https://formulae.brew.sh/api") -> None:
        self.api_url = api_url.rstrip("/")

    def fetch_latest_release(self, formula: str) -> ReleaseInfo:
        """
        Fetch the latest version from Homebrew formulae API.

        Args:
            formula: Homebrew formula name (e.g., "git" or "homebrew/cask/docker")
        """
        # Determine if it's a cask or formula
        if "/cask/" in formula or formula.startswith("homebrew/cask/"):
            return self._fetch_cask_release(formula)
        return self._fetch_formula_release(formula)

    def _fetch_formula_release(self, formula_name: str) -> ReleaseInfo:
        """Fetch release info for a Homebrew formula."""
        # Handle tap-prefixed formulas
        if "/" in formula_name:
            # For custom taps, we need to query differently
            # For now, let's handle the common case of homebrew/core formulas
            formula_name = formula_name.split("/")[-1]

        formula_url = f"{self.api_url}/formula/{formula_name}.json"

        try:
            response = requests.get(formula_url, timeout=10)
            response.raise_for_status()
            formula_data = response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch Homebrew formula {formula_name}: {e}"
            raise ValueError(msg) from e

        # Extract version information
        versions = formula_data.get("versions", {})
        latest_version = versions.get("stable")

        if not latest_version:
            msg = f"No stable version found for Homebrew formula {formula_name}"
            raise ValueError(msg)

        # Extract additional metadata
        homepage = formula_data.get("homepage", "")
        formula_data.get("desc", "")

        # Create assets
        assets = []

        # Homebrew install command
        install_command = f"brew install {formula_name}"
        assets.append(
            ReleaseAsset(
                name="Install Command",
                download_url=install_command,
                api_url=formula_url,
            ),
        )

        # Formula page
        formula_page_url = f"https://formulae.brew.sh/formula/{formula_name}"
        assets.append(
            ReleaseAsset(
                name="Homebrew Formula Page",
                download_url=formula_page_url,
                api_url=formula_page_url,
            ),
        )

        # Homepage if available
        if homepage:
            assets.append(
                ReleaseAsset(
                    name="Project Homepage",
                    download_url=homepage,
                    api_url=homepage,
                ),
            )

        # Source URLs if available
        urls = formula_data.get("urls", {})
        stable_url = urls.get("stable", {}).get("url", "")
        if stable_url:
            assets.append(
                ReleaseAsset(
                    name="Source Archive",
                    download_url=stable_url,
                    api_url=stable_url,
                ),
            )

        return ReleaseInfo(tag=latest_version, assets=assets)

    def _fetch_cask_release(self, cask_name: str) -> ReleaseInfo:
        """Fetch release info for a Homebrew cask."""
        # Handle tap-prefixed casks
        if "/" in cask_name:
            cask_name = cask_name.split("/")[-1]

        cask_url = f"{self.api_url}/cask/{cask_name}.json"

        try:
            response = requests.get(cask_url, timeout=10)
            response.raise_for_status()
            cask_data = response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch Homebrew cask {cask_name}: {e}"
            raise ValueError(msg) from e

        # Extract version information
        version = cask_data.get("version")
        if not version:
            msg = f"No version found for Homebrew cask {cask_name}"
            raise ValueError(msg)

        # Extract additional metadata
        homepage = cask_data.get("homepage", "")
        name = cask_data.get("name", [])
        name[0] if name else cask_name

        # Create assets
        assets = []

        # Homebrew install command
        install_command = f"brew install --cask {cask_name}"
        assets.append(
            ReleaseAsset(
                name="Install Command",
                download_url=install_command,
                api_url=cask_url,
            ),
        )

        # Cask page
        cask_page_url = f"https://formulae.brew.sh/cask/{cask_name}"
        assets.append(
            ReleaseAsset(
                name="Homebrew Cask Page",
                download_url=cask_page_url,
                api_url=cask_page_url,
            ),
        )

        # Homepage if available
        if homepage:
            assets.append(
                ReleaseAsset(
                    name="Application Homepage",
                    download_url=homepage,
                    api_url=homepage,
                ),
            )

        # Download URL if available
        url = cask_data.get("url")
        if url:
            assets.append(
                ReleaseAsset(
                    name="Direct Download",
                    download_url=url,
                    api_url=url,
                ),
            )

        return ReleaseInfo(tag=version, assets=assets)
