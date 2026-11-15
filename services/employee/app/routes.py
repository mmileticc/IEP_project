from bson import ObjectId
from flask import Blueprint, jsonify, request

from common.jwt_auth import role_required
from common.mongo import serialize_asset
from common.orders import create_buy_order, create_sell_order
from common.roles import EMPLOYEE_ROLE
from common.validation import (
    ValidationError,
    is_positive_number,
    is_valid_name,
    is_valid_object_id,
    require_fields,
)

from .extensions import assets_collection, redis_client
from .search import build_search_query

bp = Blueprint("employee", __name__)


@bp.post("/search")
@role_required(EMPLOYEE_ROLE)
def search():
    body = request.get_json(silent=True) or {}
    query = build_search_query(body)
    assets = [serialize_asset(doc) for doc in assets_collection.find(query)]
    return jsonify({"assets": assets}), 200


@bp.post("/create_buy_order")
@role_required(EMPLOYEE_ROLE)
def create_buy_order_route():
    body = request.get_json(silent=True) or {}
    require_fields(body, ["name", "categories", "buying_price", "info"])

    if not is_valid_name(body["name"]):
        raise ValidationError("Invalid name.")

    categories = body["categories"]
    if not isinstance(categories, list) or len(categories) == 0:
        raise ValidationError("Categories list is empty.")
    if not all(isinstance(c, str) and c for c in categories):
        raise ValidationError("Invalid categories.")

    if not is_positive_number(body["buying_price"]):
        raise ValidationError("Invalid buying price.")

    if not isinstance(body["info"], dict):
        raise ValidationError("Invalid info.")

    create_buy_order(redis_client, body["name"], categories, body["buying_price"], body["info"])
    return "", 200


@bp.post("/create_sell_order")
@role_required(EMPLOYEE_ROLE)
def create_sell_order_route():
    body = request.get_json(silent=True) or {}
    require_fields(body, ["id"])

    asset_id = body["id"]
    if not _is_sellable(asset_id):
        raise ValidationError("Invalid id.")

    require_fields(body, ["selling_price"])
    if not is_positive_number(body["selling_price"]):
        raise ValidationError("Invalid selling price.")

    create_sell_order(redis_client, asset_id, body["selling_price"])
    return "", 200


def _is_sellable(asset_id) -> bool:
    """The asset must exist and must not have been sold already."""
    if not is_valid_object_id(asset_id):
        return False
    asset = assets_collection.find_one({"_id": ObjectId(asset_id)})
    return asset is not None and asset.get("selling_price") is None
