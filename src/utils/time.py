import datetime
import pytz

def get_seconds_until_next_hour() -> int:
    delta = datetime.timedelta(hours=1)
    now = datetime.datetime.now()
    next_hour = (now + delta).replace(microsecond=0, second=0, minute=1)
    wait_seconds = (next_hour - now).seconds
    return wait_seconds

def get_seconds_until_next_day_for_timezone(timezone: str) -> int:
    day_delta = datetime.timedelta(days=1)
    now = datetime.datetime.now(pytz.timezone(timezone))
    next_day = (now + day_delta).replace(microsecond=0, second=0, minute=1, hour=0)
    wait_seconds = (next_day - now).seconds
    return wait_seconds

def get_start_of_previous_hour_utc() -> datetime.datetime:
    delta = datetime.timedelta(hours=1)
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    return (now - delta).replace(microsecond=0, second=0, minute=0)
