import datetime as dt

import pytest

from prpr.date_utils import (
    _day_in_next_month,
    _day_in_previous_month,
    month_start_and_end,
)


@pytest.mark.parametrize(
    "some_date, start_of_month, expected",
    [
        (dt.date(2021, 5, 26), 15, dt.date(2021, 6, 15)),
        (dt.date(2020, 12, 16), 15, dt.date(2021, 1, 15)),
    ],
)
def test_next_month(some_date, start_of_month, expected):
    assert _day_in_next_month(some_date, start_of_month) == expected


@pytest.mark.parametrize(
    "some_date, start_of_month, expected",
    [
        (dt.date(2021, 5, 26), 15, dt.date(2021, 4, 15)),
        (dt.date(2021, 1, 16), 15, dt.date(2020, 12, 15)),
    ],
)
def test_previous_month(some_date, start_of_month, expected):
    assert _day_in_previous_month(some_date, start_of_month) == expected


@pytest.mark.parametrize(
    "day, month_start, expected_start_and_end",
    [
        (dt.date(2021, 5, 26), 15, (dt.date(2021, 5, 16), dt.date(2021, 6, 15))),
        (dt.date(2021, 5, 16), 15, (dt.date(2021, 5, 16), dt.date(2021, 6, 15))),
        (dt.date(2021, 5, 15), 15, (dt.date(2021, 4, 16), dt.date(2021, 5, 15))),
        (dt.date(2021, 1, 15), 15, (dt.date(2020, 12, 16), dt.date(2021, 1, 15))),
    ],
)
def test_month_start_and_end(day, month_start, expected_start_and_end):
    assert month_start_and_end(day, month_start) == expected_start_and_end
