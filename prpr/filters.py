from __future__ import annotations

import datetime as dt
from enum import Enum, auto
from typing import Any, Iterable, Optional, Union

from dateutil.relativedelta import relativedelta
from loguru import logger

from prpr.date_utils import month_start_and_end
from prpr.homework import CLOSED_STATUSES, OPEN_STATUSES, Homework, Status

DEFAULT_MONTH_START = 16


class FilterMode(Enum):
    STANDARD = auto()
    ALL = auto()
    OPEN = auto()
    CLOSED = auto()
    CLOSED_THIS_MONTH = auto()
    CLOSED_PREVIOUS_MONTH = auto()

    def __str__(self):
        return self.name.lower().replace("_", "-")

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_string(mode: str) -> FilterMode:
        try:
            return FilterMode[mode.upper().replace("-", "_")]
        except KeyError:
            logger.error(f"Unexpected mode: '{mode}' 😿")
            return mode


def filter_homeworks(
    homeworks: list[Homework],
    *,
    mode: FilterMode,
    config: dict[str, Union[str, int, dict[str, Any]]],
    problems: Optional[list[int]] = None,
    no: Optional[int] = None,
    student: Optional[str] = None,
    cohorts: Optional[str] = None,
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

    if mode == FilterMode.STANDARD:
        result = _filter_homeworks_by_status(homeworks, CLOSED_STATUSES, invert=True)
    elif mode == FilterMode.ALL:
        result = homeworks
    elif mode == FilterMode.OPEN:
        result = _filter_homeworks_by_status(homeworks, OPEN_STATUSES)
    elif mode == FilterMode.CLOSED:
        result = _filter_homeworks_by_status(homeworks, CLOSED_STATUSES)
    elif mode in (FilterMode.CLOSED_THIS_MONTH, FilterMode.CLOSED_PREVIOUS_MONTH):
        if from_date or to_date:
            logger.warning(f"date filters are ignored for mode {mode} ⚠️")
        result = _filter_homeworks_by_status(homeworks, CLOSED_STATUSES)
        month_start = config.get("month_start", DEFAULT_MONTH_START)
        day_in_month = dt.date.today()
        if mode == FilterMode.CLOSED_PREVIOUS_MONTH:
            day_in_month = day_in_month + relativedelta(months=-1)
        from_date, to_date = month_start_and_end(day_in_month, month_start=month_start)
        logger.info(f"Chosen 'month' is {from_date:%Y-%m-%d} -- {to_date:%Y-%m-%d}.")
    else:
        logger.error(f"{mode=}")

    if problems:
        result = [h for h in result if h.problem in problems]
    if student:
        result = [h for h in result if student in h.student]
    if cohorts:
        result = [h for h in result if h.cohort in cohorts]
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
