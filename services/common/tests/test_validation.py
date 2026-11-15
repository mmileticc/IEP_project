import pytest

from common.validation import (
    ValidationError,
    is_number,
    is_positive_number,
    is_valid_email,
    is_valid_eth_address,
    is_valid_object_id,
    is_valid_password,
    is_valid_uuid,
    require_fields,
)


def test_require_fields_reports_first_missing_field_in_order():
    with pytest.raises(ValidationError) as exc:
        require_fields({"forename": " ", "surname": ""}, ["forename", "surname", "email"])
    assert exc.value.message == "Field surname is missing."


def test_require_fields_accepts_non_string_values():
    require_fields({"info": {}, "price": 0}, ["info", "price"])


@pytest.mark.parametrize("email, valid", [
    ("john@gmail.com", True),
    ("john@gmail.c", False),
    ("john@gmail", False),
    ("john gmail.com", False),
    ("a@b.com" + "m" * 300, False),
    (123, False),
])
def test_is_valid_email(email, valid):
    assert is_valid_email(email) is valid


def test_password_needs_eight_characters():
    assert is_valid_password("12345678")
    assert not is_valid_password("1234567")
    assert not is_valid_password(12345678)


def test_identifier_validators():
    assert is_valid_object_id("0123456789abcdef01234567")
    assert not is_valid_object_id("not-an-id")
    assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000")
    assert not is_valid_uuid("not-a-uuid")
    assert is_valid_eth_address("0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1")
    assert not is_valid_eth_address("0x123")


def test_booleans_are_not_numbers():
    assert is_number(1.5)
    assert not is_number(True)
    assert is_positive_number(1)
    assert not is_positive_number(0)
    assert not is_positive_number(-3)
