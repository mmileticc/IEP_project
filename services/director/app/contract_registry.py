"""Tracks, in Redis, which deployed voting contracts are still awaiting an
outcome and which pending order each one belongs to. The pending order
itself stays in Redis until the vote concludes (see listener.py); only then
is it removed and recorded in MongoDB.

    contract:<address>     -> order uuid
    order_contract:<uuid>  -> contract address (one contract per order)
    active_contracts       -> SET of addresses still being watched
"""
ACTIVE_CONTRACTS_KEY = "active_contracts"


def _contract_key(address: str) -> str:
    return f"contract:{address}"


def _order_contract_key(order_uuid: str) -> str:
    return f"order_contract:{order_uuid}"


def reserve_order(redis_client, order_uuid: str) -> bool:
    """Claims the order for a vote before the contract is deployed. Returns
    False if a vote for this order already exists (or is being created)."""
    return bool(redis_client.set(_order_contract_key(order_uuid), "", nx=True))


def release_order(redis_client, order_uuid: str) -> None:
    redis_client.delete(_order_contract_key(order_uuid))


def link_contract(redis_client, address: str, order_uuid: str) -> None:
    pipe = redis_client.pipeline()
    pipe.set(_contract_key(address), order_uuid)
    pipe.set(_order_contract_key(order_uuid), address)
    pipe.sadd(ACTIVE_CONTRACTS_KEY, address)
    pipe.execute()


def get_order_uuid(redis_client, address: str):
    return redis_client.get(_contract_key(address))


def unlink_contract(redis_client, address: str, order_uuid=None) -> None:
    pipe = redis_client.pipeline()
    pipe.delete(_contract_key(address))
    pipe.srem(ACTIVE_CONTRACTS_KEY, address)
    if order_uuid is not None:
        pipe.delete(_order_contract_key(order_uuid))
    pipe.execute()


def list_active_contracts(redis_client):
    return redis_client.smembers(ACTIVE_CONTRACTS_KEY)
