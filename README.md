# 🔔 Release Tracker

A comprehensive, multi-platform release monitoring system that tracks software releases across different platforms and sends notifications when new versions are available. Built with Python and designed for reliability, extensibility, and ease of use.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/release-tracker.git
cd release-tracker

# Install dependencies
pip install -r requirements.txt

# Copy and configure the example config
cp config.example.yaml config.yaml
# Edit config.yaml with your settings

# Run the tracker
python main.py
```

## 📋 Table of Contents

- [Features](#-features)
- [Supported Platforms](#-supported-platforms)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Docker Deployment](#-docker-deployment)
- [CLI Usage](#-cli-usage)
- [Watchers](#-watchers)
- [Persistence Backends](#-persistence-backends)
- [Notification Systems](#-notification-systems)
- [Configuration Reference](#-configuration-reference)
- [Environment Variables](#-environment-variables)
- [Usage Examples](#-usage-examples)
- [Documentation](#-documentation)
- [Extending the System](#-extending-the-system)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## ✨ Features

- **Multi-Platform Monitoring**: Track releases from GitHub, GitLab, PyPI, APKMirror, APKPure, and F-Droid
- **Smart Deduplication**: Only notify on new releases using persistent state storage
- **Asset Downloading**: Automatically download release assets (binaries, APKs, packages)
- **Flexible Notifications**: Send alerts via 80+ services using Apprise
- **Robust Architecture**: Built-in retry logic, error handling, and graceful degradation
- **Multiple Config Sources**: Load configuration from local files, HTTP(S) URLs, or S3/R2
- **Environment Variable Support**: Dynamic configuration with `${VAR}` placeholder expansion
- **Docker Ready**: Full containerization with Docker Compose support
- **Extensible Design**: Easy to add new platforms, persistence backends, and notifiers

## 🌐 Supported Platforms

| Platform      | Type           | Authentication   | Asset Support | Status |
|---------------|----------------|------------------|---------------|--------|
| **GitHub**    | Git Repository | Token (optional) | ✅             | Stable |
| **GitLab**    | Git Repository | Token (optional) | ✅             | Stable |
| **PyPI**      | Python Package | None             | ✅             | Stable |
| **APKMirror** | Android APK    | Token            | ✅             | Stable |
| **APKPure**   | Android APK    | None             | ✅             | Stable |
| **F-Droid**   | Android APK    | None             | ✅             | Stable |

## 🛠 Installation

### Prerequisites

- Python 3.11+
- Redis (for persistence)
- Docker (optional, for containerized deployment)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/your-username/release-tracker.git
cd release-tracker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file for sensitive configuration:

```bash
# GitHub (optional, for higher rate limits)
GH_TOKEN=ghp_your_github_token

# GitLab (optional, for private repos)
GITLAB_TOKEN=glpat-your_gitlab_token

# Apprise notification URL
APPRISE_URL=discord://webhook_id/webhook_token

# Redis connection (if using external Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# AWS credentials (if loading config from S3)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

## ⚙️ Configuration

The system uses YAML configuration files with support for environment variable expansion. Configuration can be loaded from:

- **Local file**: `config.yaml` (default)
- **HTTP(S) URL**: `https://example.com/config.yaml`
- **S3/R2 bucket**: `s3://bucket-name/config.yaml`

### Basic Configuration Structure

```yaml
# Platform-specific watchers
watchers:
  github:
    type: github
    config:
      token: "${GH_TOKEN}"  # Optional, for higher rate limits

  pypi:
    type: pypi
    config: {}  # No authentication needed

# Repositories to monitor
repos:
  - name: "Example GitHub Repo"
    repo: "owner/repository"
    watcher: github
    config:
      upload_assets: true

  - name: "Python Package"
    repo: "package-name"
    watcher: pypi
    config:
      upload_assets: false

# State persistence
persistence:
  type: redis
  config:
    host: "${REDIS_HOST:-redis}"
    port: ${REDIS_PORT:-6379}
    db: ${REDIS_DB:-0}

# Notification configuration
notifiers:
  - type: apprise
    config:
      url: "${APPRISE_URL}"
    format: "markdown"  # or "text", "html"

# Global settings
upload_assets: false  # Default for all repos
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  release-tracker:
    build: .
    environment:
      - CONFIG_SOURCE=config.yaml
      - GH_TOKEN=${GH_TOKEN}
      - APPRISE_URL=${APPRISE_URL}
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./downloads:/app/downloads
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

Run with:
```bash
docker-compose up -d
```

### Manual Docker Build

```bash
# Build the image
docker build -t release-tracker .

