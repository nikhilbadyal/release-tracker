# Redis Utility Scripts

This directory contains utility scripts for managing Redis data used by the Release Tracker application.

## 🏗️ **New Data Structure**

The Redis storage uses an efficient set-based structure:

**Structure:**
```
Key: release-tracker  Value: SET(
  "github_AChep/keyguard-app:r20250530",
  "fdroid_com.termux:0.118.0",
  "pypi_requests:2.28.1"
)
```

## 📜 **Scripts**

### 1. `delete_redis_keys.py` - Simple Repository Deletion Script

Delete tracked repositories with optional filtering by prefix.

**Usage:**
```bash
# Delete all tracked repositories
python delete_redis_keys.py

# Delete only GitHub repositories
python delete_redis_keys.py github

# Delete only F-Droid repositories
python delete_redis_keys.py fdroid

# Show help
python delete_redis_keys.py --help
```

**Features:**
- Loads Redis credentials from `config.yaml` automatically
- Shows preview of repositories to be deleted
- Requires user confirmation before deletion
- Supports filtering by repository prefix (e.g., `github`, `pypi`, `fdroid`)

### 2. `redis_utils.py` - Full-Featured Redis Utility

A comprehensive utility script with multiple Redis operations.

**Usage:**
```bash
# List all tracked repositories
python redis_utils.py list

# List repositories with specific prefix
python redis_utils.py list -p github

# Delete all repositories (with confirmation)
python redis_utils.py delete

# Delete repositories with specific prefix
python redis_utils.py delete -p pypi

# Force delete without confirmation
python redis_utils.py delete --force

# Get version of specific repository
python redis_utils.py get -r github_docker/docker

# Show repository statistics
python redis_utils.py stats

# Show help
python redis_utils.py --help
```

**Features:**
- Multiple operations: list, delete, get, stats
- Repository prefix filtering
- Force deletion option
- Repository statistics with watcher type breakdown
- Comprehensive help system

## 🔧 **RedisStore Class**

The `RedisStore` class in `persistence/redis_store.py` uses a set-based structure:

### Core Features

- **Single Redis Key**: Uses one key (e.g., `release-tracker`) instead of many
- **Set Data Type**: Stores repository-version pairs in a Redis SET
- **Efficient Operations**: Faster queries and updates
- **Better Scalability**: Reduced memory overhead

### Key Methods

#### `get_last_release(repo: str) -> str | None`
Finds the repository in the set and returns its version.

#### `set_last_release(repo: str, tag: str) -> None`
Updates or adds a repository-version pair in the set.

#### `delete_all_keys_with_prefix(prefix: str | None = None) -> int`
Deletes repository entries matching the prefix, or clears the entire set.

#### `get_all_keys_with_prefix(prefix: str | None = None) -> list[str]`
Returns repository entries matching the prefix in "repo:version" format.

#### `get_all_repositories() -> dict[str, str]`
Returns all repositories as a dictionary mapping repo names to versions.

#### `get_repository_count() -> int`
Returns the total number of tracked repositories.

#### `remove_repository(repo: str) -> bool`
Removes a specific repository from tracking.

**Example Usage:**
```python
redis_store = RedisStore(host="localhost", port=6379)

# Get all repositories
repos = redis_store.get_all_repositories()
# Returns: {"github_user/repo": "v1.0.0", "pypi_package": "v2.0.0"}

# Get repository count
count = redis_store.get_repository_count()
# Returns: 2

# Remove specific repository
removed = redis_store.remove_repository("github_user/repo")
# Returns: True if found and removed
```

## ⚙️ **Configuration**

All scripts automatically load Redis configuration from your `config.yaml` file:

```yaml
persistence:
  type: redis
  config:
    host: "your-redis-host"
    port: 6379
    password: "your-password"
    db: 0
    prefix: "release-tracker"  # This becomes the set key name
```

Environment variables in the config (like `${REDIS_PASSWORD}`) are automatically resolved.

## 🛡️ **Safety Features**

- **Confirmation prompts**: Scripts ask for confirmation before destructive operations
- **Preview functionality**: Shows repositories before deletion
- **Error handling**: Graceful error handling with informative messages
- **Connection management**: Automatic connection cleanup

## 📊 **Benefits of Set Structure**

### Performance Improvements
- **Fewer Redis operations**: Single key instead of many
- **Atomic updates**: Set operations are atomic
- **Memory efficient**: Reduced Redis memory usage
- **Faster queries**: Set operations are O(1) for most cases

### Operational Benefits
- **Simpler backups**: Only one key to backup
- **Better monitoring**: Easier to track total repositories
- **Atomic operations**: All-or-nothing updates
- **Scalability**: Better performance with large repository counts

## 🚀 **Usage Examples**

### Monitor Repository Status
```bash
# See all tracked repositories
python redis_utils.py list

# Check specific repository
python redis_utils.py get -r github_docker/docker

# Get statistics
python redis_utils.py stats
```

### Clean Up Data
```bash
# Remove all GitHub repositories
python redis_utils.py delete -p github

# Remove specific repository type
python delete_redis_keys.py pypi

# Clean everything (with confirmation)
python redis_utils.py delete

# Force clean everything
python redis_utils.py delete --force
```

### Purge All Data
```bash
# Delete all tracked repositories
python delete_redis_keys.py

# Or using the full utility
python redis_utils.py delete --force
```

The set-based structure provides better performance, simpler operations, and easier maintenance while maintaining all existing functionality.
