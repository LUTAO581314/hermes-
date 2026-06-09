# Phase 25 微信图片发送计划接口报告

## 背景

主人实测“发张图片测试”后，微信侧表现为：

- 沫汐先发出自然 ACK：“我看一下这张图，等我一下哦～”
- 后续回复只发出图片路径：`/media/image/...png`
- 微信桥接器明确提示“目前只能发文字，不能把图片文件本身直发出去”

这说明 Phase 24 的兼容兜底已经生效，但还缺少一个让微信桥接器执行真实图片发送的稳定接口。

## 本阶段目标

新增连接器可调用的媒体投递计划接口，让微信、飞书、QQ、网页桥接器在拿到图片结果后，可以问 runtime：

- 当前应该直接发本地图片文件吗？
- 当前应该先上传到平台再发送吗？
- 当前只能发文字兜底吗？
- 发送完成后应该回报哪个 lifecycle event？

## 已完成

- 新增 `hermes_runtime/media_delivery.py`
  - `plan_media_delivery()`
  - `MediaDeliveryPlan`
- 新增 HTTP 接口：
  - `POST /media/plan-send`
- 更新 `HermesConnectorClient`
  - 新增 `plan_media_send()`
- 更新 `/frontend/contract`
  - 新增 `media_plan_send` endpoint 描述
- 新增测试：
  - 支持本地图片发送时返回 `send_image_file`
  - 不支持图片发送时返回 `send_text_fallback`
  - connector client 可以调用媒体计划接口

## 新接口契约

请求示例：

```json
{
  "channel": "wechat",
  "target_id": "user-1",
  "outbound_media": {
    "kind": "sticker",
    "channel": "wechat",
    "text_fallback": "测试图生成好了，但当前桥接器只能发文字。"
  },
  "source_ref": "/media/image/image_2026-06-09T00-30-20_1.png",
  "text_fallback": "测试图生成好了，但当前桥接器只能发文字。",
  "bridge_capabilities": {
    "send_text": true,
    "send_image_file": true,
    "upload_then_send": false
  }
}
```

可能返回：

- `action=send_image_file`：桥接器应该按本地图片/文件发送。
- `action=upload_then_send`：桥接器应该先上传到平台，再按平台 token 发送。
- `action=send_text_fallback`：桥接器还不能发图，立即发文字兜底。
- `action=reject_unsafe_request`：桥接器既不能发图也不能兜底，停止并报错。

## 安全边界

- 接口不接收图片字节。
- 接口不保存图片。
- `source_ref` 只作为连接器本地引用，不接受 `http://`、`https://`、`file://`。
- 日志只返回 `source_ref_present`，不记录完整敏感内容。
- `media_id`、`image_key`、临时文件路径、平台 token 和 API key 不进入 Git。

## 对微信桥接器的要求

下一步白龙马/ClawBot 发送图片时应改为：

```text
生成图片 -> 得到 source_ref
  -> POST /media/plan-send
  -> action=send_image_file 时调用桥接器图片发送
  -> action=send_text_fallback 时发送 text_fallback
  -> POST /jobs/event 回报 final_delivered 或 failure_delivered
```

这样就不会再把图片路径当作最终文本结果发给用户。

## 验证结果

- `python -m unittest discover -s tests`: 26 tests OK
- `python -m compileall hermes_runtime tests`: 通过

## 下一步

- 在服务器 BaiLongma/ClawBot 代码里实际接入 `/media/plan-send`。
- 找到当前微信桥接器真实可用的图片发送函数。
- 如果支持本地文件发送，启用 `send_image_file`。
- 如果不支持，保留文字兜底，但不要再把裸路径当成最终回复。
