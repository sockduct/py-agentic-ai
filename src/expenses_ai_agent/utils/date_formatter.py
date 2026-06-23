from datetime import datetime
from zoneinfo import ZoneInfo


def format_datetime(datetime_str: str, timezone_str: str | None = None) -> str:
    """
    Parse datetime string from ISO format including support for specified
    timezone
    """

    dt = datetime.fromisoformat(datetime_str)

    if timezone_str:
        tzinfo = ZoneInfo(timezone_str)
        dt = dt.astimezone(tzinfo)

    return dt.strftime("%a %b %d, %Y %I:%M %p %Z")
