# Vendor Runtime Integration

## Corrected Productization Decision

The product direction is mature-source-first, not blank-slate AI rewriting.
Hermes may directly use mature open-source runtime code when it helps the
product become more reliable and deployable.

The commercialization requirement is a quality bar:

- the product must be deployable, testable, observable, and maintainable;
- brand and customer-facing fields must default to `bairui`;
- licenses, notices, upstream names, and attribution must remain visible;
- GPL/AGPL runtimes can be used when the project accepts the corresponding
  public-source obligations or keeps them isolated as services;
- third-party runtime source belongs under `vendor/runtimes/` or an equally
  explicit boundary;
- our added value is productization: adapters, platform contract, deployment,
  license flow, readiness checks, audit, operations, and support workflow.

Do not replace mature working internals with AI-written blank-slate code just
to claim self-development. Prefer source-level control over source-level
reinvention.

本文档定义 Hermes 如何直接集成外部项目源码，同时保持商业产品边界。

## 1. 决策

为了更快交付产品，Hermes 可以直接集成外部运行时源码。

但集成方式必须是：

- `vendor/runtimes/` 子模块或独立 runtime；
- Hermes 自研代码在 `src/`；
- 通过 adapter、API、MCP、worker、进程边界调用；
- 保留外部项目许可证、来源、版本和替换能力；
- 不把外部项目代码复制进 Hermes core。

## 2. 当前集成

| 项目 | 路径 | 用途 | 许可证 |
| --- | --- | --- | --- |
| EverOS | `vendor/runtimes/everos` | 自动记忆提取、检索、候选事实 | Apache-2.0 |
| TrendRadar | `vendor/runtimes/trendradar` | 热点、趋势、RSS、舆情输入 | GPLv3 |
| MiroFish | `vendor/runtimes/mirofish` | 多 Agent 推演、场景模拟、报告 | AGPLv3 |
| SearXNG | Docker / Linux checkout | 可选元搜索 | AGPLv3 |

## 3. 商用边界

### Apache-2.0

EverOS 适合更深度集成，但仍应保留 NOTICE、LICENSE 和来源。

### GPLv3

TrendRadar 可以作为独立运行时使用。若分发包含它的产品包，必须遵守 GPLv3 的源代码提供义务。

### AGPLv3

MiroFish 和 SearXNG 属于更强 copyleft。若作为网络服务对客户提供，通常需要向网络用户提供对应源代码和修改。正式售卖前必须做许可证清单和交付说明。

本说明不是法律意见，正式合同和大规模商用前应做专业许可证审查。

## 4. Hermes Adapter 原则

Hermes adapter 负责：

- 启动或发现 runtime；
- 做健康检查；
- 发送请求；
- 标准化响应；
- 写审计；
- 处理超时和错误；
- 标注 capability 状态。

Runtime 负责自己的内部实现。

## 5. SearXNG 特殊说明

SearXNG 仓库包含 Windows 不兼容文件名，不能可靠 checkout 到当前 Windows 工作树。

当前策略：

- Windows 开发机不直接工作树集成；
- 服务器或 Linux 环境中用 Docker 运行；
- Hermes 只对接 SearXNG HTTP API；
- 源码来源记录为 `https://github.com/searxng/searxng`。

## 6. 下一步

下一步应在 `src/` 中实现：

- `src/hermes/config.py`
- `src/hermes/server.py`
- `src/hermes/capabilities.py`
- `src/hermes/adapters/everos.py`
- `src/hermes/adapters/trendradar.py`
- `src/hermes/adapters/mirofish.py`

并以测试确认：

- Hermes 可启动；
- `/health`、`/ready`、`/capabilities` 可用；
- vendor runtime 状态能显示为 `ready`、`missing_config`、`disabled` 或 `planned`。
