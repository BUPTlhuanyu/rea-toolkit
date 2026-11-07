#!/usr/bin/env python3
"""打印单个能力的紧凑摘要，避免把完整账本读进对话。

用法：
  python3 tools/capabilities/show_capability.py                 # 列出 ID
  python3 tools/capabilities/show_capability.py <feature-id>    # 单个功能
  python3 tools/capabilities/show_capability.py --grep <文本>   # 搜索名称/ID
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "capabilities"


def main() -> int:
    index = json.loads((CAP / "index.json").read_text(encoding="utf-8"))
    manifest = json.loads((CAP / "case-manifest.json").read_text(encoding="utf-8"))
    caps = index["capabilities"]

    args = sys.argv[1:]
    if not args:
        for cap in caps:
            print(f"{cap['id']}\t{cap['name']}\t"
                  f"{cap['source']['status']}/{cap['effect']['status']}")
        return 0

    if args[0] == "--grep":
        needle = " ".join(args[1:]).lower()
        for cap in caps:
            if needle in cap["id"].lower() or needle in cap["name"].lower():
                print(f"{cap['id']}\t{cap['name']}\t"
                      f"{cap['source']['status']}/{cap['effect']['status']}")
        return 0

    cap_id = args[0]
    cap = next((item for item in caps if item["id"] == cap_id), None)
    if cap is None:
        print(f"not found: {cap_id}", file=sys.stderr)
        return 1

    cases = [
        case for case in manifest["cases"]
        if cap_id in case.get("capabilities", [])
    ]
    print(f"# {cap['name']} ({cap['id']})")
    print(f"category: {cap.get('category') or '未分类'}")
    print(f"kind: {cap.get('kind') or 'n/a'}")
    print(f"tags: {', '.join(cap.get('tags', [])) or 'n/a'}")
    print(f"source: {cap['source']['status']}")
    print(f"effect: {cap['effect']['status']}")
    print(f"completion: {cap['completion']}")
    print(f"dossier: capabilities/{cap['id']}/README.md")
    print()
    print(f"cases ({len(cases)}):")
    for case in cases[:20]:
        print(f"  {case['id']}\t{case.get('origin','')}\t"
              f"{case.get('effect',{}).get('status','')}/"
              f"{case.get('source',{}).get('status','')}\t{case.get('path','')}")
    if len(cases) > 20:
        print(f"  ... {len(cases) - 20} more")
    print()
    print("source refs:")
    for ref in cap["source"].get("refs", [])[:8]:
        print(f"  {ref}")
    if len(cap["source"].get("refs", [])) > 8:
        print(f"  ... {len(cap['source']['refs']) - 8} more")
    print("effect refs:")
    for ref in cap["effect"].get("refs", [])[:8]:
        print(f"  {ref}")
    if len(cap["effect"].get("refs", [])) > 8:
        print(f"  ... {len(cap['effect']['refs']) - 8} more")
    if cap.get("details"):
        text = " ".join(cap["details"].split())
        print("details:")
        print(f"  {text[:600]}{'…' if len(text) > 600 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
