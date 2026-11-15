#!/usr/bin/env bash
# Builds the service images, applies the Kubernetes manifests and waits until
# everything is ready. Bash equivalent of k8s-up.ps1 (see it for why every
# build also gets a unique timestamp tag).
#
# Usage: scripts/k8s-up.sh [--skip-build]
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
namespace="iep-fund"
images=(auth employee director)
deployments=(auth employee director ganache)
statefulsets=(mongo postgres redis)
exposed=(auth employee director ganache)

build_tag=""
if [[ "${1:-}" != "--skip-build" ]]; then
  build_tag="$(date +%Y%m%d%H%M%S)"
  echo "==> Building images (auth, employee, director), tag: $build_tag"
  for svc in "${images[@]}"; do
    docker build -f "$root/services/$svc/Dockerfile" \
      -t "iep/$svc:latest" -t "iep/$svc:$build_tag" "$root/services"
  done
else
  echo "==> Skipping build (--skip-build)."
fi

echo "==> Applying manifests"
kubectl apply -f "$root/k8s"

if [[ -n "$build_tag" ]]; then
  echo "==> Switching deployments to the fresh tag ($build_tag)"
  for svc in "${images[@]}"; do
    kubectl set image "deployment/$svc" "$svc=iep/$svc:$build_tag" -n "$namespace"
  done
fi

echo "==> Waiting for workloads to become ready (up to 3 min)"
for d in "${deployments[@]}"; do
  kubectl rollout status "deployment/$d" -n "$namespace" --timeout=180s
done
for s in "${statefulsets[@]}"; do
  kubectl rollout status "statefulset/$s" -n "$namespace" --timeout=180s
done

if [[ -n "$build_tag" ]]; then
  echo "==> Removing old timestamp tags"
  for svc in "${images[@]}"; do
    docker images "iep/$svc" --format '{{.Tag}}' \
      | grep -vxE "latest|$build_tag" \
      | xargs -r -I{} docker rmi "iep/$svc:{}" >/dev/null 2>&1 || true
  done
fi

echo "==> Waiting for LoadBalancer EXTERNAL-IPs (up to 60s)"
for name in "${exposed[@]}"; do
  ip=""
  for _ in $(seq 30); do
    ip="$(kubectl get svc "$name" -n "$namespace" \
      -o jsonpath='{.status.loadBalancer.ingress[0].ip}{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)"
    [[ -n "$ip" ]] && break
    sleep 2
  done
  if [[ -z "$ip" ]]; then
    echo "Service '$name' got no EXTERNAL-IP within 60s." >&2
    exit 1
  fi
  echo "    $name: $ip"
done

cat <<MSG

Done. Services:
  auth      http://127.0.0.1:5000
  employee  http://127.0.0.1:5001
  director  http://127.0.0.1:5002
  ganache   http://127.0.0.1:8545
MSG