# Run with Redis
docker run -d --name redis redis:7-alpine
docker run -d --name release-tracker \
  --link redis:redis \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/downloads:/app/downloads \
  -e GH_TOKEN="$GH_TOKEN" \
  -e APPRISE_URL="$APPRISE_URL" \
  release-tracker
```

## 💻 CLI Usage

The Release Tracker supports both full checking mode and single repository mode via command-line interface.

### Check All Repositories (Default)
```bash
python main.py
```

### Check Single Repository
```bash
# Check a GitHub repository (explicit watcher)
python main.py -r microsoft/vscode -w github

# Check a repository configured in config.yaml (automatic watcher detection)
python main.py -r microsoft/vscode

# Check a PyPI package
python main.py -r django -w pypi
```

### Available Options
- `-r, --repo`: Repository identifier (format varies by platform)
- `-w, --watcher`: Platform type (optional if repo is in config.yaml)
- `--help`: Show help message

**Note:**
- If `--watcher` is not provided, the tool looks for the repository in your `config.yaml` file to determine the watcher type
- All other configuration (asset downloading, notifications, etc.) comes from your `config.yaml` file

For detailed CLI documentation, see [docs/CLI_USAGE.md](docs/CLI_USAGE.md).

## 👁️ Watchers

Watchers are platform-specific components that fetch release information. Each watcher implements the same interface but handles different APIs and data formats.

### GitHub Watcher

Monitors GitHub repository releases using the GitHub REST API.

```yaml
watchers:
  github:
    type: github
    config:
      token: "${GH_TOKEN}"  # Optional, increases rate limits
      base_url: "https://api.github.com"  # Optional, for GitHub Enterprise

repos:
  - name: "Docker"
    repo: "docker/docker"  # Format: owner/repository
    watcher: github
    config:
      upload_assets: true
```

**Features:**
- Automatic asset detection (binaries, source archives)
- Rate limiting handling
- Support for private repositories (with token)

### GitLab Watcher

Monitors GitLab repository releases using the GitLab API.

```yaml
watchers:
  gitlab:
    type: gitlab
    config:
      token: "${GITLAB_TOKEN}"  # Optional, for private repos
      base_url: "https://gitlab.com/api/v4"  # Configurable for self-hosted

repos:
  - name: "GitLab CE"
    repo: "gitlab-org/gitlab"  # Format: namespace/project
    watcher: gitlab
```

**Features:**
- Support for self-hosted GitLab instances
- Asset link extraction
- Private repository access

### PyPI Watcher

Monitors Python package releases on the Python Package Index.

```yaml
watchers:
  pypi:
    type: pypi
    config: {}  # No authentication required

repos:
  - name: "Requests Library"
    repo: "requests"  # Just the package name
    watcher: pypi
    config:
      upload_assets: true  # Downloads .whl and .tar.gz files
```

**Features:**
- No authentication required
- Automatic detection of wheels and source distributions
- Version string parsing

### APKMirror Watcher

Monitors Android app releases on APKMirror.

```yaml
watchers:
  apkmirror:
    type: apkmirror
    config:
      auth_token: "${APKMIRROR_TOKEN}"
      user_agent: "release-tracker"
      api_url: "https://www.apkmirror.com/wp-json/apkm/v1/app_exists/"

repos:
  - name: "WhatsApp"
    repo: "com.whatsapp"  # Android package name
    watcher: apkmirror
```

**Features:**
- APK file downloading
- Version code tracking
- Multiple APK variants support

### APKPure Watcher

Monitors Android app releases on APKPure using web scraping.

```yaml
watchers:
  apkpure:
    type: apkpure
    config:
      user_agent: "Mozilla/5.0 (compatible; release-tracker)"

repos:
  - name: "Telegram"
    repo: "org.telegram.messenger"  # Package identifier
    watcher: apkpure
```

**Features:**
- Web scraping based
- No API key required
- Version extraction from HTML

### F-Droid Watcher

Monitors open-source Android app releases on F-Droid.

```yaml
watchers:
  fdroid:
    type: fdroid
    config:
      base_url: "https://f-droid.org/en/packages/"
      repo_url: "https://f-droid.org/repo/"
      user_agent: "release-tracker"

repos:
  - name: "Signal"
    repo: "org.thoughtcrime.securesms"  # F-Droid package ID
    watcher: fdroid
```

**Features:**
- Open-source apps only
- Direct APK downloads
- No authentication required

## 💾 Persistence Backends

Persistence backends store the last seen release version to prevent duplicate notifications.

### Redis Backend (Recommended)

```yaml
persistence:
  type: redis
  config:
    host: "localhost"
    port: 6379
    db: 0
    password: "${REDIS_PASSWORD}"  # Optional
