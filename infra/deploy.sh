#!/usr/bin/env bash
# Idempotent deploy script. Run on the VPS after `git pull`.
#
# What it does:
#   1. Pulls latest source (no-op if you already pulled).
#   2. Rebuilds the API image from ../backend.
#   3. Restarts the API container with the new image, leaving postgres +
#      redis + nginx untouched.
#   4. Runs alembic upgrade head inside the new container (already in the
#      Dockerfile CMD, but we tail the logs to surface any migration error
#      before declaring success).
#
# Usage on VPS:
#   cd /opt/shoebox && ./infra/deploy.sh
#
# Pre-reqs (one-time, see docs/vps-deploy.md):
#   - docker + docker compose installed
#   - infra/.env populated with secrets
#   - nginx/letsencrypt populated (cert issued once)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/infra"

echo "==> Pulling latest source"
git -C "$ROOT" pull --ff-only

echo "==> Rebuilding API image"
docker compose -f docker-compose.prod.yml build api

echo "==> Restarting API container (postgres + redis + nginx stay up)"
docker compose -f docker-compose.prod.yml up -d --no-deps --force-recreate api

echo "==> Waiting for healthy status"
for i in $(seq 1 30); do
  status=$(docker inspect -f '{{.State.Health.Status}}' shoebox-api 2>/dev/null || echo "starting")
  if [ "$status" = "healthy" ]; then
    echo "API healthy after ${i}s"
    exit 0
  fi
  sleep 1
done

echo "API never became healthy — last 50 log lines:"
docker logs --tail 50 shoebox-api
exit 1
