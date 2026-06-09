# Phase 33 QQ 个人 NapCat 桥接阶段报告

## 本阶段目标

把 Phase 32 的“QQ 个人扫码”占位面板推进到真实可启动的桥接路线：

- 选用 NapCat 作为第一版个人 QQ 扫码桥接器。
- 用 Docker 隔离 NapCat，不把 QQ 会话文件、二维码、WebUI token、账号信息写入 Git。
- 让 BaiLongma Brain UI 的 QQ 个人扫码面板能读取真实桥接状态。
- 保持 QQ 官方机器人和 QQ 个人扫码两条路线分离。

## 已完成

1. 服务器安装与运行
   - 服务器 Docker 可用。
   - NapCat 镜像已通过镜像源拉取成功。
   - 容器名：`moxi-napcat`。
   - WebUI 仅绑定本机：`127.0.0.1:6099`。
   - OneBot 端口仅绑定本机：`127.0.0.1:3001`。
   - QQ 数据目录放在服务器运行目录，不进入仓库。

2. BaiLongma 后端桥接
   - 新增运行时桥接模块：`src/social/qq-personal-bridge.js`。
   - `GET /social/qq-personal/qr` 现在返回真实状态：
     - `bridge_missing`
     - `stopped`
     - `starting`
     - `webui_ready`
     - `qr_ready`
     - `connected`
   - `POST /social/qq-personal/start` 会启动或创建 NapCat 容器。
   - `POST /social/qq-personal/logout` 会停止 NapCat 容器，但不删除 QQ 数据。

3. Brain UI 面板
   - QQ 个人扫码面板现在能显示 NapCat 状态。
   - 当 NapCat 日志里出现登录二维码 URL 时，接口返回 `qr_ready + qr_url`，前端直接生成二维码。
   - 当只有 WebUI 可用时，前端显示 WebUI 扫码入口。

4. 服务器权限
   - `hermes` 用户已加入 `docker` 组，BaiLongma 服务可以控制本地 NapCat 容器。
   - BaiLongma 服务保留本机监听，不把 NapCat WebUI 裸露到公网。

## 验证结果

服务器验证：

```text
bailongma.service: active
moxi-napcat: running
GET http://127.0.0.1:3721/social/qq-personal/qr -> ok=true, status=qr_ready
```

安全验证：

- 没有把真实 QQ 二维码 URL 写入仓库。
- 没有把 NapCat WebUI token 写入仓库。
- 没有提交 QQ session、cookies、账号 id 或私聊/群聊 id。
- NapCat WebUI 和 OneBot 端口只绑定 `127.0.0.1`。

## 当前边界

本阶段完成的是“QQ 个人扫码桥接器启动与登录状态入口”，还不是完整 QQ 收发消息机器人。

下一阶段需要继续做：

1. 配置 NapCat OneBot 11 正向或反向 WebSocket。
2. 新增 BaiLongma QQ event receiver。
3. 把 QQ 入站消息转成 Hermes `/social/turn`。
4. 对慢任务发送 quick ACK。
5. 对最终回复走 QQ send message。
6. 给 QQ 图片、语音、表情包做和微信一致的媒体兼容层。

## 风险提示

个人 QQ 协议桥接高于官方机器人风险，可能受到平台风控、版本变更或扫码登录失效影响。QQ 个人路线只适合个人陪伴、轻量通知和低风险对话，不应直接执行公司、资金、法务、HR、交易等高风险动作。

## 仓库固化

- 新增 overlay patch：`patches/bailongma/phase-33-qq-personal-napcat-bridge.patch`
- 更新 QQ 连接器文档。
- 更新 Hermes 前端适配计划。
- 更新 README 阶段报告入口。
