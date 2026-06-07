# 表情包桥接层

## 1. 目标

表情包桥接层负责把“沫汐应该发什么表情”转换成各聊天平台可执行的发送指令。

本阶段不把任何表情包图片下载进仓库，也不提交运行时生成的图片。仓库只保存：

- 表情意图。
- 风格偏好。
- Provider 名称。
- 搜索关键词或平台素材 ID。
- 授权和归属提示。
- 飞书、微信、网页等渠道的发送策略。

这样可以满足“准备好的可爱、女生用、二次元风格表情包”需求，同时避免把版权图片、临时文件、平台 media id 或 API key 写进 Git。

## 2. 当前实现

代码入口：

- `hermes_runtime/sticker_bridge.py`
- `tests/test_sticker_bridge.py`

运行配置：

```env
HERMES_STICKER_BRIDGE_ENABLED=false
HERMES_STICKER_DEFAULT_PROVIDER=metadata_only
HERMES_STICKER_DEFAULT_STYLE=kawaii_anime
HERMES_STICKER_IMAGE_GENERATION_ENABLED=false
HERMES_STICKER_IMAGE_GENERATION_MODEL=
HERMES_STICKER_GENERATION_REVIEW_REQUIRED=true
HERMES_STICKER_RUNTIME_CACHE_ENABLED=false
HERMES_STICKER_API_KEY=
```

`/health` 只暴露配置状态，不暴露真实 key：

```json
{
  "stickers": {
    "bridge_enabled": false,
    "default_provider": "metadata_only",
    "default_style": "kawaii_anime",
    "api_key_configured": false,
    "image_generation_enabled": false,
    "image_generation_model": "",
    "generation_review_required": true,
    "runtime_cache_enabled": false
  }
}
```

## 3. 准备好的表情意图

第一批意图保持少而准，适合沫汐的人设和聊天节奏：

| Intent | 用途 | 文本兜底 |
| --- | --- | --- |
| `cute_greeting` | 打招呼、上线、醒来 | 嘿嘿，来啦～ |
| `happy_praise` | 夸奖、庆祝、给主人鼓劲 | 啊啊啊太棒啦！ |
| `soft_comfort` | 安慰、抱抱、陪伴 | 抱抱你，我在呢。 |
| `shy_like` | 害羞、撒娇、轻亲密 | 哼，才没有很想你呢。 |
| `working_hard` | 学习、工作、加油 | 继续冲呀，我陪你。 |
| `sleepy_goodnight` | 晚安、困困、睡前 | 晚安安，记得好好睡呀。 |
| `thank_you` | 感谢、乖巧回应 | 谢谢主人～ |

每个意图会生成一组检索标签，例如 `kawaii`、`anime girl`、`hug`、`blush`、`good night`。渠道适配器后续可以用这些标签去 Stipop、GIPHY 或生图 API 查找/生成候选。

## 4. Provider 选择

### 4.1 首选：Stipop

Stipop 是最贴近聊天软件表情包的方案。它提供 Messaging Sticker API、sticker search、sticker store 和 SDK，官网也强调它面向聊天界面、评论、视频通话等应用场景。

适合：

- 可爱、二次元、女生风格表情搜索。
- 聊天软件内的表情包面板。
- 后续做“沫汐表情包推荐器”。

边界：

- 需要 API key。
- 表情素材按 Stipop API 和服务条款使用。
- 仓库不存图片，只存 provider、query、id 和授权提示。

### 4.2 备选：GIPHY Stickers

GIPHY 提供 stickers search endpoint，适合做动图或贴纸搜索。但它要求使用 API key，并且使用 GIPHY API 的应用需要展示 Powered by GIPHY 归属。

适合：

- 网页端预览。
- 轻量反应贴纸。
- 有归属展示能力的 UI。

边界：

- 不直接下载并提交素材。
- 需要按 GIPHY 要求处理 attribution、analytics、rate limit。
- 飞书/微信发送时仍然要先运行时解析、再上传到平台。

### 4.3 安全兜底：OpenMoji 和 Noto Emoji

OpenMoji 与 Noto Emoji 更像开源 emoji 资源，不够“女生二次元表情包”，但适合做无 API key 的兜底。

边界：

