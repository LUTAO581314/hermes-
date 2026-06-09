# BaiLongma MOXI Overlay

Technical path source: https://github.com/LUTAO581314/hermes-

This directory records the MOXI changes that should be applied to a BaiLongma
checkout. It is intentionally an overlay, not a full copy of upstream source.

## Current Overlay Scope

- brand the public Brain UI as MOXI while preserving BaiLongma as the upstream
  runtime,
- add social connector settings for Feishu, WeChat, WeCom, and QQ,
- connect social surfaces to the Hermes runtime `/social/turn` and
  `/jobs/event` contract,
- keep voice input, browser TTS, image understanding, prepared stickers, and
  memory governance as explicit runtime capabilities,
- prevent high-risk company or money actions from running without owner
  confirmation.

## Patch Policy

- Never commit real `.env`, API keys, webhook secrets, cookies, QR-code session
  data, group ids, or private chat ids.
- Preserve upstream MIT license notices.
- Keep each patch focused: UI, connector, memory, performance, or deployment.
- Prefer small documented overlays over large source copies.
- Every phase that changes BaiLongma should add a Chinese report under
  `reports/`.

## Patch Files

- [phase-16-capability-matrix-and-qq-settings.patch](phase-16-capability-matrix-and-qq-settings.patch)
  adds a Brain UI capability matrix panel, a secret-safe `/capabilities`
  endpoint that can bridge Hermes backend readiness, and QQ official bot
  settings fields.
- [phase-18-social-turn-progress-bridge.patch](phase-18-social-turn-progress-bridge.patch)
  proxies `/frontend/contract` through BaiLongma and lets `/message` call
  Hermes `/social/turn` before queueing the native BaiLongma agent turn. Slow
  routes emit a natural progress ACK and report `ack_sent` to `/jobs/event`.
- [phase-19-progress-aware-chat-ui.patch](phase-19-progress-aware-chat-ui.patch)
  adds a lightweight Brain UI progress strip that consumes `moxi_progress`
  events, shows route-aware status text, and clears when the final message is
  delivered.
- [phase-20-channel-plane-badges.patch](phase-20-channel-plane-badges.patch)
  adds route-aware and channel-aware badges to Brain UI chat bubbles so personal,
  web, company, runtime, and approval surfaces are visibly separated.
- [phase-21-tool-lifecycle-events.patch](phase-21-tool-lifecycle-events.patch)
  connects the native BaiLongma turn loop and `send_message` delivery path back
  to Hermes `/jobs/event`, reporting `worker_started`, `worker_completed`,
  `worker_failed`, and `final_delivered` while keeping secrets out of Git.
- [phase-22-follow-up-job-merge.patch](phase-22-follow-up-job-merge.patch)
  makes BaiLongma respect Hermes `append_to_active_job` plans at the `/message`
  boundary: follow-up text is persisted as context and acknowledged, but not
  queued as a new interrupting LLM turn.
- [phase-23-company-read-connectors.patch](phase-23-company-read-connectors.patch)
  adds read-only Feishu OpenAPI tools for company identity lookup and Bitable
  record listing, including tool schemas, router triggers, low-risk policy, and
  secret-safe result shaping.
- [phase-24-social-media-fallback.patch](phase-24-social-media-fallback.patch)
  documents the BaiLongma-side media compatibility adapter: read Hermes
  `outbound_media`, upload and send when the channel supports it, or send the
  text fallback and log the reason when WeChat-style image delivery is not
  verified yet.
- [phase-25-wechat-media-plan-send.patch](phase-25-wechat-media-plan-send.patch)
  documents the next BaiLongma-side step for real WeChat image delivery: call
  Hermes `/media/plan-send` after image generation, then either send the local
  image file, upload-and-send, or text-fallback according to the runtime plan.
- [phase-27-frontend-same-origin-routing.patch](phase-27-frontend-same-origin-routing.patch)
  documents the Brain UI browser-side routing fix: use same-origin API paths
  instead of `127.0.0.1:3721`, and configure `/events` as an SSE-friendly Nginx
  reverse-proxy location.
- [phase-28-settings-tab-state-cleanup.patch](phase-28-settings-tab-state-cleanup.patch)
  documents the Brain UI settings-panel state cleanup: one shared tab activation
  path, per-tab refresh behavior, and repaired Chinese labels for the capability
  and QQ settings blocks.
- [phase-29-settings-control-center.patch](phase-29-settings-control-center.patch)
  turns Brain UI settings into a Hermes control center: overview, capability
  matrix, frontend contract, performance budget, memory status, async jobs,
  social channels, model, media, voice, search, security, appearance, and
  update domains, plus read-only `/performance` and `/jobs` Hermes proxies.
- [phase-30-hermes-config-schema.patch](phase-30-hermes-config-schema.patch)
  documents the next BaiLongma-side writable-settings overlay: proxy Hermes
  `/config/schema` and `/config/update`, render schema groups dynamically, and
  keep secret fields write-only.
- [phase-31-runtime-config-ui.patch](phase-31-runtime-config-ui.patch)
  records the deployed BaiLongma runtime-config settings UI: schema proxy
  endpoints, `运行配置` tab, dynamic field rendering, changed-field save, and
  schema form styling.
- [phase-32-qq-personal-scan-panel.patch](phase-32-qq-personal-scan-panel.patch)
  splits QQ into official bot credentials and a planned personal scan bridge
  panel. The personal path reports `bridge_missing` until NapCat or Lagrange is
  installed.
- [phase-33-qq-personal-napcat-bridge.patch](phase-33-qq-personal-napcat-bridge.patch)
  turns the QQ personal scan path into a real NapCat Docker bridge: BaiLongma
  can start/stop the local container, read status, surface QR-ready login state,
  and keep session material outside Git.

Future patch files should be named by phase and purpose:

```text
phase-33-<purpose>.patch
```

The server checkout may still contain local runtime-specific changes. Patch
files in this directory are the reviewed MOXI overlay boundary.
