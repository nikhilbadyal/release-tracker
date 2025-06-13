import requests

from watcher.base import ReleaseAsset, ReleaseInfo, Watcher


class MavenCentralWatcher(Watcher):
    """
    Watcher for Maven Central artifacts.

    Repo format: "groupId:artifactId" (e.g., "org.springframework:spring-core")
    """

    def __init__(self, base_url: str = "https://search.maven.org") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/solrsearch/select"

    def fetch_latest_release(self, artifact: str) -> ReleaseInfo:
        """
        Fetch the latest version from Maven Central.

        Args:
            artifact: Maven artifact in format "groupId:artifactId"
        """
        if ":" not in artifact:
            msg = f"Invalid Maven artifact format: {artifact}. Expected 'groupId:artifactId'"
            raise ValueError(msg)

        group_id, artifact_id = artifact.split(":", 1)

        # Search for the latest version
        params: dict[str, str | int] = {
            "q": f"g:{group_id} AND a:{artifact_id}",
            "rows": 1,
            "wt": "json",
            "sort": "timestamp desc",  # Get the latest version
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            search_data = response.json()
        except requests.RequestException as e:
            msg = f"Failed to search Maven Central for {artifact}: {e}"
            raise ValueError(msg) from e

        # Parse search results
        response_data = search_data.get("response", {})
        docs = response_data.get("docs", [])

        if not docs:
            msg = f"No artifacts found for {artifact} in Maven Central"
            raise ValueError(msg)

        latest_artifact = docs[0]

        # Extract version and metadata
        version = latest_artifact.get("latestVersion", latest_artifact.get("v"))
        if not version:
            msg = f"No version information found for {artifact}"
            raise ValueError(msg)

        # Build download URLs
        group_path = group_id.replace(".", "/")
        base_artifact_url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}"

        # Create assets for common Maven artifact types
        assets = []

        # JAR file (main artifact)
        jar_url = f"{base_artifact_url}/{artifact_id}-{version}.jar"
        assets.append(
            ReleaseAsset(
                name=f"{artifact_id}-{version}.jar",
                download_url=jar_url,
                api_url=jar_url,
            ),
        )

        # Sources JAR
        sources_url = f"{base_artifact_url}/{artifact_id}-{version}-sources.jar"
        assets.append(
            ReleaseAsset(
                name=f"{artifact_id}-{version}-sources.jar",
                download_url=sources_url,
                api_url=sources_url,
            ),
        )

        # Javadoc JAR
        javadoc_url = f"{base_artifact_url}/{artifact_id}-{version}-javadoc.jar"
        assets.append(
            ReleaseAsset(
                name=f"{artifact_id}-{version}-javadoc.jar",
                download_url=javadoc_url,
                api_url=javadoc_url,
            ),
        )

        # POM file
        pom_url = f"{base_artifact_url}/{artifact_id}-{version}.pom"
        assets.append(
            ReleaseAsset(
                name=f"{artifact_id}-{version}.pom",
                download_url=pom_url,
                api_url=pom_url,
            ),
        )

        # Maven Central page
        central_page_url = f"{self.base_url}/artifact/{group_id}/{artifact_id}/{version}/jar"
        assets.append(
            ReleaseAsset(
                name="Maven Central Page",
                download_url=central_page_url,
                api_url=central_page_url,
            ),
        )

        return ReleaseInfo(tag=version, assets=assets)
