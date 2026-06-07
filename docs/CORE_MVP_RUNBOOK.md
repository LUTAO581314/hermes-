# Core Hermes and BaiLongma MVP Runbook

## 1. Locked Scope

Current core scope:

- Hermes orchestration.
- BaiLongma Brain UI and Chinese interaction layer.
- GPT-5.5 through the configured custom OpenAI-compatible gateway.
- TrendRadar as the external search and trend runtime.
- Governed, human-like memory.
- Tool calling.
- Image understanding and OCR.
- Voice input through local Whisper.

Frozen for this phase:

- Video understanding.
- AI video generation.
- Voice cloning.
- Autonomous trading.
- Feishu company management.

The goal is not to enable every possible feature. The goal is to prove a clean loop:

```text
owner message
  -> BaiLongma or Hermes
  -> governed memory context
  -> selected tools
  -> model response
  -> useful result
  -> Obsidian inbox or phase report
  -> memory dream consolidation
  -> reviewed cleanup
```

## 2. Current Runtime Map

| Component | Current Role | Status |
| --- | --- | --- |
| Hermes | Backend orchestrator, MCP and tool runner | Installed on the VPS |
| BaiLongma | Brain UI, Chinese interaction, WeChat companion bridge | Running behind protected `bairui.chat` |
| GPT-5.5 gateway | Main model and vision-capable model path | Configured in BaiLongma |
| TrendRadar | External search, RSS, trend and news runtime | Enabled through Hermes MCP |
| Local Whisper | Transitional ASR for voice input | Installed in a dedicated venv |
| Image tool | Screenshot/image/OCR analysis | Exposed as `analyze_image` |
| Video tool | Not part of the current phase | Hidden from routing/schema |
| Obsidian | Durable source of truth | Governed write-back workflow documented |

## 3. What It Can Do Now

The current core can support:

- Chinese natural chat through BaiLongma Brain UI.
- Owner personal chat through the restored WeChat ClawBot state, if the saved login remains valid.
- Model calls through the custom GPT-5.5 gateway.
- Tool routing from Hermes and BaiLongma.
- Trend and search intelligence through Hermes + TrendRadar.
- Image recognition and OCR through `analyze_image`.
- Voice input transcription through local Whisper.
- Short-term BaiLongma working memory with a governed promotion path.

Memory rule:

```text
BaiLongma memory = working memory
Obsidian = durable memory
reports = phase facts and delivery record
indexes = rebuildable lookup helpers
```

## 4. What It Must Not Do Yet

Do not treat these as ready:

- Real video understanding.
- Voice output or TTS without a configured approved provider key.
- Voice cloning.
- Feishu company operations.
- Broker or trading execution.
- Unreviewed permanent memory writes.
- WeChat-based money, HR, legal, company approval, or trading actions.

## 5. Tool Calling Acceptance Gate

Each tool capability must pass three checks before it is treated as usable:

| Capability | Required Check | Pass Criteria |
| --- | --- | --- |
| Hermes MCP | `hermes mcp list` | TrendRadar appears enabled |
| Brain UI | `/health` and `/status` | Service is running and memory count is visible |
| Model gateway | BaiLongma settings/status | Provider is `custom`, model is the intended model |
| Image | `analyze_image` smoke test | A test image can be described or OCR'd correctly |
| Voice | `/voice/cloud` transcript smoke | Local Whisper returns `asr_status`, `config_ok`, and a real transcript through BaiLongma |
| Memory | pre/post memory count | Setup tests do not create noisy durable memories |
| Search | TrendRadar MCP call or report | Output contains sources or clear uncertainty |
| Runtime graph | `/memory/graph?limit=80` | Returns governed graph with working/review/durable/noise counts |

## 6. Server Verification Commands

Run these on the VPS. They do not print secrets.

```bash
systemctl status bailongma --no-pager -l
systemctl status trendradar-mcp --no-pager -l
systemctl status nginx --no-pager -l
ss -ltnp | grep -E ':(3333|3721|3723|80|443)\b' || true
```

Protected BaiLongma checks:

