"""
Redis utility script for Release Tracker.
Provides various Redis operations using configuration from config file.
"""

import argparse
import sys
from typing import Any

from config.loader import load_config
from env_parser import resolve_env_placeholders_recursive
from persistence.redis_store import RedisStore


def get_redis_config_from_file() -> dict[str, Any]:
    """Load Redis configuration from the config file."""
    try:
        config = load_config()
        persistence_config = config.get("persistence", {})

        if persistence_config.get("type") != "redis":
            print("❌ Persistence backend is not Redis in config file")
            sys.exit(1)

        redis_config = persistence_config.get("config", {})
        if not redis_config:
            print("❌ No Redis configuration found in config file")
            sys.exit(1)

        # Resolve environment variables in the config
        resolved_config = resolve_env_placeholders_recursive(redis_config)

        print("✅ Successfully loaded Redis configuration from config file")

    except Exception as e:
        print(f"❌ Failed to load Redis configuration: {e}")
        sys.exit(1)
    else:
        return resolved_config


def list_repositories(redis_store: RedisStore, prefix: str | None = None) -> None:
    """List all repositories and their versions."""
    try:
        if prefix:
            # Get entries matching the prefix
            entries = redis_store.get_all_keys_with_prefix(prefix)
            title = f"repositories with prefix '{prefix}'"
        else:
            # Get all repositories
            entries = redis_store.get_all_keys_with_prefix()
            title = "repositories"

        if not entries:
            print(f"ℹ️ No {title} found")
            return

        print(f"\n📋 Tracked {title} ({len(entries)} total):")
        print("-" * 80)

        # Parse and display entries
        for i, entry in enumerate(sorted(entries), 1):
            if ":" in entry:
                repo, version = entry.split(":", 1)
                print(f"  {i:3d}. {repo:<50} -> {version}")
            else:
                print(f"  {i:3d}. {entry} (invalid format)")

        # Show summary
        print("-" * 80)
        print(f"Total repositories: {len(entries)}")

    except Exception as e:
        print(f"❌ Failed to list repositories: {e}")


def delete_repositories(redis_store: RedisStore, prefix: str | None = None, force: bool = False) -> None:
    """Delete repositories matching the prefix."""
    try:
        if prefix:
            entries = redis_store.get_all_keys_with_prefix(prefix)
            title = f"repositories with prefix '{prefix}'"
        else:
            entries = redis_store.get_all_keys_with_prefix()
            title = "ALL repositories"

        if not entries:
            print(f"ℹ️ No {title} found")
            return

        print(f"\n📋 {title.capitalize()} to be deleted ({len(entries)} total):")
        print("-" * 50)

        # Show first 10 entries as preview
        for i, entry in enumerate(sorted(entries)[:10]):
            if ":" in entry:
                repo, version = entry.split(":", 1)
                print(f"  {i+1}. {repo} -> {version}")
            else:
                print(f"  {i+1}. {entry}")

        if len(entries) > 10:
            print(f"  ... and {len(entries) - 10} more repositories")

        if not force:
            print("-" * 50)
            response = (
                input(f"\n⚠️  Are you sure you want to delete {len(entries)} repositories? (yes/no): ").lower().strip()
            )
            if response not in ["yes", "y"]:
                print("❌ Deletion cancelled by user")
                return

        # Perform deletion
        print(f"\n🗑️  Deleting {title}...")
        deleted_count = redis_store.delete_all_keys_with_prefix(prefix)

        if deleted_count > 0:
            print(f"✅ Successfully deleted {deleted_count} repositories")
        else:
            print("ℹ️ No repositories were deleted")

    except Exception as e:
        print(f"❌ Failed to delete repositories: {e}")


def get_repository_version(redis_store: RedisStore, repo: str) -> None:
    """Get the version of a specific repository."""
    try:
        version = redis_store.get_last_release(repo)
        if version is None:
            print(f"❌ Repository '{repo}' not found")
        else:
            print(f"✅ {repo} -> {version}")
    except Exception as e:
        print(f"❌ Failed to get repository version: {e}")


def show_stats(redis_store: RedisStore) -> None:
    """Show statistics about tracked repositories."""
    try:
        count = redis_store.get_repository_count()
        print("\n📊 Repository Statistics:")
        print("-" * 30)
        print(f"Total repositories tracked: {count}")

        if count > 0:
            # Get all repositories and group by watcher type
            all_repos = redis_store.get_all_repositories()
            watcher_stats: dict[str, int] = {}

            for repo_name in all_repos:
                # Extract watcher type (first part before underscore)
                if "_" in repo_name:
                    watcher_type = repo_name.split("_", 1)[0]
                    watcher_stats[watcher_type] = watcher_stats.get(watcher_type, 0) + 1
                else:
                    watcher_stats["unknown"] = watcher_stats.get("unknown", 0) + 1

            print("\nBy watcher type:")
            for watcher, count in sorted(watcher_stats.items()):
                print(f"  {watcher}: {count}")

    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Redis utility script for Release Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python redis_utils.py list                    # List all tracked repositories
  python redis_utils.py list -p github         # List repositories with 'github' prefix
  python redis_utils.py delete                 # Delete all repositories (with confirmation)
  python redis_utils.py delete -p github       # Delete repositories with 'github' prefix
  python redis_utils.py delete --force         # Delete without confirmation
  python redis_utils.py get -r github_user/repo # Get version of specific repository
  python redis_utils.py stats                  # Show repository statistics
        """,
    )

    parser.add_argument(
        "action",
        choices=["list", "delete", "get", "stats"],
        help="Action to perform",
    )

    parser.add_argument(
        "-p",
        "--prefix",
        help="Repository prefix to filter by (e.g., 'github', 'pypi')",
    )

    parser.add_argument(
        "-r",
        "--repo",
        help="Specific repository identifier (used with 'get' action)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt for delete action",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.action == "get" and not args.repo:
        print("❌ --repo is required for 'get' action")
        sys.exit(1)

    print(f"🔧 Redis Utility - {args.action.upper()} operation")
    print("=" * 50)

    # Load Redis configuration and connect
    redis_config = get_redis_config_from_file()

    try:
        redis_store = RedisStore(**redis_config)
        print(f"✅ Connected to Redis at {redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}")
        print(f"🗄️  Using Redis set key: '{redis_store.prefix}'")

        if args.prefix:
            print(f"🔍 Filtering by prefix: '{args.prefix}'")

    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        sys.exit(1)

    # Perform the requested action
    try:
        if args.action == "list":
            list_repositories(redis_store, args.prefix)
        elif args.action == "delete":
            delete_repositories(redis_store, args.prefix, args.force)
        elif args.action == "get":
            get_repository_version(redis_store, args.repo)
        elif args.action == "stats":
            show_stats(redis_store)
    finally:
        redis_store.close()
        print("🔌 Redis connection closed")


if __name__ == "__main__":
    main()
