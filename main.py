import os
from pathlib import Path
from typing import TYPE_CHECKING, cast

from config.loader import load_config
from env_parser import resolve_env_placeholders_recursive
from render_message import RenderFormat, render_message
from utils import build_watcher, download_asset, get_backend, get_notifier

if TYPE_CHECKING:
    from watcher.base import ReleaseInfo, Watcher


def main() -> None:  # noqa: C901,PLR0915,PLR0912
    config = load_config()
    repos = config["repos"]
    watchers_conf = config["watchers"]

    backend = get_backend(config["persistence"])
    notifiers = [get_notifier(nconf) for nconf in config.get("notifiers", [])]

    watcher_cache: dict[str, Watcher] = {}

    for entry in repos:
        print(f"🔍 Processing {entry}")
        repo_id = entry["repo"]
        watcher_key = entry["watcher"]
        override = entry.get("config", {})

        base_conf = watchers_conf[watcher_key]
        watcher_type = base_conf["type"]
        merged_conf = resolve_env_placeholders_recursive({**base_conf.get("config", {}), **override})

        # Cache watcher instances by config hash to avoid rebuilds
        cache_key = f"{watcher_key}:{hash(frozenset(merged_conf.items()))}"
        if cache_key not in watcher_cache:
            watcher_cache[cache_key] = build_watcher(watcher_type, merged_conf)

        watcher = watcher_cache[cache_key]

        try:
            release: ReleaseInfo | None = watcher.fetch_latest_release(repo_id)
        except Exception as e:
            print(f"⚠️  Failed to fetch release for {repo_id}: {e}")
            continue

        if not release:
            print(f"ℹ️  No releases found for {repo_id}")  # noqa: RUF001
            continue

        last_tag = backend.get_last_release(watcher_key + "_" + repo_id)
        force_notify = os.getenv("FORCE_NOTIFY")
        if last_tag == release.tag and not force_notify:
            print(f"✅ Already up-to-date: {repo_id} @ {release.tag}")
            continue
        if last_tag == release.tag:
            print(
                f"🔁 FORCE_NOTIFY is {force_notify} — re-notifying for {repo_id} @ {release.tag} (no version change)",
            )
        else:
            print(f"🆕 New release detected for {repo_id}")
            print(f"📦 Old: {last_tag}")
            print(f"📦 New: {release.tag}")

        Path("downloads").mkdir(exist_ok=True)

        attachment_paths: list[Path] = []
        upload_assets: bool = merged_conf.get("upload_assets", config.get("upload_assets", False))

        for asset in release.assets:
            if upload_assets:
                filename = Path("downloads") / asset.name
                try:
                    download_asset(asset.api_url, filename, token=merged_conf.get("token"))
                    attachment_paths.append(filename)
                except Exception as e:
                    print(f"❌ Failed to download {asset.name} for {repo_id}: {e}")

        for notifier in notifiers:
            format_pref = cast("RenderFormat", getattr(notifier, "message_format", "text"))
            message_body = render_message(repo_id, release, render_format=format_pref)

            notify_status = notifier.send(
                title=f"New Release: {repo_id}",
                body=message_body,
                attachments=attachment_paths,
            )
            if not notify_status:
                print(f"❌ Notification failed for {repo_id} via {type(notifier).__name__}")
            else:
                print(f"📣 Notification sent for {repo_id} via {type(notifier).__name__}")

        backend.set_last_release(watcher_key + "_" + repo_id, release.tag)


if __name__ == "__main__":
    main()
