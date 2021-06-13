from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum
from typing import Optional, Tuple

from loguru import logger

from prpr.date_utils import LOCAL_TIMEZONE, parse_datetime


class Status(IntEnum):
    UNKNOWN = -1
    IN_REVIEW = 0
    OPEN = 1
    ON_THE_SIDE_OF_USER = 2
    RESOLVED = 3
    CLOSED = 4

    # If a new status is added, update Homework.pretty_status accordingly

    @staticmethod  # can't have class variables in Enums
    def from_string(status: str) -> Status:
        status_map = {
            "inReview": Status.IN_REVIEW,
            "open": Status.OPEN,
            "onTheSideOfUser": Status.ON_THE_SIDE_OF_USER,
            "resolved": Status.RESOLVED,
            "closed": Status.CLOSED,
        }
        assert len(Status) - 1 == len(status_map), "status_map is probably missing some keys."
        try:
            return status_map[status]
        except KeyError:
            logger.error(f"Unexpected status: {status}.")
            return Status.UNKNOWN


OPEN_STATUSES = {Status.OPEN, Status.IN_REVIEW}
CLOSED_STATUSES = {Status.CLOSED, Status.RESOLVED}


class Homework:
    SECONDS_PER_MINUTE = 60
    SECONDS_PER_HOUR = 3600
    DEADLINE_FORMAT = "%A, %H:%M"  # TODO: move these to settings
    UPDATED_FORMAT = "%m-%d (%A), %H:%M"
    UPDATED_LONG_AGO_FORMAT = "%m-%d"

    def __init__(
        self,
        issue_key: str,  # e.g. "PCR-12345"
        summary: str,  # e.g. "[1] Даниил Хармс (yuvachev@yandex.ru)"
        cohort: str,  # e.g. "16", "1+"
        status: str,  # e.g. "open"
        status_updated: str,  # e.g. "2020-09-23T22:14:37.658+0000"
        description: str,
        number: int,  # the ordinal number in of all one's tickets sorted by issue key
        first: bool,
        course: str,  # e.g. "backend-developer"
        transitions: Optional[list[StatusTransition]] = None,
    ):
        self.first = first  # TODO: remove
        self.number = number
        self.status_updated = parse_datetime(status_updated)
        self.description = description
        problem, student = self._extract_problem_and_student(summary)
        self.problem = problem
        self.student = student
        self.cohort = cohort
        self.status = Status.from_string(status)
        self.issue_key = issue_key
        self.course = course
        self._iteration: Optional[int] = StatusTransition.compute_iteration(transitions)
        self.last_opened: Optional[datetime] = StatusTransition.compute_last_opened(transitions)

    @property
    def iteration(self):
        if cached := self._iteration:
            return cached
        if self.resolved:
            return None
        # We could retrieve iterations here, lazily. I don't want to inject the client instance though.
        # Suggestions are welcome.

    @property
    def deadline(self) -> Optional[datetime]:
        return self._compute_deadline(self.status_updated, self.status, self.last_opened)

    @property
    def deadline_string(self) -> Optional[str]:
        if self.deadline is None:
            return None
        return f"{self.deadline:{self.DEADLINE_FORMAT}}"

    @property
    def resolved(self) -> bool:
        return self.status in CLOSED_STATUSES

    @property
    def open_or_in_review(self) -> bool:
        return self.status in OPEN_STATUSES

    @property
    def updated_string(self) -> Optional[str]:
        if self.status_updated is None or self.deadline:
            return None
        age = datetime.now(LOCAL_TIMEZONE) - self.status_updated
        if age > timedelta(days=7):
            return f"{self.status_updated:{self.UPDATED_LONG_AGO_FORMAT}} ({age.days} days ago)"
        return f"{self.status_updated:{self.UPDATED_FORMAT}}"

    @property
    def _left_seconds(self) -> Optional[int]:
        """Seconds to deadline. Negative for missed deadlines"""
        if self.deadline is None:
            return None
        td = self.deadline - datetime.now(LOCAL_TIMEZONE)
        return int(td.total_seconds())

    @property
    def _left_hours_and_minutes(self) -> Optional[Tuple[int, int, bool]]:
        """Return hours, minutes and True if deadline is missed, False otherwise"""
        if self.deadline is None:
            return None
        total_seconds = self._left_seconds
        hours, seconds = divmod(abs(total_seconds), self.SECONDS_PER_HOUR)
        minutes = seconds // self.SECONDS_PER_MINUTE
        return hours, minutes, total_seconds < 0

    @property
    def left(self) -> Optional[str]:
        """E.g. "1:03"."""
        if self.deadline is None:
            return None
        hours, minutes, missed = self._left_hours_and_minutes
        if missed:
            return f"-{hours:d}:{minutes:02d}"
        return f"{hours:d}:{minutes:02d}"

    @property
    def deadline_missed(self):
        return self._left_seconds is not None and self._left_seconds < 0

    @property
    def pretty_status(self) -> str:
        if self.deadline_missed and self.status == Status.OPEN:
            return "🙀"
        return {
            Status.IN_REVIEW: "🔎",
            Status.OPEN: "🔧",
            Status.ON_THE_SIDE_OF_USER: "🎓",
            Status.RESOLVED: "✔️",
            Status.CLOSED: "✔️",
        }.get(self.status, "⁉️")

    @staticmethod
    def _compute_deadline(
        status_updated: Optional[datetime], status: Status, last_opened: Optional[datetime] = None
    ) -> Optional[datetime]:
        if status in {Status.OPEN, Status.IN_REVIEW}:
            if updated := (last_opened or status_updated):
                return updated + timedelta(days=1)
        return None

    def __str__(self) -> str:
        if self.iteration:
            problem = f"{self.problem}.{self.iteration}"
        else:
            problem = f"{self.problem}"
        return f"{self.issue_key}, no {self.number}: {problem} {self.student} ({self.status.name})"

    @staticmethod
    def _extract_problem_and_student(summary) -> Tuple[int, str]:
        if m := re.match(r"\[(?P<problem>\d+)( \(back_cohort_(?P<cohort>\d+)\))?\] (?P<student>.*)", summary):
            return int(m.group("problem")), m.group("student")
        raise ValueError(f"Couldn't parse summary '{summary}' 😿")

    @property
    def issue_url(self) -> str:
        return f"https://st.yandex-team.ru/{self.issue_key}"

    @staticmethod
    def to_issue_key_number(key: str) -> int:
        """E.g. "PCR-69105" -> 69105."""
        assert key.startswith("PCR-")
        return int(key.removeprefix("PCR-"))

    @property
    def issue_key_number(self) -> int:
        return self.to_issue_key_number(self.issue_key)

    @property
    def revisor_url(self) -> str:
        if m := re.search(
            r"==(?P<url>https://praktikum-admin\.yandex-team\.ru/office/revisor-review/(\d+)/(\w+))\b",
            self.description,
        ):
            return m.group("url")
        logger.warning(f"Failed to extract Revisor url from '{self.description}' 😿")
        return None

    @staticmethod
    def order_key(homework: Homework) -> Tuple[int, datetime]:
        return homework.status, homework.status_updated


@dataclass
class StatusTransition:
    from_: Optional[Status]
    to: Status
    timestamp: datetime

    @staticmethod
    def compute_iteration(transitions: Optional[list[StatusTransition]]) -> Optional[int]:
        if not transitions:
            return None
        iteration = sum(1 for t in transitions if t.to == Status.OPEN)
        return iteration

    @staticmethod
    def compute_last_opened(transitions: Optional[list[StatusTransition]]) -> Optional[datetime]:
        if not transitions:
            return None
        opened_timestamps = [t.timestamp for t in transitions if t.to == Status.OPEN]
        last_opened = opened_timestamps[-1] if opened_timestamps else None
        return last_opened
