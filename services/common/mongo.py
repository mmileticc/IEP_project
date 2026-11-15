import os

from pymongo import MongoClient

from .dates import to_iso_string


def _build_mongo_uri() -> str:
    uri = os.environ.get("MONGO_URI")
    if uri:
        return uri
    host = os.environ.get("MONGO_HOST", "mongo")
    port = os.environ.get("MONGO_PORT", "27017")
    user = os.environ.get("MONGO_USER")
    password = os.environ.get("MONGO_PASSWORD")
    if user and password:
        return f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"
    return f"mongodb://{host}:{port}/"


def get_assets_collection():
    client = MongoClient(_build_mongo_uri())
    database = client[os.environ.get("MONGO_DB", "iep_fund")]
    return database[os.environ.get("MONGO_ASSETS_COLLECTION", "assets")]


def serialize_asset(doc: dict) -> dict:
    """Maps an internal Mongo asset document to the API response shape
    of the API (id as string ObjectId, ISO 8601 dates, selling_*
    fields present only when the asset was actually sold)."""
    result = {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "categories": doc.get("categories", []),
        "buying_date": to_iso_string(doc["buying_date"]),
        "buying_price": doc["buying_price"],
    }
    if doc.get("selling_price") is not None and doc.get("selling_date") is not None:
        result["selling_date"] = to_iso_string(doc["selling_date"])
        result["selling_price"] = doc["selling_price"]
    result["info"] = doc.get("info", {})
    return result
