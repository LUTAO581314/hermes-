# Phase 31 白龙马运行配置前端适配阶段报告

## 结论

本阶段把 Hermes Phase 30 的可写配置 schema 接入到了服务器上的白龙马 Brain UI。设置面板现在新增“运行配置”页，可以动态读取 Hermes `/config/schema`，按 schema 分组渲染可写字段，并通过 `/config/update` 保存白名单配置。

这一步解决了主人指出的核心问题：设置页不能再是零散表单，而要完整映射 Hermes 后端真实配置。

## 已完成

1. 服务器 Hermes runtime 同步 Phase 30 控制面
   - `/opt/hermes-system` 运行的服务原本没有 `/config/schema`。
   - 已补齐 `config_schema.py`、`media_delivery.py`、`server.py`、`frontend_contract.py`。
   - 已重启 `hermes-runtime.service`。
   - 已验证 `http://127.0.0.1:8787/config/schema` 返回 `ok`，schema version 为 `1`。

2. 白龙马服务新增 Hermes 配置代理
   - `GET /config/schema` 代理 Hermes runtime 的 secret-safe schema。
   - `POST /config/update` 代理 Hermes runtime 的白名单写入接口。
   - 写入接口保留 `requireLocalOrToken` 保护，不做公网裸写。

3. Brain UI 设置页新增“运行配置”
   - 设置侧栏新增 `运行配置` tab。
   - 页面从 `/config/schema` 动态渲染模型、搜索、媒体、性能四组字段。
   - 支持 `text`、`url`、`int`、`bool`、`select`、`secret` 字段。
   - secret 字段只显示“已配置/未配置”，输入框留空不提交。
   - 保存时只提交发生变化的字段。
   - 保存成功后刷新 schema、总览、能力矩阵。

4. 前端样式补齐
   - 新增 schema group、field、pill、key、hint 样式。
   - 桌面端两列字段，移动端自动单列。
   - 保持 Brain UI 当前克制的工作台风格，没有额外装饰化。

## 服务器验证

已验证：

```text
systemctl is-active hermes-runtime.service
systemctl is-active bailongma.service
curl http://127.0.0.1:8787/config/schema
curl http://127.0.0.1:3721/config/schema
curl http://127.0.0.1:3721/src/ui/brain-ui/app-shell.js
curl http://127.0.0.1:3721/src/ui/brain-ui/app.js
curl http://127.0.0.1:3721/src/ui/brain-ui/styles.css
POST http://127.0.0.1:3721/config/update
```

结果：

```text
hermes-runtime.service active
bailongma.service active
3721 /config/schema -> ok, schema_version=1, groups=4
app-shell contains runtime-config
app.js contains loadHermesConfigSchema
styles.css contains settings-schema-group
POST /config/update -> ok, changed_keys includes HERMES_SOCIAL_FAST_REPLY_TARGET_MS
```

## 风险处理

- 没有把任何真实 API key、密码、微信会话、飞书密钥写入仓库。
- 没有清理或回滚服务器已有白龙马本地改动。
- `/opt/hermes-system/hermes_runtime/routing.py` 有中文路由热修，已保留，没有覆盖。
- 服务器更新前已创建 `/home/hermes/backups/hermes-system-phase31-before-*` 备份。
- 由于服务器 `/opt/hermes-system` 有本地热修，本阶段没有强行 `git merge --ff-only` 覆盖整个目录，而是只同步必需 runtime 文件。

## 下一步

下一阶段建议继续收口设置中心：

1. 把旧“模型/媒体/搜索”表单逐步迁移为 Hermes schema 驱动。
2. 保存前显示变更摘要，尤其是 secret 与性能参数。
3. 为 `/config/update` 增加前端二次确认，用于后续高级配置。
4. 增加设置页 Playwright 视觉 smoke，检测 tab 可点击、字段可渲染、保存错误可展示。
