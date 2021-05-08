#!/usr/bin/env python3

from loguru import logger
from rich import box
from rich.console import Console
from rich.table import Table

from prpr.config import get_config
from prpr.homework import Homework, Status
from prpr.startrack_client import get_startack_client

DISPLAYED_TAIL_LENGTH = None


def print_issue_table(homeworks: list[Homework], last=None):
    table = setup_table(last)

    start_from = -last if last else last
    for table_number, homework in enumerate(homeworks[start_from:], 1):
        row_columns = (
            str(table_number),
            homework.issue_url,
            str(homework.number),
            str(homework.problem),
            homework.student,
            homework.pretty_status,
            homework.deadline_string,
            homework.left,
            homework.updated_string,
        )
        table.add_row(
            *row_columns,
            style="dim" if homework.status == Status.ON_THE_SIDE_OF_USER else None,
        )

    console = Console()
    console.print(table)


def setup_table(last: int) -> Table:
    table = Table(title="My Praktikum Review Tickets", box=box.MINIMAL_HEAVY_HEAD)
    table.add_column("#", justify="right")
    table.add_column("ticket")
    table.add_column("no", justify="right")
    table.add_column("pr", justify="right")
    table.add_column("student"),
    table.add_column("st")
    table.add_column("deadline", justify="right")
    table.add_column("left", justify="right")
    table.add_column("updated")
    return table


def sort_homeworks(homeworks: list[Homework]) -> list[Homework]:
    return sorted(homeworks, key=Homework.order_key)


def filter_homeworks(homeworks: list[Homework]) -> list[Homework]:
    return [h for h in homeworks if h.status != Status.RESOLVED]


if __name__ == "__main__":
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
