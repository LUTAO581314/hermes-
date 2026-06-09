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

Future patch files should be named by phase and purpose:

```text
phase-25-feishu-readiness-ui.patch
```

The server checkout may still contain local runtime-specific changes. Patch
files in this directory are the reviewed MOXI overlay boundary.
