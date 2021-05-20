from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, Optional

from loguru import logger

from prpr.homework import Homework, Status

OPEN_STATUSES = {Status.OPEN, Status.IN_REVIEW}
CLOSED_STATUSES = {Status.RESOLVED, Status.CLOSED}


class Mode(Enum):
    DEFAULT = auto()
    ALL = auto()
    OPEN = auto()
    CLOSED = auto()

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_string(mode: str) -> Mode:
        try:
            return Mode[mode.upper()]
        except KeyError:
            logger.error(f"Unexpected mode: '{mode}' 😿")
            return mode


def filter_homeworks(
    homeworks: list[Homework],
    *,
    mode: Mode,
    projects: Optional[list[int]] = None,
    no: Optional[int] = None,
    student: Optional[str] = None,
) -> list[Homework]:
    # TODO: return description as well to be used in the table title
    if no:
        result = [h for h in homeworks if h.number == no]
        if not result:
            logger.error(f"Homework with no {no} was not found 😿")
            exit(1)
        return result

    if mode == Mode.DEFAULT:
        result = _filter_homeworks_by_status(homeworks, CLOSED_STATUSES, invert=True)
    elif mode == Mode.ALL:
        result = homeworks
    elif mode == Mode.OPEN:
        result = _filter_homeworks_by_status(homeworks, OPEN_STATUSES)
    elif mode == Mode.CLOSED:
        result = _filter_homeworks_by_status(homeworks, CLOSED_STATUSES)

    if projects:
        result = [h for h in result if h.project in projects]
    if student:
        result = [h for h in result if student in h.student]
    return result


def _filter_homeworks_by_status(homeworks: Iterable[Homework], statuses: set[Status], invert: bool = False):
    if not invert:
        return [h for h in homeworks if h.status in statuses]
    return [h for h in homeworks if h.status not in statuses]
