#!/usr/bin/env bash
set -euo pipefail

cd "${APP_DIR:-/opt/hermes-system}"

if command -v docker compose >/dev/null 2>&1; then
  docker compose down
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose down
else
  echo "Docker Compose not found. Stop the foreground python process manually."
fi
