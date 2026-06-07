# WeChat Companion Channel

## 1. Decision

WeChat should be a personal companion and lightweight reminder channel, not the
primary company-management or high-risk execution channel.

The current implementation uses BaiLongma's WeChat ClawBot bridge for the
personal companion plane. Official channels remain the preferred production
route for lower platform risk.

- Official channels are preferred.
- The personal-account bridge is allowed only for the owner-controlled
  companion plane.
- Sensitive commands stay blocked in WeChat.
- Proactive chat is disabled by default and must be rate-limited when enabled.
- Secrets stay in the server-side `.env` file and never enter Git.

## 2. Recommended Channel Order

Use the lowest-risk official route first:

| Order | Channel | Use Case | Status |
| --- | --- | --- | --- |
| 1 | WeChat Official Account | Owner chat, quick capture, lightweight replies | Preferred first WeChat path |
| 2 | WeCom customer service | Customer-style service conversations and company-owned account flows | Good when WeCom is acceptable |
| 3 | Mini Program or Official Account combination | Richer UI, forms, and structured personal tools | Later |
| 4 | Personal-account bridge | Private-account style chat | In use for owner companion, not company control |

## 3. Configuration

Runtime flags:

```env
HERMES_WECHAT_MODE=disabled
HERMES_WECHAT_CHANNEL=official_account
HERMES_WECHAT_PERSONA_MODE=companion
HERMES_WECHAT_PROACTIVE_CHAT=false
HERMES_WECHAT_MAX_DAILY_PROACTIVE_MESSAGES=3
HERMES_WECHAT_PERSONAL_BRIDGE_ENABLED=false
```

Official Account placeholders:

```env
HERMES_WECHAT_OFFICIAL_APP_ID=
HERMES_WECHAT_OFFICIAL_APP_SECRET=
HERMES_WECHAT_OFFICIAL_TOKEN=
HERMES_WECHAT_OFFICIAL_AES_KEY=
```

WeCom placeholders:

```env
HERMES_WECOM_CORP_ID=
HERMES_WECOM_AGENT_ID=
HERMES_WECOM_SECRET=
HERMES_WECOM_CUSTOMER_SERVICE_TOKEN=
```

The `/health` endpoint may report whether these values are configured, but it
must never expose the actual values.

## 4. Human-Like Chat Behavior

"Human-like" means the assistant should feel natural and present while staying
honest about being an AI assistant.

Allowed behavior:

- Warm Chinese replies with the owner's preferred style.
- Context-aware follow-ups from recent conversation and governed memory.
- Short proactive check-ins when enabled by the owner.
- Natural pacing, such as avoiding multiple rapid-fire messages for one thought.
- Cute prepared stickers when the sticker bridge is enabled and the channel can upload/send media.
- Memory-aware personalization after facts pass the memory intake gate.
- Summaries, reminders, quick capture, and personal planning.

Not allowed:

- Pretending to be a real human.
- Hiding that automation is involved when identity matters.
- Spamming or mass messaging.
- Downloading copyrighted sticker packs into Git or sending unreviewed generated images.
- Using WeChat for weakly authenticated money, HR, legal, or account actions.
- Bypassing platform login, access, or anti-automation restrictions.

## 5. Proactive Chat Rules

Proactive WeChat messages are useful only when they remain rare and relevant.

Default:

```text
HERMES_WECHAT_PROACTIVE_CHAT=false
```

Before enabling proactive chat:

- The owner must approve the schedule.
- Daily proactive messages must have a hard maximum.
- Each message must have a reason: reminder, health check, follow-up, or owner
  preference.
- The system must keep an audit log.
- The owner must be able to mute the channel quickly.

## 6. Memory Boundary

WeChat messages should enter memory through the same governed flow as other
channels.

Flow:

```text
WeChat message
  -> temporary conversation context
  -> memory candidate extraction
  -> Obsidian inbox or review note
  -> owner correction or approval
  -> durable Obsidian note
  -> optional search/vector index
```

Do not store every message as permanent memory. Durable memory should be
relationship-rich and source-backed:

- owner preferences,
- recurring goals,
- important people,
- projects,
- decisions,
- reminders,
- risks,
- useful reflections.

Current BaiLongma rule:

