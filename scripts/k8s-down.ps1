<#
.SYNOPSIS
    Deletes the 'iep-fund' namespace: all pods, services and persistent data.

.EXAMPLE
    .\scripts\k8s-down.ps1
#>

$ErrorActionPreference = "Continue"

Write-Host "==> Deleting namespace 'iep-fund' (pods, services and data)" -ForegroundColor Cyan
kubectl delete namespace iep-fund --ignore-not-found

Write-Host ""
Write-Host "Done. Start again with: .\scripts\k8s-up.ps1" -ForegroundColor Green
