# Phase 02 中文报告：核心 Hermes + 白龙马 MVP

## 1. 阶段目标

本阶段不追求一次性接满所有媒体能力，而是先解决核心闭环：

- Hermes 核心运行。
- 白龙马 Brain UI 稳定访问。
- GPT-5.5 作为主脑。
- TrendRadar 作为外部搜索项目能力。
- 类人记忆治理。
- 工具调用。
- 图片理解。
- 本地语音输入。

视频理解、AI 视频生成、交易自动执行、飞书公司管理暂时不进入本阶段。

## 2. 已完成事项

- `bairui.chat` 已代理到白龙马 Brain UI。
- 白龙马后端服务运行正常。
- 主模型已配置为 `custom / gpt-5.5`。
- Hermes 已安装，版本为 `v0.16.0`。
- TrendRadar MCP 已启用，地址为 `127.0.0.1:3333/mcp`。
- 微信 ClawBot 已从持久化凭证恢复，说明之前扫码状态仍可用。
- 本地 Whisper `tiny` 已安装在独立虚拟环境中。
- 白龙马 `/voice/cloud` 已支持本地 Whisper，并增加了等待重试，避免首次加载模型时抢跑失败。
- 已修复白龙马 `/voice/cloud` 本地代理问题：WebSocket 现在区分二进制 PCM 音频帧和 JSON 控制帧，避免把 `flush` 当成音频转发给 Whisper。
- 已增加本地 Whisper 就绪前的音频帧缓冲，避免前端开始说话早于 Whisper `config_ok` 时丢帧。
- 图片理解工具 `analyze_image` 已接入当前主模型。
- 视频理解工具暂不暴露给模型，避免阶段跑偏。
- 白龙马 Brain UI 记忆图谱已升级为“工作记忆候选图”，区分工作记忆、待审核、Obsidian 正本边界、清理风险和关系轴。
- 新增只读接口 `/memory/graph`，只用于前端展示，不写入、不晋升、不替代 Obsidian。

## 3. 验证结果

已验证：

- `bailongma` 服务为 active。
- `trendradar-mcp` 服务为 active。
- `nginx` 服务为 active。
- `https://bairui.chat/health` 返回正常。
- 白龙马 `/status` 返回 running，当前记忆数量为 31。
- 主模型状态显示 `custom / gpt-5.5`。
- Hermes MCP 列表显示 TrendRadar enabled。
- 本地 Whisper WebSocket 返回 `asr_status` 和 `config_ok`。
- 3723 本地语音端口由 Whisper Python 服务监听。
- 白龙马 `/voice/cloud` 已完成真实转写烟测，返回文本：`Hello world this is a final local voice test.`
- `analyze_image` 对 PNG 测试图识别出 `MOXI CORE OK`。
- `/memory/graph?limit=80` 返回正常：当前 31 条白龙马运行时记忆、69 个图谱节点、200 条连线。
- Brain UI 前端资源已验证包含 `memory-governance` 状态条和 `/memory/graph` 调用。
- 本次图谱验证后记忆数量仍为 31，没有新增测试垃圾记忆。

## 4. 当前缺口

- 白龙马自己的 Web Search 配置为空；当前先走 Hermes + TrendRadar。
- TTS 配置入口存在，但还没有 MiniMax、豆包、OpenAI TTS 或 ElevenLabs key。
- MiniMax 未配置，所以图片生成、音乐、歌词、MiniMax TTS 暂不启用。
- 飞书凭证未配置，飞书公司管理未开始。
- Obsidian 写回流程已经补成固定文档流程，但还没有做成自动化 Hermes 工具。
- 白龙马运行时记忆整理已升级为“做梦整理”思路：先生成只读梦境报告，再由主人确认遗忘、合并、入 inbox、写报告或晋升。

## 5. 记忆治理结论

当前采用：

```text
聊天/日志
  -> 白龙马工作记忆候选
  -> 记忆准入门
  -> Obsidian 00-Inbox/needs-review
  -> 主人修正或每周整合
  -> 持久双链笔记
  -> 可重建索引
```

白龙马图谱定位：

```text
白龙马图谱 = 当前工作记忆/候选记忆的可视化
Obsidian 图谱 = 主人确认后的长期正本
```

规则：

- 不把日志当记忆。
- 不把测试输出当长期记忆。
- 不把问候、临时情绪、角色语气实验自动记入长期记忆。
- 稳定偏好、架构决策、项目事实、重复模式、主人明确要求记住的内容才允许写入。
- 每个阶段结束都要做梦整理新增记忆，先看混乱信号，再清掉测试垃圾或合并重复记忆。

## 6. 下一阶段建议

下一阶段优先做：

1. 把 Obsidian `00-Inbox/needs-review` 写回流程做成 Hermes 工具。
2. 把白龙马“做梦整理”的建议进一步接到主人确认后的遗忘、合并、入 inbox、晋升动作。
3. 如果主人提供 MiniMax 或豆包 TTS key，再启用语音输出。
4. 等核心稳定后，再进入飞书公司管理 MVP。

## 7. 风险

- 微信个人桥接适合主人个人陪伴，不适合公司敏感操作。
- 本地 Whisper tiny 省钱但准确率和延迟不如成熟云 ASR。
- 图片理解会把图片内容发送到主模型接口，私密图片需要主人明确同意。
- 自动记忆如果没有梦境整理和主人确认后的清理，仍可能积累垃圾。

## 8. 本次文档补齐

新增：

- `docs/CORE_MVP_RUNBOOK.md`：核心 Hermes + 白龙马验收手册。
- `docs/OBSIDIAN_WRITEBACK_WORKFLOW.md`：Obsidian 写回、准入、纠错、清理流程。
- `scripts/check-core-mvp.sh`：服务器核心能力检查脚本。
- 白龙马服务器端 `/memory/graph` 只读接口和 Brain UI 记忆治理状态条。

已同步：

- `README.md`
- `docs/ROADMAP.md`
- `docs/API_INTEGRATIONS.md`
- `docs/MEMORY_GOVERNANCE.md`
- `docs/SEARCH_RUNTIME.md`
- `docs/SUSTAINABLE_ITERATION_BLUEPRINT.md`
- `docs/ARCHITECTURE.md`
- `docs/MASTER_PLAN.md`
