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
from watcher.fdroid import FdroidWatcher
from watcher.github import GitHubWatcher
from watcher.gitlab import GitLabWatcher
from watcher.pypi import PyPIWatcher


def build_watcher(watcher_type: str, config: dict[str, Any]) -> Watcher:
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
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


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
