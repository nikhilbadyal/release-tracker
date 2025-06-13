import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class DockerHubWatcher(Watcher):
    """
    Watcher for Docker Hub container images.

    Repo format: "library/nginx" or "username/repository"
    """

    def __init__(self, token: str | None = None) -> None:
        self.base_url = "https://hub.docker.com/v2/repositories"
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def fetch_latest_release(self, repo: str) -> ReleaseInfo:
        """
        Fetch the latest image tag from Docker Hub.

        Args:
            repo: Docker repository in format "namespace/repository" or "library/repository"
        """
        # Handle official images (they're under 'library' namespace)
        if "/" not in repo:
            repo = f"library/{repo}"

        # Get repository info first to check if it exists
        repo_url = f"{self.base_url}/{repo}"

        try:
            repo_response = requests.get(repo_url, headers=self.headers, timeout=10)
            repo_response.raise_for_status()
        except requests.RequestException as e:
            msg = f"Failed to fetch Docker Hub repository {repo}: {e}"
            raise ValueError(msg) from e

        # Get tags for the repository
        tags_url = f"{self.base_url}/{repo}/tags"
        params: dict[str, str | int] = {
            "page_size": 50,  # Get more tags to find latest non-latest tag
            "ordering": "-last_updated",  # Order by most recent
        }

        try:
            tags_response = requests.get(tags_url, headers=self.headers, params=params, timeout=10)
            tags_response.raise_for_status()
            tags_data = tags_response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch tags for Docker Hub repository {repo}: {e}"
            raise ValueError(msg) from e

        results = tags_data.get("results", [])
        if not results:
            msg = f"No tags found for Docker Hub repository {repo}"
            raise ValueError(msg)

        # Find the latest semantic version tag (avoid 'latest', 'main', etc.)
        latest_tag = None
        for tag_info in results:
            tag_name = tag_info["name"]

            # Skip common non-version tags
            skip_tags = {"latest", "main", "master", "dev", "development", "staging", "nightly"}
            if tag_name.lower() in skip_tags:
                continue

            # Prefer tags that look like version numbers
            if any(char.isdigit() for char in tag_name):
                latest_tag = tag_info
                break

        # Fallback to first tag if no version-like tag found
        if not latest_tag:
            latest_tag = results[0]

        tag_name = latest_tag["name"]

        # Create asset representing the Docker image
        pull_command = f"docker pull {repo}:{tag_name}"
        image_url = f"https://hub.docker.com/r/{repo}/tags?name={tag_name}"

        # Docker images don't have traditional "downloadable assets"
        # but we can provide the pull command and registry info
        assets = [
            ReleaseAsset(
                name=f"{repo}:{tag_name}",
                download_url=pull_command,
                api_url=image_url,
            ),
        ]

        return ReleaseInfo(tag=tag_name, assets=assets)
