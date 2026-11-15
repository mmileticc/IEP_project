import time

from flask import Flask
from sqlalchemy.exc import IntegrityError, OperationalError

from common.app_setup import init_common

from .config import Config
from .extensions import db, jwt
from .routes import bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    init_common(app, jwt)
    app.register_blueprint(bp)

    with app.app_context():
        _wait_for_db_and_init()

    return app


def _wait_for_db_and_init(retries: int = 30, delay: float = 1.0):
    """Postgres may still be starting when the pod comes up, so retry the
    schema setup for a while before giving up."""
    from . import models  # noqa: F401  (register mappings before create_all)
    from .seed import seed_director

    last_error = None
    for _ in range(retries):
        try:
            _create_tables_idempotent()
            _seed_director_idempotent(seed_director)
            return
        except OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    if last_error is not None:
        raise last_error


def _create_tables_idempotent() -> None:
    """db.create_all() checks whether each table exists before creating it,
    but that check-then-act is not atomic. When several gunicorn workers (or
    replicas) start at once, more than one can try to create the same table;
    Postgres lets one win and fails the rest with an IntegrityError on its
    catalog. The resulting schema is correct either way, so the error is
    swallowed."""
    try:
        db.create_all()
    except IntegrityError:
        db.session.rollback()


def _seed_director_idempotent(seed_director) -> None:
    """Same race for the seeded director row: the loser hits the
    UNIQUE(email) constraint, which is expected."""
    try:
        seed_director()
    except IntegrityError:
        db.session.rollback()
