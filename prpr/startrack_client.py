from typing import Optional

import requests_cache
from loguru import logger
from requests.utils import check_header_validity
from yandex_tracker_client import TrackerClient
from yandex_tracker_client.connection import Connection
from yandex_tracker_client.exceptions import TrackerClientError
from yandex_tracker_client.objects import Resource

from prpr.date_utils import parse_datetime
from prpr.homework import Homework, Status, StatusTransition

YANDEX_ORG_ID = 0
STARTREK_TOKEN_KEY_NAME = "startrek_token"


class CachedConnection(Connection):
    def __init__(self, token, org_id, headers=None, verify=True, **kwargs):
        super().__init__(token, org_id, headers=headers, verify=verify, **kwargs)
        self.session = requests_cache.CachedSession(backend='memory')

        self.session.verify = verify

        if headers is not None:
            self.session.headers.update(headers)

        self.session.headers['Authorization'] = 'OAuth ' + (token or 'not provided')
        self.session.headers['X-Org-Id'] = org_id or 'not provided'
        self.session.headers['Content-Type'] = 'application/json'

        # Check validity headers for requests >= 2.11
        for header in self.session.headers.items():
            check_header_validity(header)


class PraktikTrackerClient(TrackerClient):
    def __init__(self, *args, **kwargs):
        self.connector = kwargs.pop('connector', Connection)
        connection = kwargs.pop('connection', None)
        if connection is None:
            connection = self.connector(*args, **kwargs)

        super().__init__(*args, connection=connection, **kwargs)
        self.token = kwargs["token"]

    def _get_filter_expression(self, user: Optional[str] = None):
        return {
            "queue": "PCR",
            "assignee": user or "me()",
        }

    def get_issues(self, user: Optional[str] = None):
        logger.debug("Fetching issues...")
        issues = self.issues.find(filter=self._get_filter_expression(user))
        sorted_issues = sorted(issues, key=by_issue_key)
        return sorted_issues

    def get_status_history(self, issue) -> Optional[list[StatusTransition]]:
        issue_key, issue_status = issue.key, issue.status.key
        if issue_status not in {"open", "inReview"}:  # TODO: make configurable
            return None
        logger.debug(f"Fetching status history for {issue_key}")
        try:
            changes = issue.changelog.get_all()
        except TrackerClientError:
            logger.exception("Failed to fetch status history for {} 😿", issue_key)
            return []

        transitions = []
        for change in changes:
            if not isinstance(change, Resource):
                logger.warning(f"Unexpected change for {issue_key}: {change} 😿")
                return []
            try:
                timestamp = change.updatedAt
                parsed_timestamp = parse_datetime(timestamp)
            except AttributeError:
                logger.exception("Failed to parse change {} for {} 😿", change, issue_key)
            for field in change.fields or []:
                if field["field"].id == "status":
                    from_status_string = getattr(field["from"], "key", None)  # to Status
                    to_status_string = field["to"].key
                    from_status = Status.from_string(from_status_string) if from_status_string else None
                    to_status = Status.from_string(to_status_string)
                    t = StatusTransition(from_status, to_status, parsed_timestamp)
                    transitions.append(t)
        return transitions


def get_startack_client(config) -> PraktikTrackerClient:
    if STARTREK_TOKEN_KEY_NAME not in config:
        logger.error(f"{STARTREK_TOKEN_KEY_NAME} top-level key not found in config 😿")
        exit(1)
    token = config[STARTREK_TOKEN_KEY_NAME]
    return PraktikTrackerClient(
        org_id=YANDEX_ORG_ID,
        base_url="https://st-api.yandex-team.ru",
        token=token,
        connector=CachedConnection,
    )


def by_issue_key(issue) -> int:
    key: str = issue.key  # e.g. PCR-12345
    return Homework.to_issue_key_number(key)