```bash
PASS=$(awk -F': ' '/^password:/{print $2}' /root/bairui-chat-basic-auth.txt)
curl -sS https://bairui.chat/health
curl -sS -u "owner:$PASS" -H 'Origin: https://bairui.chat' https://bairui.chat/status
curl -sS -u "owner:$PASS" -H 'Origin: https://bairui.chat' https://bairui.chat/settings/voice | python3 -m json.tool
curl -sS -u "owner:$PASS" -H 'Origin: https://bairui.chat' 'https://bairui.chat/memory/graph?limit=80' | python3 -m json.tool
unset PASS
```

Hermes MCP check:

```bash
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.local/bin:/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  hermes mcp list
```

Image routing smoke check:

```bash
cd /home/hermes/external/BaiLongma
/home/hermes/.hermes/node/bin/node --input-type=module - <<'JS'
import { selectTools } from './src/memory/tool-router.js'
const tools = selectTools({ messageBody: '帮我识别图片里有什么', mmCaps: [] })
console.log(JSON.stringify({
  hasAnalyzeImage: tools.includes('analyze_image'),
  hasAnalyzeVideo: tools.includes('analyze_video')
}, null, 2))
JS
```

Expected result:

```json
{
  "hasAnalyzeImage": true,
  "hasAnalyzeVideo": false
}
```

Voice transcript smoke check:

```bash
cd /home/hermes/external/BaiLongma
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  /home/hermes/.hermes/node/bin/node scripts/smoke-voice-cloud.mjs
```

Expected result:

```text
transcript: Hello world this is a final local voice test.
```

If `npm ci` or any Electron-related install step has just run in the BaiLongma
repository, rebuild the Node native SQLite module before restarting the backend:

```bash
cd /home/hermes/external/BaiLongma
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  npm rebuild better-sqlite3 --build-from-source
systemctl restart bailongma
```

## 7. Memory Hygiene During Tests

Before a smoke test:

- Record the current BaiLongma memory count.
- Prefix pure test messages with a clear test label.
- Avoid personal facts, preferences, credentials, or private screenshots.
- Use `skip_recognition` when the turn is only a status check, greeting, or setup test.

After a smoke test:

- Check the memory count again.
- If memory count increased, run a memory dream report before deciding what to change.
- Delete, downgrade, merge, or archive setup noise only after review.
- Put useful setup facts into the phase report, not into permanent memory.

Test output such as `API OK`, `MOXI CORE OK`, `permission fixed`, QR login state, and health-check status should not become durable memory.

Memory dream report command:

```bash
curl -fsS -u "owner:$BAILONGMA_PASS" -H "Origin: https://bairui.chat" \
  "https://bairui.chat/memory/graph?limit=120" > data/memory-graph.json
python scripts/memory-dream.py \
  --input data/memory-graph.json \
  --output data/memory-dream-report.md \
  --source "https://bairui.chat/memory/graph?limit=120"
```

`data/memory-dream-report.md` is ignored by Git by default because it may contain private memory content. Commit only cleaned phase summaries and general governance rules.

## 8. Owner-Facing Capability Test Script

Use this checklist when testing through the UI:

```text
1. Chat: ask one normal Chinese question.
2. Tool: ask for one current trend or search-style result through Hermes/TrendRadar.
3. Image: upload or point to one harmless image and ask for OCR/description.
4. Voice: send one short voice input and confirm text transcription.
5. Memory: ask what it remembers only after the memory count is checked.
6. Dream: generate a memory dream report if the graph looks noisy.
7. Cleanup: remove, merge, or downgrade setup/test memory only after review.
```

Do not use real credentials, financial account screenshots, private contracts, or sensitive customer material in the first test batch.

## 9. Completion Gate

The core phase is considered stable only when:

- Services are active.
- Brain UI is reachable through the protected domain.
- Hermes MCP shows TrendRadar enabled.
- Image route exposes `analyze_image` and hides video.
- Voice route returns a real transcript through local Whisper.
- Memory count does not jump because of smoke tests, or a memory dream report identifies and contains the noise.
- Brain UI memory graph shows runtime memory as candidates, with Obsidian marked as source of truth.
- Obsidian write-back workflow exists.
- Chinese phase report is updated.
- Git secret scan finds no committed key, password, token, or QR material.
