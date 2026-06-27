from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from expenses_ai_agent.utils.exceptions import (
    InvalidDateTimeError,
    InvalidTimeZoneError,
)


def format_datetime(datetime_str: str, timezone_str: str | None = None) -> str:
    """
    Parse datetime string from ISO format including support for specified
    timezone
    """

    try:
        dt = datetime.fromisoformat(datetime_str)
    except ValueError as err:
        raise InvalidDateTimeError(
            f"Datetime string not in valid ISO format: {datetime_str}"
        ) from err

    if timezone_str is not None:
        try:
            tzinfo = ZoneInfo(timezone_str)
            dt = dt.astimezone(tzinfo)
        except (ZoneInfoNotFoundError, ValueError) as err:
            raise InvalidTimeZoneError(f"Invalid timezone: {timezone_str}") from err

    return dt.strftime("%a %b %d, %Y %I:%M %p %Z")
