import sys
from calendar import timegm
from datetime import datetime, tzinfo

from dateutil import tz as dateutil_tz
from pytz import utc

if sys.version_info >= (3, 9):  # pragma: no cover
    from zoneinfo import ZoneInfo
else:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo


def _can_detect_ambiguous(tz: tzinfo) -> bool:
    """Helper function to determine if a timezone can detect ambiguous times using dateutil."""

    return isinstance(tz, ZoneInfo) or hasattr(tz, "is_ambiguous")


def _is_ambigious(dt: datetime, tz: tzinfo) -> bool:
    """Helper function to determine if a timezone is ambiguous using python's dateutil module.

    Returns False if the timezone cannot detect ambiguity, or if there is no ambiguity, otherwise True.

    In order to detect ambiguous datetimes, the timezone must be built using ZoneInfo, or have an is_ambiguous
    method. Previously, pytz timezones would throw an AmbiguousTimeError if the localized dt was ambiguous,
    but now we need to specifically check for ambiguity with dateutil, as pytz is deprecated.
    """

    return _can_detect_ambiguous(tz) and dateutil_tz.datetime_ambiguous(dt)


def is_naive(dt: datetime) -> bool:
    """Return True if :class:`~datetime.datetime` is naive, meaning it doesn't have timezone info set."""
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def make_aware(dt: datetime, tz: tzinfo) -> datetime:
    """Set timezone for a :class:`~datetime.datetime` object."""

    dt = dt.replace(tzinfo=tz)
    if _is_ambigious(dt, tz):  # pragma: no cover
        dt = min(dt.replace(fold=0), dt.replace(fold=1))
    return dt


def make_utc(dt: datetime) -> datetime:
    if is_naive(dt):
        dt = make_aware(dt, tz=utc)
    return dt


def aware_utcnow() -> datetime:
    return make_utc(datetime.utcnow())


def datetime_to_epoch(dt: datetime) -> int:
    return timegm(dt.utctimetuple())


# def datetime_from_epoch(ts):
#     return make_utc(datetime.utcfromtimestamp(ts))
