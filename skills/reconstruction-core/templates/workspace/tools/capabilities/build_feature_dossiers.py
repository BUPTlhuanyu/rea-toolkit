#!/usr/bin/env python3
"""为每个能力生成/刷新一份档案。

档案是“这个功能怎么还原出来的”稳定入口：

  capabilities/<feature-id>/README.md

自动生成段在 GENERATED 标记内，可重复刷新；标记外的人工笔记会保留。
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "capabilities"
START = "<!-- GENERATED:START -->"
END = "<!-- GENERATED:END -->"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def refs(items: list[str], limit: int = 30) -> str:
    if not items:
        return "- 无\n"
    lines = [f"- `{item}`" for item in items[:limit]]
    if len(items) > limit:
        lines.append(f"- … 共 {len(items)} 条，见 `capabilities/index.json`")
    return "\n".join(lines) + "\n"


def generated(cap: dict, cases: list[dict], generated_at: str) -> str:
    lines = [
        START,
        f"_Generated {generated_at} from `capabilities/index.json` and "
        "`capabilities/case-manifest.json`. Do not edit inside this block._",
        "",
        "## 判定",
        "",
        f"- source: `{cap['source']['status']}`",
        f"- effect: `{cap['effect']['status']}`",
        f"- completion: `{cap['completion']}`",
        f"- regression: `{cap.get('regressionStatus') or 'n/a'}`",
        f"- next: `{cap.get('nextState') or 'n/a'}`",
        "",
        "## Case",
        "",
    ]
    if cases:
        lines += [
            "| case | origin | mapping | effect | source | path |",
            "|---|---|---|---|---|---|",
        ]
        for case in cases:
            effect = case.get("effect", {}).get("status", "")
            source = case.get("source", {}).get("status", "")
            lines.append(
                f"| `{case['id']}` | {case.get('origin', '')} | {case.get('mapping', '')} | "
                f"{effect} | {source} | `{case.get('path', '')}` |"
            )
        lines.append("")
    else:
        lines += ["_No case mapped to this capability yet._", ""]

    lines += ["## 源码引用", "", refs(cap["source"].get("refs", []))]
    if cap["source"].get("verdict"):
        lines += ["", f"**Verdict:** {cap['source']['verdict']}"]
    if cap["source"].get("gap"):
        lines += ["", f"**Gap:** {cap['source']['gap']}"]
    lines += ["", "## 效果引用", "", refs(cap["effect"].get("refs", []))]
    if cap["effect"].get("verdict"):
        lines += ["", f"**Verdict:** {cap['effect']['verdict']}"]
    if cap.get("details"):
        lines += ["", "## 账本详情", "", cap["details"]]
    lines += ["", END, ""]
    return "\n".join(lines)


def main() -> int:
    index = load(CAP / "index.json")
    manifest = load(CAP / "case-manifest.json")
    by_cap: dict[str, list[dict]] = defaultdict(list)
    for case in manifest["cases"]:
        for cap_id in case.get("capabilities", []):
            by_cap[cap_id].append(case)

    generated_at = date.today().isoformat()
    for cap in index["capabilities"]:
        cap_id = cap["id"]
        path = CAP / cap_id / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        block = generated(cap, by_cap.get(cap_id, []), generated_at)
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if START in text and END in text:
                before, rest = text.split(START, 1)
                _, after = rest.split(END, 1)
                path.write_text(before + block + after, encoding="utf-8")
            else:
                path.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8")
        else:
            title = f"# {cap['name']} (`{cap_id}`)\n\n"
            facts = [
                f"- 分类: {cap.get('category') or '未分类'}",
                f"- 类型: `{cap.get('kind') or 'n/a'}`",
                f"- 标签/协议: {', '.join(f'`{tag}`' for tag in cap.get('tags', [])) or 'n/a'}",
                "",
            ]
            manual = (
                "## 人工笔记\n\n"
                "补这里（生成器不会改这段）：\n\n"
                "- Observed behavior:\n"
                "- Key source addresses / functions:\n"
                "- Key files changed:\n"
                "- Remaining gaps / next step:\n"
            )
            path.write_text(title + "\n".join(facts) + "\n" + block + "\n" + manual, encoding="utf-8")
        print(path.relative_to(ROOT))
    print(f"dossiers: {len(index['capabilities'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
