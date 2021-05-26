import json
from datetime import datetime
from typing import Optional, Tuple

import requests
from loguru import logger
from yandex_tracker_client import TrackerClient

from prpr.date_utils import parse_datetime
from prpr.homework import Homework, Status, StatusTransition

YANDEX_ORG_ID = 0
STARTREK_TOKEN_KEY_NAME = "startrek_token"


class PraktikTrackerClient(TrackerClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = kwargs["token"]

    def get_issues(self):
        filter_expression = {
            "queue": "PCR",
            "assignee": "me()",
        }
        logger.debug("Fetching issues...")
        issues = self.issues.find(filter=filter_expression)
        sorted_issues = sorted(issues, key=by_issue_key)
        return sorted_issues

    def get_status_history(self, issue_key: str, issue_status: str) -> Optional[list[StatusTransition]]:
        if issue_status not in {"open", "inReview"}:  # TODO: make configurable
            return None
        try:
            changes = requests.get(
                f"https://st-api.yandex-team.ru/v2/issues/{issue_key}/changelog",
                headers={"Authorization": f"OAuth {self.token}"},
            ).json()
        except (requests.RequestException, json.JSONDecodeError):
            logger.exception("Failed to fetch status history for {} 😿", issue_key)
        transitions = []
        for change in changes:
            if not isinstance(change, dict):
                logger.warning(f"Unexpected change for {issue_key}: {change} 😿")
                return []
            try:
                timestamp = change.get("updatedAt")
                parsed_timestamp = parse_datetime(timestamp)
            except AttributeError:
                logger.exception("Failed to parse change {} for {} 😿", change, issue_key)
            for field in change.get("fields", []):
                if field["field"]["id"] == "status":
                    from_status_string = (field.get("from", {}) or {}).get("key", None)  # to Status
                    to_status_string = field["to"]["key"]
                    from_status = Status.from_string(from_status_string) if from_status_string else None
                    to_status = Status.from_string(to_status_string)
                    t = StatusTransition(from_status, to_status, parsed_timestamp)
                    transitions.append(t)
        return transitions

    def get_iteration_and_updated(self, key) -> Tuple[int, Optional[datetime]]:
        transitions = self.get_status_history(key)
        iteration = StatusTransition.compute_iteration(transitions)
        timestamps = [t.timestamp for t in transitions if t.to == Status.OPEN]
        last_open = timestamps[-1] if timestamps else None
        return iteration, last_open


def get_startack_client(config) -> PraktikTrackerClient:
    if STARTREK_TOKEN_KEY_NAME not in config:
        logger.error(f"{STARTREK_TOKEN_KEY_NAME} top-level key not found in config 😿")
        exit(1)
    token = config[STARTREK_TOKEN_KEY_NAME]
    return PraktikTrackerClient(org_id=YANDEX_ORG_ID, base_url="https://st-api.yandex-team.ru", token=token)


def by_issue_key(issue) -> int:
    key: str = issue.key  # e.g. PCR-12345
    return Homework.to_issue_key_number(key)
