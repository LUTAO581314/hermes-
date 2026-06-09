#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

ENV_FILE=${BAIRUI_HERMES_ENV_FILE:-/etc/bairui/hermes.env}
INSTALL_SYSTEMD=${BAIRUI_INSTALL_SYSTEMD:-0}
RUN_COMPOSE=${BAIRUI_RUN_COMPOSE:-1}
SYSTEMD_UNIT_PATH=${BAIRUI_SYSTEMD_UNIT_PATH:-/etc/systemd/system/bairui-hermes.service}

cd "$PROJECT_ROOT"

echo "bairui Hermes deploy: project root is $PROJECT_ROOT"

if ! command -v python >/dev/null 2>&1; then
  echo "python is required. Install Python before running this script." >&2
  exit 1
fi

python -m compileall src tests
PYTHONPATH=. python -m unittest discover -s tests

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    chmod 600 .env || true
    echo "created local .env from .env.example"
  else
    echo ".env.example is missing" >&2
    exit 1
  fi
fi

mkdir -p data/hermes logs/hermes obsidian-vault tmp/hermes

if [ "$RUN_COMPOSE" = "1" ]; then
  if docker compose version >/dev/null 2>&1; then
    docker compose -f docker-compose.production.yml up -d --build
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker-compose.production.yml up -d --build
  else
    echo "Docker Compose is required when BAIRUI_RUN_COMPOSE=1." >&2
    exit 1
  fi
else
  echo "Docker Compose start skipped because BAIRUI_RUN_COMPOSE=0"
fi

cp "$PROJECT_ROOT/infra/hermes/systemd/bairui-hermes.service" "$PROJECT_ROOT/tmp/hermes/bairui-hermes.service"
echo "systemd unit template written to $PROJECT_ROOT/tmp/hermes/bairui-hermes.service"

if [ -f "$ENV_FILE" ]; then
  echo "production environment file detected at $ENV_FILE"
else
  echo "production environment file not found at $ENV_FILE"
  echo "copy infra/hermes/env.example to $ENV_FILE and set real values before production use"
fi

if [ "$INSTALL_SYSTEMD" = "1" ]; then
  if [ "$(id -u)" -ne 0 ]; then
    echo "BAIRUI_INSTALL_SYSTEMD=1 requires root because it writes $SYSTEMD_UNIT_PATH" >&2
    exit 1
  fi
  cp "$PROJECT_ROOT/infra/hermes/systemd/bairui-hermes.service" "$SYSTEMD_UNIT_PATH"
  systemctl daemon-reload
  systemctl enable bairui-hermes
  systemctl restart bairui-hermes
  systemctl status bairui-hermes --no-pager
else
  echo "systemd install skipped. Set BAIRUI_INSTALL_SYSTEMD=1 as root to install the service."
fi

echo "Hermes health:       http://127.0.0.1:8787/health"
echo "Hermes ready:        http://127.0.0.1:8787/ready"
echo "Hermes capabilities: http://127.0.0.1:8787/capabilities"
