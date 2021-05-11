from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Tuple

from loguru import logger


class Status(Enum):
    IN_REVIEW = "inReview"
    OPEN = "open"
    ON_THE_SIDE_OF_USER = "onTheSideOfUser"
    RESOLVED = "resolved"


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
        status: str,  # e.g. "open"
        status_updated: str,  # e.g. "2020-09-23T22:14:37.658+0000"
        description: str,
        number: int,  # the ordinal number in of all one's tickets sorted by issue key
        first: bool,
    ):
        self.first = first  # TODO: remove
        self.number = number
        self.status_updated = self._parse_datetime(status_updated)
        self.problem, self.student = self._extract_problem_and_student(summary)
        self.status = Status(status)
        self.issue_key = issue_key

    @property
    def deadline(self) -> datetime:
        return self._compute_deadline(self.status_updated, self.status)

    @property
    def deadline_string(self) -> Optional[str]:
        if self.deadline is None:
            return None
        return f"{self.deadline:{self.DEADLINE_FORMAT}}"

    @property
    def updated_string(self) -> Optional[str]:
        if self.status_updated is None or self.deadline:
            return None
        age = datetime.now().astimezone(tz=None) - self.status_updated
        if age > timedelta(days=7):
            return f"{self.status_updated:{self.UPDATED_LONG_AGO_FORMAT}} ({age.days} days ago)"
        return f"{self.status_updated:{self.UPDATED_FORMAT}}"

    @property
    def _left_seconds(self) -> Optional[int]:
        """Seconds to deadline. Negative for missed deadlines"""
        if self.deadline is None:
            return None
        td = self.deadline - datetime.now().astimezone(tz=None)
        return int(td.total_seconds())

    @property
    def _left_hours_and_minutes(self) -> Optional[Tuple[int, int]]:
        if self.deadline is None:
            return None
        total_seconds = self._left_seconds
        hours, seconds = divmod(total_seconds, self.SECONDS_PER_HOUR)
        minutes = seconds // self.SECONDS_PER_MINUTE
        return hours, minutes

    @property
    def left(self) -> Optional[str]:
        """E.g. "1:03"."""
        if self.deadline is None:
            return None
        hours, minutes = self._left_hours_and_minutes
        return f"{hours:2d}:{minutes:02d}"

    @property
    def deadline_missed(self):
        return self._left_seconds is not None and self._left_seconds < 0

    @property
    def pretty_status(self) -> str:
        if self.deadline_missed:
            return "🙀"
        return {
            Status.IN_REVIEW: "🔎",
            Status.OPEN: "🔧",
            Status.ON_THE_SIDE_OF_USER: "🎓",
            Status.RESOLVED: "✔️",
        }.get(self.status, "⁉️")

    @staticmethod
    def _compute_deadline(status_updated: Optional[datetime], status: Status) -> Optional[datetime]:
        # TODO: handle IN_REVIEW homeworks (relies on iteration support)
        return status_updated + timedelta(days=1) if status in {Status.OPEN} else None

    def __repr__(self) -> str:
        return f"no {self.number}: {self.student} {self.problem} ({self.status})"

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

    @staticmethod
    def order_key(homework: Homework) -> Tuple[int, datetime]:
        status_order = {
            Status.IN_REVIEW: 0,
            Status.OPEN: 1,
            Status.ON_THE_SIDE_OF_USER: 2,
            Status.RESOLVED: 3,
        }
        if homework.status not in status_order:
            logger.warning(f"Unexpected status: {homework.status} for {homework.issue_key}")
        return status_order.get(homework.status, -1), homework.status_updated

    @staticmethod
    def _parse_datetime(datetime_string: Optional[str]) -> Optional[datetime]:
        """E.g. "2020-09-23T22:14:37.658+0000" -> datetime(2020, 9, 23, 22, 14, 37) (more or less)."""
        if datetime_string is None:
            return None
        # Note to self: dateutil can parse these dates.
        utc_tz_suffix = "+0000"
        if not datetime_string.endswith(utc_tz_suffix):
            raise ValueError(f"Unexpected datetime string format: {datetime_string} 😿")
        datetime_wo_tz = datetime_string.removesuffix(utc_tz_suffix)
        naive_utc_datetime = datetime.fromisoformat(datetime_wo_tz)
        local_datetime = naive_utc_datetime.replace(tzinfo=timezone.utc).astimezone(tz=None)
        # It's not actually local, it's naive. TODO: add local tz
        return local_datetime
