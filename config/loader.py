import os
import sys
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from config.loaders.http import HTTPConfigLoader
from config.loaders.local import LocalConfigLoader
from config.loaders.s3 import S3ConfigLoader
from logging_config import get_logger

if TYPE_CHECKING:
    from config.loaders.base import ConfigLoader

logger = get_logger(__name__)


def get_config_source() -> str:
    # Priority: CLI > ENV > Default
    if len(sys.argv) > 1 and sys.argv[1].startswith("--config="):
        source = sys.argv[1].split("=", 1)[1]
        logger.info("Using config source from CLI argument: %s", source)
        return source

    env_source = os.getenv("CONFIG_SOURCE")
    if env_source:
        logger.info("Using config source from CONFIG_SOURCE env var: %s", env_source)
        return env_source

    logger.info("Using default config source: config.yaml")
    return "config.yaml"


def load_config() -> dict[str, Any]:
    source = get_config_source()
    parsed = urlparse(source)

    loader: ConfigLoader

    if parsed.scheme == "s3":
        logger.info("Using S3ConfigLoader for config source: %s", source)
        loader = S3ConfigLoader(source)
    elif parsed.scheme in {"http", "https"}:
        logger.info("Using HTTPConfigLoader for config source: %s", source)
        loader = HTTPConfigLoader(source)
    else:
        logger.info("Using LocalConfigLoader for config source: %s", source)
        loader = LocalConfigLoader(source)

    return loader.load()
