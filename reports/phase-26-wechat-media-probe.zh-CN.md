# Phase 26 微信图片发送能力探测报告

## 本阶段目标

主人已经实测确认：微信文字链路正常，图片生成结果目前仍以路径文本形式返回。Phase 25 已经提供 `/media/plan-send`，但还需要确认服务器上 BaiLongma/ClawBot 是否有真实图片/文件发送函数。

本阶段新增一个只读探测脚本，用来定位服务器源码里的微信媒体发送能力。

## 已完成

- 新增 `scripts/probe-bailongma-wechat-media.sh`。
- 脚本默认扫描：
  - `/home/hermes/external/BaiLongma`
  - `src/social`
  - 微信、ClawBot、message、send、media 相关文件
- 搜索关键词包括：
  - `sendImage`
  - `sendImageFile`
  - `sendFile`
  - `sendMedia`
  - `uploadAndSendImage`
  - `media_id`
  - `image_key`
  - `/media/image`
  - `downloadMedia`

## 安全边界

- 脚本只读。
- 不发送微信消息。
- 不修改服务器文件。
- 不读取或打印 token、cookie、QR 状态。
- 不上传图片。
- 只输出源码文件名、匹配行和语法检查结果。

## 使用方式

在服务器终端执行：

```bash
cd /home/hermes/external/BaiLongma
bash /home/hermes/hermes-/scripts/probe-bailongma-wechat-media.sh
```

如果仓库不在 `/home/hermes/hermes-`，可以先把脚本内容放到任意临时路径，或指定：

```bash
BAILONGMA_ROOT=/home/hermes/external/BaiLongma bash scripts/probe-bailongma-wechat-media.sh
```

## 输出判断

- 如果看到 `sendImageFile` / `sendFile` / `uploadAndSendImage`：
  - 可以继续把 `/media/plan-send` 的 `send_image_file` 或 `upload_then_send` 接到真实微信发送函数。
- 如果只看到 `downloadMedia`：
  - 当前桥接器大概率只能读入站图片，不能发出站图片。
  - 需要换支持发图的桥接器，或继续保留文字兜底。

## 下一步

主人在服务器运行探测脚本，把输出贴回 Codex。之后按真实函数名做 BaiLongma/ClawBot 服务端补丁。
