#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-local}"
DOMAIN="${DOMAIN:-}"

step() {
  printf '== %s ==\n' "$1"
}

new_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 24
  else
    tr -dc 'a-f0-9' </dev/urandom | head -c 48
  fi
}

ensure_env_file() {
  if [[ ! -f .env ]]; then
    [[ -f .env.example ]] || { echo ".env.example is missing" >&2; exit 1; }
    cp .env.example .env
    chmod 600 .env || true
  fi
}

ensure_env_value() {
  local name="$1"
  local value="$2"
  if grep -qE "^${name}=" .env; then
    if grep -qE "^${name}=$" .env; then
      sed -i.bak "s|^${name}=.*$|${name}=${value}|" .env
      rm -f .env.bak
    fi
  else
    printf '%s=%s\n' "$name" "$value" >> .env
  fi
}

step "Preparing MOXI Hermes runtime environment"
ensure_env_file
ensure_env_value "POSTGRES_DB" "moxi"
ensure_env_value "POSTGRES_USER" "moxi"

if ! grep -qE '^POSTGRES_PASSWORD=.+$' .env; then
  ensure_env_value "POSTGRES_PASSWORD" "$(new_secret)"
fi

ensure_env_value "HERMES_ENV" "production"
ensure_env_value "HERMES_HOST" "127.0.0.1"
ensure_env_value "HERMES_PORT" "8787"

mkdir -p src tests data/postgres logs obsidian-vault

if [[ "$MODE" == "domain" && -z "$DOMAIN" ]]; then
  echo "Domain mode requires DOMAIN, for example: MODE=domain DOMAIN=moxi.example.com scripts/deploy-usable.sh" >&2
  exit 1
fi

step "Starting PostgreSQL and Hermes"
if docker compose version >/dev/null 2>&1; then
  docker compose -f docker-compose.production.yml up -d --build
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f docker-compose.production.yml up -d --build
else
  echo "Docker Compose is required." >&2
  exit 1
fi

step "Deployment started"
printf 'Hermes health:       http://127.0.0.1:8787/health\n'
printf 'Hermes ready:        http://127.0.0.1:8787/ready\n'
printf 'Hermes capabilities: http://127.0.0.1:8787/capabilities\n'
