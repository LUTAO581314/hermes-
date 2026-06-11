#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-local}"
DOMAIN="${DOMAIN:-}"
HERMES_LOCAL_URL="${HERMES_LOCAL_URL:-http://127.0.0.1:8787}"
READINESS_FILE="${READINESS_FILE:-data/readiness.json}"
READINESS_TIMEOUT_SECONDS="${READINESS_TIMEOUT_SECONDS:-90}"

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

set_env_value() {
  local name="$1"
  local value="$2"
  if grep -qE "^${name}=" .env; then
    sed -i.bak "s|^${name}=.*$|${name}=${value}|" .env
    rm -f .env.bak
  else
    printf '%s=%s\n' "$name" "$value" >> .env
  fi
}

fetch_url() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS "$url"
    return
  fi
  python - "$url" <<'PY'
import sys
import urllib.request

with urllib.request.urlopen(sys.argv[1], timeout=5) as response:
    sys.stdout.write(response.read().decode("utf-8"))
PY
}

wait_for_endpoint() {
  local label="$1"
  local path="$2"
  local deadline=$((SECONDS + READINESS_TIMEOUT_SECONDS))
  local url="${HERMES_LOCAL_URL}${path}"
  while (( SECONDS < deadline )); do
    if fetch_url "$url" >/dev/null 2>&1; then
      printf '%s reachable: %s\n' "$label" "$url"
      return 0
    fi
    sleep 2
  done
  echo "$label did not become reachable before timeout: $url" >&2
  return 1
}

write_readiness_file() {
  mkdir -p "$(dirname "$READINESS_FILE")"
  python - "$HERMES_LOCAL_URL" "$READINESS_FILE" <<'PY'
import json
import sys
import time
import urllib.request

base_url = sys.argv[1].rstrip("/")
target = sys.argv[2]
paths = {
    "health": "/health",
    "ready": "/ready",
    "capabilities": "/capabilities",
    "runtime_readiness": "/runtime/readiness",
}
payload = {
    "generated_at_unix": int(time.time()),
    "base_url": base_url,
    "endpoints": {},
}
overall = "ready"
for name, path in paths.items():
    url = base_url + path
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body) if body else {}
            payload["endpoints"][name] = {
                "status": "reachable",
                "http_status": response.status,
                "url": url,
                "body": data,
            }
    except Exception as exc:
        overall = "blocked"
        payload["endpoints"][name] = {
            "status": "error",
            "url": url,
            "error": str(exc),
        }

demo_flow_url = base_url + "/demo/flow"
try:
    request = urllib.request.Request(
        demo_flow_url,
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body) if body else {}
        payload["endpoints"]["demo_flow"] = {
            "status": "completed",
            "http_status": response.status,
            "url": demo_flow_url,
            "body": data,
        }
        if data.get("demo_flow", {}).get("status") != "completed":
            overall = "partial"
except Exception as exc:
    overall = "blocked"
    payload["endpoints"]["demo_flow"] = {
        "status": "error",
        "url": demo_flow_url,
        "error": str(exc),
    }

runtime = payload["endpoints"].get("runtime_readiness", {}).get("body", {}).get("runtime_readiness")
if isinstance(runtime, dict) and runtime.get("status") == "blocked":
    overall = "blocked"
elif overall == "ready" and isinstance(runtime, dict) and runtime.get("status") == "partial":
    overall = "partial"

payload["status"] = overall
payload["console_url"] = base_url + "/console"
with open(target, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write("\n")
PY
}

step "Preparing bairui runtime environment"
ensure_env_file
set_env_value "POSTGRES_DB" "bairui"
set_env_value "POSTGRES_USER" "bairui"

if ! grep -qE '^POSTGRES_PASSWORD=.+$' .env; then
  ensure_env_value "POSTGRES_PASSWORD" "$(new_secret)"
fi

if ! grep -qE '^SONIC_PASSWORD=.+$' .env; then
  ensure_env_value "SONIC_PASSWORD" "$(new_secret)"
fi

ensure_env_value "HERMES_ENV" "production"
ensure_env_value "HERMES_HOST" "127.0.0.1"
ensure_env_value "HERMES_PORT" "8787"
ensure_env_value "SONIC_HOST" "sonic"
ensure_env_value "SONIC_PORT" "1491"

mkdir -p src tests data/postgres data/sonic logs obsidian-vault

if [[ "$MODE" == "domain" && -z "$DOMAIN" ]]; then
  echo "Domain mode requires DOMAIN, for example: MODE=domain DOMAIN=bairui.example.com scripts/deploy-usable.sh" >&2
  exit 1
fi

step "Starting PostgreSQL and bairui"
if docker compose version >/dev/null 2>&1; then
  docker compose -f docker-compose.production.yml up -d --build
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f docker-compose.production.yml up -d --build
else
  echo "Docker Compose is required." >&2
  exit 1
fi

step "Deployment started"
wait_for_endpoint "bairui health" "/health"
wait_for_endpoint "bairui ready" "/ready"
wait_for_endpoint "Runtime readiness" "/runtime/readiness"
write_readiness_file

printf 'bairui health:       %s/health\n' "$HERMES_LOCAL_URL"
printf 'bairui ready:        %s/ready\n' "$HERMES_LOCAL_URL"
printf 'bairui capabilities: %s/capabilities\n' "$HERMES_LOCAL_URL"
printf 'Runtime readiness:   %s/runtime/readiness\n' "$HERMES_LOCAL_URL"
printf 'bairui console:      %s/console\n' "$HERMES_LOCAL_URL"
printf 'Demo Flow evidence:  %s -> endpoints.demo_flow\n' "$READINESS_FILE"
printf 'Readiness file:      %s\n' "$READINESS_FILE"
