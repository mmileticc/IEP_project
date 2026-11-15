"""Background poller that watches every active voting contract and, once a
majority is reached on-chain, applies the outcome to MongoDB/Redis.

It polls the contract's `finished()`/`approved()` view functions instead of
subscribing to event logs: plain `eth_call` works on every JSON-RPC
provider, while filter support (`eth_newFilter`) varies. The cost is up to
POLL_INTERVAL_SECONDS of latency.

Outcomes are applied through `claim_order`, so even if two listeners ran at
once an order would still be applied only once. The director still runs as
a single replica with one worker to avoid duplicate RPC polling."""
import logging
import threading
import time

from common.orders import claim_order

from . import contract_registry
from .asset_repo import apply_order
from .blockchain import get_voting_status
from .extensions import redis_client

POLL_INTERVAL_SECONDS = 2

logger = logging.getLogger(__name__)


def resolve_if_finished(address: str) -> None:
    order_uuid = contract_registry.get_order_uuid(redis_client, address)
    if order_uuid is None:
        contract_registry.unlink_contract(redis_client, address)
        return

    finished, approved = get_voting_status(address)
    if not finished:
        return

    order = claim_order(redis_client, order_uuid)
    if order is not None and approved:
        apply_order(order)
    contract_registry.unlink_contract(redis_client, address, order_uuid)
    logger.info("Vote %s finished for order %s (approved=%s)", address, order_uuid, approved)


def poll_once() -> None:
    for address in list(contract_registry.list_active_contracts(redis_client)):
        try:
            resolve_if_finished(address)
        except Exception:
            # One failing contract must not block the others; it stays
            # active and is retried on the next tick.
            logger.exception("Failed to resolve voting contract %s", address)


def _poll_loop():
    while True:
        try:
            poll_once()
        except Exception:
            # Redis may be unreachable (e.g. still starting); a transient
            # failure must never kill the listener thread.
            logger.exception("Voting listener tick failed")
        time.sleep(POLL_INTERVAL_SECONDS)


def start_listener() -> threading.Thread:
    thread = threading.Thread(target=_poll_loop, name="voting-listener", daemon=True)
    thread.start()
    return thread
