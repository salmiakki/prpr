from datetime import datetime, timedelta, timezone

import pytest

from prpr.homework import Homework

TIMEZONE = timezone(timedelta(hours=1))
NOW = datetime(2021, 5, 12, 3, 20, tzinfo=TIMEZONE)


@pytest.mark.freeze_time(NOW)
@pytest.mark.parametrize(
    "status_updated, expected_hours, expected_minutes, deadline_missed",
    [
        ("2021-05-11T02:13:00.000+0000", 0, 7, True),  # NOW - (1 day + 7 minutes) in UTC
        ("2021-05-11T02:23:00.000+0000", 0, 3, False),
        ("2021-05-11T01:23:00.000+0000", 0, 57, True),
        ("2021-05-11T03:23:00.000+0000", 1, 3, False),
    ],
)
def test_left_hours_and_minutes(status_updated, expected_hours, expected_minutes, deadline_missed):
    assert datetime.now(TIMEZONE) == NOW
    homework = Homework(
        "PCR-12345",
        "[1] Даниил Хармс (yuvachev@yandex.ru)",
        "open",
        status_updated,
        "",
        1,
        True,
    )
    assert homework._left_hours_and_minutes == (expected_hours, expected_minutes, deadline_missed)


@pytest.mark.freeze_time(NOW)
@pytest.mark.parametrize(
    "status_updated, expected",
    [
        ("2021-05-11T02:13:00.000+0000", "-0:07"),  # NOW - (1 day + 7 minutes) in UTC
        ("2021-05-11T02:23:00.000+0000", "0:03"),
        ("2021-05-11T01:23:00.000+0000", "-0:57"),
        ("2021-05-11T03:23:00.000+0000", "1:03"),
    ],
)
def test_left(status_updated, expected):
    assert datetime.now(TIMEZONE) == NOW
    homework = Homework(
        "PCR-12345",
        "[1] Даниил Хармс (yuvachev@yandex.ru)",
        "open",
        status_updated,
        "",
        1,
        True,
    )
    assert homework.left == expected
