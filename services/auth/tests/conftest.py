import os
import sys
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SERVICE_DIR), str(SERVICE_DIR.parent)]

# Must be set before the app's config module is imported.
os.environ["DATABASE_URL"] = "sqlite://"

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.seed import seed_director  # noqa: E402


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_director()
    yield


@pytest.fixture
def client(app):
    return app.test_client()
