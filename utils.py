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
from watcher.github import GitHubWatcher
from watcher.gitlab import GitLabWatcher


def build_watcher(watcher_type: str, config: dict[str, Any]) -> Watcher:
    if watcher_type == "github":
        return GitHubWatcher(token=config.get("token"))
    if watcher_type == "gitlab":
        return GitLabWatcher(token=config.get("token"), base_url=config.get("base_url", "https://gitlab.com/api/v4"))
    if watcher_type == "apkmirror":
        return APKMirrorWatcher(config=config)
    if watcher_type == "apkpure":
        return APKPureWatcher(user_agent=config.get("user_agent"))
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
        notifier = AppriseNotifier(config["config"])
    else:
        msg = f"Unsupported notifier type: {notifier_type}"
        raise ValueError(msg)

    # Attach format preference to the notifier instance (e.g., "markdown", "html", "text")
    notifier.message_format = config.get("format", "text").lower()
    return notifier
