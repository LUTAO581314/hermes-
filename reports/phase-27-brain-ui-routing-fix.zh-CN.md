# Phase 27 Brain UI 前端路由报错报告

## 现象

浏览器控制台报错：

```text
127.0.0.1:3721/settings/voice Failed to load resource: net::ERR_CONNECTION_REFUSED
brain-ui.html:1 Uncaught (in promise) Error: A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received
events:1 Failed to load resource: net::ERR_HTTP2_PROTOCOL_ERROR
```

## 判断

核心问题是浏览器端请求了 `127.0.0.1:3721`。

当主人在本机浏览器打开 `https://bairui.chat/brain-ui.html` 时，浏览器里的 `127.0.0.1` 指向主人的电脑，不是 VPS。所以 `/settings/voice` 会连接失败。

`events:1 ERR_HTTP2_PROTOCOL_ERROR` 更像 SSE `/events` 反代没有按长连接配置，尤其是 HTTP/2、proxy buffering 或超时配置不适合 EventSource。

浏览器扩展报错：

```text
A listener indicated an asynchronous response by returning true...
```

通常来自浏览器扩展或页面消息监听器，不是当前最关键故障。先修 API base 和 `/events`。

## 修复原则

- 浏览器端 API base 必须使用同源相对路径：`/settings/voice`、`/events`。
- 不允许浏览器端写死 `http://127.0.0.1:3721`。
- 服务器内部反代仍然可以把公网 `/settings/voice` 转到 `127.0.0.1:3721/settings/voice`。
- SSE `/events` 需要 Nginx 关闭 buffering，并保持长连接。

## 已新增

- `scripts/probe-bailongma-frontend-routing.sh`
- `patches/bailongma/phase-27-frontend-same-origin-routing.patch`

## 服务器实修结果

已在服务器 `/home/hermes/external/BaiLongma` 实际修复：

- `src/ui/brain-ui/app.js`
  - `import { API }` 改为 `import { API, apiUrl }`。
  - 两处 `fetch("http://127.0.0.1:3721/settings/voice")` 改为 `fetch(apiUrl('/settings/voice'))`。
- `src/ui/brain-ui/api-client.js`
  - 浏览器端默认 API base 改为空字符串，即同源路径。
  - 禁止把 `127.0.0.1` / `localhost` 作为公网 Brain UI 的浏览器 API base。
- `/etc/nginx/conf.d/bairui-chat.conf`
  - 在 HTTPS server block 增加 `location = /events`。
  - `/events` 关闭 `proxy_buffering`，设置 `proxy_http_version 1.1` 和 `X-Accel-Buffering no`。

服务器备份目录：

```text
/home/hermes/backups/bailongma-phase27-frontend-routing-20260609010607
```

验证结果：

- `node --check src/ui/brain-ui/app.js`: 通过。
- `node --check src/ui/brain-ui/api-client.js`: 通过。
- `nginx -t`: 通过。
- `systemctl restart bailongma`: 完成，服务 active。
- `systemctl reload nginx`: 完成，服务 active。
- `https://bairui.chat/settings/voice`: 返回 HTTP 200。
- 公网 `app.js` 不再包含 `127.0.0.1:3721/settings/voice`。
- 公网 `app.js` 包含 `apiUrl('/settings/voice')`。
- `https://bairui.chat/events` 用 HTTP/1.1 可收到 SSE `connected` 事件。

## 服务器探测命令

```bash
cd /home/hermes/external/BaiLongma
bash /home/hermes/hermes-/scripts/probe-bailongma-frontend-routing.sh
```

如果脚本路径不存在，可以先在服务器拉取/更新本仓库，或把脚本复制到临时文件运行。

## 预期修复方向

Brain UI 前端：

```js
const API = ''
fetch(`${API}/settings/voice`)
new EventSource(`${API}/events`)
```

Nginx `/events`：

```nginx
location /events {
  proxy_pass http://127.0.0.1:3721/events;
  proxy_http_version 1.1;
  proxy_set_header Connection '';
  proxy_buffering off;
  proxy_cache off;
  proxy_read_timeout 1h;
  add_header X-Accel-Buffering no;
}
```

## 下一步

主人刷新浏览器并清缓存后复测 Brain UI。若仍看到 `127.0.0.1:3721`，优先排查浏览器缓存或旧 service worker；若仍看到 `/events` HTTP2 报错，再检查浏览器是否复用了旧连接。