- OpenMoji 是 CC BY-SA 4.0，需要署名和注意相同方式共享。
- Noto Emoji 字体和图像资源许可不同，仓库应只记录来源和许可，不直接混入素材文件。
- 如果未来要把这些资源打包进前端，必须单独做 license notice。

### 4.4 平台内置：LINE sticker id

LINE Messaging API 可以通过 `packageId` 和 `stickerId` 发送平台内置 sticker。这种方式只适合 LINE 渠道，对飞书和微信没有直接作用，但可以作为平台内置素材 ID 模式的参考。

### 4.5 新增能力：图片生成 API

现在 API 已经具备生图能力，所以桥接层保留 `image_generation` provider。

适合：

- 生成“沫汐专属”原创可爱二次元表情。
- 生成统一风格的系列表情，例如打招呼、抱抱、晚安、加油。
- 当外部表情包 API 找不到合适素材时兜底。

边界：

- 默认关闭：`HERMES_STICKER_IMAGE_GENERATION_ENABLED=false`。
- 默认需要审核：`HERMES_STICKER_GENERATION_REVIEW_REQUIRED=true`。
- 生成图片只允许运行时缓存，不提交 Git。
- 发送前需要内容安全检查和主人确认规则。
- 平台发送仍然要走飞书 `image_key` 或微信 `media_id` 等上传流程。

推荐生成提示词骨架：

```text
original kawaii anime chat sticker, soft pastel girl, expressive,
{intent tags}, transparent background, no text
```

不要生成带平台商标、现成动漫角色、真人肖像或第三方 IP 风格的表情。

## 5. 渠道发送策略

### 5.1 Web

Web 可以做表情候选预览，但只有在 provider 允许 embed 或 API 展示时才渲染远程预览。

失败时：

- 显示文本兜底。
- 保留 provider 查询状态。
- 不把远程图片写入仓库。

### 5.2 飞书

飞书发送图片消息需要先上传图片，拿到 `image_key` 后再发送 `msg_type=image`。

桥接层只返回发送指令：

```text
resolve or generate -> upload to Feishu -> send by image_key
```

飞书适配器负责：

- 使用 tenant access token 上传图片。
- 记录上传结果和发送结果。
- 不把 `image_key` 当作长期素材库。
- 群聊回复必须保持在原群。

### 5.3 微信

微信官方路线通常要上传素材并获得 `media_id`，再通过客服消息、公众号或企业微信能力发送。

个人微信桥接则由当前运行时适配器决定是否支持图片发送。

桥接层只返回发送指令：

```text
resolve or generate -> upload through WeChat bridge or official media API -> send by media id
```

失败时：

- 使用文本兜底。
- 不重试刷屏。
- 不让公司、高风险动作走微信表情入口。

## 6. 决策原则

1. 先用 metadata-only 跑通渠道协议。
2. 再接 Stipop 作为主表情包 provider。
3. GIPHY 只在可以展示归属和合规使用时启用。
4. 开源 emoji 只做兜底，不当作二次元主风格。
5. 生图 API 用于原创 MOXI/沫汐专属表情，但要经过审核、内容安全和运行时缓存策略。
6. 任何平台临时文件、media id、image key、API key 都不进 Git。

## 7. 后续落地顺序

1. 在 Web UI 增加表情意图按钮和候选预览。
2. 给飞书适配器加运行时上传并发送 `image_key`。
3. 给微信适配器加运行时上传或桥接发送。
4. 接 Stipop API key 后做真实候选检索。
5. 接图片生成 API 后生成沫汐专属表情候选，先主人审核后启用。
6. 增加发送频控，避免聊天里表情刷屏。

## 8. 参考来源

- Stipop API docs: <https://docs.stipop.io/en/api>
- Stipop chat sticker docs: <https://docs.stipop.io/en/chat/get-started/before-you-begin>
- GIPHY API docs: <https://developers.giphy.com/docs/api/>
- OpenMoji FAQ: <https://www.openmoji.org/faq>
- Noto Emoji GitHub: <https://github.com/googlefonts/noto-emoji>
- LINE message types: <https://developers.line.biz/en/docs/messaging-api/message-types/>
- Feishu upload image API: <https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/image/create>
- Feishu message content image format: <https://open.larksuite.com/document/server-docs/im-v1/message-content-description/create_json>
- WeChat temporary material API: <https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/New_temporary_materials.html>
- WeChat customer service messages: <https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Service_Center_messages.html>
