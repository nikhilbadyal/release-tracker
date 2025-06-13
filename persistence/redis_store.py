import redis

from persistence.base import PersistenceBackend


class RedisStore(PersistenceBackend):

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        prefix: str = "release-tracker",
    ) -> None:
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            ssl=True,
            decode_responses=True,  # Changed to True for easier string handling
        )
        self.prefix = prefix

    def get_last_release(self, repo: str) -> str | None:
        """Get the last release version for a repository from the set."""
        set_key = self.prefix

        # Get all members of the set
        members = self.redis.smembers(set_key)

        # Find the entry for this repo
        for member in members:
            if member.startswith(f"{repo}:"):
                # Extract version from "repo:version" format
                return member.split(":", 1)[1]  # type: ignore[no-any-return]

        return None

    def set_last_release(self, repo: str, tag: str) -> None:
        """Set the last release version for a repository in the set."""
        set_key = self.prefix
        new_entry = f"{repo}:{tag}"

        # Remove any existing entry for this repo first
        members = self.redis.smembers(set_key)
        for member in members:
            if member.startswith(f"{repo}:"):
                self.redis.srem(set_key, member)
                break

        # Add the new entry
        self.redis.sadd(set_key, new_entry)

    def delete_all_keys_with_prefix(self, prefix: str | None = None) -> int:
        """
        Delete all repository entries from the set or delete the entire set.

        Args:
            prefix: The prefix to match. If None, deletes the entire set.

        Returns
        -------
            int: Number of entries deleted
        """
        set_key = self.prefix if prefix is None else prefix

        # If we're deleting the entire set
        if prefix is None or prefix == self.prefix:
            members = self.redis.smembers(set_key)
            count = len(members)
            if count > 0:
                self.redis.delete(set_key)
            return count

        # If we're deleting entries with a specific repo prefix
        set_key = self.prefix
        members = self.redis.smembers(set_key)
        deleted_count = 0

        for member in members:
            if member.startswith((f"{prefix}:", prefix)):
                self.redis.srem(set_key, member)
                deleted_count += 1

        return deleted_count

    def get_all_keys_with_prefix(self, prefix: str | None = None) -> list[str]:
        """
        Get all repository entries from the set that match the prefix.

        Args:
            prefix: The prefix to match. If None, returns all entries.

        Returns
        -------
            list[str]: List of repository entries matching the prefix
        """
        set_key = self.prefix
        members = self.redis.smembers(set_key)

        if prefix is None:
            # Return all entries in "repo:version" format
            return list(members)

        # Filter entries that match the prefix
        matching_entries = []
        for member in members:
            if member.startswith((f"{prefix}:", prefix)):
                matching_entries.append(member)  # noqa: PERF401

        return matching_entries

    def get_all_repositories(self) -> dict[str, str]:
        """
        Get all repositories and their versions as a dictionary.

        Returns
        -------
            dict[str, str]: Dictionary mapping repository names to their versions
        """
        set_key = self.prefix
        members = self.redis.smembers(set_key)

        repo_dict = {}
        for member in members:
            if ":" in member:
                repo, version = member.split(":", 1)
                repo_dict[repo] = version

        return repo_dict

    def get_repository_count(self) -> int:
        """
        Get the total number of repositories being tracked.

        Returns
        -------
            int: Number of repositories in the set
        """
        set_key = self.prefix
        return self.redis.scard(set_key)  # type: ignore[no-any-return]

    def remove_repository(self, repo: str) -> bool:
        """
        Remove a specific repository from tracking.

        Args:
            repo: Repository identifier to remove

        Returns
        -------
            bool: True if repository was found and removed, False otherwise
        """
        set_key = self.prefix
        members = self.redis.smembers(set_key)

        for member in members:
            if member.startswith(f"{repo}:"):
                self.redis.srem(set_key, member)
                return True

        return False

    def close(self) -> None:
        self.redis.close()
