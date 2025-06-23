from pathlib import Path
from typing import Any

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
from watcher.wordpress import WordPressWatcher


def build_watcher(watcher_type: str, config: dict[str, Any]) -> Watcher:  # noqa: C901
    if watcher_type == "github":
        return GitHubWatcher(token=config.get("token"))
    if watcher_type == "gitlab":
        return GitLabWatcher(token=config.get("token"), base_url=config.get("base_url", "https://gitlab.com/api/v4"))
    if watcher_type == "apkmirror":
        return APKMirrorWatcher(config=config)
    if watcher_type == "apkpure":
        return APKPureWatcher(user_agent=config.get("user_agent"))
    if watcher_type == "fdroid":
        return FdroidWatcher()
    if watcher_type == "pypi":
        return PyPIWatcher()
    if watcher_type == "dockerhub":
        return DockerHubWatcher(token=config.get("token"))
    if watcher_type == "npm":
        return NPMWatcher(registry_url=config.get("registry_url", "https://registry.npmjs.org"))
    if watcher_type == "maven":
        return MavenCentralWatcher(base_url=config.get("base_url", "https://search.maven.org"))
    if watcher_type == "wordpress":
        return WordPressWatcher(api_url=config.get("api_url", "https://api.wordpress.org/plugins/info/1.2"))
    if watcher_type == "homebrew":
        return HomebrewWatcher(api_url=config.get("api_url", "https://formulae.brew.sh/api"))
    msg = f"[ERROR] Watcher type '{watcher_type}' not supported"
    raise NotImplementedError(msg)


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
