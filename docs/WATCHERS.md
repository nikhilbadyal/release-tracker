# 🔍 Watchers Guide

Release Tracker supports **12 different watchers** to track releases across various platforms and package managers.

## 📊 **Available Watchers**

### **🐙 GitHub**
Track releases from GitHub repositories.

**Type:** `github`
**Repo Format:** `owner/repository`

```yaml
watchers:
  github:
    type: github
    config:
      token: "${GH_TOKEN}"  # Optional but recommended for rate limits

repos:
  - name: "Docker"
    repo: "moby/moby"
    watcher: github
```

### **🦊 GitLab**
Track releases from GitLab repositories.

**Type:** `gitlab`
**Repo Format:** `namespace/project`

```yaml
watchers:
  gitlab:
    type: gitlab
    config:
      token: "${GITLAB_TOKEN}"  # Optional
      base_url: "https://gitlab.com/api/v4"  # Optional, for self-hosted

repos:
  - name: "GitLab CE"
    repo: "gitlab-org/gitlab-foss"
    watcher: gitlab
```

### **🐍 PyPI**
Track Python packages from the Python Package Index.

**Type:** `pypi`
**Repo Format:** `package-name`

```yaml
watchers:
  pypi:
    type: pypi
    config: {}

repos:
  - name: "Django"
    repo: "django"
    watcher: pypi
  - name: "Requests"
    repo: "requests"
    watcher: pypi
```

### **🐳 Docker Hub**
Track container images from Docker Hub.

**Type:** `dockerhub`
**Repo Format:** `namespace/repository` or `library/repository` (official images)

```yaml
watchers:
  dockerhub:
    type: dockerhub
    config:
      token: "${DOCKER_TOKEN}"  # Optional

repos:
  - name: "Nginx"
    repo: "library/nginx"  # Official image
    watcher: dockerhub
  - name: "Custom App"
    repo: "mycompany/myapp"  # Custom image
    watcher: dockerhub
```

### **📦 NPM**
Track Node.js packages from the NPM registry.

**Type:** `npm`
**Repo Format:** `package-name` or `@scope/package-name`

```yaml
watchers:
  npm:
    type: npm
    config:
      registry_url: "https://registry.npmjs.org"  # Optional

repos:
  - name: "Express"
    repo: "express"
    watcher: npm
  - name: "TypeScript Types"
    repo: "@types/node"  # Scoped package
    watcher: npm
```

### **☕ Maven Central**
Track Java/JVM libraries from Maven Central.

**Type:** `maven`
**Repo Format:** `groupId:artifactId`

```yaml
watchers:
  maven:
    type: maven
    config:
      base_url: "https://search.maven.org"  # Optional

repos:
  - name: "Spring Boot"
    repo: "org.springframework.boot:spring-boot-starter"
    watcher: maven
  - name: "Jackson Core"
    repo: "com.fasterxml.jackson.core:jackson-core"
    watcher: maven
```

### **🌐 WordPress**
Track WordPress plugins from the official repository.

**Type:** `wordpress`
**Repo Format:** `plugin-slug`

```yaml
watchers:
  wordpress:
    type: wordpress
    config:
      api_url: "https://api.wordpress.org/plugins/info/1.2"  # Optional

repos:
  - name: "Akismet"
    repo: "akismet"
    watcher: wordpress
  - name: "Contact Form 7"
    repo: "contact-form-7"
    watcher: wordpress
```

### **🍺 Homebrew**
Track macOS packages from Homebrew.

**Type:** `homebrew`
**Repo Format:** `formula-name` or `homebrew/cask/app-name`

```yaml
watchers:
  homebrew:
    type: homebrew
    config:
      api_url: "https://formulae.brew.sh/api"  # Optional

repos:
  - name: "Git"
    repo: "git"  # Formula
    watcher: homebrew
  - name: "Docker Desktop"
    repo: "homebrew/cask/docker"  # Cask
    watcher: homebrew
```

### **📱 APKMirror**
Track Android APKs from APKMirror.

**Type:** `apkmirror`
**Repo Format:** `package.name`

```yaml
watchers:
  apkmirror:
    type: apkmirror
    config:
      auth_token: "YXBpLWFwa3VwZGF0ZXI6cm01cmNmcnVVakt5MDRzTXB5TVBKWFc4"
      user_agent: "release-tracker"
      api_url: "https://www.apkmirror.com/wp-json/apkm/v1/app_exists/"

repos:
  - name: "WhatsApp"
    repo: "com.whatsapp"
    watcher: apkmirror
```

### **📱 APKPure**
Track Android APKs from APKPure.

**Type:** `apkpure`
**Repo Format:** `package.name`

