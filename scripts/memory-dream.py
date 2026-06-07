#!/usr/bin/env python3
"""Generate a safe memory dream report from a BaiLongma graph JSON snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes_runtime.memory_dream import analyze_graph, load_graph_json, render_markdown


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a BaiLongma memory graph and write a dream report."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to memory graph JSON exported from /memory/graph.",
    )
    parser.add_argument(
        "--output",
        help="Markdown output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--source",
        default="/memory/graph",
        help="Human-readable source label for the report.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=20,
        help="Maximum items per signal section.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    graph = load_graph_json(input_path.read_text(encoding="utf-8-sig"))
    analysis = analyze_graph(graph, max_items=args.max_items)
    markdown = render_markdown(analysis, source=args.source)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
