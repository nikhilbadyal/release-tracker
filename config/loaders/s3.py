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

        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
        )

        obj = s3.get_object(Bucket=bucket, Key=key)
        return yaml.safe_load(obj["Body"].read().decode())  # type: ignore[no-any-return]
