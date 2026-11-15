# Operations

Commands for working with a running deployment in the `iep-fund` namespace.

## Status

```bash
kubectl get pods -n iep-fund
kubectl get svc -n iep-fund
kubectl logs deployment/director -n iep-fund -f
```

## Rebuilding a single service by hand

`kubectl rollout restart` alone does not pick up a rebuilt `:latest` image on Docker Desktop
(see *Unique image tags* in the README). Give each build a unique tag and point the deployment
at it:

```bash
tag=$(date +%Y%m%d%H%M%S)
docker build -f services/director/Dockerfile -t iep/director:latest -t "iep/director:$tag" services/
kubectl set image deployment/director "director=iep/director:$tag" -n iep-fund
kubectl rollout status deployment/director -n iep-fund
```

The same works for `auth` and `employee`.

## Inspecting the databases

Each image ships its own CLI client.

PostgreSQL (`users` table):

```bash
kubectl exec -it postgres-0 -n iep-fund -- psql -U iep -d iep_auth -c 'SELECT id, email, role FROM users;'
```

MongoDB (`assets` collection):

```bash
kubectl exec -it mongo-0 -n iep-fund -- mongosh iep_fund --eval 'db.assets.find().pretty()'
```

Redis (pending orders and active voting contracts):

```bash
kubectl exec -it redis-0 -n iep-fund -- redis-cli SMEMBERS pending_orders
kubectl exec -it redis-0 -n iep-fund -- redis-cli SMEMBERS active_contracts
```

To use a GUI client (pgAdmin, MongoDB Compass, RedisInsight), forward the port in a separate
terminal and connect to `127.0.0.1`:

```bash
kubectl port-forward -n iep-fund svc/postgres 5432:5432
```

With Docker Compose, use `docker compose exec postgres psql -U iep -d iep_auth` and the
equivalent commands for `mongo` and `redis`.

## Clean restart

All state lives in the namespace's persistent volumes. Deleting the namespace resets everything:

```bash
./scripts/k8s-down.sh && ./scripts/k8s-up.sh --skip-build
```
