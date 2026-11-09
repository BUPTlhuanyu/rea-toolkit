#!/usr/bin/env python3
"""Render a branch-coverage inventory as Mermaid + standalone HTML.

输入 inventory.json：

{
  "project": "wps-chart",
  "functions": [
    {
      "id": "pieBestFit",
      "address": "0xf5cfd0",
      "target": "src/layout/pie-bestfit.ts:42",
      "branches": [
        {
          "id": "b1",
          "condition": "count == 0",
          "source": "0xf5cff0",
          "target": "src/layout/pie-bestfit.ts:48",
          "true": "b2",
          "false": "b3",
          "status": "covered",
          "cases": ["pie/empty"],
          "note": ""
        }
      ]
    }
  ]
}

status: covered | partial | uncovered | unknown

用法：
  python3 branch_coverage.py branches.json --out-html coverage.html
  python3 branch_coverage.py branches.json --out-mermaid coverage.mmd
  python3 branch_coverage.py branches.json --markdown
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

STATUS_ORDER = ("covered", "partial", "uncovered", "unknown")
STATUS_LABEL = {
    "covered": "已覆盖",
    "partial": "部分覆盖",
    "uncovered": "未覆盖",
    "unknown": "未知",
}
STATUS_CLASS = {
    "covered": "covered",
    "partial": "partial",
    "uncovered": "uncovered",
    "unknown": "unknown",
}


def clean(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value)


def node_id(function_id: str, branch_id: str) -> str:
    return f"b_{clean(function_id)}_{clean(branch_id)}"


def terminal_id(function_id: str, target: str) -> str:
    return f"t_{clean(function_id)}_{clean(target)}"


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "functions" not in data:
        raise SystemExit("inventory.json 缺少 functions")
    return data


def summarize(inventory: dict) -> dict:
    counts = {status: 0 for status in STATUS_ORDER}
    total = 0
    functions = 0
    for function in inventory["functions"]:
        functions += 1
        for branch in function.get("branches", []):
            status = branch.get("status", "unknown")
            counts[status if status in counts else "unknown"] += 1
            total += 1
    covered = counts["covered"]
    return {
        "functions": functions,
        "branches": total,
        "covered": covered,
        "partial": counts["partial"],
        "uncovered": counts["uncovered"],
        "unknown": counts["unknown"],
        "branchCoverage": round(covered / total, 4) if total else 0.0,
    }


def mermaid(inventory: dict) -> str:
    lines = ["flowchart TD"]
    class_assignments: list[tuple[str, str]] = []

    for function in inventory["functions"]:
        fid = function["id"]
        branches = function.get("branches", [])
        branch_ids = {branch["id"] for branch in branches}
        header = f"{fid}"
        if function.get("address"):
            header += f" @{function['address']}"
        entry = f"entry_{clean(fid)}"
        lines.append(f'  {entry}["{header}"]')
        if branches:
            lines.append(f"  {entry} --> {node_id(fid, branches[0]['id'])}")

        for branch in branches:
            bid = branch["id"]
            condition = str(branch.get("condition", bid)).replace('"', "'")
            lines.append(f'  {node_id(fid, bid)}{{"{bid}: {condition}"}}')
            status = branch.get("status", "unknown")
            class_assignments.append((node_id(fid, bid), STATUS_CLASS.get(status, "unknown")))

            for edge, target_key in (("true", "true"), ("false", "false")):
                target = branch.get(target_key)
                if not target:
                    continue
                edge_cases = branch.get(f"{edge}Cases") or branch.get("cases", [])
                cases = ", ".join(edge_cases)
                label = edge + (f"<br/>{cases}" if cases else "")
                if target in branch_ids:
                    lines.append(
                        f"  {node_id(fid, bid)} -->|{label}| {node_id(fid, target)}"
                    )
                else:
                    lines.append(
                        f'  {node_id(fid, bid)} -->|{label}| {terminal_id(fid, target)}["{target}"]'
                    )

    lines += [
        "  classDef covered fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20",
        "  classDef partial fill:#fff9c4,stroke:#f9a825,color:#5d4037",
        "  classDef uncovered fill:#ffcdd2,stroke:#c62828,color:#b71c1c",
        "  classDef unknown fill:#e0e0e0,stroke:#616161,color:#212121",
    ]
    for target, klass in class_assignments:
        lines.append(f"  class {target} {klass}")
    return "\n".join(lines) + "\n"


def markdown(inventory: dict) -> str:
    summary = summarize(inventory)
    lines = [
        f"# Branch coverage: {inventory.get('project', '')}",
        "",
        f"- functions: {summary['functions']}",
        f"- branches: {summary['branches']}",
        f"- covered: {summary['covered']}",
        f"- partial: {summary['partial']}",
        f"- uncovered: {summary['uncovered']}",
        f"- unknown: {summary['unknown']}",
        f"- branch coverage: {summary['branchCoverage']:.1%}",
        "",
        "| function | address | branch | condition | status | cases | source | target |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for function in inventory["functions"]:
        for branch in function.get("branches", []):
            lines.append(
                "| {fn} | {addr} | {bid} | {cond} | {status} | {cases} | {source} | {target} |".format(
                    fn=function.get("id", ""),
                    addr=function.get("address", ""),
                    bid=branch.get("id", ""),
                    cond=str(branch.get("condition", "")).replace("|", "\\|"),
                    status=STATUS_LABEL.get(branch.get("status", "unknown"), "未知"),
                    cases=", ".join(branch.get("cases", [])),
                    source=branch.get("source", ""),
                    target=branch.get("target", ""),
                )
            )
    return "\n".join(lines) + "\n"


def html_report(inventory: dict, mermaid_text: str) -> str:
    summary = summarize(inventory)
    rows = []
    for function in inventory["functions"]:
        for branch in function.get("branches", []):
            status = branch.get("status", "unknown")
            rows.append(
                "<tr>"
                f"<td>{html.escape(function.get('id', ''))}</td>"
                f"<td><code>{html.escape(function.get('address', ''))}</code></td>"
                f"<td>{html.escape(branch.get('id', ''))}</td>"
                f"<td>{html.escape(str(branch.get('condition', '')))}</td>"
                f'<td><span class="status {STATUS_CLASS.get(status, "unknown")}">'
                f"{STATUS_LABEL.get(status, '未知')}</span></td>"
                f"<td>{html.escape(', '.join(branch.get('cases', [])))}</td>"
                f"<td><code>{html.escape(branch.get('source', ''))}</code></td>"
                f"<td><code>{html.escape(branch.get('target', ''))}</code></td>"
                "</tr>"
            )
    return f"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>Branch coverage</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; color: #222; }}
  h1 {{ font-size: 20px; }}
  .summary {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0; }}
  .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 10px 14px; min-width: 110px; }}
  .card b {{ display: block; font-size: 20px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th, td {{ border: 1px solid #e0e0e0; padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #f5f5f5; }}
  code {{ font-size: 12px; }}
  .status {{ padding: 2px 8px; border-radius: 10px; font-size: 12px; }}
  .covered {{ background: #c8e6c9; color: #1b5e20; }}
  .partial {{ background: #fff9c4; color: #5d4037; }}
  .uncovered {{ background: #ffcdd2; color: #b71c1c; }}
  .unknown {{ background: #e0e0e0; color: #212121; }}
  .mermaid {{ border: 1px solid #eee; border-radius: 8px; padding: 12px; overflow: auto; }}
</style>
<h1>Branch coverage: {html.escape(inventory.get('project', ''))}</h1>
<div class="summary">
  <div class="card">functions<b>{summary['functions']}</b></div>
  <div class="card">branches<b>{summary['branches']}</b></div>
  <div class="card">covered<b>{summary['covered']}</b></div>
  <div class="card">partial<b>{summary['partial']}</b></div>
  <div class="card">uncovered<b>{summary['uncovered']}</b></div>
  <div class="card">unknown<b>{summary['unknown']}</b></div>
  <div class="card">branch coverage<b>{summary['branchCoverage']:.1%}</b></div>
</div>
<div class="mermaid">
{mermaid_text}
</div>
<h2>Branches</h2>
<table>
<thead><tr><th>function</th><th>address</th><th>branch</th><th>condition</th><th>status</th><th>cases</th><th>source</th><th>target</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose' }});
</script>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory")
    parser.add_argument("--out-html", default=None)
    parser.add_argument("--out-mermaid", default=None)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    inventory = load(Path(args.inventory))
    diagram = mermaid(inventory)
    if args.out_mermaid:
        Path(args.out_mermaid).write_text(diagram, encoding="utf-8")
        print(f"MERMAID {args.out_mermaid}")
    if args.out_html:
        Path(args.out_html).write_text(html_report(inventory, diagram), encoding="utf-8")
        print(f"HTML {args.out_html}")
    if args.markdown:
        print(markdown(inventory))
    if not args.out_html and not args.out_mermaid and not args.markdown:
        print(diagram)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
