from datetime import timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from common.roles import EMPLOYEE_ROLE, ROLES_FIELD
from common.validation import (
    ValidationError,
    is_valid_email,
    is_valid_name,
    is_valid_password,
    normalize_email,
    require_fields,
)

from .extensions import db
from .models import User

bp = Blueprint("auth", __name__)

TOKEN_LIFETIME = timedelta(hours=1)


@bp.post("/register")
def register():
    body = request.get_json(silent=True) or {}
    require_fields(body, ["forename", "surname", "email", "password"])

    for field in ("forename", "surname"):
        if not is_valid_name(body[field]):
            raise ValidationError(f"Invalid {field}.")
    if not is_valid_email(body["email"]):
        raise ValidationError("Invalid email.")
    if not is_valid_password(body["password"]):
        raise ValidationError("Invalid password.")

    email = normalize_email(body["email"])
    if User.query.filter_by(email=email).first() is not None:
        raise ValidationError("Email already exists.")

    db.session.add(User(
        forename=body["forename"],
        surname=body["surname"],
        email=email,
        password_hash=generate_password_hash(body["password"]),
        role=EMPLOYEE_ROLE,
    ))
    db.session.commit()
    return "", 200


@bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    require_fields(body, ["email", "password"])

    if not is_valid_email(body["email"]):
        raise ValidationError("Invalid email.")

    user = User.query.filter_by(email=normalize_email(body["email"])).first()
    password = body["password"]
    if user is None or not isinstance(password, str) or not check_password_hash(user.password_hash, password):
        raise ValidationError("Invalid credentials.")

    token = create_access_token(
        identity=user.email,
        additional_claims={
            "forename": user.forename,
            "surname": user.surname,
            ROLES_FIELD: user.role,
        },
        expires_delta=TOKEN_LIFETIME,
    )
    return jsonify({"accessToken": token}), 200


@bp.post("/delete")
@jwt_required()
def delete():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    if user is None:
        raise ValidationError("Unknown user.")

    db.session.delete(user)
    db.session.commit()
    return "", 200
