from datetime import datetime, timezone
from typing import Optional
from dateutil import tz


# def get_local_timezone():
#     """Return the local timezone."""
#     return tz.gettz()


# def localized_utcnow():
#     """Return the current time in UTC with the timezone set to the local timezone."""
#     tz = get_local_timezone()
#     return datetime.now(tz).astimezone()


# def utcnow():
#     """Return the current time in UTC."""
#     return datetime.utcnow().replace(tzinfo=timezone.utc)

def utcnow_iso():
    """Return the current time in UTC."""
    return datetime.utcnow().isoformat() + "Z"

def get_most_recent(datetime_list):
    """Return the most recent datetime in a list of datetimes."""
    return max(datetime_list)