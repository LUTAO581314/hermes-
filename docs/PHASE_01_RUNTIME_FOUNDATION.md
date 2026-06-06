# Phase 01 Runtime Foundation

## 1. Goal

Create the minimal Hermes runtime foundation that can run safely on a lightweight VPS.

This phase is intentionally small. It proves that Hermes can start, answer health checks, write logs, and keep runtime secrets outside Git before Feishu, WeChat, Obsidian write-back, TrendRadar, Graphify, or trading-related capabilities are added.

## 2. Deliverables

- Python standard-library HTTP runtime under `hermes_runtime/`.
- Health endpoint: `GET /health`.
- Readiness endpoint: `GET /ready`.
- Version endpoint: `GET /version`.
- Structured JSONL logs under `logs/hermes-runtime.jsonl`.
- `.env.example` with placeholders only.
- OpenAI-compatible multi-model gateway placeholders.
- WeChat companion-channel placeholders with safe defaults.
- `Dockerfile` and `docker-compose.yml`.
- VPS helper scripts under `scripts/`.
- systemd service template for non-Docker VPS deployment.
- Unit tests under `tests/`.
- Chinese owner report under `reports/phase-01-runtime-foundation.zh-CN.md`.

## 3. Local Run

```powershell
python -m hermes_runtime
```

Then check:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/health
Invoke-RestMethod http://127.0.0.1:8787/ready
```

## 4. Docker Run

Copy `.env.example` to `.env` and review values:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

Then check:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke-test.ps1
```

## 5. VPS Layout

Recommended path:

```text
/opt/hermes-system/
  .env
  data/
  logs/
  obsidian-vault/
  backups/
```

Install base directories and service user:

```bash
sudo bash scripts/install-vps.sh
```

Start:

```bash
bash scripts/start.sh
```

Install and start with systemd:

```bash
sudo bash scripts/install-systemd.sh
```

Stop:

```bash
bash scripts/stop.sh
```

Update:

```bash
bash scripts/update.sh
```

Deployed verification snapshot:

```text
Service: hermes-runtime.service
Path: /opt/hermes-system
Runtime user: hermes
Bind address: 127.0.0.1:8787
Health: ok
Readiness: ready
Safe mode: true
AI provider: supermoxi
AI API key: configured on server only when provided by the owner
WeChat mode: disabled
WeChat channel: official_account
WeChat personal bridge: disabled
```

## 6. Security Defaults

- The default host is `127.0.0.1`.
- Compose exposes the service only to localhost.
- `.env` is ignored by Git.
- `.env.example` contains placeholders only.
- Safe mode is enabled by default.
- The systemd service runs as the non-root `hermes` user.
- The systemd service uses `NoNewPrivileges`, `PrivateTmp`, and restricted write paths.
- Feishu smoke testing is disabled until credentials are added on the server.
- WeChat is configuration-ready only; the real callback adapter is not enabled.
- WeChat proactive chat is disabled by default.
- WeChat personal-account bridging is disabled by default.
- No broker API, shell executor, or public dashboard is enabled.

## 7. Phase 1 Exit Criteria

- Runtime starts locally.
- `/health` responds.
- `/health` reports AI and WeChat configuration state without exposing secrets.
- `/ready` responds after runtime directories exist.
- Logs are written.
- No secrets are committed.
- VPS SSH reachability is checked before deployment.
- VPS deployment is verified through systemd.
- Chinese report is written.
