from datetime import datetime
from typing import Optional

from loguru import logger
from rich import box
from rich.console import Console
from rich.table import Table

from prpr.homework import Homework, Status

DISPLAYED_TAIL_LENGTH = None


def print_issue_table(homeworks: list[Homework], last=None, last_processed=None, title: Optional[str] = None):
    if not homeworks:
        logger.warning("No homeworks for chosen filter combination.")
        return
    table = setup_table(homeworks, title)

    start_from = -last if last else last
    for table_number, homework in enumerate(homeworks[start_from:], 1):
        row_columns = (  # TODO: Move to Homework
            str(table_number),
            homework.issue_url,
            str(homework.number),
            str(homework.problem),
            homework.iteration and str(homework.iteration),
            homework.student,
            homework.cohort,
            homework.pretty_status,
            homework.deadline_string,
            homework.left,
            homework.updated_string,
        )
        table.add_row(
            *row_columns,
            style=compute_style(homework, last_processed=last_processed),
        )

    console = Console()
    console.print(table)


def compute_style(homework: Homework, last_processed=None):  # TODO: consider moving to Homework
    if homework == last_processed:
        return "dim"
    if homework.deadline_missed:
        return "red"  # TODO: Move to dotfile
    if homework.deadline and homework.deadline.date() == datetime.now().date():
        return "bold"
    if homework.status == Status.ON_THE_SIDE_OF_USER:
        return "dim"


def setup_table(homeworks: list[Homework], title: Optional[str] = None) -> Table:
    table = Table(title=title, box=box.MINIMAL_HEAVY_HEAD)
    table.add_column("#", justify="right")
    min_ticket_width = max(len(hw.issue_url) for hw in homeworks) if homeworks else None
    table.add_column("ticket", min_width=min_ticket_width)
    table.add_column("no", justify="right")
    table.add_column("pr", justify="right")
    table.add_column("i")
    table.add_column("student")
    table.add_column("co", justify="right")
    table.add_column("st")
    table.add_column("deadline", justify="right")
    table.add_column("left", justify="right")
    table.add_column("updated")
    # TODO: column count should always match tuple length; configure together.
    return table
