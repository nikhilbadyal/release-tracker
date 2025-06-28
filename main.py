import os
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import click

from config.loader import load_config
from env_parser import resolve_env_placeholders_recursive
from notifier.base import Notifier
from persistence.base import PersistenceBackend

# noinspection PyUnresolvedReferences
from render_message import RenderFormat, render_message
from utils import build_watcher, download_asset, get_backend, get_notifier

if TYPE_CHECKING:
    from watcher.base import ReleaseInfo, Watcher


def process_assets(release: "ReleaseInfo", upload_assets: bool, token: str | None) -> list[Path]:
    """Downloads assets for a release if upload_assets is True."""
    if not upload_assets:
        return []

    Path("downloads").mkdir(exist_ok=True)
    paths: list[Path] = []
    print(f"⬇️ Processing assets for {release.tag}")
    for asset in release.assets:
        dest = Path("downloads") / asset.name
        try:
            print(f"  Downloading {asset.name}...")
            download_asset(asset.api_url, dest, token=token)
            paths.append(dest)
            print(f"  ✅ Downloaded {asset.name}")
        except Exception as e:
            print(f"  ❌ Failed to download {asset.name}: {e}")
    return paths


def notify_all(repo_id: str, release: "ReleaseInfo", notifiers: list[Notifier], attachments: list[Path]) -> None:
    """Sends notifications for a new release using all configured notifiers."""
    print(f"📣 Sending notifications for {repo_id} @ {release.tag}")
    if not notifiers:
        print("ℹ️ No notifiers configured.")
        return

    for notifier in notifiers:
        # noinspection PyTypeHints
        fmt = cast("RenderFormat", getattr(notifier, "message_format", "text"))
        try:
            body = render_message(repo_id, release, render_format=fmt)
            title = f"New Release: {repo_id}"
            success = notifier.send(title=title, body=body, attachments=attachments)
            if success:
                print(f"✅ Notification sent via {type(notifier).__name__}")
            else:
                print(f"❌ Notification failed via {type(notifier).__name__}")
        except Exception as e:
            print(f"❌ Error rendering message or sending notification via {type(notifier).__name__}: {e}")


