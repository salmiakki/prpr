#!/usr/bin/env python3

from loguru import logger
from rich import box
from rich.console import Console
from rich.table import Table

from prpr.config import get_config
from prpr.startrack_client import get_startack_client

DISPLAYED_TAIL_LENGTH = 15


def print_issue_table(issues, last=None):
    table = setup_table(last)

    start_from = -last if last else last
    for table_number, issue in enumerate(issues[start_from:], 1):
        row_columns = (
            str(table_number),
            f"https://st.yandex-team.ru/{issue.key}",
            str(issue.prpr_number),
            issue.summary,
        )
        table.add_row(
            *row_columns,
            end_section=table_number == 10,
            style="dim" if table_number > 10 else None,
        )

    console = Console()
    console.print(table)


def setup_table(last):
    table = Table(title=f"My Praktikum Review Tickets ({last} last)", box=box.MINIMAL_HEAVY_HEAD)
    table.add_column("#", justify="right")
    table.add_column("ticket")
    table.add_column("no")
    table.add_column("summary")
    return table


if __name__ == "__main__":
    config = get_config()
    client = get_startack_client(config)

    issues = client.get_issues()
    logger.debug(f"Got {len(issues)} issues.")
    print_issue_table(issues, last=DISPLAYED_TAIL_LENGTH)
