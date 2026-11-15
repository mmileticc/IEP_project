"""Deploys the OrderVoting contract and builds the unsigned vote
transactions returned by POST /decision. Only used when BLOCKCHAIN_ENABLED
is true; nothing here touches the network at import time.

The contract is compiled ahead of time: contracts/Voting.compiled.json holds
the ABI and bytecode (regenerate with scripts/compile-contract.*). The
director image therefore needs no Solidity compiler and no network access
to fetch one, at build or run time."""
import json
import os

from web3 import Web3

_COMPILED_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "contracts", "Voting.compiled.json")

_compiled_interface = None


def get_compiled_contract() -> dict:
    """Loads {abi, bytecode} from Voting.compiled.json, cached after the first call."""
    global _compiled_interface
    if _compiled_interface is None:
        with open(_COMPILED_CONTRACT_PATH, encoding="utf-8") as artifact_file:
            data = json.load(artifact_file)
        _compiled_interface = {"abi": data["abi"], "bytecode": data["bytecode"]}
    return _compiled_interface


def get_web3() -> Web3:
    provider_url = os.environ.get("BLOCKCHAIN_PROVIDER_URL", "http://ganache:8545")
    return Web3(Web3.HTTPProvider(provider_url))


def _deployer_account(web3: Web3) -> str:
    index = int(os.environ.get("GANACHE_DEPLOYER_ACCOUNT_INDEX", "0"))
    return web3.eth.accounts[index]


def _bound_contract(web3: Web3, address: str):
    return web3.eth.contract(address=Web3.to_checksum_address(address), abi=get_compiled_contract()["abi"])


def deploy_voting_contract(voters) -> str:
    """Deploys a fresh OrderVoting contract restricted to `voters`, paying gas
    from an account Ganache pre-funds. Returns the contract address."""
    web3 = get_web3()
    interface = get_compiled_contract()
    factory = web3.eth.contract(abi=interface["abi"], bytecode=interface["bytecode"])

    checksum_voters = [Web3.to_checksum_address(v) for v in voters]
    tx_hash = factory.constructor(checksum_voters).transact({"from": _deployer_account(web3)})
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.contractAddress


def build_vote_transactions(address: str, web3: Web3 = None):
    """Returns (approve_transaction, reject_transaction) as unsigned {to, data}
    dicts. Each voter fills in from/gas/nonce and signs them; the service
    never signs or sends on a voter's behalf."""
    contract = _bound_contract(web3 or get_web3(), address)
    return (
        {"to": address, "data": contract.encodeABI(fn_name="approveOrder")},
        {"to": address, "data": contract.encodeABI(fn_name="rejectOrder")},
    )


def get_voting_status(address: str):
    """Returns (finished, approved) read straight from the contract."""
    contract = _bound_contract(get_web3(), address)
    finished = contract.functions.finished().call()
    approved = contract.functions.approved().call() if finished else None
    return finished, approved
