from flask_jwt_extended import JWTManager

from common.mongo import get_assets_collection
from common.redis_client import get_redis_client

jwt = JWTManager()

# Process-wide clients: MongoClient and redis.Redis are thread-safe and keep
# their own connection pools, so one instance per gunicorn worker is enough.
assets_collection = get_assets_collection()
redis_client = get_redis_client()
