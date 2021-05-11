#!/usr/bin/env python3

from loguru import logger

from prpr.config import get_config
from prpr.homework import Homework, Status
from prpr.startrack_client import get_startack_client
from prpr.table import DISPLAYED_TAIL_LENGTH, print_issue_table


def sort_homeworks(homeworks: list[Homework]) -> list[Homework]:
    return sorted(homeworks, key=Homework.order_key)


def filter_homeworks(homeworks: list[Homework]) -> list[Homework]:
    return [h for h in homeworks if h.status != Status.RESOLVED]


def main():
    config = get_config()
    client = get_startack_client(config)

    issues = client.get_issues()
    logger.debug(f"Got {len(issues)} homeworks.")
    homeworks = [
        Homework(
            issue_key=issue.key,
            summary=issue.summary,
            status=issue.status.key,
            status_updated=issue.statusStartTime,
            description=issue.description,
            number=number,
            first=issue.previousStatus is None,
        )
        for number, issue in enumerate(issues, 1)
    ]
    filtered_homeworks = filter_homeworks(homeworks)
    sorted_homeworks = sort_homeworks(filtered_homeworks)
    print_issue_table(sorted_homeworks, last=DISPLAYED_TAIL_LENGTH)


if __name__ == "__main__":
    main()
