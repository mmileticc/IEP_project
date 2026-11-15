#!/usr/bin/env bash
# Deletes the 'iep-fund' namespace: all pods, services and persistent data.
set -uo pipefail
kubectl delete namespace iep-fund --ignore-not-found
