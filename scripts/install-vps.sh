#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hermes-system}"
SERVICE_USER="${SERVICE_USER:-hermes}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "install-vps.sh must run as root" >&2
  exit 1
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

mkdir -p "$APP_DIR"/{data,logs,obsidian-vault,backups}
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
chmod 750 "$APP_DIR"

if [[ ! -f "$APP_DIR/.env" && -f "$APP_DIR/.env.example" ]]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  chown "$SERVICE_USER:$SERVICE_USER" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
fi

echo "Hermes runtime base prepared at $APP_DIR"
echo "Next: copy repository files into $APP_DIR, review .env, then run scripts/install-systemd.sh or scripts/start.sh"
