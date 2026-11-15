"""Pending BUY/SELL order storage in Redis, shared by the employee service
(which creates orders) and the director service (which lists and resolves
them). Schema:

    order:<uuid>      -> JSON-encoded order dict (order_type + fields)
    pending_orders    -> Redis SET of uuids currently awaiting a decision
"""
import json
import uuid as uuid_module

PENDING_ORDERS_KEY = "pending_orders"


def _order_key(order_uuid: str) -> str:
    return f"order:{order_uuid}"


def _store_order(redis_client, order: dict) -> str:
    order_uuid = str(uuid_module.uuid4())
    pipe = redis_client.pipeline()
    pipe.set(_order_key(order_uuid), json.dumps(order))
    pipe.sadd(PENDING_ORDERS_KEY, order_uuid)
    pipe.execute()
    return order_uuid


def create_buy_order(redis_client, name, categories, buying_price, info) -> str:
    return _store_order(redis_client, {
        "order_type": "BUY",
        "name": name,
        "categories": categories,
        "buying_price": buying_price,
        "info": info,
    })


def create_sell_order(redis_client, asset_id, selling_price) -> str:
    return _store_order(redis_client, {
        "order_type": "SELL",
        "id": asset_id,
        "selling_price": selling_price,
    })


def get_order(redis_client, order_uuid: str):
    raw = redis_client.get(_order_key(order_uuid))
    if raw is None:
        return None
    order = json.loads(raw)
    order["uuid"] = order_uuid
    return order


def order_exists(redis_client, order_uuid: str) -> bool:
    return bool(redis_client.sismember(PENDING_ORDERS_KEY, order_uuid))


def claim_order(redis_client, order_uuid: str):
    """Atomically removes the order from the pending set and returns it.
    SREM succeeds for exactly one caller, so concurrent decisions (or the
    blockchain listener racing a retry) can never apply the same order
    twice. Returns None if someone else already claimed it."""
    if redis_client.srem(PENDING_ORDERS_KEY, order_uuid) != 1:
        return None
    order = get_order(redis_client, order_uuid)
    redis_client.delete(_order_key(order_uuid))
    return order


def list_pending_orders(redis_client):
    orders = []
    for order_uuid in redis_client.smembers(PENDING_ORDERS_KEY):
        order = get_order(redis_client, order_uuid)
        if order is not None:
            orders.append(order)
    return orders
