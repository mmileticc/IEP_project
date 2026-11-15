import os


class JwtConfig:
    """flask-jwt-extended settings shared by all services. The secret must
    be the same everywhere so tokens issued by auth verify elsewhere."""

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-in-production")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_TYPE = "Bearer"
    JWT_HEADER_NAME = "Authorization"
