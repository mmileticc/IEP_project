import os

from werkzeug.security import generate_password_hash

from common.roles import DIRECTOR_ROLE

from .extensions import db
from .models import User

DIRECTOR_FORENAME = os.environ.get("DIRECTOR_SEED_FORENAME", "Scrooge")
DIRECTOR_SURNAME = os.environ.get("DIRECTOR_SEED_SURNAME", "McDuck")
DIRECTOR_EMAIL = os.environ.get("DIRECTOR_SEED_EMAIL", "onlymoney@gmail.com")
DIRECTOR_PASSWORD = os.environ.get("DIRECTOR_SEED_PASSWORD", "evenmoremoney")


def seed_director():
    """Ensures the single pre-provisioned director account exists. Directors
    cannot register through the API, so the account is created on startup.
    Idempotent: safe to call on every boot."""
    if User.query.filter_by(email=DIRECTOR_EMAIL).first() is not None:
        return

    db.session.add(User(
        forename=DIRECTOR_FORENAME,
        surname=DIRECTOR_SURNAME,
        email=DIRECTOR_EMAIL,
        password_hash=generate_password_hash(DIRECTOR_PASSWORD),
        role=DIRECTOR_ROLE,
    ))
    db.session.commit()
