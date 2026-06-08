# Phase 07 中文报告：上下文瘦身与慢任务异步骨架

## 1. 本阶段目标

本阶段目标是把“回复慢”拆成可控链路：普通聊天少加载上下文和工具，读图、生图、搜索、舆情、飞书公司任务进入慢任务队列，并且先给用户自然提示，最终结果继续补发。

## 2. 已完成内容

新增 `hermes_runtime/context_budget.py`，根据路由结果给出每类消息的上下文预算，包括记忆深度、最近消息数量、是否允许长记忆、是否允许 Obsidian 检索、工具组和工具 schema 数量。

新增 `hermes_runtime/async_jobs.py`，提供慢任务状态机：

```text
queued -> acknowledged -> running -> completed -> delivered
queued -> acknowledged -> running -> failed -> failure_delivered
queued/running -> cancelled
```

新增运行时接口：

```text
GET /context?message=...
GET /jobs
POST /jobs
POST /jobs/transition
```

这些接口只保存安全元数据：job id、route、channel、target id、输入长度预览、tool name、状态、时间戳、结果指针、错误摘要和是否需要主人确认。不会保存用户消息正文、API 响应、截图、密钥、私密聊天记录或工具原始输出。

## 3. 对实际体验的影响

真实连接器后续可以这样执行：

1. 收到消息后先走轻量路由。
2. 根据 `/context` 拿上下文预算。
3. 慢任务先发自然 ACK。
4. 通过 `/jobs` 创建任务。
5. worker 执行真实读图、生图、搜索、舆情或飞书任务。
6. 通过 `/jobs/transition` 更新状态。
7. 完成后由对应渠道补发最终结果。

这样可以满足“5 秒内先有答复，需要思考就有提示”的体验目标。

## 4. 验收结果

- 上下文预算接口已实现。
- 慢任务状态机已实现。
- 单元测试已覆盖上下文预算、job 创建、job 状态推进和隐私约束。
- 文档和公开技术路径已更新。
- 未提交真实密钥、服务器密码、服务器 IP 或私密聊天内容。

Technical path source: https://github.com/LUTAO581314/hermes-
