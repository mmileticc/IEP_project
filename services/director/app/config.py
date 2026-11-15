import os

from common.config import JwtConfig


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Config(JwtConfig):
    pass


# Selects the /decision behaviour: immediate {uuid, approved} processing, or
# the blockchain-backed {uuid, voters} flow that deploys a voting contract.
BLOCKCHAIN_ENABLED = _env_bool("BLOCKCHAIN_ENABLED", False)
