# Environment Variables Reference

This document provides a comprehensive reference for all environment variables supported by the Release Tracker project, including their purposes, usage examples, and default values.

## 📋 Table of Contents

- [Core Configuration](#-core-configuration)
- [Authentication Tokens](#-authentication-tokens)
- [AWS/S3 Configuration](#-awss3-configuration)
- [Redis Configuration](#-redis-configuration)
- [Notification Configuration](#-notification-configuration)
- [Runtime Control](#-runtime-control)
- [Usage Examples](#-usage-examples)
- [Best Practices](#-best-practices)

## 🔧 Core Configuration

### CONFIG_SOURCE
- **Purpose**: Specifies the location of the configuration file
- **Format**: Local file path, HTTP(S) URL, or S3 bucket URL
- **Default**: `config.yaml`
- **Examples**:
  ```bash
  # Local file
  export CONFIG_SOURCE="config.yaml"
  export CONFIG_SOURCE="/path/to/custom-config.yaml"
  
  # HTTP(S) URL
  export CONFIG_SOURCE="https://raw.githubusercontent.com/user/repo/main/config.yaml"
  
  # S3 bucket
  export CONFIG_SOURCE="s3://my-bucket/config.yaml"
  ```

## 🔐 Authentication Tokens

### GH_TOKEN
- **Purpose**: GitHub Personal Access Token for GitHub API access
- **Required**: Optional (but recommended for higher rate limits)
- **Permissions**: `public_repo` (for public repos), `repo` (for private repos)
- **Usage**: Increases GitHub API rate limits from 60/hour to 5000/hour
- **Example**:
  ```bash
  export GH_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  ```

### GITLAB_TOKEN
- **Purpose**: GitLab Personal Access Token for GitLab API access
- **Required**: Optional (required for private repositories)
- **Scopes**: `read_api`, `read_repository`
- **Usage**: Access private GitLab repositories and increase rate limits
- **Example**:
  ```bash
  export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
  ```

### DOCKER_TOKEN
- **Purpose**: Docker Hub authentication token
- **Required**: Optional (for private repositories or higher rate limits)
- **Usage**: Access private Docker repositories and avoid rate limiting
- **Example**:
  ```bash
  export DOCKER_TOKEN="dckr_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  ```

### APKMIRROR_TOKEN
- **Purpose**: APKMirror API authentication token
- **Required**: Required for APKMirror watcher
- **Usage**: Access APKMirror API for Android app version checking
- **Example**:
  ```bash
  export APKMIRROR_TOKEN="your_apkmirror_api_token"
  ```

## ☁️ AWS/S3 Configuration

Used when loading configuration from S3 buckets or CloudFlare R2.

### AWS_ACCESS_KEY_ID
- **Purpose**: AWS access key for S3 authentication
- **Required**: Required when using S3 config source
- **Usage**: Authenticate with AWS S3 to download configuration files
- **Example**:
  ```bash
  export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
  ```

### AWS_SECRET_ACCESS_KEY
- **Purpose**: AWS secret key for S3 authentication
- **Required**: Required when using S3 config source
- **Usage**: Authenticate with AWS S3 to download configuration files
- **Example**:
  ```bash
  export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  ```

### AWS_REGION
- **Purpose**: AWS region for S3 bucket location
- **Required**: Required when using S3 config source
- **Default**: No default, must be specified
- **Example**:
  ```bash
  export AWS_REGION="us-east-1"
  ```

### S3_ENDPOINT_URL
- **Purpose**: Custom S3-compatible endpoint URL
- **Required**: Optional (for non-AWS S3 services like CloudFlare R2)
- **Usage**: Use S3-compatible services like CloudFlare R2, MinIO, etc.
- **Example**:
  ```bash
  export S3_ENDPOINT_URL="https://your-account-id.r2.cloudflarestorage.com"
  ```

## 🗄️ Redis Configuration

Used for persistent state storage to track last seen releases.

### REDIS_HOST
- **Purpose**: Redis server hostname or IP address
- **Required**: Required when using Redis persistence
- **Default**: `localhost` (when not specified in config)
- **Example**:
  ```bash
  export REDIS_HOST="redis-server.example.com"
  export REDIS_HOST="127.0.0.1"
  ```

### REDIS_PORT
- **Purpose**: Redis server port number
- **Required**: Optional
- **Default**: `6379`
- **Example**:
  ```bash
  export REDIS_PORT="6379"
  export REDIS_PORT="16379"  # Custom port
  ```

### REDIS_DB
- **Purpose**: Redis database number to use
- **Required**: Optional
- **Default**: `0`
- **Range**: 0-15 (typically)
- **Example**:
  ```bash
  export REDIS_DB="0"
  export REDIS_DB="1"  # Use database 1
  ```

### REDIS_PASSWORD
- **Purpose**: Redis authentication password
- **Required**: Optional (required for password-protected Redis)
- **Usage**: Authenticate with Redis servers that require authentication
- **Example**:
  ```bash
  export REDIS_PASSWORD="your_redis_password"
  ```

## 🔔 Notification Configuration

### APPRISE_URL
- **Purpose**: Apprise notification service URL
- **Required**: Required for notifications
- **Supports**: 80+ notification services (Discord, Slack, Telegram, etc.)
- **Examples**:
  ```bash
  # Discord webhook
  export APPRISE_URL="discord://webhook_id/webhook_token"
  
  # Telegram bot
  export APPRISE_URL="tgram://bot_token/chat_id"
  
  # Slack webhook
  export APPRISE_URL="slack://webhook_token"
  
  # Email (SMTP)
  export APPRISE_URL="mailto://user:pass@smtp.example.com:587/recipient@example.com"
  
  # Multiple services (comma-separated)
  export APPRISE_URL="discord://webhook1,tgram://bot_token/chat_id"
  ```

## 🎛️ Runtime Control

### FORCE_NOTIFY
- **Purpose**: Force notifications even for already-seen releases
- **Required**: Optional
- **Usage**: Re-send notifications for releases that have already been processed
- **Values**: Any non-empty value enables force mode
- **Examples**:
  ```bash
  # Enable force notifications
  export FORCE_NOTIFY="1"
  export FORCE_NOTIFY="true"
  export FORCE_NOTIFY="yes"
  
  # Run with force notifications
  FORCE_NOTIFY=1 python main.py
  
  # Disable (default)
  unset FORCE_NOTIFY
  ```

## 💡 Usage Examples

### Development Environment
```bash
# Basic setup for development
export CONFIG_SOURCE="config.yaml"
export GH_TOKEN="ghp_your_development_token"
export APPRISE_URL="discord://your_webhook"

# Local Redis
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
```

### Production Environment
```bash
# Production setup with S3 config
export CONFIG_SOURCE="s3://prod-configs/release-tracker/config.yaml"
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"

# Authentication tokens
export GH_TOKEN="ghp_production_token"
export GITLAB_TOKEN="glpat_production_token"
export DOCKER_TOKEN="dckr_pat_production_token"

# Production Redis (managed service)
export REDIS_HOST="prod-redis.cache.amazonaws.com"
export REDIS_PORT="6379"
export REDIS_PASSWORD="your_redis_password"
export REDIS_DB="0"

# Production notifications
export APPRISE_URL="tgram://bot_token/chat_id,slack://webhook_token"
```

### Docker Environment
```bash
# Docker Compose with environment variables
version: '3.8'
services:
  release-tracker:
    image: release-tracker
    environment:
      - CONFIG_SOURCE=config.yaml
      - GH_TOKEN=${GH_TOKEN}
      - GITLAB_TOKEN=${GITLAB_TOKEN}
      - APPRISE_URL=${APPRISE_URL}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0
    depends_on:
      - redis
      
  redis:
    image: redis:7-alpine
```

### Testing Environment
```bash
# Testing with force notifications
export CONFIG_SOURCE="test-config.yaml"
export FORCE_NOTIFY="1"
export APPRISE_URL="mailto://test@example.com"

# Test Redis
export REDIS_HOST="localhost"
export REDIS_DB="15"  # Use separate test database
```

## 🛡️ Best Practices

### Security
- **Never commit tokens** to version control
- **Use `.env` files** for local development (add to `.gitignore`)
- **Use secrets management** in production (AWS Secrets Manager, HashiCorp Vault)
- **Rotate tokens regularly** and use minimal required permissions

### Configuration Management
- **Environment-specific configs**: Use different config files for dev/staging/prod
- **Variable validation**: Ensure required variables are set before running
- **Default values**: Use fallback values in config files with `${VAR:-default}`

### Redis Security
- **Use authentication** in production (`REDIS_PASSWORD`)
- **Use SSL/TLS** for remote Redis connections
- **Separate databases** for different environments (`REDIS_DB`)

### Example .env File
```bash
# .env file for local development (DO NOT COMMIT)
CONFIG_SOURCE=config.yaml
GH_TOKEN=ghp_your_github_token_here
GITLAB_TOKEN=glpat_your_gitlab_token_here
APPRISE_URL=discord://your_webhook_id/your_webhook_token
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Loading .env File
```bash
# Load .env file in bash
set -a && source .env && set +a

# Then run the application
python main.py
```

---

**Note**: Environment variables in YAML configuration files use the `${VARIABLE_NAME}` syntax and support default values with `${VARIABLE_NAME:-default_value}`. 
