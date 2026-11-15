import datetime

import pytest
from bson import ObjectId

import app.routes as routes
from common.orders import create_buy_order, create_sell_order, order_exists

VOTERS = [
    "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1",
    "0xFFcf8FDEE72ac11b5c542428B35EEF5769C409f0",
    "0x22d491Bde2303f2f43325b2108D26f1eAbA1e32b",
]


@pytest.mark.parametrize("method, path", [
    ("get", "/pending_orders"),
    ("post", "/decision"),
    ("get", "/report"),
])
def test_endpoints_require_director_role(client, auth_headers, method, path):
    for headers in ({}, auth_headers("employee")):
        response = getattr(client, method)(path, headers=headers)
        assert response.status_code == 401
        assert response.get_json() == {"msg": "Missing Authorization Header"}


def test_pending_orders_lists_both_types(client, auth_headers, redis):
    create_buy_order(redis, "AssetAlpha", ["Tech"], 100, {})
    create_sell_order(redis, "0123456789abcdef01234567", 150)

    orders = client.get("/pending_orders", headers=auth_headers("director")).get_json()["orders"]
    assert sorted(o["order_type"] for o in orders) == ["BUY", "SELL"]


@pytest.mark.parametrize("body, message", [
    ({}, "Field uuid is missing."),
    ({"uuid": "not-a-uuid"}, "Invalid uuid."),
    ({"uuid": "550e8400-e29b-41d4-a716-446655440000"}, "Invalid uuid."),
])
def test_decision_uuid_validation(client, auth_headers, body, message):
    response = client.post("/decision", json=body, headers=auth_headers("director"))
    assert response.status_code == 400
    assert response.get_json() == {"message": message}


def test_approved_buy_creates_asset(client, auth_headers, redis, assets):
    order_uuid = create_buy_order(redis, "AssetAlpha", ["Tech"], 100, {"region": "EU"})

    response = client.post("/decision", json={"uuid": order_uuid, "approved": True}, headers=auth_headers("director"))

    assert response.status_code == 200
    assert not order_exists(redis, order_uuid)
    assert assets.find_one({"name": "AssetAlpha"})["info"] == {"region": "EU"}


def test_rejected_order_is_discarded(client, auth_headers, redis, assets):
    order_uuid = create_buy_order(redis, "AssetAlpha", ["Tech"], 100, {})
    client.post("/decision", json={"uuid": order_uuid, "approved": False}, headers=auth_headers("director"))
    assert not order_exists(redis, order_uuid)
    assert assets.count_documents({}) == 0


def test_approved_sell_marks_asset_sold(client, auth_headers, redis, assets):
    asset_id = assets.insert_one({
        "name": "A", "categories": ["Tech"], "buying_price": 100,
        "buying_date": datetime.datetime(2026, 1, 1), "info": {},
    }).inserted_id
    order_uuid = create_sell_order(redis, str(asset_id), 150)

    client.post("/decision", json={"uuid": order_uuid, "approved": True}, headers=auth_headers("director"))

    assert assets.find_one({"_id": ObjectId(asset_id)})["selling_price"] == 150


def test_decision_requires_boolean(client, auth_headers, redis):
    order_uuid = create_buy_order(redis, "AssetAlpha", ["Tech"], 100, {})
    response = client.post("/decision", json={"uuid": order_uuid, "approved": "yes"}, headers=auth_headers("director"))
    assert response.get_json() == {"message": "Invalid decision."}


@pytest.fixture
def blockchain_mode(monkeypatch):
    deployed = []

    def fake_deploy(voters):
        deployed.append(voters)
        return f"0x{len(deployed):040x}"

    monkeypatch.setattr(routes, "BLOCKCHAIN_ENABLED", True)
    monkeypatch.setattr(routes, "deploy_voting_contract", fake_deploy)
    monkeypatch.setattr(
        routes, "build_vote_transactions", lambda a: ({"to": a, "data": "0x1"}, {"to": a, "data": "0x2"}),
    )
    return deployed


@pytest.mark.parametrize("voters, message", [
    ([], "Field voters is missing."),
    (["not-an-address"], "Invalid voter address."),
    (VOTERS[:2], "Even number of voters."),
])
def test_blockchain_decision_validation(client, auth_headers, redis, blockchain_mode, voters, message):
    order_uuid = create_buy_order(redis, "AssetAlpha", ["Tech"], 100, {})
    response = client.post("/decision", json={"uuid": order_uuid, "voters": voters}, headers=auth_headers("director"))
    assert response.get_json() == {"message": message}


def test_blockchain_decision_deploys_one_contract_per_order(client, auth_headers, redis, blockchain_mode):
    order_uuid = create_buy_order(redis, "AssetAlpha", ["Tech"], 100, {})
    body = {"uuid": order_uuid, "voters": VOTERS}

    first = client.post("/decision", json=body, headers=auth_headers("director"))
    second = client.post("/decision", json=body, headers=auth_headers("director"))

    assert first.status_code == 200
    assert set(first.get_json()) == {"approve_transaction", "reject_transaction"}
    assert second.get_json() == {"message": "Invalid uuid."}
    assert len(blockchain_mode) == 1
    # The order stays pending until the on-chain vote finishes.
    assert order_exists(redis, order_uuid)


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}
