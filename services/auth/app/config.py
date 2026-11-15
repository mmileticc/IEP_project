import os

from common.config import JwtConfig


def _database_uri() -> str:
    # DATABASE_URL overrides everything (used by the test suite with SQLite).
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    return (
        f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER', 'iep')}:"
        f"{os.environ.get('POSTGRES_PASSWORD', 'iep')}@"
        f"{os.environ.get('POSTGRES_HOST', 'postgres')}:"
        f"{os.environ.get('POSTGRES_PORT', '5432')}/"
        f"{os.environ.get('POSTGRES_DB', 'iep_auth')}"
    )


class Config(JwtConfig):
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
