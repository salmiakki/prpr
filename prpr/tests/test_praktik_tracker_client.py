from unittest import mock

import pytest
from loguru import logger

from prpr.startrack_client import PraktikTrackerClient


@pytest.fixture()
def client():
    return PraktikTrackerClient(token="fake-token", org_id="fake-org-id")


@pytest.mark.parametrize("user,assignee", (
    ("", "me()"),
    ("user", "user"),
))
def test__get_filter_expression(user, assignee, client):
    query = client._get_filter_expression(user)
    assert query["assignee"] == assignee


@pytest.mark.parametrize("user,filter_queue", (
    ("", {"queue": "PCR", "assignee": "me()"}),
    ("user", {"queue": "PCR", "assignee": "user"}),
))
@mock.patch("yandex_tracker_client.collections.Issues.find")
def test_get_issues(find_mock, user, filter_queue, client):
    logger.disable("prpr.startrack_client")
    client.get_issues(user)
    logger.enable("prpr.startrack_client")
    find_mock.assert_called_once_with(filter=filter_queue)
