import os
from typing import Any
from urllib.parse import urlparse

import boto3
import yaml

from .base import ConfigLoader


class S3ConfigLoader(ConfigLoader):
    def __init__(self, s3_url: str) -> None:
        self.s3_url = s3_url
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL")  # Optional
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION")

    def load(self) -> dict[str, Any]:
        parsed = urlparse(self.s3_url)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        if not bucket or not key:
            msg = f"Invalid S3 URL format: {self.s3_url}. Expected format: s3://bucket/path/to/config.yaml"
            raise ValueError(msg)

        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                endpoint_url=self.endpoint_url,
                region_name=self.region_name,
            )

            obj = s3.get_object(Bucket=bucket, Key=key)
            content = obj["Body"].read().decode()

            if not content.strip():
                msg = f"Empty S3 config file: {self.s3_url}"
                raise ValueError(msg)

            config = yaml.safe_load(content)
            if config is None:
                msg = f"S3 config file contains only whitespace or is empty: {self.s3_url}"
                raise ValueError(msg)

        except yaml.YAMLError as e:
            msg = f"Invalid YAML in S3 config file {self.s3_url}: {e}"
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"Failed to load config from S3 {self.s3_url}: {e}"
            raise ConnectionError(msg) from e
        else:
            return config  # type: ignore[no-any-return]
