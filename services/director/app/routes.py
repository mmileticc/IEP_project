from flask import Blueprint, jsonify, request

from common.jwt_auth import role_required
from common.orders import claim_order, list_pending_orders, order_exists
from common.roles import DIRECTOR_ROLE
from common.validation import ValidationError, is_valid_eth_address, is_valid_uuid, require_fields

from . import contract_registry
from .asset_repo import apply_order
from .blockchain import build_vote_transactions, deploy_voting_contract
from .config import BLOCKCHAIN_ENABLED
from .extensions import redis_client
from .report import build_report

bp = Blueprint("director", __name__)


@bp.get("/pending_orders")
@role_required(DIRECTOR_ROLE)
def pending_orders():
    orders = list_pending_orders(redis_client)
    return jsonify({"orders": [_serialize_pending_order(order) for order in orders]}), 200


def _serialize_pending_order(order: dict) -> dict:
    item = {"uuid": order["uuid"], "order_type": order["order_type"]}
    if order["order_type"] == "BUY":
        item.update({
            "name": order["name"],
            "categories": order["categories"],
            "info": order["info"],
            "buying_price": order["buying_price"],
        })
    else:
        item.update({
            "id": order["id"],
            "selling_price": order["selling_price"],
        })
    return item


@bp.post("/decision")
@role_required(DIRECTOR_ROLE)
def decision():
    body = request.get_json(silent=True) or {}
    require_fields(body, ["uuid"])

    order_uuid = body["uuid"]
    if not is_valid_uuid(order_uuid) or not order_exists(redis_client, order_uuid):
        raise ValidationError("Invalid uuid.")

    if BLOCKCHAIN_ENABLED:
        return _decision_blockchain(order_uuid, body)
    return _decision_immediate(order_uuid, body)


def _decision_immediate(order_uuid: str, body: dict):
    require_fields(body, ["approved"])
    approved = body["approved"]
    if not isinstance(approved, bool):
        raise ValidationError("Invalid decision.")

    order = claim_order(redis_client, order_uuid)
    if order is None:
        # Another request resolved this order in the meantime.
        raise ValidationError("Invalid uuid.")
    if approved:
        apply_order(order)
    return "", 200


def _decision_blockchain(order_uuid: str, body: dict):
    voters = body.get("voters")
    if not voters or not isinstance(voters, list):
        raise ValidationError("Field voters is missing.")
    if not all(is_valid_eth_address(voter) for voter in voters):
        raise ValidationError("Invalid voter address.")
    if len(voters) % 2 == 0:
        raise ValidationError("Even number of voters.")

    # One vote per order: a second /decision for the same order is rejected.
    if not contract_registry.reserve_order(redis_client, order_uuid):
        raise ValidationError("Invalid uuid.")
    try:
        address = deploy_voting_contract(voters)
    except Exception:
        contract_registry.release_order(redis_client, order_uuid)
        raise
    contract_registry.link_contract(redis_client, address, order_uuid)

    approve_tx, reject_tx = build_vote_transactions(address)
    return jsonify({"approve_transaction": approve_tx, "reject_transaction": reject_tx}), 200


@bp.get("/report")
@role_required(DIRECTOR_ROLE)
def report():
    return jsonify({"statistics": build_report()}), 200
