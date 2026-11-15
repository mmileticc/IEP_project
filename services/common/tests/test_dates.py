import datetime

from common.dates import parse_iso_datetime, to_iso_string


def test_parse_converts_to_naive_utc():
    parsed = parse_iso_datetime("2026-01-01T12:00:00+02:00")
    assert parsed == datetime.datetime(2026, 1, 1, 10, 0, 0)
    assert parse_iso_datetime("2026-01-01T10:00:00Z") == parsed


def test_round_trip_uses_millisecond_precision():
    value = datetime.datetime(2026, 1, 1, 10, 0, 0, 123456)
    assert to_iso_string(value) == "2026-01-01T10:00:00.123Z"
