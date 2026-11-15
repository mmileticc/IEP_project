"""ISO-8601 <-> naive-UTC datetime conversion shared by the employee and
director services (MongoDB stores and returns naive UTC datetimes)."""
import datetime


def parse_iso_datetime(value: str) -> datetime.datetime:
    dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(datetime.UTC).replace(tzinfo=None)
    return dt


def to_iso_string(value: datetime.datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{value.microsecond // 1000:03d}Z"


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
