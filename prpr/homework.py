import re
from datetime import datetime, timedelta
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
        issue_key: str,  # e.g. PCR-12345
        summary: str,
        status: str,  # e.g. "open"
        status_updated: datetime,
        description: str,
        number: int,
        first: bool,
    ):
        self.first = first
        self.number = number
        self.status_updated = status_updated
        self.problem, self.student = self._extract_problem_and_student(summary)
        self.status = Status(status)
        self.deadline: Optional[datetime] = self._compute_deadline(status, status_updated)
        self.issue_key = issue_key

    @staticmethod
    def _compute_deadline(status, status_updated):
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
