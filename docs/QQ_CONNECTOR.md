# QQ Connector Plan

Technical path source: https://github.com/LUTAO581314/hermes-

## 1. Why QQ Was Missing

QQ was not omitted because it is impossible. It was outside the first social
surface scope. The earlier implementation prioritized:

- Feishu for company operations,
- WeChat / ClawBot for personal companionship,
- web chat for local testing and dashboard use.

QQ should be added as a third social connector after the runtime contract is
stable, using the same `/social/turn` and `/jobs/event` lifecycle as WeChat and
Feishu.

## 2. Recommended QQ Routes

MOXI now keeps two QQ routes separate:

- Official QQ bot: lower protocol risk, best for public or formal bot use.
- Personal QQ scan bridge: NapCat-backed personal account route, useful for
  companionship and private chat surfaces, but with higher platform-risk.

Use the official QQ bot route for stable public deployments.

Expected credentials:

- `HERMES_QQ_MODE`
- `HERMES_QQ_BOT_APP_ID`
- `HERMES_QQ_BOT_TOKEN`
- `HERMES_QQ_BOT_SECRET`
- `HERMES_QQ_WEBHOOK_TOKEN`

The runtime health endpoint only reports whether these values are configured.
It must never return the raw values.

### Personal QQ Scan Bridge

The first implemented personal route uses NapCat in Docker:

- container name: `moxi-napcat`,
- WebUI bound to `127.0.0.1:6099`,
- OneBot bound to `127.0.0.1:3001`,
- runtime config directory: `/opt/napcat/config`,
- runtime QQ data directory: `/opt/napcat/qq-data`.

BaiLongma exposes:

- `GET /social/qq-personal/qr`
- `POST /social/qq-personal/start`
- `POST /social/qq-personal/logout`

The status endpoint may return `bridge_missing`, `stopped`, `starting`,
`webui_ready`, `qr_ready`, or `connected`. QR URLs and WebUI tokens are runtime
materials only and must not be committed or copied into public docs.

## 3. Runtime Target IDs

Use stable target ids:

- direct message: `qq:user:<id>`
- group: `qq:group:<id>`
- guild/channel: `qq:guild:<guild_id>:channel:<channel_id>`

Raw platform ids should stay in the private connector runtime and not appear in
public reports.

## 4. Connector Flow

```text
QQ webhook or polling event
  -> normalize target id
  -> client.plan_social_turn(channel="qq", target_id=..., message=...)
  -> send ACK when returned
  -> report ack_sent
  -> run fast reply or slow worker
  -> report worker_started / worker_completed / worker_failed
  -> deliver final QQ message
  -> report final_delivered / failure_delivered
```

## 5. Safety Rules

- QQ is a social surface, not a company-write surface.
- Company, money, HR, legal, account, and trading actions require owner
  confirmation and should route to Feishu or a protected admin flow.
- The connector must not store raw message bodies, images, voice files, or QQ
  credentials in durable job records.
- Public docs must not include real QQ app ids, tokens, secrets, group ids, or
  user ids.

## 6. Frontend Settings Requirements

The social settings UI should include QQ as a first-class channel next to
Feishu, WeCom, and WeChat ClawBot:

- QQ Official Bot card,
- status chip: disabled / missing credentials / connected / error,
- credential fields: App ID, Bot Token, Bot Secret, Webhook Token,
- runtime base URL selector,
- test connection button,
- webhook copy button,
- last check result and timestamp,
- clear warning that QQ should not execute high-risk company actions.

For the personal scan card, the frontend should render:

- `qr_ready`: generate a QR image from `qr_url`,
- `webui_ready`: show a WebUI link if available,
- `starting`: keep polling,
- `connected`: hide QR and show connected status,
- `stopped` / `bridge_missing`: show a start action.
