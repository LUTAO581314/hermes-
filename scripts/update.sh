#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hermes-system}"
SERVICE_USER="${SERVICE_USER:-hermes}"
SERVICE_NAME="${SERVICE_NAME:-hermes-runtime}"

cd "$APP_DIR"

if [[ "$(id -u)" -eq 0 ]] && id "$SERVICE_USER" >/dev/null 2>&1; then
  run_as_service_user=(runuser -u "$SERVICE_USER" --)
else
  run_as_service_user=()
fi

"${run_as_service_user[@]}" git pull --ff-only

if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files "$SERVICE_NAME.service" >/dev/null 2>&1; then
  systemctl restart "$SERVICE_NAME.service"
else
  bash scripts/start.sh
fi

curl -fsS "http://127.0.0.1:${HERMES_PORT:-8787}/health"
echo
