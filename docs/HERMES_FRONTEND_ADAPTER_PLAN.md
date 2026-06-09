# Hermes Frontend Adapter Plan

Technical path source: https://github.com/LUTAO581314/hermes-

## Core Decision

Hermes has its own agent logic. MOXI should integrate with it instead of
rewriting that logic in the frontend.

Phase 36 tightens this decision: Hermes is the only long-term backend
authority. BaiLongma should no longer run as a second backend once its useful
frontend assets and hotspot-panel shape are migrated. The target is MOXI /
Brain UI calling Hermes endpoints directly.

The frontend adapter owns:

- channel UI,
- capability display,
- settings UX,
- quick acknowledgement state,
- worker progress state,
- permission hints,
- human confirmation surfaces.

Hermes owns:

- native agent reasoning flow,
- internal tool orchestration,
- long-running task execution,
- memory and skill logic that already belongs to Hermes.

MOXI runtime owns:

- secret-safe capability matrix,
- social-turn planning,
- job lifecycle events,
- latency telemetry,
- channel policy,
- owner confirmation boundaries,
- public technical path and reproducible overlay docs.

## Frontend Architecture

```text
MOXI / Brain UI
  -> settings panel
  -> capability matrix panel
  -> chat / voice / image / sticker controls
  -> Hermes backend
       -> GET /capabilities
       -> GET /frontend/contract
       -> GET /config/schema
       -> POST /config/update
       -> GET /hotspots
       -> POST /social/turn
       -> POST /jobs/event
       -> GET /latency
       -> upstream Hermes native actions
```

## UI Improvements

### Settings

- Split social settings into channel cards.
- Add QQ as a first-class social channel.
- Add runtime connector settings.
- Show status chips from `/capabilities`.
- Keep save/test/copy actions near each channel.

### Chat

- Send a natural quick acknowledgement for slow tasks.
- Show "thinking / looking / generating" state before final result.
- Do not cancel an active image/search/company job when the user sends a
  follow-up; append it as context unless the user explicitly cancels.

### Company Plane

- Feishu company management must show identity and group context.
- Company writes require owner confirmation.
- The same companion persona can speak warmly, but permissions must remain
  separated by channel and action type.

### Personal Plane

- WeChat, QQ, and web chat can use the companion persona.
- Personal channels cannot approve company, money, legal, HR, or destructive
  actions.

## Implementation Order

1. Add `/capabilities` to the MOXI runtime. Done in Phase 15.
2. Render capability cards in the public website and Brain UI settings. Done in Phase 16.
3. Export the first BaiLongma patch for settings UI and QQ entry. Done in Phase 16.
4. Add runtime frontend contract endpoint. Done in Phase 17.
5. Configure the server runtime bridge and proxy `/frontend/contract` through BaiLongma. Done in Phase 18.
6. Add first `/message` to `/social/turn` progress bridge. Done in Phase 18.
7. Add runtime connector test buttons.
8. Add richer progress events to chat UI. Done in Phase 19.
9. Add company/persona permission badges. Done in Phase 20.
10. Connect BaiLongma native worker lifecycle events to Hermes `/jobs/event`.
11. Promote Brain UI settings into a Hermes control center. Done in Phase 29:
    overview, capability matrix, frontend contract, performance profile,
    memory status, async jobs, social channels, model, media, voice, search,
    security, appearance, and update domains now have separated UI surfaces.
    Done in Phase 21.
11. Merge active-job follow-ups without interrupting the running native turn.
    Done in Phase 22.
12. Add read-only Feishu company data tools. Done in Phase 23.
13. Add social image/sticker compatibility through `outbound_media`. Done in Phase 24.
14. Add GitHub Pages deployment for the public technical path.
15. Add secret-safe writable Hermes config schema. Done in Phase 30.
16. Render Hermes writable config schema inside BaiLongma Brain UI. Done in Phase 31.
17. Split QQ setup into official bot and personal scan bridge surfaces. Done in Phase 32.
18. Retire BaiLongma as a backend authority and move hotspot data to Hermes
    `/hotspots`. Started in Phase 36.

## Phase 16 Patch

`patches/bailongma/phase-16-capability-matrix-and-qq-settings.patch` applies
the first real BaiLongma overlay:

- backend `/capabilities` endpoint inside BaiLongma,
- Hermes backend bridge probe through `HERMES_RUNTIME_BASE_URL`,
- QQ official bot credential fields,
- Brain UI capability matrix cards in the social settings tab,
- status rendering for runtime, model, image, search, Feishu, WeChat, WeCom,
  QQ, voice, TTS, stickers, and reviewed image generation.

