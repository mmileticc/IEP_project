import fakeredis
import pytest

from common.orders import (
    claim_order,
    create_buy_order,
    create_sell_order,
    get_order,
    list_pending_orders,
    order_exists,
)


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


def test_created_orders_are_pending(redis_client):
    buy_uuid = create_buy_order(redis_client, "Asset", ["Tech"], 100, {"risk": "low"})
    sell_uuid = create_sell_order(redis_client, "0123456789abcdef01234567", 150)

    assert order_exists(redis_client, buy_uuid)
    assert get_order(redis_client, sell_uuid)["order_type"] == "SELL"
    assert {o["uuid"] for o in list_pending_orders(redis_client)} == {buy_uuid, sell_uuid}


def test_claim_order_succeeds_only_once(redis_client):
    order_uuid = create_buy_order(redis_client, "Asset", ["Tech"], 100, {})

    first = claim_order(redis_client, order_uuid)
    second = claim_order(redis_client, order_uuid)

    assert first["name"] == "Asset"
    assert second is None
    assert not order_exists(redis_client, order_uuid)
    assert get_order(redis_client, order_uuid) is None
