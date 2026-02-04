from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from notifier.apprise import AppriseNotifier
from notifier.base import Notifier
from persistence.base import PersistenceBackend
from persistence.redis_store import RedisStore
from watcher.apkmirror import APKMirrorWatcher
from watcher.apkpure import APKPureWatcher
from watcher.base import Watcher
from watcher.dockerhub import DockerHubWatcher
from watcher.fdroid import FdroidWatcher
from watcher.github import GitHubWatcher
from watcher.gitlab import GitLabWatcher
from watcher.homebrew import HomebrewWatcher
from watcher.maven import MavenCentralWatcher
from watcher.npm import NPMWatcher
from watcher.pypi import PyPIWatcher

if TYPE_CHECKING:
    from collections.abc import Callable


def build_watcher(watcher_type: str, config: dict[str, Any]) -> Watcher:
    """Build a watcher instance based on the watcher type and configuration."""
    watcher_builders: dict[str, Callable[[], Watcher]] = {
        "github": lambda: GitHubWatcher(token=config.get("token")),
        "gitlab": lambda: GitLabWatcher(
            token=config.get("token"),
            base_url=config.get("base_url", "https://gitlab.com/api/v4"),
        ),
        "apkmirror": lambda: APKMirrorWatcher(config=config),
        "apkpure": lambda: APKPureWatcher(user_agent=config.get("user_agent")),
        "fdroid": FdroidWatcher,
        "pypi": PyPIWatcher,
        "dockerhub": lambda: DockerHubWatcher(token=config.get("token")),
        "npm": lambda: NPMWatcher(registry_url=config.get("registry_url", "https://registry.npmjs.org")),
        "maven": lambda: MavenCentralWatcher(base_url=config.get("base_url", "https://search.maven.org")),
        "homebrew": lambda: HomebrewWatcher(api_url=config.get("api_url", "https://formulae.brew.sh/api")),
    }

    if watcher_type not in watcher_builders:
        msg = f"[ERROR] Watcher type '{watcher_type}' not supported"
        raise NotImplementedError(msg)

    return watcher_builders[watcher_type]()


def get_backend(config: dict[str, Any]) -> PersistenceBackend:
    if config["type"] == "redis":
        return RedisStore(**config["config"])
    msg = f"[ERROR] Persistence backend '{config['type']}' not supported"
    raise NotImplementedError(msg)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def download_asset(url: str, dest: Path, token: str | None = None) -> None:
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers, stream=True, timeout=10)
    response.raise_for_status()

    with Path(dest).open("wb") as f:
        f.writelines(response.iter_content(chunk_size=8192))


def get_notifier(config: dict[str, Any]) -> Notifier:
    notifier_type = config.get("type")
    if notifier_type == "apprise":
        # Pass the format in the config so AppriseNotifier can handle it properly
        notifier_config = config["config"].copy()
        if "format" in config:
            notifier_config["format"] = config["format"]
        notifier = AppriseNotifier(notifier_config)
    else:
        msg = f"Unsupported notifier type: {notifier_type}"
        raise ValueError(msg)

    return notifier