The patch intentionally reports missing Hermes bridge configuration instead of
pretending the deep adapter is complete. The next implementation phase should
start the Hermes runtime bridge and then wire `/social/turn` and `/jobs/event`
into chat progress.

## Phase 17 Runtime Contract

`GET /frontend/contract` is the machine-readable contract for BaiLongma and any
future MOXI frontend. It exposes:

- endpoint paths for `/capabilities`, `/performance`, `/social/turn`,
  `/jobs/event`, and `/latency/turn`,
- UI states for `direct_reply`, `quick_ack`, `append_to_active_job`, and
  `approval_required`,
- route labels and progress kinds for image reading, image generation, search,
  public opinion, Feishu company tasks, memory review, and high-risk actions,
- channel planes for WeChat, QQ, web chat, and Feishu,
- privacy rules that forbid raw messages, media bytes, platform ids, and secrets
  from being stored in frontend contracts or public job records.

This keeps Hermes as the backend logic owner while giving BaiLongma a stable
adapter surface for progress UI, permission badges, and slow-task behavior.

## Phase 18 Server Bridge

The server now runs the MOXI/Hermes runtime on `127.0.0.1:8787`, and BaiLongma
is configured with `HERMES_RUNTIME_BASE_URL=http://127.0.0.1:8787`.

The BaiLongma overlay patch
`patches/bailongma/phase-18-social-turn-progress-bridge.patch` adds:

- shared Hermes runtime JSON helpers,
- `GET /frontend/contract` proxy on the BaiLongma service,
- `/message` preflight planning through Hermes `/social/turn`,
- natural quick ACK emission through the existing SSE `message` event,
- `ack_sent` lifecycle reporting to Hermes `/jobs/event`,
- response metadata showing `first_action`, `route`, `ack_sent`, and `job_id`.

This is deliberately a surface-first bridge. The final answer still comes from
BaiLongma's native agent loop, while Hermes owns the route plan, progress
metadata, and job lifecycle.

## Phase 19 Progress UI

The BaiLongma overlay patch
`patches/bailongma/phase-19-progress-aware-chat-ui.patch` adds a compact
progress strip inside Brain UI chat history. It:

- consumes `moxi_progress` SSE events,
- maps Hermes routes to user-visible status text,
- shows the active route as a small chip,
- opens the chat surface when progress starts,
- clears progress after final `message` delivery or terminal lifecycle events.

Before this phase, users could see the quick ACK bubble but not a persistent
"what is happening now" state. After this phase, slow work has both a natural
ACK and a visible progress strip.

The server source cleanup for this phase archived 98 historical `.bak*` and
temporary files out of `/home/hermes/external/BaiLongma/src` into
`/home/hermes/backups/`, leaving the active source tree clean for future patch
exports.

## Phase 20 Channel Plane Badges

The BaiLongma overlay patch
`patches/bailongma/phase-20-channel-plane-badges.patch` adds visible plane
badges to chat bubbles:

- WeChat and QQ map to personal companionship,
- web chat maps to web companionship,
- Feishu, Lark, and WeCom map to the company plane,
- `company_task` routes override the fallback plane to company,
- `high_risk` routes override the fallback plane to owner confirmation,
- `moxi_progress` ACK bubbles can show runtime/progress context.

The Hermes runtime route classifier also gained Chinese keywords for image,
search, public-opinion, company, memory, and high-risk routes. This keeps the
Chinese production path aligned with the UI boundary labels.

## Phase 21 Tool Lifecycle Events

The BaiLongma overlay patch
`patches/bailongma/phase-21-tool-lifecycle-events.patch` closes the runtime
feedback loop between BaiLongma and Hermes:

- `runTurn` reports `worker_started` when a queued Hermes job begins native
  processing.
- normal completion reports `worker_completed` unless the message delivery
  path has already completed the job.
- non-abort failures report `worker_failed` with a short sanitized error.
- `send_message` reports `worker_completed` and `final_delivered` after the
  final message is written to the conversation log and visible to the user.
- `moxi_progress` SSE events mirror these lifecycle states so Brain UI can show
  progress without guessing.

Server verification used a Feishu-style `/message` request. The returned Hermes
job advanced to `delivered` with a metadata-only `conversation:<id>` result
pointer. No raw message bodies, secrets, platform tokens, or media bytes are
stored in the public job record.

## Phase 22 Follow-Up Job Merge

The BaiLongma overlay patch
`patches/bailongma/phase-22-follow-up-job-merge.patch` makes `/message` respect
Hermes `append_to_active_job` plans:

