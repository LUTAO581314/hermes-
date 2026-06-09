# Single Backend Hermes Architecture

Technical path source: https://github.com/LUTAO581314/hermes-

## Decision

MOXI should converge to one backend and one frontend:

- Backend authority: Hermes.
- Frontend surface: MOXI / Brain UI design adapted from BaiLongma.
- No long-term BaiLongma backend.
- No extra bridge layer between the frontend and Hermes when Hermes can expose
  the endpoint directly.

This changes the old "Hermes + BaiLongma runtime loop" into a simpler product
boundary:

```text
MOXI / Brain UI frontend
  -> Hermes backend endpoints
     -> Hermes native tools, memory, skills, MCP, sessions, cron, gateway
     -> external runtimes such as TrendRadar when needed
```

## What To Migrate From BaiLongma

Keep these because they are useful product work:

- Brain UI visual layout, chat surface, settings patterns, progress strip, voice
  buttons, image attachment UX, and hotspot panel design.
- Hotspot panel data shape: clickable title, source URL, source/platform label,
  short summary, and bottom feed cards.
- Channel isolation lesson: web/API/voice turns must not leak to WeChat, Feishu,
  or QQ unless the owner explicitly confirms a cross-channel send.
- Frontend state ideas: quick acknowledgement, active job progress, route badges,
  and owner-confirmation surfaces.
- Browser TTS fallback and microphone/conversation button separation.

## What Not To Migrate

Retire or discard these backend responsibilities:

- BaiLongma model loop as a second agent brain.
- BaiLongma memory database as durable memory authority.
- BaiLongma settings endpoints as the main configuration source.
- BaiLongma Feishu tools as backend authority.
- NapCat personal QQ control as the default QQ route.
- Any hardcoded public-data keys, QR URLs, WebUI tokens, chat ids, or runtime
  secrets.

## Hotspot Migration

BaiLongma's hotspot feature is worth keeping as a frontend capability, but the
backend should move to Hermes.

Hermes now exposes:

```text
GET /hotspots
```

The endpoint reads normalized TrendRadar JSON output from:

```env
HERMES_TRENDRADAR_OUTPUT_DIR=/home/hermes/external/TrendRadar/output
```

It returns the same UI-friendly concepts the Brain UI panel needs:

- `items`
- `feed`
- `platforms`
- source URLs for clickable titles
- source/platform labels

This keeps the hotspot panel real, but removes BaiLongma as a backend
dependency for public-opinion display.

## Frontend Target

The final MOXI/Brain UI frontend should call Hermes directly:

```text
GET  /health
GET  /ready
GET  /capabilities
GET  /frontend/contract
GET  /config/schema
POST /config/update
GET  /hotspots
POST /social/turn
POST /jobs/event
GET  /jobs
GET  /latency
POST /media/plan-send
```

If a feature cannot be mapped to Hermes yet, the frontend should show it as
`planned` or `missing_config`, not silently call BaiLongma backend.

## Retirement Sequence

1. Back up `/home/hermes/external/BaiLongma` to `/home/hermes/backups`.
2. Extract only frontend assets and documented UI patches.
3. Move useful backend surfaces into Hermes endpoints.
4. Point the protected domain to the Hermes-hosted frontend.
5. Verify chat stays local in web UI and does not send to WeChat.
6. Verify `/hotspots` returns real TrendRadar-backed items.
7. Stop `bailongma.service`.
8. Disable `bailongma.service` only after the Hermes frontend is stable.

Do not delete the BaiLongma checkout before steps 1-6 pass.
