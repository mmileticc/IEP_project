"""Request-body validation helpers shared by every service.

A field counts as "missing" only when it is absent from the body or is an
empty string. A whitespace-only string (e.g. `" "`) is a present value that
then has to pass the field-specific format check (email regex, password
length, ...). Error messages are part of the public API contract, so they
are kept stable.
"""
import re
import uuid as uuid_module

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
OBJECT_ID_RE = re.compile(r"^[0-9a-fA-F]{24}$")
ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

MAX_NAME_LENGTH = 256


class ValidationError(Exception):
    """Raised by validators; carries the exact message the client should see."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def is_missing(value) -> bool:
    """True if the field is absent (value is None) or an empty string."""
    return value is None or (isinstance(value, str) and len(value) == 0)


def require_fields(body: dict, field_names):
    """Raises ValidationError("Field <name> is missing.") for the first
    missing field, in the given order."""
    for name in field_names:
        if is_missing(body.get(name)):
            raise ValidationError(f"Field {name} is missing.")


def is_valid_email(email) -> bool:
    return isinstance(email, str) and len(email) <= MAX_NAME_LENGTH and bool(EMAIL_RE.match(email))


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_password(password) -> bool:
    return isinstance(password, str) and len(password) >= 8


def is_valid_name(value) -> bool:
    return isinstance(value, str) and len(value) <= MAX_NAME_LENGTH


def is_valid_object_id(value) -> bool:
    return isinstance(value, str) and bool(OBJECT_ID_RE.match(value))


def is_valid_uuid(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        uuid_module.UUID(value)
    except ValueError:
        return False
    return True


def is_valid_eth_address(value) -> bool:
    return isinstance(value, str) and bool(ETH_ADDRESS_RE.match(value))


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_positive_number(value) -> bool:
    return is_number(value) and value > 0
