# Phase 07 中文报告：上下文瘦身与慢任务异步骨架

## 1. 本阶段目标

本阶段继续优化“社交回复太慢、不像真人”的问题，重点从底层链路入手：

- 普通聊天不能加载全量记忆、全量工具和长上下文。
- 读图、生图、搜索、舆情、飞书公司任务要进入慢任务队列。
- 慢任务开始前先给用户一个自然的快速回应，最终结果不能丢。
- 性能诊断接口不能暴露密钥、服务器信息、聊天正文、截图或工具原始输出。

## 2. 已完成内容

### 2.1 新增上下文瘦身策略

新增 `hermes_runtime/context_budget.py`，根据路由结果给出每类消息的上下文预算。

现在运行时可以通过：

```text
GET /context?message=generate%20image%20avatar
```

返回：

- 路由类型；
- 记忆深度；
- 最多加载几条最近消息；
- 是否允许长记忆；
- 是否允许 Obsidian 检索；
- 应加载哪组工具 schema；
- 最多加载多少个工具 schema。

这一步的意义是：普通微信/飞书聊天不会再默认背着整套“大脑”和工具包跑，只有真正需要读图、生图、搜索、舆情或公司任务时才加载对应能力。

### 2.2 新增慢任务状态机

新增 `hermes_runtime/async_jobs.py`，为慢任务提供安全的进度状态。

已支持状态：

```text
queued -> acknowledged -> running -> completed -> delivered
queued -> acknowledged -> running -> failed -> failure_delivered
queued/running -> cancelled
```

已新增运行时接口：

```text
GET /jobs
POST /jobs
POST /jobs/transition
```

当前 job 只保存：

- job id；
- route；
- channel；
- target id；
- 输入文本长度预览；
- tool name；
- 状态；
- 时间戳；
- result pointer；
- error message；
- 是否需要主人确认。

不会保存用户消息正文、API 响应、截图、密钥、私密聊天记录或工具原始输出。

### 2.3 接入最小 HTTP runtime

`hermes_runtime/server.py` 已接入：

- `/context`：用于连接器在加载记忆/工具前先做预算；
- `/jobs`：用于创建和查询慢任务；
- `/jobs/transition`：用于推进慢任务状态；
- `/latency`：继续记录安全阶段耗时；
- `/route`：继续做规则优先的意图路由。

这让后续微信、飞书、网页前端都可以走同一套底层协议。

### 2.4 测试覆盖

新增测试覆盖：

- `/context` 对生图消息返回瘦身后的上下文预算；
- 生图任务可以创建 job；
- job 可以从 `queued` 推进到 `running` 再到 `completed`；
- job 列表不保存输入正文中的敏感片段；
- 性能、延迟、上下文和任务端点都不暴露 `api_key` 或 `secret`。

## 3. 对实际体验的影响

这阶段不是直接让模型变快，而是把“慢”拆成可控链路：

1. 收到消息后先走轻量路由。
2. 判断是否需要慢任务。
3. 若需要慢任务，先发自然 ACK，例如“我看一下这张图，等我一下哦”。
4. 创建 job，异步执行读图、生图、搜索、舆情或飞书任务。
5. job 完成后补发最终结果。
6. 用户中途补一句话时，不会默认打断上一轮慢任务。

这正好对应主人要求的“5 秒内先有答复，需要思考的就有提示”。

## 4. 当前边界

本阶段完成的是底层安全骨架，还没有把真实微信、飞书、图片生成 worker 全部接到 job runner。

下一阶段需要把连接器改成：

- 进消息先调用 `/route` 或内部 router；
- 慢任务先发 ACK；
- 调用 `/context` 拿上下文预算；
- 调用 `/jobs` 创建 job；
- worker 执行真实工具；
- 调用 `/jobs/transition` 更新状态；
- 完成后由对应渠道补发最终结果。

## 5. 下一阶段建议

下一阶段优先做“真实连接器落地”：

1. 微信桥接层接入 quick ack + job 创建。
2. 飞书事件回调接入 quick ack + job 创建。
3. 图片识别和生图 worker 接入 job transition。
4. 搜索/舆情 worker 接入 job transition。
5. 加入 job 超时和失败提醒。
6. 在前端显示“思考中/处理中”的状态，而不是静默等待。

## 6. 验收结果

本阶段验收通过：

- 运行时已有上下文预算接口；
- 运行时已有慢任务状态机；
- 单元测试通过；
- 文档已更新；
- 公开技术路径保留来源声明；
- 未提交任何真实密钥、服务器密码、服务器 IP 或私密聊天内容。

Technical path source: https://github.com/LUTAO581314/hermes-
