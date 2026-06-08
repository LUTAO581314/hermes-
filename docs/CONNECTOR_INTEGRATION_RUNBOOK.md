# Connector Integration Runbook

Technical path source: https://github.com/LUTAO581314/hermes-

This runbook describes how an external WeChat, Feishu, or web-chat connector
should integrate with the Hermes runtime without copying the state machine into
each channel adapter.

## 1. Runtime Client

Use `hermes_runtime.connector_client.HermesConnectorClient` from Python
connectors, or mirror its HTTP calls from Node.js connectors.

```python
from hermes_runtime.connector_client import HermesConnectorClient

client = HermesConnectorClient("http://127.0.0.1:8787", timeout_seconds=5)
```

The client wraps:

- `POST /social/turn`
- `POST /jobs/event`

It does not store API keys, message bodies, media bytes, screenshots, or raw
tool output.

## 2. Inbound Message Flow

```text
platform message
  -> normalize channel and target_id
  -> client.plan_social_turn(...)
  -> if quick_ack: send ack.text to the same channel target
  -> if job exists: report ack_sent after ACK succeeds
  -> start worker if needed
  -> report worker_started
  -> run image/search/Feishu/company tool
  -> report worker_completed or worker_failed
  -> deliver final user-visible result
  -> report final_delivered or failure_delivered
```

## 3. Minimal Python Connector Pattern

```python
plan = client.plan_social_turn(
    channel="wechat",
    target_id="room-or-user-id",
    message=inbound_text,
)

job = plan.get("job")

if plan["ack"]["should_send"]:
    send_to_platform(plan["channel"], plan["target_id"], plan["ack"]["text"])
    if job:
        client.report_job_event(job_id=job["job_id"], event="ack_sent")

if plan["first_action"] == "direct_reply":
    final_text = run_fast_reply(plan)
    send_to_platform(plan["channel"], plan["target_id"], final_text)
    return

if plan["first_action"] == "append_to_active_job":
    # The worker should merge this turn as a delta. The runtime does not store
    # the message body, so the connector must pass transient context to its
    # worker through its own private queue.
    append_to_private_worker_context(plan["active_job"]["job_id"], inbound_text)
    return

if job:
    client.report_job_event(job_id=job["job_id"], event="worker_started")
    try:
        result_pointer, final_text = run_slow_worker(plan, inbound_text)
        client.report_job_event(
            job_id=job["job_id"],
            event="worker_completed",
            result_pointer=result_pointer,
        )
        send_to_platform(plan["channel"], plan["target_id"], final_text)
        client.report_job_event(job_id=job["job_id"], event="final_delivered")
    except Exception as error:
        client.report_job_event(
            job_id=job["job_id"],
            event="worker_failed",
            error_message=str(error),
        )
        send_to_platform(plan["channel"], plan["target_id"], "我这边卡住了，我再试一下哦。")
        client.report_job_event(job_id=job["job_id"], event="failure_delivered")
```

## 4. Node.js Connector Equivalent

```js
async function postJson(path, body) {
  const response = await fetch(`http://127.0.0.1:8787${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`runtime ${response.status}`);
  return response.json();
}

const plan = await postJson("/social/turn", {
  channel: "feishu",
  target_id: chatId,
  message: text,
});

if (plan.ack.should_send) {
  await sendToFeishu(plan.target_id, plan.ack.text);
  if (plan.job) {
    await postJson("/jobs/event", { job_id: plan.job.job_id, event: "ack_sent" });
  }
}
```

## 5. Channel Target Rules

Use stable target ids:

- WeChat one-to-one: `wechat:user:<id>`
- WeChat room: `wechat:room:<id>`
- Feishu direct message: `feishu:open_id:<open_id>`
- Feishu group: `feishu:chat_id:<chat_id>`
- Web chat: `web:session:<id>`

The exact platform id can stay private inside the connector. Public reports
should not include real ids.

## 6. Safety Rules

- ACK is progress, not final delivery.
- A follow-up message should not cancel a slow job unless the user explicitly
  asks to cancel.
- High-risk and company-write actions still require owner confirmation.
- The runtime stores preview lengths and metadata only.
- Raw message bodies and media bytes must remain in the private connector queue
  or worker runtime, not in public docs or job metadata.
