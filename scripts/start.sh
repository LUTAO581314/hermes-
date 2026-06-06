#!/usr/bin/env bash
set -euo pipefail

cd "${APP_DIR:-/opt/hermes-system}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if command -v docker compose >/dev/null 2>&1; then
  docker compose up -d --build
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose up -d --build
else
  python -m hermes_runtime
fi
