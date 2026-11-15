from web3 import Web3

import app.listener as listener
from app import contract_registry
from app.blockchain import build_vote_transactions
from common.orders import create_buy_order, order_exists

ADDRESS = "0x" + "1" * 40


def test_vote_transactions_encode_contract_calls():
    approve_tx, reject_tx = build_vote_transactions(ADDRESS, web3=Web3())

    assert approve_tx["to"] == reject_tx["to"] == ADDRESS
    assert approve_tx["data"] != reject_tx["data"]
    assert approve_tx["data"].startswith("0x") and len(approve_tx["data"]) == 10


def test_listener_applies_approved_vote_once(monkeypatch, redis, assets):
    order_uuid = create_buy_order(redis, "AssetAlpha", ["Tech"], 100, {})
    contract_registry.link_contract(redis, ADDRESS, order_uuid)
    monkeypatch.setattr(listener, "get_voting_status", lambda address: (True, True))

    listener.resolve_if_finished(ADDRESS)
    listener.resolve_if_finished(ADDRESS)

    assert assets.count_documents({"name": "AssetAlpha"}) == 1
    assert not order_exists(redis, order_uuid)
    assert ADDRESS not in contract_registry.list_active_contracts(redis)


def test_listener_waits_for_unfinished_vote(monkeypatch, redis, assets):
    order_uuid = create_buy_order(redis, "AssetAlpha", ["Tech"], 100, {})
    contract_registry.link_contract(redis, ADDRESS, order_uuid)
    monkeypatch.setattr(listener, "get_voting_status", lambda address: (False, None))

    listener.resolve_if_finished(ADDRESS)

    assert order_exists(redis, order_uuid)
    assert assets.count_documents({}) == 0


def test_listener_loop_survives_redis_outage(monkeypatch):
    class StopLoop(Exception):
        pass

    calls = []

    def failing_poll():
        calls.append(1)
        raise ConnectionError("redis is not reachable yet")

    def sleep(_seconds):
        if len(calls) >= 2:
            raise StopLoop

    monkeypatch.setattr(listener, "poll_once", failing_poll)
    monkeypatch.setattr(listener.time, "sleep", sleep)

    try:
        listener._poll_loop()
    except StopLoop:
        pass
    assert len(calls) == 2