- Voice or text chat may influence the current conversation.
- Only stable preferences, decisions, recurring patterns, and owner-approved
  facts become durable memory.
- Setup tests, greetings, affection phrases, and one-off noise should use
  `skip_recognition` or be cleaned during phase closeout.
- Useful WeChat captures should first land in Obsidian `00-Inbox/needs-review`.

## 7. Command Boundary

Allowed by default in WeChat:

- Personal chat.
- Reviewed companion stickers and lightweight media expression.
- Personal reminders.
- Idea capture.
- Reading safe summaries.
- Requesting a draft.

Requires stronger channel or owner confirmation:

- Company task changes.
- Employee instructions.
- External commitments.
- Contract, legal, HR, or finance actions.
- Server configuration changes.
- Any trading or broker action.

Company operations should route to Feishu or a protected admin flow.

## 8. Feishu CLI and MCP Position

Feishu Channel SDK and app callbacks should be the entry layer for Feishu chat
and events.

Feishu CLI and MCP tools should be a controlled tool layer for actions such as:

- reading tables, docs, tasks, calendars, and approvals,
- creating drafts,
- updating approved records,
- running smoke tests and diagnostics.

They should not replace the Feishu app callback entry, and they should not be
exposed directly to WeChat without the channel policy router and approval gate.

## 9. First Real WeChat MVP

The next actual WeChat implementation should prove only one safe slice:

1. Receive one owner message through an official channel.
2. Verify request signature or token.
3. Route it to Hermes as a personal-plane message.
4. Generate a short companion reply.
5. Return the reply through the same official channel.
6. Log the event without storing secrets.
7. Write only a useful memory candidate to Obsidian inbox.

Exit criteria:

- No personal-account bridge is enabled.
- No sensitive commands are executable from WeChat.
- `/health` shows the channel and configured-secret state.
- A Chinese phase report records the result and remaining risks.

## 9.1 Current ClawBot Runtime State

Current verified state:

- BaiLongma logs show ClawBot restored saved credentials.
- One context token was restored.
- This means the previous QR scan likely succeeded.
- The channel is suitable for personal companion chat and quick capture.
- Inbound WeChat image items now have a server-side read-image path. ClawBot
  downloads image media through `wechat-ilink-client`, saves at most four
  images under the BaiLongma sandbox upload folder, and sends those saved paths
  into the same `analyze_image` tool used by Brain UI.
- This read-image path uses the current GPT-5.5 vision-capable gateway. MiniMax
  is not required for image understanding.

Boundaries:

- Do not use WeChat for company approvals, money, HR, legal, or trading.
- Do not send mass messages.
- Do not enable proactive chat without owner-approved schedule and daily cap.
- Do not store raw WeChat content as durable memory without intake review.
- Do not treat WeChat voice messages as completed voice chat yet. Voice needs a
  separate ASR intake path after image intake is confirmed.
- Live WeChat image delivery still requires an owner retest with a harmless
  image. Syntax, service health, and ClawBot startup are verified; live CDN
  download depends on the current WeChat session and platform response.

Current core phase uses WeChat as a personal surface only. Feishu remains the
planned company-management surface.

## 9.2 Sticker Bridge Position

WeChat sticker sending should use the shared Hermes sticker bridge rather than
hard-coded assets in the WeChat adapter.

Flow:

```text
intent
  -> sticker metadata or generated candidate
  -> owner/channel policy review when needed
  -> runtime upload through the active WeChat bridge or official media API
  -> send image/media id
  -> text fallback if upload fails
```

Rules:

- No sticker image files are committed to Git.
- No generated images are committed to Git.
- No WeChat media id, QR state, session token, or bridge credential is committed.
- AI-generated MOXI stickers must be original, review-gated, and blocked from imitating existing anime IP or real people.
- Company, finance, HR, legal, and approval flows should not use WeChat sticker reactions as action confirmation.

## 10. Source Notes

Primary references:

- Feishu/Lark agent integration capabilities:
  <https://open.feishu.cn/document/mcp_open_tools/overview-of-lark-agent-integration-capabilities>
- WeChat Official Account message receiving:
  <https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Receiving_standard_messages.html>
- WeChat Official Account customer-service messages:
  <https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Service_Center_messages.html>
- WeCom customer service documentation:
  <https://developer.work.weixin.qq.com/document/path/94648>
