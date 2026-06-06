#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hermes-system}"
SERVICE_USER="${SERVICE_USER:-hermes}"
SERVICE_NAME="${SERVICE_NAME:-hermes-runtime}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "install-systemd.sh must run as root" >&2
  exit 1
fi

if [[ ! -f "$APP_DIR/scripts/$SERVICE_NAME.service" ]]; then
  echo "Missing $APP_DIR/scripts/$SERVICE_NAME.service" >&2
  exit 1
fi

install -m 0644 "$APP_DIR/scripts/$SERVICE_NAME.service" "/etc/systemd/system/$SERVICE_NAME.service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME.service"
systemctl restart "$SERVICE_NAME.service"

echo "$SERVICE_NAME started"
systemctl --no-pager --full status "$SERVICE_NAME.service" || true
