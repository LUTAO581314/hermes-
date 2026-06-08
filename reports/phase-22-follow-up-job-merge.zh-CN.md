# Phase 22 Follow-Up 合并报告

## 本阶段目标

解决用户在慢任务运行中继续补充一句话时，BaiLongma 把补充消息当成新一轮
LLM turn，导致当前图片、搜索、飞书或公司任务被误打断、重复排队的问题。

## 已完成

- 服务器 BaiLongma `/message` 已识别 Hermes
  `first_action=append_to_active_job`。
- follow-up 会继续发送自然 ACK，例如“刚才那件事没丢，我把这句一起算进去”。
- follow-up 会写入 conversations，成为当前任务可见的上下文。
- follow-up 会发出 `moxi_progress`，状态为 `append_to_active_job`。
- follow-up HTTP 响应新增：
  - `queued:false`
  - `appended_to_active_job:true`
- follow-up 不再进入 `pushMessage`，因此不会触发 `interruptCallback`，不会抢跑一个新的
  LLM turn。
- 正常首条慢任务仍然照旧进入队列，并使用 `lockUntilProcessed` 保持处理锁。

## 验证结果

服务器服务状态：

- `bailongma.service`: active
- `hermes-runtime.service`: active

语法检查：

- `node --check src/api.js`: 通过

真实链路 smoke：

1. 第一次向 BaiLongma `/message` 发送“生成一张可爱表情包”。
2. 返回：
   - `queued:true`
   - `appended_to_active_job:false`
   - `first_action:quick_ack`
   - route: `image_generate`
   - 创建 Hermes job。
3. 马上发送“要粉色一点，更软一点”。
4. 返回：
   - `queued:false`
   - `appended_to_active_job:true`
   - `first_action:append_to_active_job`
   - 复用同一个 Hermes job id。
5. `/jobs` 只出现一个对应 slow job，没有创建第二个重复任务。

## 当前意义

Phase 21 让 Hermes 知道 BaiLongma 原生任务已经开始、完成、送达。Phase 22 让用户
在任务运行中继续补充上下文时，不会把系统打乱。

这对真实微信、QQ、飞书体验很关键：用户通常会连续说几句，而不是等 AI 完全处理完。
现在系统可以把第二句当成“补充上下文”，而不是“打断并重新开始”。

## 风险与边界

- 当前 follow-up 只做“记录上下文 + 不打断”。如何让正在运行的 worker 立刻读取新补充，
  还需要后续进一步做 active job context buffer。
- 明确取消语义仍由 Hermes planner 识别；后续可以把取消请求接到
  `cancel_requested` 和 UI 恢复入口。
- 该 patch 仍是 overlay，不复制 BaiLongma 全量源码，不包含服务器密钥、真实群 ID、
  二维码会话或 API key。

## 下一步

- Phase 23：接 Feishu 只读公司数据，优先通讯录身份、群项目映射、云文档和多维表格。
- 给 Brain UI 增加 active job follow-up 的更明确视觉提示。
- 后续设计 active job context buffer，让正在运行的 worker 可以更及时吸收补充消息。
