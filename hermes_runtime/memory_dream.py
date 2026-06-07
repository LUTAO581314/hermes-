"""Memory dream analysis for BaiLongma runtime graph snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from typing import Any


NOISE_PATTERNS = (
    "api ok",
    "moxi core ok",
    "permission fixed",
    "health check",
    "config_ok",
    "asr_status",
    "hello world",
    "final local voice test",
    "smoke",
    "smoke-test",
    "setup test",
    "test output",
    "二维码",
    "扫码",
    "登录状态",
    "权限问题已永久解决",
)

SENSITIVE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|password|passwd|token|secret)\b"),
)

AXIS_WORDS = (
    "owner",
    "project",
    "person",
    "company",
    "decision",
    "goal",
    "risk",
    "report",
    "obsidian",
    "主人",
    "项目",
    "人物",
    "公司",
    "决策",
    "目标",
    "风险",
    "报告",
)


@dataclass(frozen=True)
class DreamNode:
    node_id: str
    label: str
    kind: str
    degree: int
    redacted: bool = False


@dataclass(frozen=True)
class DreamAnalysis:
    total_nodes: int
    total_links: int
    working_memory_count: int
    review_candidate_count: int
    durable_boundary_count: int
    noise_candidates: list[DreamNode]
    sensitive_candidates: list[DreamNode]
    duplicate_groups: list[list[DreamNode]]
    isolated_nodes: list[DreamNode]
    weak_axis_nodes: list[DreamNode]
    hub_nodes: list[DreamNode]

    @property
    def needs_dream(self) -> bool:
        return bool(
            self.noise_candidates
            or self.sensitive_candidates
            or self.duplicate_groups
            or self.weak_axis_nodes
        )


def analyze_graph(graph: dict[str, Any], max_items: int = 20) -> DreamAnalysis:
    nodes = _extract_nodes(graph)
    links = _extract_links(graph)
    degree = _degree_map(links)
    dream_nodes = [_to_dream_node(node, degree) for node in nodes]
    by_id = {node.node_id: node for node in dream_nodes}

    noise_candidates = [
        node for node in dream_nodes if _looks_noisy(node.label, node.kind)
    ][:max_items]
    sensitive_candidates = [
        DreamNode(node.node_id, _redacted_label(node.label), node.kind, node.degree, True)
        for node in dream_nodes
        if _looks_sensitive(node.label, node.kind)
    ][:max_items]
    duplicate_groups = _duplicate_groups(dream_nodes, max_items)
    isolated_nodes = [node for node in dream_nodes if node.degree == 0][:max_items]
    weak_axis_nodes = [
        node
        for node in dream_nodes
        if node.degree <= 1
        and not _is_axis_node(node)
        and not _is_durable_boundary(node)
        and node not in noise_candidates
    ][:max_items]
    hub_nodes = sorted(
        [node for node in dream_nodes if node.degree >= 8],
        key=lambda node: node.degree,
        reverse=True,
    )[:max_items]

    return DreamAnalysis(
        total_nodes=len(dream_nodes),
        total_links=len(links),
        working_memory_count=sum(_is_working_memory(node) for node in dream_nodes),
        review_candidate_count=sum(_is_review_candidate(node) for node in dream_nodes),
        durable_boundary_count=sum(_is_durable_boundary(node) for node in dream_nodes),
        noise_candidates=noise_candidates,
        sensitive_candidates=sensitive_candidates,
        duplicate_groups=duplicate_groups,
        isolated_nodes=[by_id[node.node_id] for node in isolated_nodes if node.node_id in by_id],
        weak_axis_nodes=weak_axis_nodes,
        hub_nodes=hub_nodes,
    )


def render_markdown(
    analysis: DreamAnalysis,
    *,
    source: str,
    created_at: str | None = None,
) -> str:
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    state = "需要做梦整理" if analysis.needs_dream else "暂未发现明显混乱"

    sections = [
        "# 记忆梦境整理报告",
        "",
        "## 1. 梦境摘要",
        "",
        f"- 来源：`{source}`",
        f"- 生成时间：`{created_at}`",
        f"- 状态：{state}",
        f"- 图谱规模：{analysis.total_nodes} 个节点 / {analysis.total_links} 条关系",
        f"- 工作记忆：{analysis.working_memory_count}",
        f"- 待审核候选：{analysis.review_candidate_count}",
        f"- Obsidian 正本边界：{analysis.durable_boundary_count}",
        "",
        "## 2. 混乱信号",
        "",
        _render_signal("疑似测试/临时噪音", analysis.noise_candidates),
        _render_signal("疑似敏感内容", analysis.sensitive_candidates),
        _render_duplicate_groups(analysis.duplicate_groups),
        _render_signal("孤立节点", analysis.isolated_nodes),
        _render_signal("关系轴不足节点", analysis.weak_axis_nodes),
        _render_signal("高连接中心节点", analysis.hub_nodes),
        "",
        "## 3. 梦境整理建议",
        "",
        "- `forget-candidate`：测试输出、状态检查、一次性故障语句、敏感误捕获，等待主人确认后删除或降级。",
        "- `merge-candidate`：语义重复的节点先合并摘要，再保留来源和最新时间。",
        "- `inbox-candidate`：有价值但关系不清的内容进入 Obsidian `00-Inbox/needs-review`。",
        "- `report-only`：运行事实、烟测结果和部署过程写入阶段中文报告，不进入长期记忆。",
        "- `promote-candidate`：稳定偏好、架构决策、项目事实、重复模式，才允许进入 Obsidian 正本。",
        "",
        "## 4. 安全边界",
        "",
        "- 本报告只做梦境分析，不自动删除白龙马记忆。",
        "- 本报告不自动晋升任何记忆到 Obsidian。",
        "- 涉及密钥、二维码、登录态、客户隐私、财务账户的信息必须先脱敏或删除。",
        "- 任何 `forget`、`merge`、`promote` 动作都需要主人确认或明确规则授权。",
        "",
    ]
    return "\n".join(sections)


def load_graph_json(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("memory graph payload must be a JSON object")
    return payload


def _extract_nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    raw_nodes = graph.get("nodes") or graph.get("memory_nodes") or []
    if not isinstance(raw_nodes, list):
        return []
    return [node for node in raw_nodes if isinstance(node, dict)]


def _extract_links(graph: dict[str, Any]) -> list[dict[str, Any]]:
    raw_links = graph.get("links") or graph.get("edges") or graph.get("relationships") or []
    if not isinstance(raw_links, list):
        return []
    return [link for link in raw_links if isinstance(link, dict)]


def _degree_map(links: list[dict[str, Any]]) -> Counter[str]:
    degree: Counter[str] = Counter()
    for link in links:
        source = _node_ref(link.get("source") or link.get("from"))
        target = _node_ref(link.get("target") or link.get("to"))
        if source:
            degree[source] += 1
        if target:
            degree[target] += 1
    return degree


def _node_ref(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("id") or value.get("node_id") or "")
    if value is None:
        return ""
    return str(value)


def _to_dream_node(node: dict[str, Any], degree: Counter[str]) -> DreamNode:
    node_id = str(node.get("id") or node.get("node_id") or node.get("key") or "")
    label = str(
        node.get("label")
        or node.get("title")
        or node.get("name")
        or node.get("content")
        or node.get("text")
        or node_id
    )
    kind = " ".join(
        str(node.get(key, ""))
        for key in ("type", "kind", "group", "status", "layer", "risk")
        if node.get(key)
    )
    return DreamNode(node_id=node_id, label=label, kind=kind, degree=degree[node_id])


def _looks_noisy(label: str, kind: str) -> bool:
    text = f"{label} {kind}".lower()
    return any(pattern.lower() in text for pattern in NOISE_PATTERNS) or any(
        word in text for word in ("noise", "cleanup", "garbage", "test")
    )


def _looks_sensitive(label: str, kind: str) -> bool:
    text = f"{label} {kind}"
    return any(pattern.search(text) for pattern in SENSITIVE_PATTERNS)


def _redacted_label(label: str) -> str:
    if re.search(r"(?i)\b(api[_-]?key|password|passwd|token|secret)\b", label):
        return "[sensitive memory redacted]"
    label = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "sk-***REDACTED***", label)
    label = re.sub(
        r"(?i)(api[_-]?key|password|passwd|token|secret)\s*[:=]\s*\S+",
        r"\1=***REDACTED***",
        label,
    )
    if len(label) > 120:
        return label[:117] + "..."
    return label


def _duplicate_groups(nodes: list[DreamNode], max_items: int) -> list[list[DreamNode]]:
    groups: defaultdict[str, list[DreamNode]] = defaultdict(list)
    for node in nodes:
        key = _normalize_label(node.label)
        if key:
            groups[key].append(node)
    duplicate_groups = [group for group in groups.values() if len(group) > 1]
    duplicate_groups.sort(key=len, reverse=True)
    return duplicate_groups[:max_items]


def _normalize_label(label: str) -> str:
    text = label.lower().strip()
    text = re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)
    return text[:80]


def _is_working_memory(node: DreamNode) -> bool:
    text = f"{node.label} {node.kind}".lower()
    return any(word in text for word in ("working", "runtime", "bailongma", "工作记忆", "运行时"))


def _is_review_candidate(node: DreamNode) -> bool:
    text = f"{node.label} {node.kind}".lower()
    return any(word in text for word in ("review", "candidate", "inbox", "待审核", "候选"))


def _is_durable_boundary(node: DreamNode) -> bool:
    text = f"{node.label} {node.kind}".lower()
    return any(word in text for word in ("obsidian", "durable", "source", "正本", "长期"))


def _is_axis_node(node: DreamNode) -> bool:
    text = f"{node.label} {node.kind}".lower()
    return any(word.lower() in text for word in AXIS_WORDS)


def _render_signal(title: str, nodes: list[DreamNode]) -> str:
    if not nodes:
        return f"### {title}\n\n未发现。\n"
    lines = [f"### {title}", ""]
    for node in nodes:
        label = node.label
        redacted = node.redacted or _looks_sensitive(node.label, node.kind)
        if redacted:
            label = _redacted_label(node.label)
        marker = "（已脱敏）" if redacted else ""
        lines.append(f"- `{node.node_id}` {label}{marker}；degree={node.degree}；kind=`{node.kind}`")
    lines.append("")
    return "\n".join(lines)


def _render_duplicate_groups(groups: list[list[DreamNode]]) -> str:
    if not groups:
        return "### 疑似重复记忆\n\n未发现。\n"
    lines = ["### 疑似重复记忆", ""]
    for index, group in enumerate(groups, start=1):
        labels = " / ".join(f"`{node.node_id}`" for node in group)
        lines.append(f"- 组 {index}: {labels}，建议合并后保留来源和最新时间。")
    lines.append("")
    return "\n".join(lines)
