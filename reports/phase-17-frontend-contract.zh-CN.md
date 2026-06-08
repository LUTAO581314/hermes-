# Phase 17 - 前端深度适配契约

技术路径来源: https://github.com/LUTAO581314/hermes-

## 本阶段目标

白龙马前端继续作为主 UI，但不应该硬编码 Hermes 的内部逻辑。本阶段把前端需要知道的状态、接口、权限边界和慢任务进度，整理成一个机器可读的 runtime contract，让白龙马前端可以深度适配 Hermes 后端，同时保持上游逻辑边界清晰。

## 已完成

- 新增 `GET /frontend/contract`。
- 契约包含白龙马前端要调用的核心接口：
  - `/capabilities`
  - `/performance`
  - `/social/turn`
  - `/jobs/event`
  - `/latency/turn`
- 契约包含前端状态映射：
  - `direct_reply`
  - `quick_ack`
  - `append_to_active_job`
  - `approval_required`
- 契约包含 route 到 UI 的映射：
  - 日常聊天
  - 快速回答
  - 图片识别
  - 图片生成
  - 搜索
  - 舆情
  - 飞书公司任务
  - 记忆整理
  - 高风险确认
- 契约包含 channel plane：
  - 微信、QQ、网页聊天属于个人陪伴面。
  - 飞书属于公司管理面。
  - 公司写入、资金、法律、HR、审批等动作默认必须经过主人确认。

## 关键价值

白龙马前端后续不用猜“现在该不该显示思考中、该不该发 ACK、这个任务是不是公司权限”，而是直接读取 `/frontend/contract`。这样 Hermes 保持自己的 Agent 逻辑，MOXI 只负责前端适配、通道权限、状态可视化和可复制技术路径。

## 安全边界

`/frontend/contract` 不返回 API key、密码、原始消息、媒体字节、截图、平台用户 ID。前端和连接器只保存任务状态、route 元数据、预览长度和结果指针。

## 下一步

- 在服务器上启动或配置 Hermes/MOXI runtime，使白龙马的 `HERMES_RUNTIME_BASE_URL` 指向真实可用的 8787 runtime。
- 在白龙马聊天前端接入 `/frontend/contract` 和 `/social/turn`。
- 慢任务先显示自然 ACK，例如“我看一下这张图，等我一下哦～”。
- 任务运行期间用 `/jobs/event` 更新“看图、搜索、生成、读飞书”等进度。
- 给微信/QQ/网页个人面和飞书公司面加清晰 badge，高风险动作显示主人确认卡。
