"""
Script to delete repository entries from Redis set using configuration from config file.
This script will delete repository entries that start with the specified prefix.
"""

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


def confirm_deletion(redis_store: RedisStore, prefix: str | None = None) -> bool:
    """Show repositories to be deleted and confirm with user."""
    try:
        if prefix:
            entries = redis_store.get_all_keys_with_prefix(prefix)
            title = f"repositories with prefix '{prefix}'"
        else:
            entries = redis_store.get_all_keys_with_prefix()
            title = "ALL repositories"

        if not entries:
            print(f"ℹ️ No {title} found")
            return False

        print(f"\n📋 {title.capitalize()} to be deleted ({len(entries)} total):")
        print("-" * 60)

        # Show first 10 entries as preview
        for i, entry in enumerate(sorted(entries)[:10]):
            if ":" in entry:
                repo, version = entry.split(":", 1)
                print(f"  {i+1}. {repo:<40} -> {version}")
            else:
                print(f"  {i+1}. {entry} (invalid format)")

        if len(entries) > 10:
            print(f"  ... and {len(entries) - 10} more repositories")

        print("-" * 60)

        response = (
            input(f"\n⚠️  Are you sure you want to delete {len(entries)} repositories? (yes/no): ").lower().strip()
        )

    except Exception as e:
        print(f"❌ Failed to list repositories: {e}")
        return False
    else:
        return response in ["yes", "y"]


def main() -> None:
    """Main function to delete repository entries."""
    print("🗑️  Redis Repository Deletion Script")
    print("=" * 40)

    # Parse command line arguments
    custom_prefix = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Usage: python delete_redis_keys.py [repository_prefix]")
            print("  repository_prefix: Optional prefix to filter repositories (e.g., 'github', 'pypi')")
            print("  If not provided, deletes ALL tracked repositories")
            print()
            print("Examples:")
            print("  python delete_redis_keys.py           # Delete all repositories")
            print("  python delete_redis_keys.py github    # Delete only GitHub repositories")
            print("  python delete_redis_keys.py fdroid    # Delete only F-Droid repositories")
            sys.exit(0)
        custom_prefix = sys.argv[1]

    # Load Redis configuration
    redis_config = get_redis_config_from_file()

    # Create Redis store instance
    try:
        redis_store = RedisStore(**redis_config)
        print(f"✅ Connected to Redis at {redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}")
        print(f"🗄️  Using Redis set key: '{redis_store.prefix}'")

        # Show current filtering
        if custom_prefix:
            print(f"🔍 Filtering by prefix: '{custom_prefix}'")
        else:
            print("🔍 No prefix filter - will affect ALL repositories")

    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        sys.exit(1)

    # Show repositories and confirm deletion
    if not confirm_deletion(redis_store, custom_prefix):
        print("❌ Deletion cancelled by user")
        redis_store.close()
        sys.exit(0)

    # Perform deletion
    try:
        print("\n🗑️  Deleting repositories...")
        deleted_count = redis_store.delete_all_keys_with_prefix(custom_prefix)

        if deleted_count > 0:
            print(f"✅ Successfully deleted {deleted_count} repositories")
        else:
            print("ℹ️ No repositories were deleted")

    except Exception as e:
        print(f"❌ Failed to delete repositories: {e}")
        sys.exit(1)
    finally:
        redis_store.close()
        print("🔌 Redis connection closed")


if __name__ == "__main__":
    main()
