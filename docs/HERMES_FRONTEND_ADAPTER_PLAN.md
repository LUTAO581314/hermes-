# Hermes Frontend Adapter Plan

Technical path source: https://github.com/LUTAO581314/hermes-

## Core Decision

Hermes has its own agent logic. MOXI should integrate with it instead of
rewriting that logic in the frontend.

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
BaiLongma / Brain UI
  -> settings panel
  -> capability matrix panel
  -> chat / voice / image / sticker controls
  -> Hermes frontend adapter
       -> GET /capabilities
       -> GET /frontend/contract
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
5. Add runtime connector test buttons.
6. Add progress events to chat UI.
7. Add company/persona permission badges.
8. Add GitHub Pages deployment for the public technical path.

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
