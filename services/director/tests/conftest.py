import sys
import types
from pathlib import Path

import fakeredis
import mongomock
import pytest

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SERVICE_DIR), str(SERVICE_DIR.parent)]

# The app creates its Mongo/Redis clients at import time, so swap in
# in-memory fakes before importing it.
import common.mongo  # noqa: E402
import common.redis_client  # noqa: E402

common.mongo.MongoClient = mongomock.MongoClient
# Replace only the module reference: patching redis.Redis itself would break
# fakeredis, which inspects redis.Redis to decide which kwargs it accepts.
common.redis_client.redis = types.SimpleNamespace(Redis=fakeredis.FakeRedis)

from flask_jwt_extended import create_access_token  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import assets_collection, redis_client  # noqa: E402


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(autouse=True)
def clean_state():
    assets_collection.delete_many({})
    redis_client.flushall()
    yield


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    def make(role):
        with app.app_context():
            token = create_access_token(identity=f"{role}@example.com", additional_claims={"role": role})
        return {"Authorization": f"Bearer {token}"}

    return make


@pytest.fixture
def assets():
    return assets_collection


@pytest.fixture
def redis():
    return redis_client
