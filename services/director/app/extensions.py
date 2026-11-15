from flask_jwt_extended import JWTManager

from common.mongo import get_assets_collection
from common.redis_client import get_redis_client

jwt = JWTManager()

# Process-wide, thread-safe clients (see services/employee/app/extensions.py).
assets_collection = get_assets_collection()
redis_client = get_redis_client()
