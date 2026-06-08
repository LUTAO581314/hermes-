# Capability Matrix

Technical path source: https://github.com/LUTAO581314/hermes-

## Purpose

The capability matrix is the bridge between backend reality and frontend UI.
It gives Brain UI, dashboards, and channel connectors a single endpoint for
showing what is ready, missing, planned, disabled, or partially configured.

Endpoint:

```text
GET /capabilities
```

## Status States

| State | Meaning | UI Treatment |
| --- | --- | --- |
| `ready` | Usable according to local configuration | Green check |
| `partial` | Usable only through fallback or upstream runtime | Yellow status |
| `missing_config` | Intended but missing required configuration | Red or warning chip |
| `disabled` | Explicitly off | Gray chip |
| `planned` | In roadmap but not exposed as a complete runtime capability | Neutral roadmap chip |

## Current Capability Keys

- `runtime`
- `model_gateway`
- `text_chat`
- `image_understanding`
- `search_intelligence`
- `memory_governance`
- `wechat`
- `feishu_company`
- `qq`
- `voice_input`
- `voice_output`
- `stickers`
- `image_generation`

## Frontend Contract

The frontend should render each capability as a card:

- label,
- state chip,
- plane: runtime / personal / company,
- detail,
- next action.

The frontend should not infer secrets from raw config. It should only trust the
secret-safe booleans and status labels returned by `/capabilities`.

Frontend-specific progress states, route labels, and channel permission planes
are exposed through:

```text
GET /frontend/contract
```

Recommended polling:

```text
30 seconds while settings modal is open
manual refresh elsewhere
```

## Hermes Integration Rule

Hermes keeps its native agent logic. MOXI should not duplicate it in the
frontend. The frontend adapter should:

- display Hermes capability state,
- pass normalized channel messages to the runtime contract,
- show quick acknowledgement and worker status,
- keep high-risk action confirmations outside ordinary chat flow,
- never expose raw secrets, cookies, QR sessions, chat ids, or media files.
