from __future__ import annotations

import datetime as dt
from enum import Enum, auto
from typing import Any, Iterable, Optional, Union

from loguru import logger

from prpr.date_utils import month_start_and_end
from prpr.homework import Homework, Status

DEFAULT_MONTH_START = 15

OPEN_STATUSES = {Status.OPEN, Status.IN_REVIEW}
CLOSED_STATUSES = {Status.RESOLVED, Status.CLOSED}


class Mode(Enum):
    STANDARD = auto()
    ALL = auto()
    OPEN = auto()
    CLOSED = auto()
    CLOSED_THIS_MONTH = auto()

    def __str__(self):
        return self.name.lower().replace("_", "-")

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_string(mode: str) -> Mode:
        try:
            return Mode[mode.upper().replace("-", "_")]
        except KeyError:
            logger.error(f"Unexpected mode: '{mode}' 😿")
            return mode


def filter_homeworks(
    homeworks: list[Homework],
    *,
    mode: Mode,
    config: dict[str, Union[str, int, dict[str, Any]]],
    problems: Optional[list[int]] = None,
    no: Optional[int] = None,
    student: Optional[str] = None,
    from_date: Optional[dt.date] = None,
    to_date: Optional[dt.date] = None,
) -> list[Homework]:
    # TODO: return description as well to be used in the table title
    if no:
        result = [h for h in homeworks if h.number == no]
        if not result:
            logger.error(f"Homework with no {no} was not found 😿")
            exit(1)
        return result

    if mode == Mode.STANDARD:
        result = _filter_homeworks_by_status(homeworks, CLOSED_STATUSES, invert=True)
    elif mode == Mode.ALL:
        result = homeworks
    elif mode == Mode.OPEN:
        result = _filter_homeworks_by_status(homeworks, OPEN_STATUSES)
    elif mode == Mode.CLOSED:
        result = _filter_homeworks_by_status(homeworks, CLOSED_STATUSES)
    elif mode == Mode.CLOSED_THIS_MONTH:
        if from_date or to_date:
            logger.warning(f"date filters are ignored for mode {Mode.CLOSED_THIS_MONTH} ⚠️")
        result = _filter_homeworks_by_status(homeworks, CLOSED_STATUSES)
        month_start = config.get("month_start", DEFAULT_MONTH_START)
        from_date, to_date = month_start_and_end(dt.date.today(), month_start=month_start)
        logger.info(f"This 'month' is {from_date:%Y-%m-%d} -- {to_date:%Y-%m-%d}.")
    else:
        logger.error(f"{mode=}")

    if problems:
        result = [h for h in result if h.problem in problems]
    if student:
        result = [h for h in result if student in h.student]
    if from_date:
        from_date = dt.datetime.combine(from_date, dt.time.min).astimezone()
        result = [h for h in result if from_date <= h.status_updated]
    if to_date:
        to_date = dt.datetime.combine(to_date, dt.time.max).astimezone()
        result = [h for h in result if h.status_updated <= to_date]
    return result


def _filter_homeworks_by_status(homeworks: Iterable[Homework], statuses: set[Status], invert: bool = False):
    if not invert:
        return [h for h in homeworks if h.status in statuses]
    return [h for h in homeworks if h.status not in statuses]
