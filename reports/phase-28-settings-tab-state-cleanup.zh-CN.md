# Phase 28 Brain UI 设置面板状态收束报告

## 1. 本阶段目标

本阶段处理 Brain UI 设置面板“看起来乱、状态像串台”的问题。

主人指出问题不在单独的社交媒体页，而是设置面板整体状态不干净。排查后确认，核心问题是前端设置弹窗存在重复 tab 切换逻辑，并且打开设置时会无差别加载多类配置，导致用户点某个设置项时，其他设置页的加载状态也可能参与渲染，造成错位感。

## 2. 根因

服务器 BaiLongma 前端 `src/ui/brain-ui/app.js` 中存在两套设置页激活逻辑：

- 一套绑定在 `.settings-nav-item` 点击事件上。
- 一套写在 `openSettings(tab)` 中。

旧逻辑的问题是：

- 点击 tab 时只刷新部分页面，语音页没有作为独立 tab 刷新。
- 打开设置弹窗时同时调用 `loadSettings()` 和 `loadVoiceSettings()`。
- 传入指定 tab 时又手动重复切换 active 状态。

这会让设置面板在视觉上像“状态被别的页面抢了”，尤其是在语音、模型、搜索、社交等面板都有异步请求时更明显。

此外，服务器前端里还有几处中文文案已经变成问号，例如能力总览、QQ 官方机器人和输入框占位文案。这不影响运行，但会明显降低设置面板的可读性。

## 3. 已完成修复

服务器已完成以下改动：

1. 新增统一函数 `activateSettingsTab(tab, { refresh })`。
2. 所有设置导航点击统一走 `activateSettingsTab`。
3. `openSettings(tab)` 不再重复写一套 tab 切换逻辑。
4. 每个 tab 只刷新自己的数据：
   - `llm` / `media`：刷新基础设置。
   - `social`：刷新社交设置。
   - `voice`：刷新语音设置。
   - `web-search`：刷新搜索设置。
   - `security`：刷新安全设置。
   - `update`：刷新更新设置。
5. 修复问号文案：
   - `能力总览`
   - `正在读取能力状态...`
   - `QQ 官方机器人`
   - `留空保持原值...`
   - `能力状态暂时不可用`

## 4. 服务器部署状态

已在服务器 BaiLongma 目录直接部署：

```text
/home/hermes/external/BaiLongma
```

部署前已备份到：

```text
/home/hermes/backups/bailongma-phase28-settings-state-20260609093538
```

服务已重启，`bailongma` 当前为 active。

## 5. 验证结果

已完成服务器侧验证：

```text
/home/hermes/.hermes/node/bin/node --check src/ui/brain-ui/app.js
/home/hermes/.hermes/node/bin/node --check src/ui/brain-ui/app-shell.js
systemctl restart bailongma
systemctl is-active bailongma
```

结果：

```text
active
```

源码检查确认：

- `activateSettingsTab` 已存在。
- `openSettings` 已收束到统一激活函数。
- 设置面板中文标签已恢复为可读文案。

## 6. GitHub 固化

本阶段已导出 BaiLongma overlay patch：

```text
patches/bailongma/phase-28-settings-tab-state-cleanup.patch
```

这个 patch 记录的是 MOXI 对白龙马前端的轻量适配，不把白龙马完整源码复制进本仓库，符合当前 upstream overlay 策略。

## 7. 下一步建议

下一阶段建议继续处理设置面板的信息架构：

1. 把“能力总览”从社交页拆到独立“能力状态”页，避免全局能力和渠道配置混在一起。
2. 给每个设置页加独立 loading / error 状态。
3. 为设置面板增加一个轻量前端 smoke test，验证点击每个 tab 后只有一个 `.settings-tab.active`。
4. 继续清理服务器前端中历史遗留的问号注释，避免后续维护误判。
