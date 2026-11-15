"""Builds the PyMongo filter for POST /search from the optional request
fields. Client input only ever becomes values inside a filter dict; the set
of query operators a client may use is a fixed whitelist."""
import re

from common.dates import parse_iso_datetime
from common.validation import ValidationError

ALLOWED_INFO_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "nin"}
_INFO_FIELD_RE = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$")


def build_search_query(body: dict) -> dict:
    conditions = []

    name = body.get("name")
    if name:
        if not isinstance(name, str):
            raise ValidationError("Invalid name.")
        conditions.append({"name": {"$regex": re.escape(name), "$options": "i"}})

    category = body.get("category")
    if category:
        if not isinstance(category, str):
            raise ValidationError("Invalid category.")
        conditions.append({"categories": category})

    buying_date = body.get("buying_date")
    if buying_date:
        conditions.append({"buying_date": {"$gte": _parse_date(buying_date, "buying_date")}})

    selling_date = body.get("selling_date")
    if selling_date:
        # Unsold assets (no selling_price/selling_date) must never match.
        conditions.append({
            "selling_price": {"$ne": None},
            "selling_date": {"$lte": _parse_date(selling_date, "selling_date")},
        })

    info_filters = body.get("info_filters") or []
    if not isinstance(info_filters, list):
        raise ValidationError("Invalid info filter.")
    for info_filter in info_filters:
        condition = _info_condition(info_filter)
        if condition is not None:
            conditions.append(condition)

    return {"$and": conditions} if conditions else {}


def _info_condition(info_filter):
    if not isinstance(info_filter, dict):
        raise ValidationError("Invalid info filter.")
    field = info_filter.get("field")
    operator = info_filter.get("operator")
    if not field or not operator:
        return None
    if not isinstance(field, str) or not _INFO_FIELD_RE.match(field):
        raise ValidationError("Invalid info filter.")
    if operator not in ALLOWED_INFO_OPERATORS:
        raise ValidationError("Invalid info filter.")
    value = info_filter.get("value")
    if operator in ("in", "nin") and not isinstance(value, list):
        raise ValidationError("Invalid info filter.")
    return {f"info.{field}": {f"${operator}": value}}


def _parse_date(value, field_name: str):
    try:
        return parse_iso_datetime(value)
    except (ValueError, TypeError, AttributeError):
        raise ValidationError(f"Invalid {field_name}.") from None
