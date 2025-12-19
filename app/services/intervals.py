from datetime import UTC, datetime


class InvalidIntervalError(ValueError):
    pass


ALLOWED_INTERVALS = ("1h",)


def validate_interval(interval: str) -> str:
    if interval not in ALLOWED_INTERVALS:
        raise InvalidIntervalError("Only interval '1h' is supported")
    return interval


def floor_to_hour_utc(dt: datetime) -> datetime:
    """
    Floor dt to the last full hour in UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    dt = dt.astimezone(UTC)
    return dt.replace(minute=0, second=0, microsecond=0)
