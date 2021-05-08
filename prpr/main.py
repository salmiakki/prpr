#!/usr/bin/env python3

from loguru import logger

from prpr.config import get_config
from prpr.startrack_client import get_startack_client

if __name__ == "__main__":
    config = get_config()
    client = get_startack_client(config)

    issues = client.get_issues()

    for issue in issues[-15:]:
        logger.debug(f"{issue.key}, {issue.summary}")
