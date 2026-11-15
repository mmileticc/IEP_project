import datetime

import pytest

from app.search import build_search_query
from common.validation import ValidationError


def test_empty_body_matches_everything():
    assert build_search_query({}) == {}


def test_name_is_escaped_case_insensitive_regex():
    query = build_search_query({"name": "a.b"})
    assert query == {"$and": [{"name": {"$regex": r"a\.b", "$options": "i"}}]}


def test_dates_and_info_filters_are_combined():
    query = build_search_query({
        "buying_date": "2026-01-01T00:00:00Z",
        "info_filters": [{"field": "geo.country", "operator": "eq", "value": "RS"}],
    })
    assert query["$and"] == [
        {"buying_date": {"$gte": datetime.datetime(2026, 1, 1)}},
        {"info.geo.country": {"$eq": "RS"}},
    ]


@pytest.mark.parametrize("info_filter", [
    {"field": "risk", "operator": "where", "value": "1"},
    {"field": "$where", "operator": "eq", "value": "1"},
    {"field": "risk", "operator": "in", "value": "not-a-list"},
    "not-a-dict",
])
def test_unsafe_info_filters_are_rejected(info_filter):
    with pytest.raises(ValidationError):
        build_search_query({"info_filters": [info_filter]})


def test_invalid_date_is_rejected():
    with pytest.raises(ValidationError) as exc:
        build_search_query({"selling_date": "yesterday"})
    assert exc.value.message == "Invalid selling_date."
