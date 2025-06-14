# Configuration Sources

Release Tracker supports multiple configuration sources to fit different deployment scenarios. You can specify the configuration source using the `CONFIG_SOURCE` environment variable or the `--config=` CLI argument.

## 📁 **Local File** (Default)

Load configuration from a local YAML file.

**Format:** `config.yaml` or `/path/to/config.yaml`

**Example:**
```bash
export CONFIG_SOURCE="config.yaml"
# or
python main.py --config=config.yaml
```

## 🌐 **HTTP/HTTPS**

Load configuration from a remote HTTP(S) endpoint.

**Format:** `https://domain.com/path/to/config.yaml`

**Features:**
- Automatic retry on failure (3 attempts)
- 10 second timeout
- YAML validation

**Example:**
```bash
export CONFIG_SOURCE="https://raw.githubusercontent.com/user/repo/main/config.yaml"
```

## ☁️ **AWS S3**

Load configuration from an S3 bucket.

**Format:** `s3://bucket-name/path/to/config.yaml`

**Environment Variables:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region
- `S3_ENDPOINT_URL` - Custom S3 endpoint (optional)

**Example:**
```bash
export CONFIG_SOURCE="s3://my-configs/release-tracker/config.yaml"
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

## 🔄 **Configuration Priority**

Configuration sources are checked in this order:

1. **CLI Argument:** `--config=source`
2. **Environment Variable:** `CONFIG_SOURCE=source`
3. **Default:** `config.yaml`

## 🛠️ **Advanced Usage**

### Multiple Environment Support

```bash
# Development
export CONFIG_SOURCE="git+https://github.com/company/configs/dev-config.yaml@dev"

# Staging
export CONFIG_SOURCE="consul://consul-staging:8500/release-tracker/config"

# Production
export CONFIG_SOURCE="aws-ssm:///prod/release-tracker/config"
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  release-tracker:
    image: release-tracker
    environment:
      - CONFIG_SOURCE=consul://consul:8500/release-tracker/config
      - CONSUL_TOKEN=${CONSUL_TOKEN}
    depends_on:
      - consul
```

### Kubernetes Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: release-tracker-config
data:
  CONFIG_SOURCE: "aws-ssm:///k8s/release-tracker/"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: release-tracker
spec:
  template:
    spec:
      containers:
      - name: release-tracker
        image: release-tracker
        envFrom:
        - configMapRef:
            name: release-tracker-config
        env:
        - name: AWS_REGION
          value: "us-east-1"
```

## 🚨 **Error Handling**

All configuration loaders include:
- **Validation:** Ensures configuration format is correct
- **Retry Logic:** Automatic retry for network-based sources
- **Clear Error Messages:** Specific error descriptions for troubleshooting
- **Graceful Degradation:** Fallback behavior when possible

## 🔧 **Adding New Sources**

To add a new configuration source:

1. Create a new loader class inheriting from `ConfigLoader`
2. Implement the `load()` method
3. Add URL scheme detection to `config/loader.py`
4. Update this documentation

Example:
```python
from config.loaders.base import ConfigLoader

class MyCustomLoader(ConfigLoader):
    def load(self) -> dict[str, Any]:
        # Your implementation here
        return config
```
