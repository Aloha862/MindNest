from datetime import datetime


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def now() -> datetime:
    return datetime.now()


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.strftime(DATETIME_FORMAT)
