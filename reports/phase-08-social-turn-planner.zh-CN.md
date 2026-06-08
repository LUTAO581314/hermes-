# Phase 08 中文报告：社交连接器首动作规划器

## 1. 本阶段目标

上一阶段已经有 `/route`、`/context` 和 `/jobs`，但真实微信、飞书、网页聊天连接器仍然需要自己把这些接口串起来。本阶段目标是提供一个连接器可直接调用的统一入口，让任何社交渠道都能先判断：

- 要不要直接快答；
- 要不要先发自然 ACK；
- ACK 文案是什么；
- 该加载多少上下文；
- 是否需要创建慢任务；
- 慢任务完成后该如何继续投递最终结果。

## 2. 已完成内容

新增 `hermes_runtime/social_turn.py`，实现社交消息首动作规划。

新增运行时接口：

```text
POST /social/turn
```

请求示例：

```json
{
  "channel": "wechat",
  "target_id": "user-or-room-id",
  "message": "generate image avatar"
}
```

返回内容包括：

- `first_action`：`direct_reply` 或 `quick_ack`；
- `ack.should_send`：是否应该先发 ACK；
- `ack.text`：自然 ACK 文案；
- `route`：路由策略；
- `context_budget`：上下文瘦身预算；
- `job`：慢任务元数据；
- `message_preview_chars`：输入长度预览。

返回 payload 不包含消息正文，不保存真实聊天内容。

## 3. 当前 ACK 策略

已内置的自然 ACK：

- 读图：`我看一下这张图，等我一下哦～`
- 生图：`等我拍一下，马上给你～`
- 搜索：`我查一下，别急～`
- 舆情：`我去看看最新动向，等我一下～`
- 飞书公司任务：`我先看一下飞书里的上下文，马上回你～`
- 记忆整理：`我先整理一下记忆线索，等我一下～`
- 高风险任务：`这件事要认真确认一下，我先停在确认边界哦。`

普通短消息例如 `ok` 会走 `direct_reply`，不会创建 job，也不会乱发 ACK。

## 4. 对微信和飞书的意义

后续真实连接器可以简化成：

1. 收到微信/飞书消息。
2. 调用 `/social/turn`。
3. 如果 `first_action=quick_ack`，立即把 `ack.text` 发回原渠道。
4. 如果返回 `job`，按 `job_id` 启动真实 worker。
5. ACK 发送成功后把 job 推进到 `acknowledged`。
6. worker 完成后推到 `completed`，再补发最终结果。

这样能避免 20 秒静默，也能避免用户追问时打断上一轮图片、搜索或飞书任务。

## 5. 验收结果

- `/social/turn` 已实现。
- 慢任务消息会返回自然 ACK 并创建 job。
- 普通短消息走直接回复路径，不创建 job。
- 单元测试已覆盖两条路径。
- 测试验证 payload 不包含输入正文中的私密片段。
- 文档和公开技术路径已更新。

Technical path source: https://github.com/LUTAO581314/hermes-
