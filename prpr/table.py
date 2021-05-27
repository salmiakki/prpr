from datetime import datetime

from rich import box
from rich.console import Console
from rich.table import Table

from prpr.homework import Homework, Status

DISPLAYED_TAIL_LENGTH = None


def print_issue_table(homeworks: list[Homework], last=None):
    table = setup_table(last)

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
            style=compute_style(homework),
        )

    console = Console()
    console.print(table)


def compute_style(homework):  # TODO: consider moving to Homework
    if homework.deadline_missed:
        return "red"  # TODO: Move to dotfile
    if homework.deadline and homework.deadline.date() == datetime.now().date():
        return "bold"
    if homework.status == Status.ON_THE_SIDE_OF_USER:
        return "dim"


def setup_table(last: int) -> Table:
    table = Table(title="My Praktikum Review Tickets", box=box.MINIMAL_HEAVY_HEAD)
    table.add_column("#", justify="right")
    table.add_column("ticket")
    table.add_column("no", justify="right")
    table.add_column("pr", justify="right")
    table.add_column("i")
    table.add_column("student")
    table.add_column("coh")
    table.add_column("st")
    table.add_column("deadline", justify="right")
    table.add_column("left", justify="right")
    table.add_column("updated")
    # TODO: column count should always match tuple length; configure together.
    return table