```yaml
watchers:
  apkpure:
    type: apkpure
    config:
      user_agent: "release-tracker"

repos:
  - name: "Signal"
    repo: "org.thoughtcrime.securesms"
    watcher: apkpure
```

### **📱 F-Droid**
Track open-source Android apps from F-Droid.

**Type:** `fdroid`
**Repo Format:** `package.name`

```yaml
watchers:
  fdroid:
    type: fdroid
    config:
      base_url: "https://f-droid.org/en/packages/"  # Optional
      repo_url: "https://f-droid.org/repo/"  # Optional

repos:
  - name: "Termux"
    repo: "com.termux"
    watcher: fdroid
```

## 🎯 **Complete Example Configuration**

```yaml
watchers:
  github:
    type: github
    config:
      token: "${GH_TOKEN}"

  dockerhub:
    type: dockerhub
    config:
      token: "${DOCKER_TOKEN}"

  npm:
    type: npm
    config: {}

  maven:
    type: maven
    config: {}

  pypi:
    type: pypi
    config: {}

repos:
  # Source code repositories
  - name: "Kubernetes"
    repo: "kubernetes/kubernetes"
    watcher: github
    config:
      upload_assets: false

  # Container images
  - name: "Redis"
    repo: "library/redis"
    watcher: dockerhub
    config:
      upload_assets: false

  # Package managers
  - name: "React"
    repo: "react"
    watcher: npm
    config:
      upload_assets: false

  - name: "Spring Framework"
    repo: "org.springframework:spring-core"
    watcher: maven
    config:
      upload_assets: false

  - name: "Flask"
    repo: "flask"
    watcher: pypi
    config:
      upload_assets: true

persistence:
  type: redis
  config:
    host: "localhost"
    port: 6379
    db: 0

notifiers:
  - type: apprise
    config:
      url: "${APPRISE_URL}"
```

## 🔧 **Watcher Configuration Options**

### **Common Configuration**
- `upload_assets`: Boolean to control asset downloading (can be set globally or per repo)
- `token`: Authentication token for private repositories or higher rate limits

### **Platform-Specific Options**

#### **GitLab**
- `base_url`: Custom GitLab instance URL (default: https://gitlab.com/api/v4)

#### **NPM**
- `registry_url`: Custom NPM registry URL (default: https://registry.npmjs.org)

#### **Maven Central**
- `base_url`: Custom Maven search URL (default: https://search.maven.org)

#### **WordPress**
- `api_url`: WordPress API endpoint (default: https://api.wordpress.org/plugins/info/1.2)

#### **Homebrew**
- `api_url`: Homebrew API endpoint (default: https://formulae.brew.sh/api)

#### **APKMirror**
- `auth_token`: Base64 encoded authentication token
- `user_agent`: Custom user agent string
- `api_url`: APKMirror API endpoint

#### **F-Droid**
- `base_url`: F-Droid base URL for package pages
- `repo_url`: F-Droid repository URL
- `user_agent`: Custom user agent string

## 🚀 **Usage Tips**

### **Rate Limiting**
- Use authentication tokens when available to increase rate limits
- GitHub: Unauthenticated requests are limited to 60/hour
- Docker Hub: Authentication provides higher rate limits

### **Asset Management**
- Set `upload_assets: false` for watchers that don't provide downloadable assets
- Docker Hub and package managers provide links rather than direct downloads

### **Repository Naming**
- Use descriptive names for your repositories in notifications
- Group related repositories with consistent naming

### **Platform Coverage**
With these 12 watchers, you can track releases across:
- **Source Code**: GitHub, GitLab
- **Containers**: Docker Hub
- **Web Development**: NPM, WordPress
- **Enterprise Java**: Maven Central
- **Python Ecosystem**: PyPI
- **macOS Development**: Homebrew
- **Mobile Development**: APKMirror, APKPure, F-Droid

## 🔮 **Future Watchers**

Potential watchers that could be added:
- **🦀 Crates.io** - Rust packages
- **💎 RubyGems** - Ruby gems
- **🐘 Packagist** - PHP Composer packages
- **🏪 Chrome Web Store** - Browser extensions
- **🎮 Steam** - Game releases
- **🍎 Mac App Store** - macOS apps
- **📱 Google Play Store** - Android apps

## 📝 **Contributing New Watchers**

To add a new watcher:

1. Create a new file in `watcher/` directory
2. Inherit from `Watcher` base class
3. Implement `fetch_latest_release()` method
4. Add to `utils.py` in `build_watcher()` function
5. Update documentation

Example skeleton:
```python
from watcher.base import ReleaseAsset, ReleaseInfo, Watcher

class NewPlatformWatcher(Watcher):
    def fetch_latest_release(self, repo: str) -> ReleaseInfo:
        # Implement API call and parsing logic
        return ReleaseInfo(tag=version, assets=assets)
```