- the natural follow-up ACK is still emitted,
- the follow-up text is written to the conversation timeline for context,
- `moxi_progress` emits `append_to_active_job`,
- the HTTP response exposes `queued:false` and `appended_to_active_job:true`,
- the follow-up is not pushed into the active LLM queue and does not trigger an
  interrupt callback.

This closes the user-experience bug where a user sends "make it softer" or
"also check this" while a slow image, search, or company task is running, and
the second message accidentally starts another full turn.

## Phase 23 Feishu Read-Only Tools

The BaiLongma overlay patch
`patches/bailongma/phase-23-company-read-connectors.patch` adds the first
company-data tool layer:

- `src/social/feishu-openapi.js` wraps Feishu tenant token retrieval and
  read-only OpenAPI calls.
- `feishu_lookup_user` reads one Feishu user profile by `open_id`, `user_id`,
  or `union_id`, returning sanitized identity metadata only.
- `feishu_bitable_list_records` lists configured Bitable records, truncating
  long fields and summarizing object attachments.
- schemas, tool routing, and tool policy mark both tools as read-only/low risk.

This is intentionally not a full company operator yet. It proves the safe tool
shape first; Feishu app credentials, contact read scope, Bitable app/table
configuration, and tenant publication must be verified before real company
data can be returned.

## Phase 24 Social Media Compatibility

Hermes `/social/turn` now exposes `outbound_media` for image/sticker routes.
The frontend and social adapters should treat it as the source of truth for
media sends:

- `send_strategy=upload_then_send`: upload through the channel bridge, then send
  the platform image message.
- `send_strategy=text_fallback_until_upload_supported`: send
  `text_fallback` immediately and log `fallback_reason`.
- WeChat personal bridges should use the fallback branch until image upload or
  bridge-file sending is verified.
- Feishu adapters should upload first and send by `image_key`.

The companion BaiLongma overlay snippet is
`patches/bailongma/phase-24-social-media-fallback.patch`.

## Phase 30 Writable Config Schema

Hermes runtime now exposes:

- `GET /config/schema`,
- `POST /config/update`.

The schema lets Brain UI render and save whitelisted runtime settings for model
slots, search, media/stickers/image generation, and social performance budgets.
It deliberately excludes host, port, filesystem paths, safe mode, and other
high-risk runtime switches from the first writable UI.

Secret fields are write-only: the frontend receives only `configured: true` or
`configured: false`, and empty secret updates keep the existing value. Unknown
keys and invalid values are rejected before any env file write.

The next BaiLongma overlay should render this schema in the settings panel,
proxy `/config/schema` and `/config/update`, and keep native Hermes logic as the
backend owner.

## Phase 31 Runtime Config UI

The server BaiLongma Brain UI now includes a `运行配置` settings tab. It:

- proxies `GET /config/schema` and `POST /config/update`,
- renders Hermes schema groups dynamically,
- supports text, url, int, bool, select, and secret fields,
- skips empty secret inputs so existing keys stay untouched,
- submits only changed values,
- refreshes schema, overview, and capability state after save.

This makes the settings center schema-driven instead of a collection of
hard-coded one-off forms. Existing model, media, and search pages remain
available while their fields are gradually migrated into the Hermes schema.

## Phase 32 QQ Personal Scan Panel

QQ now has two visible setup paths in Brain UI:

- `QQ 官方机器人`: App ID, Bot Token, Bot Secret, and Webhook Token for the
  official bot route.
- `QQ 个人扫码`: a separate scan-bridge panel for future NapCat or Lagrange
  integration.

The personal scan panel currently exposes planned endpoints and returns
`bridge_missing` because the QQ personal bridge is not installed yet. This keeps
the product boundary honest: the user sees that personal QQ should be QR-based,
but the UI does not pretend QR login is available before the bridge exists.

## Phase 33 QQ Personal NapCat Bridge

The QQ personal scan path now has a real runtime bridge behind the panel:

- BaiLongma imports a `qq-personal-bridge` adapter.
- `GET /social/qq-personal/qr` reads the local NapCat container state and
  surfaces `qr_ready` when NapCat emits a login QR URL.
- `POST /social/qq-personal/start` starts or creates the local NapCat Docker
  container.
- `POST /social/qq-personal/logout` stops the container without deleting QQ
  session data.
- Brain UI renders `qr_ready`, `webui_ready`, `starting`, `stopped`, and
  `bridge_missing`.

The bridge intentionally binds NapCat WebUI and OneBot to `127.0.0.1` only.
WebUI tokens, QR URLs, QQ sessions, cookies, and account ids are treated as
runtime secrets and are not part of the repository overlay.
