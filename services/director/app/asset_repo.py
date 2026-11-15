"""Applies an approved BUY/SELL order to the MongoDB asset collection."""
from bson import ObjectId

from common.dates import utcnow

from .extensions import assets_collection


def apply_order(order: dict) -> None:
    if order["order_type"] == "BUY":
        assets_collection.insert_one({
            "name": order["name"],
            "categories": order["categories"],
            "buying_price": order["buying_price"],
            "buying_date": utcnow(),
            "info": order.get("info", {}),
        })
    else:
        assets_collection.update_one(
            {"_id": ObjectId(order["id"])},
            {"$set": {"selling_price": order["selling_price"], "selling_date": utcnow()}},
        )