class RepoProcessor:
    """Handles the end-to-end process for checking and notifying about a single repository."""

    def __init__(  # noqa: PLR0913
        self,
        repo_entry: dict[str, Any],
        watchers_conf: dict[str, Any],
        watcher_cache: dict[str, "Watcher"],
        backend: PersistenceBackend,
        notifiers: list[Notifier],
        global_upload_assets: bool,
    ) -> None:
        self.repo_entry = repo_entry
        self.watchers_conf = watchers_conf
        self.watcher_cache = watcher_cache
        self.backend = backend
        self.notifiers = notifiers
        self.global_upload_assets = global_upload_assets

        self.repo_id = self.repo_entry["repo"]
        self.watcher_key = self.repo_entry["watcher"]
        self.override_conf = self.repo_entry.get("config", {})
        self.key = f"{self.watcher_key}_{self.repo_id}"  # Key for persistence backend

    def _get_watcher(self) -> "Watcher":
        """Gets or creates the watcher instance from the cache."""
        base_conf = self.watchers_conf[self.watcher_key]
        watcher_type = base_conf["type"]
        # Merge base config with override, then resolve env vars
        merged_conf_raw = {**base_conf.get("config", {}), **self.override_conf}
        self.merged_conf = resolve_env_placeholders_recursive(merged_conf_raw)  # Store for later use (e.g., token)

        # Use a cache key based on the merged, resolved configuration
        try:
            # Create a stable hash for the configuration
            config_items = sorted(self.merged_conf.items()) if self.merged_conf else []
            cache_key = f"{self.watcher_key}:{hash(frozenset(config_items))}"
        except TypeError:
            # Fallback if config contains unhashable types
            cache_key = f"{self.watcher_key}:{id(self.merged_conf)}"

        if cache_key not in self.watcher_cache:
            print(f"🛠️ Building new watcher for {self.repo_id} ({watcher_type})")
            try:
                self.watcher_cache[cache_key] = build_watcher(watcher_type, self.merged_conf)
            except Exception as e:
                print(f"❌ Failed to build watcher for {self.repo_id}: {e}")
                raise
        else:
            print(f"♻️ Using cached watcher for {self.repo_id}")

        return self.watcher_cache[cache_key]

    def _fetch_latest_release(self, watcher: "Watcher") -> "ReleaseInfo | None":
        """Fetches the latest release using the provided watcher."""
        print(f"🌐 Fetching latest release for {self.repo_id}...")
        try:
            release = watcher.fetch_latest_release(self.repo_id)
            if release:
                print(f"✅ Latest release fetched: {release.tag}")
            else:
                print(f"ℹ️ No releases found for {self.repo_id} or watcher returned None.")
        except Exception as e:
            print(f"⚠️  Failed to fetch release for {self.repo_id}: {e}")
            return None
        else:
            return release

    def _is_new_release(self, release: "ReleaseInfo") -> bool:
        """Checks if the fetched release is newer than the last known release."""
        last_tag = self.backend.get_last_release(self.key)
        force_notify = os.getenv("FORCE_NOTIFY") is not None  # Check if env var is set

        if last_tag == release.tag:
            if force_notify:
                print(f"🔁 FORCE_NOTIFY is set — re-notifying for {self.repo_id} @ {release.tag}")
                return True  # Treat as new for notification purposes
            print(f"✅ Already up-to-date: {self.repo_id} @ {release.tag}")
            return False
        print(f"🆕 New release detected for {self.repo_id}")
        print(f"📦 Old: {last_tag if last_tag else 'None'}")
        print(f"📦 New: {release.tag}")
        return True

    # noinspection PyUnreachableCode
    def _process_and_notify(self, release: "ReleaseInfo") -> None:
        """Processes assets and sends notifications for a new release."""
        upload_assets = self.merged_conf.get("upload_assets", self.global_upload_assets)
        asset_token = self.merged_conf.get("token")  # Pass token from merged config if available

        attachments = process_assets(release, upload_assets, asset_token)
        try:
            notify_all(self.repo_id, release, self.notifiers, attachments)
        finally:
            for attachment in attachments:
                try:
                    if attachment.exists():
                        attachment.unlink(missing_ok=True)
                        print(f"🗑️  Cleaned up {attachment.name}")
                except Exception as e:
                    print(f"⚠️  Failed to clean up {attachment.name}: {e}")

    def _update_persistence(self, release: "ReleaseInfo") -> None:
        """Updates the persistence backend with the new release tag."""
        print(f"💾 Updating persistence for {self.repo_id} to {release.tag}")
        try:
            self.backend.set_last_release(self.key, release.tag)
            print("✅ Persistence updated.")
        except Exception as e:
            print(f"❌ Failed to update persistence for {self.repo_id}: {e}")

    def process(self) -> None:
        """Executes the full check and notification flow for this repository entry."""
        print(f"\n--- Processing {self.repo_id} ---")

        try:
            watcher = self._get_watcher()
            release = self._fetch_latest_release(watcher)

            if not release:
                return  # No release to process

            if self._is_new_release(release):
                # Process assets and notify only if it's a new or forced release
                self._process_and_notify(release)
                # Always update persistence for new releases (including forced notifications)
                self._update_persistence(release)

        except Exception as e:
            traceback.print_exc()
            # Catch any unhandled exceptions during the process
            print(f"🔥 An unexpected error occurred while processing {self.repo_id}: {e}")
        finally:
            print(f"--- Finished processing {self.repo_id} ---\n")


def find_repo_watcher_in_config(repo: str, config: dict[str, Any]) -> str | None:
    """Find the watcher type for a repo in the config file."""
    repos = config.get("repos", [])
    for repo_entry in repos:
        if repo_entry.get("repo") == repo:
            return repo_entry.get("watcher")  # type: ignore[no-any-return]
    return None


def check_single_repo(repo: str, watcher_type: str) -> None:
    """Check a single repository for new releases."""
    print(f"🚀 Checking single repository: {repo}")
    config = load_config()

    try:
        backend = get_backend(config.get("persistence", {}))
        print(f"🗄️ Using persistence backend: {type(backend).__name__}")
    except Exception as e:
        print(f"❌ Failed to initialize persistence backend: {e}")
        return

    # Initialize notifiers
    notifiers: list[Notifier] = []
    try:
        notifiers = [get_notifier(nc) for nc in config.get("notifiers", [])]
        print(f"🔔 Initialized {len(notifiers)} notifier(s)")
    except Exception as e:
        print(f"⚠️  Failed to initialize notifiers: {e}")
        notifiers = []

    if not notifiers:
        print("⚠️  No notifiers available - you'll only see console output.")

    # Create a single repo entry - config will be empty, using defaults from config file
    repo_entry = {
        "repo": repo,
        "watcher": watcher_type,
        "config": {},
    }

    watcher_cache: dict[str, Watcher] = {}
    global_upload_assets = config.get("upload_assets", False)

    try:
        processor = RepoProcessor(
            repo_entry=repo_entry,
            watchers_conf=config.get("watchers", {}),
            watcher_cache=watcher_cache,
            backend=backend,
            notifiers=notifiers,
            global_upload_assets=global_upload_assets,
        )
        processor.process()
    except Exception as e:
        print(f"❌ An error occurred while processing {repo}: {e}")
        traceback.print_exc()

    print("✅ Single repo check finished.")


