#!/usr/bin/env bash
# Compiles Voting.sol with the ethereum/solc Docker image and writes the ABI +
# bytecode to Voting.compiled.json. Bash equivalent of compile-contract.ps1.
#
# Usage: scripts/compile-contract.sh [solc-version]
set -euo pipefail

solc_version="${1:-0.8.19}"
contracts_dir="$(cd "$(dirname "$0")/../services/director/app/contracts" && pwd)"
output_dir="$contracts_dir/output"

rm -rf "$output_dir"
docker run --rm -v "$contracts_dir:/sources" "ethereum/solc:$solc_version" \
  -o /sources/output --abi --bin /sources/Voting.sol

python3 - "$contracts_dir" "$solc_version" <<'PY'
import glob, json, os, sys

contracts_dir, version = sys.argv[1], sys.argv[2]
output = os.path.join(contracts_dir, "output")
# solc names output files after the contract (OrderVoting), not the source file.
abi_path = glob.glob(os.path.join(output, "*.abi"))[0]
bin_path = glob.glob(os.path.join(output, "*.bin"))[0]
with open(abi_path, encoding="utf-8") as f:
    abi = json.load(f)
with open(bin_path, encoding="utf-8") as f:
    bytecode = f.read().strip()
if not bytecode:
    sys.exit(f"{bin_path} is empty; compilation did not succeed.")

artifact = {
    "_comment": (
        f"Pre-compiled output of Voting.sol (solc {version}). Loaded by app/blockchain.py; "
        "no solc needed at build or run time. Regenerate after editing Voting.sol with "
        "scripts/compile-contract.ps1 or scripts/compile-contract.sh."
    ),
    "abi": abi,
    "bytecode": "0x" + bytecode,
}
with open(os.path.join(contracts_dir, "Voting.compiled.json"), "w", encoding="utf-8") as f:
    json.dump(artifact, f, indent=2)
    f.write("\n")
PY

rm -rf "$output_dir"
echo "Updated $contracts_dir/Voting.compiled.json. Rebuild the director image to pick it up."
