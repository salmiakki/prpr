import datetime as dt
from datetime import datetime, timezone
from typing import Optional, Tuple

LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo


def parse_datetime(datetime_string: Optional[str]) -> Optional[datetime]:
    """E.g. "2020-09-23T22:14:37.658+0000" -> datetime(2020, 9, 23, 22, 14, 37) (more or less)."""
    if datetime_string is None:
        return None
    # Note to self: dateutil can parse these dates.
    utc_tz_suffix = "+0000"
    if not datetime_string.endswith(utc_tz_suffix):
        raise ValueError(f"Unexpected datetime string format: {datetime_string} 😿")
    datetime_wo_tz = datetime_string.removesuffix(utc_tz_suffix)
    naive_utc_datetime = datetime.fromisoformat(datetime_wo_tz)
    local_datetime = naive_utc_datetime.replace(tzinfo=timezone.utc).astimezone(tz=LOCAL_TIMEZONE)
    return local_datetime


def month_start_and_end(day: dt.date, month_start: int) -> Tuple[dt.date, dt.date]:
    """Return start and end of "month" containing today, start is not included.

    E.g. (2021, 4, 27), 15 -> (2021, 5, 16), (2021, 5, 15)"""
    if day.day <= month_start:
        end = dt.date(day.year, day.month, month_start)
    else:
        end = _day_in_next_month(day, month_start)
    start = _day_in_previous_month(end, month_start)
    return start + dt.timedelta(1), end


def _day_in_next_month(some_date: dt.date, day_number: int) -> dt.date:  # RENAME
    """Return date of (next month, day_number) relative to some_date.

    E.g. (2021-05-26, 15) -> 2021-06-15 and (2020-12-26, 15) -> 2021-01-15"""
    return _day_in_next_or_previous_month(some_date, day_number)


def _day_in_previous_month(some_date: dt.date, day_number: int) -> dt.date:
    """Return date of (previous month, day_number) relative to some_date."""
    return _day_in_next_or_previous_month(some_date, day_number, next_month=False)


def _day_in_next_or_previous_month(some_date, day_number, next_month=True):
    mul = 1 if next_month else -1
    assert day_number <= 31
    candidate = some_date
    while some_date.month == candidate.month or candidate.day != day_number:
        candidate += mul * dt.timedelta(days=1)
    return candidate
