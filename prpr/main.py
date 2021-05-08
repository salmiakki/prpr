#!/usr/bin/env python3

from loguru import logger
from rich import box
from rich.console import Console
from rich.table import Table

from prpr.config import get_config
from prpr.homework import Homework
from prpr.startrack_client import get_startack_client

DISPLAYED_TAIL_LENGTH = 15


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
            homework.status.value,
        )
        table.add_row(
            *row_columns,
            end_section=table_number == 10,  # Just a demo at the time of writing.
            style="dim" if table_number > 10 else None,
        )

    console = Console()
    console.print(table)


def setup_table(last: int) -> Table:
    table = Table(title=f"My Praktikum Review Tickets ({last} last)", box=box.MINIMAL_HEAVY_HEAD)
    table.add_column("#", justify="right")
    table.add_column("ticket")
    table.add_column("no", justify="right")
    table.add_column("pr", justify="right")
    table.add_column("student"),
    table.add_column("status")
    return table


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
            status_updated=None,
            description=issue.description,
            number=number,
            first=issue.previousStatus is None,
        )
        for number, issue in enumerate(issues, 1)
    ]
    print_issue_table(homeworks, last=DISPLAYED_TAIL_LENGTH)
