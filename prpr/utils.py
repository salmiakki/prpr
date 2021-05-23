from datetime import datetime, timezone
from typing import Optional

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
