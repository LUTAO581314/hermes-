# Phase 01 中文报告：Hermes 运行基础

## 1. 阶段目标

本阶段目标是先让 Hermes 具备最小可运行基础，而不是一次性接入飞书、微信、搜索、图像、视频、交易和完整记忆系统。

这一阶段交付的是“能安全启动、能健康检查、能写日志、能部署到轻量 VPS 的基础服务”。

## 2. 已完成内容

- 新增 `hermes_runtime/` 最小运行时。
- 新增 `/health` 健康检查接口。
- 新增 `/ready` 就绪检查接口。
- 新增 `/version` 版本接口。
- 新增结构化 JSONL 日志。
- 新增 `.env.example`，只放占位符，不放真实密钥。
- 新增多模型 AI 网关配置占位，按 OpenAI-compatible 接入。
- 新增 `.gitignore`，避免 `.env`、日志、数据、缓存进入 Git。
- 新增 Dockerfile 和 docker-compose。
- 新增 VPS 安装、启动、停止、更新脚本。
- 新增 systemd 服务模板，支持没有 Docker 的轻量服务器。
- 新增本地单元测试。
- 新增 Phase 01 技术说明文档。
- 已在 VPS 上完成第一次安全模式部署验证。

## 3. 当前效果

当前 Hermes 可以作为轻量后端基础服务运行。

它现在可以做到：

- 回答健康检查。
- 回答就绪检查。
- 创建数据、日志、Obsidian vault 占位目录。
- 写入结构化日志。
- 通过 Docker Compose 部署。
- 通过 systemd 在无 Docker 的 VPS 上后台运行。
- 以安全模式启动。

远程 VPS 验证结果：

```text
部署目录：/opt/hermes-system
服务名称：hermes-runtime.service
运行用户：hermes
监听地址：127.0.0.1:8787
/health：ok
/ready：ready
日志文件：/opt/hermes-system/logs/hermes-runtime.jsonl
AI 网关：supermoxi
AI 密钥：只允许写入服务器 .env，不进入 GitHub
```

它现在还不能做到：

- 连接飞书真实应用。
- 连接微信。
- 调用 TrendRadar/SearXNG 搜索项目，或调用图像、语音、视频 API。
- 写入真实 Obsidian vault。
- 执行交易或任何高风险动作。

这些能力会在后续阶段逐个接入。

## 4. 架构或决策变化

Phase 1 把 Hermes 从纯文档计划推进到可运行服务骨架。

当前服务定位：

```text
Hermes Runtime
  -> health / ready / version
  -> logs
  -> env config
  -> future adapters
```

后续飞书、Obsidian、TrendRadar、Graphify、BaiLongma、MiroFish 都应该作为适配器或外部运行时接入，不直接挤进核心服务。

搜索层纠偏：

```text
搜索不是必须配置托管搜索服务密钥。
当前按外部项目运行时接入：
TrendRadar = 第一优先
SearXNG = 可选补充
```

## 5. 风险与边界

安全边界：

- 默认只监听 `127.0.0.1`。
- 不提交 `.env`。
- 不提交服务器密码、IP 对应的密钥信息或任何真实 token。
- 不开放公开 dashboard。
- 不启用微信个人号桥接。
- 不接券商 API。
- 不允许自动交易。
- 不允许外部项目自动修改生产提示词、记忆或配置。

当前主要风险：

- 当前只在服务器本机监听，暂未配置公网反向代理。
- 如果要公网访问，需要单独配置反向代理、域名、TLS 和认证。
- 飞书回调上线前还需要签名校验和权限最小化设计。

## 6. 需要主人确认的事项

后续进入 Phase 2 前，需要主人确认：

- 是否继续使用当前 VPS。
- 是否准备飞书应用凭据。
- 是否有域名。
- 是否需要先只做内网/本机访问，还是配置公网反向代理。
- Obsidian vault 最终放在服务器、NAS、OneDrive 还是本地同步目录。

## 7. 下一阶段计划

推荐下一步：

```text
Phase 2：飞书公司管理 MVP
```

如果主人暂时没有飞书凭据，可以先做：

```text
Phase 1.5：公网入口、反向代理、TLS、认证和健康监控
```

Phase 2 优先做：

- 飞书 app 配置。
- 飞书 bot smoke test。
- 项目、客户、销售、回款、日报、风险表结构。
- 早晨经营简报。
- 主人审批队列。

## 8. 记忆整理与清理结果

本阶段应进入长期记忆的内容：

- Hermes 已经有最小运行时骨架。
- Hermes 已经在 VPS 上以 systemd 安全模式运行。
- 默认安全模式开启。
- `.env` 不进入 Git。
- Feishu、微信、TrendRadar、Graphify、MiroFish 都是后续适配器，不是 Phase 1 核心。

不进入长期记忆的内容：

- 单次测试日志。
- 临时端口输出。
- 服务器登录敏感信息。
- Docker 构建缓存。

## 9. 风险复核结果

已复核：

- 本阶段没有提交真实密钥。
- 本阶段没有启用高风险动作。
- 本阶段没有接入交易。
- 本阶段没有启用微信个人号自动化。
- 本阶段没有复制外部候选项目源码。
- 远程服务只监听服务器本机地址，未直接暴露公网。

结论：

Phase 1 已完成第一版安全运行基础，可以进入飞书 MVP 或公网入口加固。
