from calendar import timegm
from datetime import datetime, timezone, tzinfo


def is_naive(dt: datetime) -> bool:
    """Return True if :class:`~datetime.datetime` is naive, meaning it doesn't have timezone info set."""
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def make_aware(dt: datetime, tz: tzinfo) -> datetime:
    """Set timezone for a :class:`~datetime.datetime` object."""

    dt = dt.replace(tzinfo=tz)
    return dt


def make_utc(dt: datetime) -> datetime:
    if is_naive(dt):
        dt = make_aware(dt, tz=timezone.utc)
    return dt


def aware_utcnow() -> datetime:
    return make_utc(datetime.utcnow())


def datetime_to_epoch(dt: datetime) -> int:
    return timegm(dt.utctimetuple())


# def datetime_from_epoch(ts):
#     return make_utc(datetime.utcfromtimestamp(ts))
