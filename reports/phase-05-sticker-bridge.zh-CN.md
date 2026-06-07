# Phase 05 中文报告：表情包桥接层

## 1. 阶段目标

本阶段目标是给聊天软件增加一个“表情包桥接层”，让沫汐后续可以在网页、微信、飞书等渠道发送可爱、女生用、二次元风格的准备好表情包。

核心要求：

- 不把表情包图片下载进仓库。
- 不把生成图片、临时图片、平台 media id、image key、API key 提交进 Git。
- 先做可复用桥接能力，再接具体渠道发送。
- 兼容现在 API 已经可以生图的情况，但生图默认走审核和运行时缓存。

## 2. 已完成内容

本阶段已完成：

- 新增 `hermes_runtime/sticker_bridge.py`。
- 新增 `tests/test_sticker_bridge.py`。
- 更新 `hermes_runtime/config.py`，加入表情包桥接配置。
- 更新 `hermes_runtime/server.py`，让 `/health` 输出表情包桥接状态。
- 更新 `.env.example`，加入表情包 provider、风格、生图、审核、缓存和 API key 占位。
- 新增 `docs/STICKER_BRIDGE.md`，记录表情包来源、授权边界、飞书/微信发送方式和生图策略。
- 更新 `docs/API_INTEGRATIONS.md`、`docs/WECHAT_COMPANION.md`、`docs/ROADMAP.md`、`docs/RISK_AND_GUARDRAILS.md`。
- 更新 `README.md`、`index.html`、`public-ai-brief/TECHNICAL_PATH.md`、`public-ai-brief/COPY_PACK.md`、`public-ai-brief/README.md`。

## 3. 当前效果

现在仓库已经有一个 metadata-only 表情包桥接层。

它可以根据意图选择表情包候选元数据：

- `cute_greeting`：打招呼。
- `happy_praise`：开心夸奖。
- `soft_comfort`：温柔安慰。
- `shy_like`：害羞撒娇。
- `working_hard`：学习工作加油。
- `sleepy_goodnight`：晚安。
- `thank_you`：感谢。

桥接层会返回：

- provider。
- 风格。
- 查询词。
- tags。
- 授权提示。
- 文本兜底。
- 渠道发送指令。

它不会下载图片，也不会保存图片。

## 4. 架构或决策变化

本阶段把“发表情包”从单一聊天功能升级成一个受控媒体桥接能力：

```text
表情意图
  -> 表情包元数据或生图候选
  -> 渠道策略
  -> 运行时解析/生成
  -> 平台上传
  -> 发送 image_key / media_id / bridge payload
  -> 失败时文本兜底
```

Provider 决策：

- Stipop 是首选准备表情包 provider。
- GIPHY 可以作为备选，但必须处理 attribution 和 API 使用规则。
- OpenMoji、Noto Emoji 只适合做开源 emoji 兜底，不是主二次元风格。
- 当前生图 API 可以作为 `image_generation` provider，用于生成原创沫汐风格表情，但默认需要主人审核。

## 5. 风险与边界

当前边界：

- 不下载第三方表情包到 Git。
- 不提交运行时生成图片。
- 不提交飞书 `image_key`。
- 不提交微信 `media_id`。
- 不提交表情包 provider API key。
- 生图不能模仿现成动漫角色、真人、明星、平台 logo 或第三方 IP。
- 生图候选必须先审核，再变成可复用表情。
- 微信表情不能作为公司、财务、HR、法务或审批动作确认。

## 6. 需要主人确认的事项

后续需要主人确认：

1. 是否要购买或接入 Stipop API key。
2. 是否要启用当前生图 API 做沫汐专属表情。
3. 如果启用生图，第一批表情是否先做 7 个基础意图。
4. 微信和飞书是否都允许发送表情图片，还是先网页预览。
5. 表情发送频率上限，例如连续对话最多每 3 到 5 轮发一次。

## 7. 下一阶段计划

建议下一阶段按这个顺序：

1. 在 Web UI 增加表情意图按钮和候选预览。
2. 接入真实 provider 查询：优先 Stipop，其次 GIPHY。
3. 接入生图 API，生成第一批沫汐原创表情候选。
4. 做主人审核页：通过、拒绝、重新生成、只作为一次性发送。
5. 给飞书适配器增加运行时上传并发送 `image_key`。
6. 给微信适配器增加运行时上传或桥接发送。
7. 增加频控和失败兜底，避免刷屏。

## 8. 记忆整理与清理结果

本阶段不新增个人长期记忆。

值得记录为项目事实的是：

- 表情包能力采用 metadata-only 桥接。
- 生图能力可用，但默认审核、运行时缓存、不入 Git。
- 表情包来源和发送必须受版权、平台、渠道策略约束。

测试句、搜索过程和临时 provider 结果不应进入长期记忆。

## 9. 风险复核结果

本阶段风险复核：

- 未提交真实 API key。
- 未提交表情包图片。
- 未提交生成图片。
- 未提交平台 media id 或 image key。
- 未开启自动向外部平台发送图片。
- 未把微信作为高风险动作确认通道。
- 已在文档中记录版权、授权、平台上传和生图审核边界。
