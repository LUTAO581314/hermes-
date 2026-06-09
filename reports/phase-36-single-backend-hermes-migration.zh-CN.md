# Phase 36 单后端 Hermes 迁移阶段报告

## 本阶段结论

主人新的架构边界是正确的：系统只能长期保留一个后端和一个前端。

- 唯一后端：Hermes。
- 唯一前端：MOXI / Brain UI。
- 白龙马后端不再继续扩展，只作为前端设计和历史实现素材。
- 能直接进入 Hermes 的接口，不再绕一层白龙马后端。

## 白龙马值得迁移什么

值得迁移的是产品体验，不是后端大脑：

1. Brain UI 的界面设计、设置面板、聊天体验、进度条、语音按钮、图片附件体验。
2. 热点面板的数据结构和视觉入口，尤其是可点击标题、来源链接、平台标签、摘要、底部事件卡片。
3. 通道隔离规则：网页、API、语音消息不能误发到微信、QQ、飞书。
4. 慢任务体验：先给自然回应，再跑慢任务，再展示进度。
5. 浏览器 TTS fallback 和“麦克风/实时对话”分离的前端模式。

## 白龙马不该迁移什么

以下能力不再作为主后端保留：

- 白龙马模型循环。
- 白龙马记忆库作为长期记忆来源。
- 白龙马设置接口作为主配置。
- 白龙马 Feishu/QQ/微信后端控制逻辑作为最终权威。
- NapCat 个人 QQ 扫码作为 QQ 主路线。
- 任何硬编码 key、二维码、WebUI token、群号、用户 id、会话文件。

## 已落地改动

本阶段在 Hermes runtime 增加了原生热点接口：

```text
GET /hotspots
```

它读取 TrendRadar 输出目录：

```env
HERMES_TRENDRADAR_OUTPUT_DIR=/home/hermes/external/TrendRadar/output
```

返回 Brain UI 能直接消费的结构：

- `items`
- `feed`
- `platforms`
- `migration`

这样热点面板可以保留，但数据由 Hermes 提供，不再依赖白龙马后端。

## 后续服务器步骤

1. 在服务器备份白龙马目录。
2. 只提取 Brain UI 静态资源和必要前端 patch。
3. 把 Brain UI API base 改为 Hermes 同源接口。
4. 验证 `/hotspots` 能读到 TrendRadar 最新输出。
5. 验证网页聊天只回网页，不串到微信。
6. 验证设置页完整读取 `/config/schema` 并保存到 `/config/update`。
7. 上线 Hermes 托管的 MOXI/Brain UI。
8. 再停止并禁用 `bailongma.service`。

## 风险

不能现在直接删除白龙马目录。原因是热点、语音、图片附件、Brain UI 资源还有可迁移价值。
正确顺序是先迁移、验证，再退役服务。

## 验收标准

- `GET /hotspots` 通过单元测试。
- `GET /frontend/contract` 暴露热点接口说明。
- 设置 schema 包含 TrendRadar 输出目录。
- 文档明确 Hermes 是唯一后端。
- 白龙马后端被标记为待退役，不再作为新增功能承载层。
