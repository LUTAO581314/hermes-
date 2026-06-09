# Phase 24 社交媒体图片兼容报告

## 本阶段目标

解决微信等聊天软件“不能稳定发图片/表情包”时的兼容问题。当前目标不是把所有平台图片上传 API 一次性打通，而是先统一出站媒体协议，确保：

- 能发图的平台按平台规则上传后发送。
- 暂时不能发图的平台不静默失败。
- 微信个人桥接器如果还没验证图片发送，就先发送文本兜底，并记录原因。

## 已完成

- `hermes_runtime/sticker_bridge.py`
  - 新增 `OutboundMediaPayload`。
  - 新增 `build_media_envelope()`。
  - 标准化 `send_strategy`：
    - `upload_then_send`
    - `send_platform_sticker_id`
    - `text_fallback_until_upload_supported`
    - `send_text_fallback`
- `hermes_runtime/social_turn.py`
  - 图片/表情路线返回 `outbound_media`。
  - 微信默认走安全兼容：未确认上传能力时返回文本兜底策略。
- `hermes_runtime/routing.py`
  - 中文“发图 / 发图片 / 发张图”归入图片生成/媒体发送路线。
- `hermes_runtime/frontend_contract.py`
  - `/frontend/contract` 声明 `outbound_media` response key。
  - 写明微信、飞书适配规则。
- 文档更新：
  - `docs/STICKER_BRIDGE.md`
  - `docs/WECHAT_COMPANION.md`

## 兼容策略

微信当前最安全的规则：

```text
如果桥接器支持图片上传/文件发送：
  generate or resolve image -> upload through bridge -> send image
否则：
  send outbound_media.text_fallback
  log outbound_media.fallback_reason
```

这可以避免两种坏体验：

- 沫汐以为自己发了图片，但用户没收到。
- 图片发送失败后整轮回复消失。

## 安全边界

- 仓库不提交图片文件。
- 仓库不提交生成图片。
- 仓库不提交 `media_id`、`image_key`、临时文件路径或 provider secret。
- 生图 provider 仍然默认 review-gated。
- 公司、高风险、审批类流程不通过微信表情入口确认。

## 验证点

- 微信图片/表情路线会返回 `outbound_media.channel=wechat`。
- 未确认微信上传能力时，`send_strategy=text_fallback_until_upload_supported`。
- 飞书媒体 envelope 可以进入 `upload_then_send`，要求 `image_key`。
- `/frontend/contract` 暴露 `outbound_media` 规则。

## 下一步

- 在服务器 BaiLongma 微信发送适配器里读取 `outbound_media`。
- 如果 ClawBot/WeChat bridge 支持发本地文件，接入 `upload_then_send`。
- 如果不支持，先发送 `text_fallback`。
- 记录 `fallback_reason` 到日志，方便后续定位真实图片发送能力。
