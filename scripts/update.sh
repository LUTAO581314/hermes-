#!/usr/bin/env bash
set -euo pipefail

cd "${APP_DIR:-/opt/hermes-system}"

git pull --ff-only
bash scripts/start.sh
curl -fsS "http://127.0.0.1:${HERMES_PORT:-8787}/health"
echo
