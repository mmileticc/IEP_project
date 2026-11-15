import datetime

import pytest

from common.orders import list_pending_orders

BUY_ORDER = {"name": "AssetAlpha", "categories": ["Tech"], "buying_price": 100, "info": {"region": "EU"}}


def insert_asset(assets, **fields):
    doc = {
        "name": "AssetAlpha",
        "categories": ["Tech"],
        "buying_price": 100,
        "buying_date": datetime.datetime(2026, 1, 1),
        "info": {"region": "EU"},
        **fields,
    }
    return str(assets.insert_one(doc).inserted_id)


@pytest.mark.parametrize("path", ["/search", "/create_buy_order", "/create_sell_order"])
def test_endpoints_require_employee_role(client, auth_headers, path):
    for headers in ({}, auth_headers("director")):
        response = client.post(path, json={}, headers=headers)
        assert response.status_code == 401
        assert response.get_json() == {"msg": "Missing Authorization Header"}


@pytest.mark.parametrize("body, message", [
    ({"name": "A"}, "Field categories is missing."),
    ({**BUY_ORDER, "categories": []}, "Categories list is empty."),
    ({**BUY_ORDER, "buying_price": 0}, "Invalid buying price."),
    ({**BUY_ORDER, "buying_price": True}, "Invalid buying price."),
    ({**BUY_ORDER, "info": "text"}, "Invalid info."),
])
def test_buy_order_validation(client, auth_headers, body, message):
    response = client.post("/create_buy_order", json=body, headers=auth_headers("employee"))
    assert response.status_code == 400
    assert response.get_json() == {"message": message}


def test_buy_order_is_stored_as_pending(client, auth_headers, redis):
    response = client.post("/create_buy_order", json=BUY_ORDER, headers=auth_headers("employee"))
    assert response.status_code == 200
    [order] = list_pending_orders(redis)
    assert order["order_type"] == "BUY"
    assert order["name"] == "AssetAlpha"


def test_sell_order_requires_existing_unsold_asset(client, auth_headers, assets):
    headers = auth_headers("employee")
    sold_id = insert_asset(assets, selling_price=150, selling_date=datetime.datetime(2026, 2, 1))

    for asset_id in ("not-an-id", "0123456789abcdef01234567", sold_id):
        response = client.post("/create_sell_order", json={"id": asset_id, "selling_price": 10}, headers=headers)
        assert response.get_json() == {"message": "Invalid id."}


def test_sell_order_for_owned_asset(client, auth_headers, assets, redis):
    asset_id = insert_asset(assets)
    response = client.post(
        "/create_sell_order", json={"id": asset_id, "selling_price": 150}, headers=auth_headers("employee"),
    )
    assert response.status_code == 200
    [order] = list_pending_orders(redis)
    assert order == {**order, "order_type": "SELL", "id": asset_id, "selling_price": 150}


def test_search_serializes_assets(client, auth_headers, assets):
    insert_asset(assets)
    insert_asset(assets, name="Other", categories=["Energy"])

    response = client.post("/search", json={"category": "Tech"}, headers=auth_headers("employee"))

    [asset] = response.get_json()["assets"]
    assert asset["name"] == "AssetAlpha"
    assert asset["buying_date"] == "2026-01-01T00:00:00.000Z"
    assert "selling_price" not in asset


def test_search_rejects_unknown_operator(client, auth_headers):
    body = {"info_filters": [{"field": "region", "operator": "where", "value": "1"}]}
    response = client.post("/search", json=body, headers=auth_headers("employee"))
    assert response.status_code == 400
    assert response.get_json() == {"message": "Invalid info filter."}