```

**Features:**
- High performance
- Distributed deployment support
- Automatic expiration support

### File Backend

```yaml
persistence:
  type: file
  config:
    path: "./releases.json"
```

**Features:**
- No external dependencies
- Simple setup
- Suitable for single-instance deployments

## 📢 Notification Systems

The system uses [Apprise](https://github.com/caronc/apprise) for notifications, supporting 80+ services.

### Apprise Notifier

```yaml
notifiers:
  - type: apprise
    config:
      url: "${APPRISE_URL}"
    format: "markdown"  # Options: text, markdown, html
```

### Supported Services

Popular notification services include:

- **Discord**: `discord://webhook_id/webhook_token`
- **Slack**: `slack://token_a/token_b/token_c`
- **Telegram**: `tgram://bot_token/chat_id`
- **Email**: `mailto://user:pass@smtp.gmail.com`
- **Pushover**: `pover://user@token`
- **Microsoft Teams**: `msteams://token_a/token_b/token_c`

See the [Apprise documentation](https://github.com/caronc/apprise/wiki) for the complete list.

## 📝 Configuration Reference

### Global Configuration

```yaml
# Global asset download setting
upload_assets: false

# Force notifications (ignore duplicate checking)
# Controlled by FORCE_NOTIFY environment variable
```

### Repository Configuration

```yaml
repos:
  - name: "Display Name"           # Human-readable name
    repo: "identifier"             # Platform-specific identifier
    watcher: "watcher_name"        # Which watcher to use
    config:
      upload_assets: true          # Override global setting
      # Watcher-specific options can go here
```

### Watcher Configuration

Each watcher type has its own configuration schema:

```yaml
watchers:
  watcher_name:
    type: "watcher_type"
    config:
      # Watcher-specific configuration
      # See individual watcher documentation
```

## 🔧 Environment Variables

The Release Tracker supports multiple environment variables for configuration and authentication. Here's a quick reference:

| Variable                | Description                                | Default       |
|-------------------------|--------------------------------------------|---------------|
| `CONFIG_SOURCE`         | Configuration file location                | `config.yaml` |
| `FORCE_NOTIFY`          | Force notifications even for seen releases | Not set       |
| `GH_TOKEN`              | GitHub personal access token               | Not set       |
| `GITLAB_TOKEN`          | GitLab personal access token               | Not set       |
| `DOCKER_TOKEN`          | Docker Hub authentication token            | Not set       |
| `APKMIRROR_TOKEN`       | APKMirror API authentication token         | Not set       |
| `APPRISE_URL`           | Apprise notification URL                   | Not set       |
| `REDIS_HOST`            | Redis server hostname                      | `localhost`   |
| `REDIS_PORT`            | Redis server port                          | `6379`        |
| `REDIS_DB`              | Redis database number                      | `0`           |
| `REDIS_PASSWORD`        | Redis authentication password              | Not set       |
| `AWS_ACCESS_KEY_ID`     | AWS access key for S3 config               | Not set       |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 config               | Not set       |
| `AWS_REGION`            | AWS region for S3 config                   | Not set       |
| `S3_ENDPOINT_URL`       | Custom S3 endpoint (CloudFlare R2, MinIO)  | Not set       |

For detailed information, usage examples, and best practices, see **[Environment Variables Documentation](docs/ENVIRONMENT_VARIABLES.md)**.

## 📚 Usage Examples

### Monitor Popular Python Packages

```yaml
watchers:
  pypi:
    type: pypi
    config: {}

repos:
  - {name: "Django", repo: "django", watcher: pypi}
  - {name: "Flask", repo: "flask", watcher: pypi}
  - {name: "Requests", repo: "requests", watcher: pypi}
  - {name: "FastAPI", repo: "fastapi", watcher: pypi}

persistence:
  type: redis
  config: {host: redis, port: 6379, db: 0}

notifiers:
  - type: apprise
    config: {url: "${DISCORD_WEBHOOK}"}
    format: markdown
```

### Monitor Development Tools

```yaml
watchers:
  github:
    type: github
    config: {token: "${GH_TOKEN}"}

repos:
  - {name: "Docker", repo: "docker/docker", watcher: github, config: {upload_assets: true}}
  - {name: "Kubernetes", repo: "kubernetes/kubernetes", watcher: github}
  - {name: "Terraform", repo: "hashicorp/terraform", watcher: github, config: {upload_assets: true}}
  - {name: "VS Code", repo: "microsoft/vscode", watcher: github}
```

### Android App Monitoring

```yaml
watchers:
  fdroid:
    type: fdroid
    config: {}
  apkpure:
    type: apkpure
    config: {}

repos:
  - {name: "Signal", repo: "org.thoughtcrime.securesms", watcher: fdroid}
  - {name: "Telegram", repo: "org.telegram.messenger", watcher: apkpure}
  - {name: "Firefox", repo: "org.mozilla.firefox", watcher: fdroid}
```

## 📚 Documentation

For detailed information about specific topics, see the following documentation files:

- **[CLI Usage](docs/CLI_USAGE.md)** - Comprehensive CLI command reference and examples
- **[Watchers](docs/WATCHERS.md)** - Detailed watcher configurations and platform-specific features
- **[Configuration Sources](docs/CONFIG_SOURCES.md)** - Advanced configuration loading from various sources
- **[Environment Variables](docs/ENVIRONMENT_VARIABLES.md)** - Complete reference for all supported environment variables
- **[Redis Utils](docs/REDIS_UTILS.md)** - Redis setup, management, and troubleshooting utilities

## 🔌 Extending the System

### Adding a New Watcher

1. Create a new watcher class in `watcher/your_platform.py`:

```python
from watcher.base import ReleaseAsset, ReleaseInfo, Watcher

class YourPlatformWatcher(Watcher):
    def __init__(self, config=None):
        # Initialize with platform-specific config
        pass

    def fetch_latest_release(self, repo_id: str) -> ReleaseInfo:
        # Implement platform-specific logic
        # Return ReleaseInfo with tag and assets
        pass
```

2. Register the watcher in `utils.py`:

```python
from watcher.your_platform import YourPlatformWatcher

def build_watcher(watcher_type: str, config: dict[str, Any]) -> Watcher:
    # ... existing watchers ...
    if watcher_type == "your_platform":
        return YourPlatformWatcher(config)
```

3. Document the new watcher and update configuration examples.

### Adding a New Persistence Backend

1. Create a backend class in `persistence/your_backend.py`:

```python
from persistence.base import PersistenceBackend

class YourBackend(PersistenceBackend):
    def get_last_release(self, key: str) -> str | None:
        # Implement retrieval logic
        pass

    def set_last_release(self, key: str, release: str) -> None:
        # Implement storage logic
        pass
```

2. Register in `utils.py`:

```python
def get_backend(config: dict[str, Any]) -> PersistenceBackend:
    if config["type"] == "your_backend":
        return YourBackend(**config["config"])
```

### Adding a New Notifier

1. Create a notifier class in `notifier/your_notifier.py`:

```python
from notifier.base import Notifier

class YourNotifier(Notifier):
    def send(self, title: str, body: str, attachments: list = None) -> bool:
        # Implement notification logic
        # Return True on success, False on failure
        pass
```

2. Register in `utils.py`:

```python
def get_notifier(config: dict[str, Any]) -> Notifier:
    if config["type"] == "your_notifier":
        return YourNotifier(config["config"])
```

## 🔍 Troubleshooting

### Common Issues

**Configuration not found:**
```bash
# Check config file location
export CONFIG_SOURCE=/path/to/config.yaml
# Or use HTTP URL
export CONFIG_SOURCE=https://example.com/config.yaml
```

**Redis connection failed:**
```bash
# Check Redis status
redis-cli ping
# Verify connection settings in config
```

**GitHub rate limiting:**
```bash
# Add GitHub token to increase limits
export GH_TOKEN=ghp_your_token_here
```

**Assets not downloading:**
- Ensure `upload_assets: true` in repo config
- Check download permissions and disk space
- Verify network connectivity to asset URLs

### Debug Mode

Run with verbose output:
```bash
python main.py --verbose
```

Force notifications (ignore seen releases):
```bash
FORCE_NOTIFY=1 python main.py
```

### Log Analysis

The application outputs detailed logs including:
- Repository processing status
- API requests and responses
- Asset download progress
- Notification delivery status
- Error messages with context

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure code quality: `ruff check . && ruff format .`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install ruff mypy pre-commit

# Set up pre-commit hooks
pre-commit install

# Run tests
python -m pytest

# Run linting
ruff check .
ruff format .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Apprise](https://github.com/caronc/apprise) - Multi-platform notification library
- [Tenacity](https://github.com/jd/tenacity) - Retry logic library
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing for web scraping watchers
- All the platform APIs that make this monitoring possible

---

**Made with ❤️ for developers who want to stay updated on their favorite software releases.**
