from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Tuple


class Status(Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    ON_THE_SIDE_OF_USER = "onTheSideOfUser"
    REVIEW = "?"


class Homework:
    def __init__(
        self,
        issue_key: str,  # e.g. "PCR-12345"
        summary: str,
        status: str,  # e.g. "open"
        status_updated: str,  # e.g. "2020-09-23T22:14:37.658+0000"
        description: str,
        number: int,
        first: bool,
    ):
        self.first = first
        self.number = number
        self.status_updated = self._parse_datetime(status_updated)
        self.problem, self.student = self._extract_problem_and_student(summary)
        self.status = Status(status)
        self.issue_key = issue_key

    @property
    def deadline(self):
        return self._compute_deadline(self.status_updated, self.status)

    @property
    def deadline_string(self):
        if self.deadline is None:
            return None
        DEADLINE_FORMAT = "%A, %H:%M"
        return f"{self.deadline:{DEADLINE_FORMAT}}"

    @property
    def updated_string(self):
        if self.status_updated is None:
            return None
        UPDATED_FORMAT = "%m-%d (%A), %H:%M"
        return f"{self.status_updated:{UPDATED_FORMAT}}"

    @property
    def left_s(self):
        if self.deadline is None:
            return None
        td = self.deadline - datetime.now().astimezone(tz=None)
        return int(td.total_seconds())

    @property
    def left_h_m(self):
        if self.deadline is None:
            return None
        total_seconds = self.left_s
        hours, seconds = divmod(total_seconds, 3600)
        minutes = seconds // 60
        return hours, minutes

    @property
    def left(self):
        if self.deadline is None:
            return None
        hours, minutes = self.left_h_m
        return f"{hours:2d}:{minutes:02d}"

    @property
    def pretty_status(self) -> str:
        if self.missed_deadline:
            return "🙀"
        return {
            Status.REVIEW: "🔎",
            Status.OPEN: "🔧",
            Status.ON_THE_SIDE_OF_USER: "🎓",
            Status.RESOLVED: "✔️",
        }.get(self.status)

    @property
    def missed_deadline(self):
        return self.left_s is not None and self.left_s < 0

    @staticmethod
    def _compute_deadline(status_updated: Optional[datetime], status: Status) -> Optional[datetime]:
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
        """E.g. "PCR-69105" -> 69105"""
        assert key.startswith("PCR-")
        return int(key.removeprefix("PCR-"))

    @staticmethod
    def order_key(homework: Homework) -> Tuple[int, datetime]:
        status_order = {
            Status.REVIEW: 0,
            Status.OPEN: 1,
            Status.ON_THE_SIDE_OF_USER: 2,
            Status.RESOLVED: 3,
        }
        return status_order.get(homework.status, -1), homework.status_updated

    @staticmethod
    def _parse_datetime(datetime_string: Optional[str]) -> Optional[datetime]:
        if datetime_string is None:
            return None
        utc_tz_suffix = "+0000"
        if not datetime_string.endswith(utc_tz_suffix):
            raise ValueError(f"Unexpected datetime string format: {datetime_string} 😿")
        datetime_wo_tz = datetime_string.removesuffix(utc_tz_suffix)
        naive_utc_datetime = datetime.fromisoformat(datetime_wo_tz)
        local_datetime = naive_utc_datetime.replace(tzinfo=timezone.utc).astimezone(tz=None)
        return local_datetime
