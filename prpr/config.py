from pathlib import Path

import yaml
from loguru import logger

CONFIG_FILENAME = ".prpr.yaml"


def get_config():
    config_path = Path.home() / CONFIG_FILENAME
    if not config_path.exists():
        logger.error(f"{CONFIG_FILENAME} not found in your home directory 😿")
        exit(1)
    logger.debug(f"Reading config from {config_path}...")
    with open(config_path) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
