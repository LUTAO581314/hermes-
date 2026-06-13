# bairui Commercial Trial Delivery Quickstart

This guide is the operator handoff for a commercial trial build. It turns the
current source tree into a usable local or server demo while keeping the public
product surface under the `bairui` brand only.

## 0. Customer-Visible Brand Rule

Customer-facing UI, activation copy, setup steps, public contracts, demo
reports, and exported operator instructions must expose only `bairui`.

Historical source names, upstream runtime names, and third-party repository
names are internal engineering attribution. Keep them in engineering docs,
license files, or vendor boundaries. Do not show them in the activation page,
console labels, customer quickstart, product screenshots, or public product
contract.

## 1. Local Trial Quickstart

Use this path for the first customer-facing walkthrough on a Windows laptop or
local development workstation.

```powershell
python -m pip install -r requirements.txt
python -m src.hermes demo flow
python -m src.hermes serve
```

Open the console:

```text
http://127.0.0.1:8787/console
```

The local demo flow creates trial evidence for dashboard, command, report,
memory review, channel approval, CodeGraph, runtime readiness, metrics, and
diagnostics. Demo data is local evidence only:

- `will_send=false`
- no external dispatch
- no automatic long-term memory write
- owner approval remains required for sends and memory promotion

## 2. Windows Verification

Run these before a customer trial handoff:

```powershell
.\scripts\smoke-test.ps1
.\scripts\smoke-test.ps1 -FullAcceptance
.\scripts\product-acceptance.ps1
.\scripts\config-doctor.ps1
.\scripts\check-public-brand.ps1
```

Use `-FullAcceptance` when preparing a release candidate or guided demo. It
checks the product closure flow and expands into five acceptance scenarios:
research task, document knowledge base, customer communication draft, code
understanding, and runtime diagnostics.

## 3. First Activation Steps

The activation page is not a public website. It is the first-use product setup
surface for a customer/operator.

1. Open `/console` and start the activation screen.
2. Confirm the local or server runtime address.
3. Configure model gateway, data directory, log directory, vault directory,
   document output directory, CodeGraph root, and channel targets as needed.
4. If owner-token protection is enabled, set `BAIRUI_OWNER_TOKEN` on the server
   or local process.
5. Use `X-Bairui-Owner-Token` or `Authorization: Bearer <token>` for write API
   calls and protected console actions.
6. For risky self-service config fields, type the confirmation phrase:

```text
APPLY BAIRUI CONFIG
```

7. Keep configured paths inside the allowed bairui workspace/data/log/vault
   scope, or under `~/bairui` / `~/.bairui`.
8. Run `python -m src.hermes demo flow` or the dashboard `Run Demo Flow` action.
9. Open Events and export diagnostics after verification.

Owner-token protection blocks write APIs when `BAIRUI_OWNER_TOKEN` is set and a
matching token is not provided. Denied write attempts are audited.

## 4. Server Deployment Paths

For local usable deployment:

```powershell
.\scripts\deploy-usable.ps1 -Mode local
```

For Linux shell deployment:

```bash
bash scripts/deploy-usable.sh
```

For commercial Linux service assets:

```bash
sh infra/hermes/scripts/deploy-hermes.sh
```

Copy `infra/hermes/env.example` to a protected server path before service
install. Set real values there. Never commit secrets, customer data, runtime
logs, QR state, generated media, or diagnostics bundles.

Both usable deployment scripts poll `/health`, `/ready`,
`/runtime/readiness`, `/frontend/contract`, and `/demo/flow`, then write local
readiness evidence to `data/readiness.json`.

## 5. Observability And Support Commands

HTTP endpoints:

- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /metrics`
- `GET /errors`
- `GET /diagnostics/bundle`

CLI commands:

```powershell
python -m src.hermes status
python -m src.hermes runtime-readiness
python -m src.hermes diagnostics
python -m src.hermes metrics
python -m src.hermes errors
python -m src.hermes backup status
python -m src.hermes backup plan
python -m src.hermes config-status
python -m src.hermes events
```

Console support actions:

- Dashboard: run demo flow and inspect checkpoint evidence.
- Settings: apply self-service config with path and confirmation checks.
- Events: load metrics.
- Events: export diagnostics.
- Channels: inspect disabled, approval-required, and missing-config targets.

Diagnostics are redacted before export. They summarize counts, readiness,
configuration status, metrics, recent errors, and audit events without echoing
owner tokens or secret values.

## 6. Common Errors

`owner_token_required`

- Meaning: write protection is enabled.
- Fix: provide `X-Bairui-Owner-Token` or `Authorization: Bearer <token>`.

`confirmation_required`

- Meaning: a risky self-service config field needs explicit operator approval.
- Fix: type `APPLY BAIRUI CONFIG` and retry only after reviewing the change.

`outside the allowed bairui path scope`

- Meaning: a configured path points outside the permitted workspace/data/log
  scope.
- Fix: move the path under the bairui workspace, `~/bairui`, or `~/.bairui`.

`missing_config`

- Meaning: a runtime, channel, model gateway, parser, or storage dependency is
  not configured.
- Fix: open Settings or the relevant screen, fill required references, and run
  readiness again.

PostgreSQL unavailable or missing dependency

- Meaning: production database mode cannot connect or the Python database
  driver is unavailable.
- Fix: verify `POSTGRES_DB`, `POSTGRES_USER`, server address, password source,
  network access, and installed dependencies. The current product still has a
  JSONL fallback for local use.

Model gateway missing

- Meaning: model-backed agents cannot run yet.
- Fix: configure the OpenAI-compatible gateway endpoint, model name, and secret
  reference. Do not expose secrets in screenshots or logs.

Document parser missing

- Meaning: document ingestion can plan or show readiness, but parsing runtime is
  not available.
- Fix: configure the parser runtime and re-run readiness before promising file
  ingestion to a trial customer.

## 7. PostgreSQL And Backup Note

The source tree includes PostgreSQL schema, migration, and guarded backup
planning foundations, while local demos can still use JSONL-backed storage.
Before real customer data is accepted, validate production PostgreSQL
connection, migration, backup, restore, and rollback on the target server.

```powershell
python -m src.hermes backup status
python -m src.hermes backup plan
python -m src.hermes backup restore-plan --backup-path .\data\backups\postgres\example.dump
```

Restore planning is blocked unless the artifact exists and the operator types
the confirmation phrase `RESTORE BAIRUI POSTGRES`.

Do not treat a local JSONL demo as production persistence readiness.

## 8. Third-Party Attribution Boundary

Third-party source and runtime references are allowed in internal engineering
documents, license notices, dependency metadata, and vendor runtime folders.
They are not allowed in public product labels, activation copy, console routes,
customer reports, setup text, or exported customer-facing contract fields.

Before a paid trial, review the third-party attribution inventory in
`docs/28-third-party-attribution-inventory.md` and confirm every enabled runtime
license is compatible with the planned customer deployment model.

## 9. Go/No-Go Checklist

Go only when all items are true:

- Customer-visible surfaces expose only `bairui`.
- `python -m src.hermes demo flow` succeeds.
- `/console` opens and core screens render.
- `.\scripts\smoke-test.ps1 -FullAcceptance` succeeds on Windows.
- `.\scripts\product-acceptance.ps1` succeeds.
- `.\scripts\config-doctor.ps1` returns actionable diagnostics.
- `.\scripts\check-public-brand.ps1` confirms customer UI and contract assets
  expose only the `bairui` brand.
- `/metrics`, `/errors`, and `/diagnostics/bundle` return redacted support data.
- Owner-token gating is enabled and tested for the trial environment.
- Risky config fields require `APPLY BAIRUI CONFIG`.
- Demo evidence shows `will_send=false` and no automatic long-term memory write.
- Deployment writes `data/readiness.json`.
- PostgreSQL backup/restore is validated before real customer data.
- Third-party license and attribution review is complete with
  `docs/28-third-party-attribution-inventory.md` before paid delivery.

No-go when any customer data, external sending, memory promotion, model gateway
secret, parser runtime, backup/restore, or license boundary is unverified.
