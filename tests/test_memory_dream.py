from __future__ import annotations

import unittest

from hermes_runtime.memory_dream import analyze_graph, render_markdown


def sample_graph() -> dict:
    return {
        "nodes": [
            {
                "id": "mem-1",
                "label": "图片测试识别 MOXI CORE OK",
                "type": "working",
            },
            {
                "id": "mem-2",
                "label": "主人希望每阶段写中文报告",
                "type": "working",
            },
            {
                "id": "mem-3",
                "label": "主人希望每阶段写中文报告",
                "type": "candidate",
            },
            {
                "id": "mem-4",
                "label": "credential secret should-not-be-kept",
                "type": "working",
            },
            {
                "id": "axis-owner",
                "label": "主人",
                "type": "axis",
            },
            {
                "id": "obsidian",
                "label": "Obsidian 正本",
                "type": "durable",
            },
        ],
        "links": [
            {"source": "mem-2", "target": "axis-owner"},
            {"source": "mem-3", "target": "axis-owner"},
            {"source": "mem-2", "target": "obsidian"},
        ],
    }


class MemoryDreamTests(unittest.TestCase):
    def test_memory_dream_detects_noise_sensitive_and_duplicates(self) -> None:
        analysis = analyze_graph(sample_graph())

        self.assertTrue(analysis.needs_dream)
        self.assertEqual([node.node_id for node in analysis.noise_candidates], ["mem-1"])
        self.assertEqual(
            [node.node_id for node in analysis.sensitive_candidates], ["mem-4"]
        )
        self.assertTrue(analysis.duplicate_groups)
        self.assertEqual(
            {node.node_id for node in analysis.duplicate_groups[0]}, {"mem-2", "mem-3"}
        )


    def test_memory_dream_report_is_non_destructive(self) -> None:
        analysis = analyze_graph(sample_graph())
        report = render_markdown(analysis, source="fixture")

        self.assertIn("记忆梦境整理报告", report)
        self.assertIn("本报告只做梦境分析，不自动删除白龙马记忆", report)
        self.assertIn("本报告不自动晋升任何记忆到 Obsidian", report)
        self.assertIn("[sensitive memory redacted]", report)
        self.assertNotIn("credential secret should-not-be-kept", report)


if __name__ == "__main__":
    unittest.main()
