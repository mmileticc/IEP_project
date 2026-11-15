"""Role-based access control on top of flask-jwt-extended.

The API contract requires every authentication failure to look the same:
a missing header, a malformed or expired token, and a valid token with the
wrong role all return `401 {"msg": "Missing Authorization Header"}`. This
avoids leaking which part of the check failed.
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from .roles import ROLES_FIELD

_MISSING_AUTH_RESPONSE = ({"msg": "Missing Authorization Header"}, 401)


def _missing_auth():
    body, status = _MISSING_AUTH_RESPONSE
    return jsonify(body), status


def role_required(expected_role: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()  # failures are handled by the loaders below
            if get_jwt().get(ROLES_FIELD) != expected_role:
                return _missing_auth()
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def register_jwt_error_handlers(jwt_manager):
    """Make every flask-jwt-extended failure path converge on the same body."""

    @jwt_manager.unauthorized_loader
    def _missing_token(_reason):
        return _missing_auth()

    @jwt_manager.invalid_token_loader
    def _invalid_token(_reason):
        return _missing_auth()

    @jwt_manager.expired_token_loader
    def _expired_token(_header, _payload):
        return _missing_auth()
