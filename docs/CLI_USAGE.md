# CLI Usage Guide

The Release Tracker now supports CLI functionality using Click, allowing you to check specific repositories or run the full checker.

## Usage

### Full Checker Mode (Default)
Run all configured repositories from your `config.yaml`:
```bash
python main.py
```

### Single Repository Mode
Check a specific repository by providing the `--repo` argument. The `--watcher` argument is optional:

```bash
# Check a GitHub repository (explicit watcher)
python main.py --repo owner/repository --watcher github

# Check a repository that's in your config.yaml (automatic watcher detection)
python main.py --repo owner/repository

# Check a PyPI package (explicit watcher)
python main.py --repo package-name --watcher pypi
```

## Available Options

- `-r, --repo`: Repository identifier (format depends on watcher type)
- `-w, --watcher`: Watcher type to use (optional if repo is in config.yaml)
- `--help`: Show help message

**Note:** 
- If `--watcher` is not provided, the tool automatically looks for the repository in your `config.yaml` file to determine the watcher type
- If the repository is not found in config and no watcher is specified, an error is shown with helpful instructions
- All configuration settings (asset downloading, authentication tokens, notifications, etc.) are loaded from your `config.yaml` file

## Supported Watcher Types

| Watcher     | Repository Format             | Example                                        |
|-------------|-------------------------------|------------------------------------------------|
| `github`    | `owner/repo`                  | `microsoft/vscode`                             |
| `gitlab`    | `owner/repo`                  | `gitlab-org/gitlab`                            |
| `pypi`      | `package-name`                | `django`                                       |
| `dockerhub` | `namespace/image`             | `library/nginx`                                |
| `npm`       | `package-name`                | `express`                                      |
| `maven`     | `groupId:artifactId`          | `org.springframework.boot:spring-boot-starter` |
| `homebrew`  | `formula-name` or `cask-name` | `homebrew/cask/docker`                         |
| `apkmirror` | `package-name`                | `com.android.chrome`                           |
| `apkpure`   | `package-name`                | `com.android.chrome`                           |
| `fdroid`    | `package-name`                | `org.fdroid.fdroid`                            |

## Examples

```bash
# Check Django on PyPI (explicit watcher)
python main.py -r django -w pypi

# Check VS Code on GitHub (explicit watcher)
python main.py -r microsoft/vscode -w github

# Check a repository from your config.yaml (automatic watcher detection)
python main.py -r microsoft/vscode

# Check nginx Docker image
python main.py -r library/nginx -w dockerhub

# Check Express.js npm package
python main.py -r express -w npm

# Get help
python main.py --help
```

## Configuration

The CLI mode still uses your existing `config.yaml` for:
- Persistence backend configuration
- Notifier settings
- Watcher authentication tokens

Make sure your `config.yaml` has the necessary watcher configurations for the platforms you want to use.

## Automatic Watcher Detection

When you provide only the `--repo` argument (without `--watcher`), the tool will:

1. **Search your config.yaml file** for the specified repository
2. **Use the watcher type** defined in the config for that repository
3. **Apply all repo-specific settings** from the config (like authentication tokens, upload settings, etc.)

This makes it convenient to check repositories that you already have configured without having to remember or specify the watcher type.

### Example

If your `config.yaml` contains:
```yaml
repos:
  - name: "My Project"
    repo: "myuser/myproject"
    watcher: github
    config:
      upload_assets: true
```

You can simply run:
```bash
python main.py -r myuser/myproject
```

And it will automatically use the `github` watcher with the configured settings.

## Error Handling

- If you provide only `--watcher` without `--repo`, you'll get an error message
- If you provide `--repo` without `--watcher` and the repo isn't in your config, you'll get helpful instructions
- If neither is provided, the full checker mode runs
- Any watcher-specific errors (like missing authentication) will be displayed with helpful messages 
