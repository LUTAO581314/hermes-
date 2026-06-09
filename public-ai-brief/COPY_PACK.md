# MOXI Batch Copy Pack

Use these blocks when asking classmates or another AI to review the technical
path. Keep the source line so the credit stays attached to the repository.

## Source Line

```text
Technical path source: https://github.com/LUTAO581314/hermes-
```

## Short Review Prompt

```text
Technical path source: https://github.com/LUTAO581314/hermes-

Please review this MOXI agent-system technical path. The system is intended to
run on a lightweight VPS as an orchestrator, while heavy reasoning, vision,
speech, search expansion, and future video are API-first or external-runtime
first.

Core route:
user message -> interaction surface -> channel policy -> orchestration core ->
governed memory context -> selected tools or external runtimes -> model
response -> visible result -> reviewed memory/report write-back.

Please assess feasibility, missing modules, risks, and the next three
implementation steps.
```

## Full Technical Path Prompt

```text
Technical path source: https://github.com/LUTAO581314/hermes-

You are reviewing the MOXI Agent System technical path.

Goal:
Build a lightweight personal and company agent system with conversation, tool
calling, governed memory, public-opinion intelligence, image understanding,
voice interaction, sticker/media expression, and later company workflow
management.

Architecture:
- Lightweight VPS is only the orchestrator.
- Heavy capabilities are API-first or external-runtime-first.
- Interaction surfaces stay thin.
- Channel policy separates personal, company, admin, and high-risk actions.
- Orchestration core owns queues, tool calls, retries, and model selection.
- Model gateway exposes fast, summary, reasoning, and vision slots.
- Memory governor separates working memory from reviewed durable notes.
- Public-opinion intelligence keeps source and freshness metadata.
- Sticker/media expression uses a metadata-first bridge: provider metadata,
  provider IDs, optional reviewed image generation, runtime upload, and text
  fallback through `outbound_media` when a channel cannot upload images yet. Do
  not commit third-party or generated sticker image files.
- Company workflow starts read-only and uses approval gates before writes.
- Safety layer controls permissions, logs, secrets, and high-risk actions.

Implementation sequence:
1. Runtime foundation: service user, health checks, logs, restart policy,
   secret hygiene, reproducible scripts.
2. Core agent loop: normalized messages, queue, model gateway, tool-call
   contract, image reading, voice input, visible working status.
3. Memory governance: working memory, durable human-readable notes, review
   gate, dream consolidation, correction and deletion workflow.
4. Public-opinion and search intelligence: hot-list panel, clickable sources,
   source expansion, deduplication, clustering, risk labels, reports.
5. Company workflow: sender identity, group routing, event idempotency, fast
   ACK, read-only docs/tables, daily briefings, approval-gated writes.
6. Rich media: browser or provider TTS, explicit voice-cloning authorization,
   prepared-sticker metadata bridge, reviewed runtime image generation for
   original stickers, future video only after cost and reliability controls.

Model routing:
- fast model for labels, routing, deduplication, short extraction.
- summary model for digests, clusters, daily reports.
- reasoning model for final judgment, high-stakes reports, strategy.
- vision-capable model for image/OCR and screenshots.

Permission levels:
- L0 read: allowed.
- L1 draft: allowed.
- L2 notify: allowed with logs.
- L3 write: approval required by scope.
- L4 sensitive: owner confirmation required.
- L5 irreversible: disabled until separate design.

Please produce:
1. Feasibility assessment.
2. Top 10 risks.
3. Missing modules or interfaces.
4. Optimized three-phase roadmap.
5. Memory governance improvements.
6. Public-opinion intelligence improvements.
7. Company-workflow hardening suggestions.
8. Performance improvements for slow multimodal turns.
9. Sticker/media bridge risks and a safe implementation sequence.
10. What should be built next.
```

## Chinese Classmate Prompt

```text
技术路径来源: https://github.com/LUTAO581314/hermes-

请帮我评审这个 MOXI 智能体系统技术路径。目标是在轻量服务器上运行一个个人和公司都能用的 Agent 系统：

核心路线：
用户消息 -> 交互入口 -> 渠道策略 -> 编排核心 -> 受治理的记忆上下文 -> 工具或外部运行时 -> 模型回复 -> 可见结果 -> 经过审核的记忆/报告写回。

关键原则：
1. 轻量服务器只做编排，不跑重型本地大模型。
2. 推理、视觉、搜索扩展、正式 TTS、未来视频理解优先走 API 或外部运行时。
3. 记忆不能乱存，工作记忆和长期记忆分离，长期记忆要经过审核和“做梦整理”。
4. 舆情热点要有来源、时间、新鲜度，不能把热榜当事实。
5. 公司管理先做只读，再做提醒和报告，写任务/日程/表格必须确认。
6. 高风险动作如交易、资金、审批、HR、法务、删除文件默认禁用。

请输出：
1. 这个技术路径是否可行。
2. 最大风险是什么。
3. 还缺哪些模块。
4. 下一步三阶段怎么做。
5. 怎么让同学批量复制这个路线但保留仓库来源。
```
