# 🔔 Git Release Watcher

Track releases from GitHub, GitLab, and beyond — download release assets, send notifications using [Apprise](https://github.com/caronc/apprise), and persist state in Redis.

Supports Docker deployment, retry logic with `tenacity`, and a modular architecture that makes it easy to add new sources like APKMirror.

---

## 📦 Features

- ✅ Monitor multiple repositories across platforms (GitHub, GitLab)
- ✅ Only acts on new releases (using Redis for state)
- ✅ Downloads release assets (optional)
- ✅ Sends release notifications via Apprise
- ✅ Retry logic built-in via `tenacity`
- ✅ Fully Dockerized
- ✅ Config can be loaded from local files, HTTP(S), or S3/Cloudflare R2

---

## 🛠️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/release-watcher.git
cd release-watcher
```

### 2. Prepare environment

Create a `.env` file:

```dotenv
GH_TOKEN=ghp_yourtokenhere
GITLAB_TOKEN=glpat-yourtokenhere
#If using s3 for storing confg file
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
```

### 3. Define config

You can load config from:
- A local path: `config.yaml`
- An HTTP(S) URL: `https://example.com/config.yaml`
- An S3/R2 URI: `s3://my-bucket/config.yaml`

Specify config location via:
- Environment variable: `CONFIG_SOURCE`
- CLI argument: `--config`
- Or fallback to `config.yaml` in the project root

Example `config.yaml`:

```yaml
watchers:
  github:
    type: github
    config:
      token: "${GH_TOKEN}"

  gitlab:
    type: gitlab
    config:
      token: "${GITLAB_TOKEN}"
      base_url: "https://gitlab.com/api/v4"

repos:
  - name: "nikhilbadyal.github.io"
    repo: "nikhilbadyal/nikhilbadyal.github.io"
    watcher: github
    config:
      upload_assets: false

  - name: "AuroraStore"
    repo: "AuroraOSS/AuroraStore"
    watcher: gitlab
    config:
      upload_assets: false

persistence:
  type: redis
  config:
    host: "redis"
    port: 6379
    db: 0

notifier:
  type: apprise
  config:
    url: "myurl"
```

---

## 🐳 Docker

Use the provided `docker-compose.yml` to run the watcher with Redis:

```bash
docker-compose up --build
```

This will:
- Launch Redis
- Run the watcher on startup
- Persist release tags in Redis
- Send release notifications

---

## ⚙️ How It Works

- **Watchers** handle platform-specific logic (GitHub, GitLab).
- **Config Loaders** support `file://`, `http(s)://`, and `s3://` URIs.
- **Secrets** are injected from `.env` and resolved at runtime.
- **Persistence layer** stores last-seen releases to avoid duplicates.
- **Notifiers** like Apprise push release updates.
- **Tenacity** handles retrying flaky network operations.

---

## 🧩 Extending

Want to add a new platform (e.g., APKMirror)?

1. Create a new watcher in `watcher/apkmirror.py` (subclass `Watcher`).
2. Register it in `utils.build_watcher()`.
3. Add it to your `config.yaml` under `watchers`.

---

## 🧪 Testing

Run manually:

```bash
python main.py
```

Or with Docker (Redis included):

```bash
docker-compose run --rm app
```

---

## 📥 Output

Release assets are saved under `downloads/` when `upload_assets: true`.

---

## 🔐 Secrets

Use `.env` for secrets. Variables like `${GH_TOKEN}` are automatically expanded at runtime.

If using S3 or R2 for config:
- Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`
- Use `CONFIG_SOURCE=s3://bucket/config.yaml`

---

## 📄 License

MIT
