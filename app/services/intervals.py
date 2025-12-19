class InvalidIntervalError(ValueError):
    pass


ALLOWED_INTERVALS = ("1h",)


def validate_interval(interval: str) -> str:
    if interval not in ALLOWED_INTERVALS:
        raise InvalidIntervalError("Only interval '1h' is supported")
    return interval
