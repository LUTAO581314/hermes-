# Phase 11 中文报告：连接器客户端与接入 Runbook

## 1. 本阶段目标

本阶段开始把底层 runtime 协议推向真实微信、飞书、网页聊天桥接层。当前公开仓库没有服务器上真实 BaiLongma `src/social/*` 源码，因此本阶段先提供一个可复制的连接器客户端和接入 runbook，后续真实桥接层可以直接照这个协议改造。

## 2. 已完成内容

新增 `hermes_runtime/connector_client.py`。

它封装两个连接器常用接口：

```text
POST /social/turn
POST /jobs/event
```

Python 连接器可以直接使用：

```python
from hermes_runtime.connector_client import HermesConnectorClient

client = HermesConnectorClient("http://127.0.0.1:8787", timeout_seconds=5)
```

然后调用：

```python
plan = client.plan_social_turn(
    channel="wechat",
    target_id="room-or-user-id",
    message=inbound_text,
)

client.report_job_event(job_id=job_id, event="ack_sent")
```

## 3. 新增 Runbook

新增 `docs/CONNECTOR_INTEGRATION_RUNBOOK.md`，说明微信、飞书、网页聊天连接器如何按统一流程接入：

```text
platform message
  -> normalize channel and target_id
  -> client.plan_social_turn(...)
  -> if quick_ack: send ack.text
  -> report ack_sent
  -> start worker
  -> report worker_started
  -> run image/search/Feishu/company tool
  -> report worker_completed or worker_failed
  -> deliver final result
  -> report final_delivered or failure_delivered
```

Runbook 同时提供 Python 和 Node.js 接入示例。

## 4. 对真实微信/飞书桥接层的意义

后续真实桥接层不需要自己重复实现：

- 路由；
- ACK 文案；
- 上下文预算；
- 慢任务创建；
- 追问不打断；
- job 状态机；
- worker 生命周期事件。

它只需要：

1. 收到平台消息；
2. 调用 `plan_social_turn`；
3. 发送 ACK；
4. 上报 job event；
5. 调用真实工具；
6. 发送最终结果；
7. 上报最终投递事件。

## 5. 隐私与安全

连接器客户端只把当前入站文本发送到规划接口，不会把消息正文写入 job。runtime 仍然只保存预览长度、状态和元数据。

真实媒体、截图、平台 token、API 响应、聊天正文应留在私有连接器或 worker 队列中，不写入公开仓库、不写入公共报告。

## 6. 验收结果

- 新增连接器客户端。
- 新增连接器接入 runbook。
- 单元测试覆盖客户端调用 `/social/turn` 和 `/jobs/event`。
- 总测试数提升到 20 个，全部通过。
- README、内部技术路径、公开技术路径已更新。

Technical path source: https://github.com/LUTAO581314/hermes-
