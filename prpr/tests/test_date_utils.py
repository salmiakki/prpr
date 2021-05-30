import datetime as dt

import pytest

from prpr.date_utils import month_start_and_end


@pytest.mark.parametrize(
    "day, month_start, expected_start_and_end",
    [
        (dt.date(2021, 5, 26), 16, (dt.date(2021, 5, 16), dt.date(2021, 6, 15))),
        (dt.date(2021, 5, 16), 16, (dt.date(2021, 5, 16), dt.date(2021, 6, 15))),
        (dt.date(2021, 5, 15), 16, (dt.date(2021, 4, 16), dt.date(2021, 5, 15))),
        (dt.date(2021, 1, 15), 16, (dt.date(2020, 12, 16), dt.date(2021, 1, 15))),
    ],
)
def test_month_start_and_end(day, month_start, expected_start_and_end):
    assert month_start_and_end(day, month_start) == expected_start_and_end
