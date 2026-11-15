<#
.SYNOPSIS
    Compiles services/director/app/contracts/Voting.sol with the
    ethereum/solc Docker image and writes the ABI + bytecode to
    services/director/app/contracts/Voting.compiled.json.

.DESCRIPTION
    Only needed after editing Voting.sol. The director service just reads
    Voting.compiled.json and never runs solc itself. The solc image is
    pulled on first use and cached afterwards.

.PARAMETER SolcVersion
    ethereum/solc image tag; must satisfy the pragma in Voting.sol (^0.8.19).

.EXAMPLE
    .\scripts\compile-contract.ps1
    .\scripts\compile-contract.ps1 -SolcVersion 0.8.19
#>

param(
    [string]$SolcVersion = "0.8.19"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$contractsDir = Join-Path $root "services\director\app\contracts"
$outputDir = Join-Path $contractsDir "output"
$solFile = "Voting.sol"

if (-not (Test-Path (Join-Path $contractsDir $solFile))) {
    throw "'$contractsDir\$solFile' does not exist."
}

if (Test-Path $outputDir) {
    Remove-Item -Recurse -Force $outputDir
}

Write-Host "==> Compiling $solFile with ethereum/solc:$SolcVersion" -ForegroundColor Cyan
docker run --rm -v "${contractsDir}:/sources" "ethereum/solc:$SolcVersion" -o /sources/output --abi --bin "/sources/$solFile"
if ($LASTEXITCODE -ne 0) {
    throw "solc failed (exit code $LASTEXITCODE). See the output above."
}

# solc names output files after the contract (OrderVoting), not the source file.
$abiPath = Get-ChildItem -Path $outputDir -Filter "*.abi" -ErrorAction SilentlyContinue | Select-Object -First 1
$binPath = Get-ChildItem -Path $outputDir -Filter "*.bin" -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $abiPath -or -not $binPath) {
    throw "No .abi/.bin output found in '$outputDir'. Check the solc output above."
}

$abiText = (Get-Content $abiPath.FullName -Raw).Trim()
$bytecodeHex = (Get-Content $binPath.FullName -Raw).Trim()

if ([string]::IsNullOrWhiteSpace($bytecodeHex)) {
    throw "$($binPath.Name) is empty; compilation did not succeed."
}

try {
    $null = $abiText | ConvertFrom-Json
} catch {
    throw "$($abiPath.Name) is not valid JSON: $_"
}

$comment = "Pre-compiled output of Voting.sol (solc $SolcVersion). Loaded by app/blockchain.py; no solc needed at build or run time. Regenerate after editing Voting.sol with scripts/compile-contract.ps1 or scripts/compile-contract.sh."

# The ABI is inserted as raw text: round-tripping it through ConvertTo-Json
# can wrap arrays as {"Count":N,"value":[...]}.
$jsonText = @(
    '{'
    ('  "_comment": "' + $comment + '",')
    ('  "abi": ' + $abiText + ',')
    ('  "bytecode": "0x' + $bytecodeHex + '"')
    '}'
) -join "`n"

try {
    $null = $jsonText | ConvertFrom-Json
} catch {
    throw "Generated Voting.compiled.json is not valid JSON: $_"
}

# Write UTF-8 without a BOM: Python's json.load rejects a BOM, and
# Set-Content -Encoding utf8 adds one on Windows PowerShell 5.1.
$outPath = Join-Path $contractsDir "Voting.compiled.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($outPath, $jsonText, $utf8NoBom)

Remove-Item -Recurse -Force $outputDir

Write-Host ""
Write-Host "Done. Updated $outPath" -ForegroundColor Green
Write-Host "Rebuild and redeploy the director to pick it up: .\scripts\k8s-up.ps1" -ForegroundColor Yellow