def run_full_check() -> None:
    """Run the full release checker with all configured repositories."""
    print("🚀 Starting release checker...")
    config = load_config()

    try:
        backend = get_backend(config.get("persistence", {}))
        print(f"🗄️ Using persistence backend: {type(backend).__name__}")
    except Exception as e:
        print(f"❌ Failed to initialize persistence backend: {e}")
        return  # Cannot proceed without persistence

    # Initialize notifiers to an empty list before the try block
    notifiers: list[Notifier] = []
    try:
        notifiers = [get_notifier(nc) for nc in config.get("notifiers", [])]
        print(f"🔔 Initialized {len(notifiers)} notifier(s)")
    except Exception as e:
        print(
            f"⚠️  Failed to initialize one or more notifiers: {e}. Proceeding with successfully initialized notifiers.",
        )
        notifiers = [n for n in notifiers if n is not None]
        print(
            f"🔔 Successfully initialized {len(notifiers)} notifier(s) after errors.",
        )  # Optional: show the final count

    if not notifiers:
        print("❌ No notifiers available after initialization.")

    watcher_cache: dict[str, Watcher] = {}  # Cache shared across all repo processors

    global_upload_assets = config.get("upload_assets", False)
    if global_upload_assets:
        print("⬇️ Global asset download is enabled.")

    repo_entries = config.get("repos", [])
    if not repo_entries:
        print("ℹ️ No repositories configured to watch.")
        return

    print(f"👀 Watching {len(repo_entries)} repositories.")

    for entry in repo_entries:
        try:
            processor = RepoProcessor(
                repo_entry=entry,
                watchers_conf=config.get("watchers", {}),
                watcher_cache=watcher_cache,
                backend=backend,
                notifiers=notifiers,
                global_upload_assets=global_upload_assets,
            )
            processor.process()
        except Exception as e:
            # Catch errors during processor initialization or unexpected errors
            repo_id = entry.get("repo", "Unknown Repo")
            print(f"❌ An error prevented processing of {repo_id}: {e}")

    print("✅ Release checker finished.")


@click.command()
@click.option(
    "--repo",
    "-r",
    help="Repository to check (e.g., 'owner/repo' for GitHub, 'package-name' for PyPI)",
)
@click.option(
    "--watcher",
    "-w",
    type=click.Choice(
        [
            "github",
            "gitlab",
            "pypi",
            "dockerhub",
            "npm",
            "maven",
            "wordpress",
            "homebrew",
            "apkmirror",
            "apkpure",
            "fdroid",
        ],
    ),
    help="Watcher type to use for checking the repository (optional if repo is in config file)",
)
def main(repo: str | None, watcher: str | None) -> None:
    """Release Tracker - Monitor software releases across multiple platforms.

    If --repo is provided, checks only that specific repository.
    If --watcher is not provided, looks for the repo in config.yaml to determine the watcher.
    If neither --repo nor --watcher is provided, runs the full checker with all configured repositories.

    Examples
    --------
      python main.py                              # Run full checker
      python main.py -r owner/repo -w github     # Check single GitHub repo (explicit watcher)
      python main.py -r owner/repo               # Check single repo (watcher from config)
      python main.py -r package-name -w pypi     # Check single PyPI package
    """
    if repo:
        # Single repo mode
        if watcher:
            # Watcher explicitly provided
            check_single_repo(repo, watcher)
        else:
            # Try to find watcher from config file
            config = load_config()
            found_watcher = find_repo_watcher_in_config(repo, config)
            if found_watcher:
                print(f"🔍 Found {repo} in config file using watcher: {found_watcher}")
                check_single_repo(repo, found_watcher)
            else:
                click.echo(f"❌ Error: Repository '{repo}' not found in config file.", err=True)
                click.echo("Please either:", err=True)
                click.echo("  1. Add the repository to your config.yaml file, or", err=True)
                click.echo("  2. Specify the watcher type with -w/--watcher option", err=True)
                click.echo("Use 'python main.py --help' for available watcher types.", err=True)
    elif watcher:
        # Only watcher provided, repo missing
        click.echo("❌ Error: --repo must be provided when using --watcher.", err=True)
        click.echo("Use 'python main.py --help' for usage information.", err=True)
    else:
        # Full check mode
        run_full_check()


if __name__ == "__main__":
    main()
