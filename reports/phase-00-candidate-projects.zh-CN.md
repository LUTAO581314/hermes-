# Phase 00 补充中文报告：外部候选项目评估

## 1. 阶段目标

主人提供了 4 个外部项目：

- `github.com/sansan0/TrendRadar`
- `github.com/EvoMap/evolver`
- `github.com/safishamsi/graphify`
- `github.com/alchaincyf/nuwa-skill`

本报告判断它们对当前 Hermes 个人与公司 Agent 系统有没有用，以及应该放到哪个阶段、哪个架构层。

## 2. 总体结论

四个项目都有参考价值，但不能都直接接进核心。

推荐排序：

```text
第一优先：TrendRadar
第二优先：Graphify
第三优先：Nuwa Skill
第四优先：Evolver
```

最适合当前系统的是：

- TrendRadar：补搜索和趋势雷达。
- Graphify：补知识图谱和可视化记忆。
- Nuwa：补智囊团和技能蒸馏方法。
- Evolver：后期再研究，暂不进核心。

## 3. TrendRadar

仓库：

https://github.com/sansan0/TrendRadar

### 3.1 它是什么

TrendRadar 是热点新闻、RSS、趋势追踪、AI 分析和多渠道推送工具。

它有：

- 热点聚合。
- RSS。
- 趋势追踪。
- AI 分析。
- MCP 支持。
- Docker 支持。
- 飞书、企业微信、Telegram、邮件等推送方向。

### 3.2 对我们有没有用

非常有用。

它可以成为系统的“趋势雷达”和“热点搜索层”。

适合做：

- AI 行业热点。
- 市场热点。
- 竞品动态。
- 项目机会。
- 公司经营情报。
- 每日/每周趋势报告。

### 3.3 放在架构哪里

```text
TrendRadar
  -> Hermes 调度
  -> Obsidian 趋势报告
  -> 飞书经营简报
```

### 3.4 风险边界

它是 GPL-3.0 项目，不能把源码直接拷进我们的核心仓库。

正确方式：

```text
作为外部运行时
通过 MCP / HTTP / CLI / 报告文件接入
```

不要复制它的源码、提示词或内部实现到本仓库。

### 3.5 结论

建议接入，优先级高。

## 4. Graphify

仓库：

https://github.com/safishamsi/graphify

### 4.1 它是什么

Graphify 可以把代码、文档、PDF、图片、视频、URL 转成可查询知识图谱。

它有：

- 图谱 JSON。
- HTML 可视化图。
- 图谱报告。
- 查询、路径、解释命令。
- MCP stdio 支持。
- Obsidian/知识图谱方向能力。
- Codex 和 Hermes 支持说明。

### 4.2 对我们有没有用

非常有用。

它可以补强两个方向：

1. 代码和文档理解。
2. Obsidian 记忆图谱可视化。

主人之前担心记忆太乱，Graphify 可以辅助发现：

- 哪些记忆孤立。
- 哪些节点变成垃圾中心。
- 哪些项目、客户、风险、报告关系紧密。
- 哪些文档应该补链接。

### 4.3 放在架构哪里

```text
Graphify
  -> Obsidian/文档/代码图谱
  -> Hermes 查询
  -> 记忆治理
  -> 阶段复盘
```

### 4.4 风险边界

Graphify 是 MIT 许可，集成边界更宽松。

但仍建议作为工具调用，而不是复制源码。

还要注意：

- `graphify-out/` 可能很大。
- 不能把所有图谱输出都当长期记忆。
- 只保留有用报告和选定图谱。

### 4.5 结论

建议接入，优先级高。

## 5. Nuwa Skill

仓库：

https://github.com/alchaincyf/nuwa-skill

### 5.1 它是什么

Nuwa Skill 是“蒸馏人物或主题思维方式”的 Agent Skill。

它不是普通角色扮演，而是提取：

- 心智模型。
- 决策启发式。
- 表达 DNA。
- 价值观。
- 反模式。
- 诚实边界。

### 5.2 对我们有没有用

有用，但不是基础设施。

它更适合做：

- 主人的智囊团。
- 投资/产品/运营顾问视角。
- MiroFish 推演角色。
- BaiLongma 的人格/思维扩展。
- 技能生成方法论。

例如：

```text
芒格视角：投资和风险
张一鸣视角：组织和产品
费曼视角：学习和解释
马斯克视角：工程和成本
```

### 5.3 放在架构哪里

```text
Nuwa Skill
  -> Advisory skill layer
  -> BaiLongma / MiroFish / Hermes 调用
  -> 决策建议
```

### 5.4 风险边界

它是 MIT 许可。

但要注意：

- 人物 Skill 是视角，不是事实来源。
- 智囊建议不能直接变成公司决策。
- 所有高风险决策还是主人确认。

### 5.5 结论

建议作为后期智囊层接入，优先级中等。

## 6. Evolver

仓库：

https://github.com/EvoMap/evolver

### 6.1 它是什么

Evolver 是 Agent 自进化引擎，偏向分析运行历史、生成改进建议、维护进化资产。

它强调：

- 自进化。
- Genes / Capsules。
- GEP 协议。
- review mode。
- loop mode。
- 审计轨迹。

### 6.2 对我们有没有用

有研究价值，但暂时不适合进核心。

原因：

- 当前系统还没上线，先接自进化会太早。
- 它涉及自动改进、循环和外部 hub，风险更高。
- README 显示 GPL-3.0，并提到未来 source-available 转向，需要谨慎。

### 6.3 放在架构哪里

后期可以作为：

```text
Phase 10+
外部实验性复盘工具
  -> 分析阶段报告
  -> 生成改进建议
  -> 主人确认后手动采纳
```

### 6.4 风险边界

暂不允许：

- 自动修改核心提示词。
- 自动修改记忆。
- 自动修改生产配置。
- 常驻自进化循环接入生产系统。

### 6.5 结论

先研究，后期再评估，不进入第一阶段或核心架构。

## 7. 更新后的推荐架构

```text
TrendRadar = 外部趋势雷达
Graphify = 知识图谱和记忆可视化工具
Nuwa Skill = 智囊团和技能蒸馏方法
Evolver = 后期实验性自进化评估器
```

对应进入路线：

```text
Phase 3：Graphify 记忆图谱实验
Phase 4/6：TrendRadar 趋势情报接入
Phase 7/9：Nuwa Skill 智囊/推演角色
Phase 10+：Evolver 外部复盘实验
```

## 8. 最终建议

主人这几个项目里，最应该优先用的是：

1. TrendRadar：让系统有真正的外部热点和趋势雷达。
2. Graphify：让记忆和代码/文档关系可视化。

Nuwa Skill 很适合让系统变聪明，但不急着接进基础设施。

Evolver 很有野心，但应该等系统稳定后再做隔离实验，不能一开始就让它进入核心。
