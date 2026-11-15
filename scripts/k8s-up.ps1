<#
.SYNOPSIS
    Builds the service images, applies the Kubernetes manifests, waits for
    every workload to become ready and for the LoadBalancer services to get
    an EXTERNAL-IP (Docker Desktop maps it to localhost).

.DESCRIPTION
    Every build is tagged twice: iep/<svc>:latest and a unique timestamp tag
    (e.g. iep/director:20260718142530). The deployments are then switched to
    the timestamp tag with `kubectl set image`.

    Why: Docker Desktop's Kubernetes (containerd) can keep serving a stale
    image cached under iep/<svc>:latest even after a rebuild, a
    `kubectl rollout restart` or a pod deletion, because
    imagePullPolicy: IfNotPresent sees that the tag already exists. A tag
    that never existed before removes that ambiguity. Old timestamp tags are
    removed once the new pods are running.

.PARAMETER SkipBuild
    Skip the Docker build (use when the images exist and the code is unchanged).

.EXAMPLE
    .\scripts\k8s-up.ps1
    .\scripts\k8s-up.ps1 -SkipBuild
#>

param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$k8sDir = Join-Path $root "k8s"
$namespace = "iep-fund"
$ourImages = @("auth", "employee", "director")
$deployments = @("auth", "employee", "director", "ganache")
$statefulSets = @("mongo", "postgres", "redis")
$exposedServices = @("auth", "employee", "director", "ganache")

function Invoke-Checked {
    param(
        [Parameter(Mandatory)][string]$Description,
        [Parameter(Mandatory)][scriptblock]$Command
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed (exit code $LASTEXITCODE). See the output above."
    }
}

$buildTag = $null
if (-not $SkipBuild) {
    $buildTag = Get-Date -Format "yyyyMMddHHmmss"
    Write-Host "==> Building images (auth, employee, director), tag: $buildTag" -ForegroundColor Cyan
    foreach ($svc in $ourImages) {
        Invoke-Checked "Build of $svc" {
            docker build -f (Join-Path $root "services\$svc\Dockerfile") `
                -t "iep/${svc}:latest" -t "iep/${svc}:$buildTag" `
                (Join-Path $root "services")
        }
    }
} else {
    Write-Host "==> Skipping build (-SkipBuild)." -ForegroundColor Yellow
}

Write-Host "==> Applying manifests from $k8sDir" -ForegroundColor Cyan
Invoke-Checked "kubectl apply" { kubectl apply -f $k8sDir }

if ($buildTag) {
    Write-Host "==> Switching deployments to the fresh tag ($buildTag)" -ForegroundColor Cyan
    foreach ($svc in $ourImages) {
        Invoke-Checked "kubectl set image ($svc)" { kubectl set image "deployment/$svc" "${svc}=iep/${svc}:$buildTag" -n $namespace }
    }
}

# `rollout status` follows the controller, so it does not fail when an old
# pod disappears mid-rollout (unlike `kubectl wait pod --all`).
Write-Host "==> Waiting for workloads in '$namespace' to become ready (up to 3 min)" -ForegroundColor Cyan
foreach ($d in $deployments) {
    Invoke-Checked "rollout status deployment/$d" { kubectl rollout status "deployment/$d" -n $namespace --timeout=180s }
}
foreach ($s in $statefulSets) {
    Invoke-Checked "rollout status statefulset/$s" { kubectl rollout status "statefulset/$s" -n $namespace --timeout=180s }
}

if ($buildTag) {
    Write-Host "==> Removing old timestamp tags (keeping :latest and $buildTag)" -ForegroundColor Cyan
    foreach ($svc in $ourImages) {
        $oldTags = docker images "iep/${svc}" --format "{{.Tag}}" | Where-Object { $_ -and $_ -ne "latest" -and $_ -ne $buildTag }
        foreach ($t in $oldTags) {
            docker rmi "iep/${svc}:$t" 2>$null | Out-Null
        }
    }
}

Write-Host "==> Waiting for LoadBalancer EXTERNAL-IPs (up to 60s)" -ForegroundColor Cyan
foreach ($name in $exposedServices) {
    $ip = $null
    for ($i = 0; $i -lt 30; $i++) {
        $ip = kubectl get svc $name -n $namespace -o jsonpath="{.status.loadBalancer.ingress[0].ip}{.status.loadBalancer.ingress[0].hostname}" 2>$null
        if ($ip) { break }
        Start-Sleep -Seconds 2
    }
    if (-not $ip) {
        throw "Service '$name' got no EXTERNAL-IP within 60s. Check 'kubectl get svc -n $namespace' and that Kubernetes is enabled in Docker Desktop."
    }
    Write-Host "    ${name}: $ip" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Services:" -ForegroundColor Green
Write-Host "  auth      http://127.0.0.1:5000"
Write-Host "  employee  http://127.0.0.1:5001"
Write-Host "  director  http://127.0.0.1:5002"
Write-Host "  ganache   http://127.0.0.1:8545"
Write-Host ""
Write-Host "Tear down with: .\scripts\k8s-down.ps1" -ForegroundColor Yellow
