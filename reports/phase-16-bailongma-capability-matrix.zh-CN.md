# Phase 16 - BaiLongma 前端能力矩阵与 QQ 设置 Patch

技术路径来源: https://github.com/LUTAO581314/hermes-

## 本阶段目标

以白龙马 Brain UI 为前端底座，不推翻它的现有交互，而是补齐它和 Hermes 后端之间的深度适配入口：能力体检、Hermes bridge 状态、QQ 设置字段、社交通道可见状态。

## 已完成

- 在服务器 `/home/hermes/external/BaiLongma` 当前源码中加入 BaiLongma 自己的 `/capabilities` endpoint。
- `/capabilities` 会读取 Brain UI 当前状态，并尝试通过 `HERMES_RUNTIME_BASE_URL` 代理读取 Hermes 后端能力矩阵。
- 如果 Hermes 后端 bridge 未配置，前端会明确显示 `missing_config`，而不是静默失败。
- 社交媒体设置页新增“能力体检”卡片区域。
- 社交媒体设置页新增 QQ 官方机器人字段：
  - App ID
  - Bot Token
  - Bot Secret
  - Webhook Token
- 前端新增 capability card 样式，区分 ready / partial / missing_config / planned。
- 已导出正式 overlay patch：
  `patches/bailongma/phase-16-capability-matrix-and-qq-settings.patch`

## 验证结果

服务器侧已验证：

- 使用 BaiLongma 运行时 Node 检查语法通过：
  - `src/api.js`
  - `src/config.js`
  - `src/ui/brain-ui/app.js`
  - `src/ui/brain-ui/app-shell.js`
- `bailongma.service` 重启后保持 active。
- `GET http://127.0.0.1:3721/status` 返回正常。
- `GET http://127.0.0.1:3721/capabilities` 返回能力矩阵。

当前能力矩阵显示 Hermes backend 为 `missing_config`，原因是 BaiLongma `.env` 还没有配置 `HERMES_RUNTIME_BASE_URL`，服务器上也没有 8787 运行时监听。这是下一阶段要解决的真实缺口。

## 关键判断

白龙马前端可以继续作为主 UI，但它需要从“聊天界面”升级成“Agent 控制台”：

- 设置页不能只是填 key，要能看到每个能力是否真的可用。
- 社交渠道不能只是表单，要能看到哪个渠道 ready、哪个缺配置。
- Hermes 后端不能被前端重写，要通过 bridge 暴露真实 runtime 状态和任务生命周期。
- 类人陪伴和公司管理可以共用人格表达，但必须在权限、channel、动作类型上隔离。

## 下一步

- 在服务器启动 Hermes/MOXI runtime，并配置 BaiLongma `.env`：
  - `HERMES_RUNTIME_BASE_URL`
  - 如走公网保护，再配置 Basic Auth 用户和密码。
- 在 Brain UI 聊天路径接入 Hermes `/social/turn`，慢任务先显示自然 ACK。
- 把 worker 进度接入 `/jobs/event`，让用户看到“我在看图/搜索/生成/读飞书”。
- 给 Feishu 公司面、微信/QQ 个人面加权限 badge 和高风险动作确认卡。
