#!/usr/bin/env bash
set -euo pipefail

ROOT="${BAILONGMA_ROOT:-/home/hermes/external/BaiLongma}"
NODE_BIN="${NODE_BIN:-/home/hermes/.hermes/node/bin/node}"

if [[ ! -d "$ROOT" ]]; then
  echo "BaiLongma root not found: $ROOT" >&2
  exit 2
fi

cd "$ROOT"

echo "== probe target =="
pwd
echo

echo "== git state =="
git rev-parse --short HEAD 2>/dev/null || true
git status --short 2>/dev/null || true
echo

echo "== candidate files =="
find . -type f \
  \( -iname "*wechat*" -o -iname "*claw*" -o -iname "*message*" -o -iname "*send*" -o -iname "*media*" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  | sort \
  | sed -n '1,160p'
echo

echo "== send/media symbols =="
grep -RInE \
  "sendImage|send_image|sendFile|send_file|sendMedia|send_media|upload.*image|image.*upload|media_id|image_key|messageType.*image|msg_type.*image|MessageType.*Image|ImageMessage|/media/image|downloadMedia|clawbot|wechat" \
  . \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude='*.map' \
  | sed -n '1,240p' || true
echo

echo "== package hints =="
if [[ -r package.json ]]; then
  grep -nE "wechat|ilink|claw|bot|media|file" package.json || true
fi
if [[ -r package-lock.json ]]; then
  grep -nE "wechat|ilink|claw|bot" package-lock.json | sed -n '1,80p' || true
fi
echo

echo "== exported function names in likely social files =="
grep -RInE "export (async )?function|module\.exports|exports\." src/social src 2>/dev/null \
  --exclude-dir=node_modules \
  | grep -Ei "wechat|claw|send|media|message|image" \
  | sed -n '1,160p' || true
echo

echo "== syntax check likely files =="
while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  case "$file" in
    *.js|*.mjs)
      if [[ -x "$NODE_BIN" ]]; then
        "$NODE_BIN" --check "$file" >/dev/null && echo "ok $file" || echo "fail $file"
      else
        node --check "$file" >/dev/null && echo "ok $file" || echo "fail $file"
      fi
      ;;
  esac
done < <(
  find src -type f \
    \( -iname "*wechat*.js" -o -iname "*claw*.js" -o -iname "*send*.js" -o -iname "*media*.js" \) \
    -not -path "*/node_modules/*" \
    | sort
)
echo

echo "== result hint =="
echo "If you see sendImage/sendImageFile/sendFile/uploadAndSendImage above, paste the matched lines back to Codex."
echo "If only downloadMedia appears, current bridge can read inbound images but likely cannot send outbound image files yet."
