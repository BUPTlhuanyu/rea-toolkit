#!/usr/bin/env python3
"""生成能力账本和用例清单。

输入（只读）：
  - state.json                         # 能力账本 + backlog
  - capabilities/case-manifest.json    # 已有的 case 映射（人工维护优先）
  - corpus/**/case.json                # 可选的 case 声明文件
  - evidence/audit/*.json              # 可选的逐 case 判定（需显式 id）

输出：
  - capabilities/index.json            # 规范化能力表
  - capabilities/case-manifest.json    # 合并后的用例清单
  - capabilities/README.md             # 按分类列出的能力索引

用法：
  python3 tools/capabilities/build_capability_index.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAP_DIR = ROOT / "capabilities"
CORPUS = ROOT / "corpus"
MANIFEST = CAP_DIR / "case-manifest.json"


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def split_tags(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in re.split(r"[,，]", str(value)) if part.strip()]


def normalize_features(state: dict) -> list[dict]:
    """把 state.json#features 规范化为能力表。

    key 是唯一的语义 ID；没有 key 的条目会跳过并给出警告，交给校验器报错。
    """
    caps: list[dict] = []
    seen: Counter[str] = Counter()
    for raw in state.get("features", []):
        base = raw.get("key")
        if not base:
            print(
                f"WARN: feature without key skipped: {raw.get('featureName', '?')}",
                file=sys.stderr,
            )
            continue
        seen[base] += 1
        cap_id = base if seen[base] == 1 else f"{base}-{seen[base]}"
        source_status = raw.get("sourceStatus", "UNKNOWN")
        effect_status = raw.get("effectStatus", "PENDING")
        if source_status == "EXACT" and effect_status == "MATCH":
            completion = "complete"
        elif effect_status in ("MATCH", "ACCEPTED_NONPORTABLE"):
            completion = "effect-matched-source-partial"
        elif source_status == "EXACT":
            completion = "source-exact-effect-pending"
        else:
            completion = "partial"
        caps.append(
            {
                "id": cap_id,
                "name": raw.get("featureName", ""),
                "category": raw.get("category", ""),
                "kind": raw.get("kind", raw.get("chartType", "")),
                "tags": split_tags(raw.get("tags") or raw.get("ooxmlTag", "")),
                "completion": completion,
                "source": {
                    "status": source_status,
                    "verdict": raw.get("sourceVerdict"),
                    "gap": raw.get("sourceGap"),
                    "refs": raw.get("sourceRefs", []),
                },
                "effect": {
                    "status": effect_status,
                    "verdict": raw.get("effectVerdict"),
                    "refs": raw.get("effectImageRefs", []),
                },
                "cases": {
                    "refs": raw.get("caseRefs", []),
                    "verdicts": raw.get("caseVerdicts"),
                },
                "regressionStatus": raw.get("regressionStatus"),
                "nextState": raw.get("nextState"),
                "attempt": raw.get("attempt"),
                "lastChange": raw.get("lastChange"),
                "details": raw.get("details", ""),
                "flags": [k for k in ("backlogOnly",) if raw.get(k)],
            }
        )
    return caps


def normalize_backlog(state: dict) -> list[dict]:
    out = []
    for raw in state.get("backlog", []):
        if isinstance(raw, str):
            out.append(
                {
                    "id": raw,
                    "name": raw,
                    "tags": [],
                    "status": "UNKNOWN",
                    "note": "",
                }
            )
            continue
        out.append(
            {
                "id": raw.get("key", ""),
                "name": raw.get("featureName", raw.get("name", "")),
                "tags": split_tags(raw.get("tags") or raw.get("ooxmlTag", "")),
                "status": raw.get("status", "UNKNOWN"),
                "note": raw.get("note", ""),
            }
        )
    return out


def normalize_case(raw: dict, fallback_id: str, fallback_path: str = "") -> dict:
    capabilities = raw.get("capabilities") or []
    if isinstance(capabilities, str):
        capabilities = [capabilities]
    normalized = {
        "id": raw.get("id") or fallback_id,
        "origin": raw.get("origin", "derived"),
        "kind": raw.get("kind", "case"),
        "name": raw.get("name", raw.get("id") or fallback_id),
        "path": raw.get("path", fallback_path),
        "capabilities": sorted(set(capabilities)),
        "mapping": raw.get("mapping") or ("declared" if capabilities else "unmapped"),
        "effect": raw.get("effect", {}),
        "source": raw.get("source", {}),
        "files": raw.get("files"),
    }
    # 保留项目自定义字段（如 deck、xmlSignature、expected），避免重建时丢失。
    for key, value in raw.items():
        normalized.setdefault(key, value)
    return normalized


def discover_cases() -> list[dict]:
    """扫描 corpus/**/case.json。

    每个 case 目录放一个 case.json：
      { "id": "...", "origin": "provided|derived", "kind": "...",
        "capabilities": ["domain.feature"], "effect": {...}, "source": {...} }
    id / path 省略时按目录推导。
    """
    found: list[dict] = []
    if not CORPUS.is_dir():
        return found
    for descriptor in sorted(CORPUS.rglob("case.json")):
        try:
            data = json.loads(descriptor.read_text(encoding="utf-8"))
        except ValueError as error:
            print(f"WARN: invalid {descriptor}: {error}", file=sys.stderr)
            continue
        rel = descriptor.parent.relative_to(ROOT).as_posix()
        found.append(normalize_case(data, f"case:{rel}", rel))
    return found


def audit_cases() -> list[dict]:
    """读取 evidence/audit/*.json 里显式声明 id 的 case。"""
    found: list[dict] = []
    audit_dir = ROOT / "evidence" / "audit"
    if not audit_dir.is_dir():
        return found
    for path in sorted(audit_dir.glob("*.json")):
        data = load_json(path, {}) or {}
        for raw in data.get("cases", []):
            if not raw.get("id"):
                continue
            found.append(normalize_case({**raw, "mapping": raw.get("mapping", "audit")}, raw["id"]))
    return found


def merge_cases(existing: list[dict], discovered: list[dict]) -> list[dict]:
    """人工维护的 case-manifest 优先于自动发现。"""
    merged: dict[str, dict] = {}
    for case in [*discovered, *existing]:
        if not case.get("id"):
            print(
                f"WARN: case without id skipped: {case.get('path', '?')}",
                file=sys.stderr,
            )
            continue
        normalized = normalize_case(case, case["id"])
        merged[normalized["id"]] = normalized
    return sorted(merged.values(), key=lambda item: item["id"])


def main() -> None:
    state = load_json(ROOT / "state.json", {}) or {}
    caps = normalize_features(state)
    backlog = normalize_backlog(state)

    existing_manifest = load_json(MANIFEST, {}) or {}
    existing_cases = existing_manifest.get("cases", []) or []
    cases = merge_cases(existing_cases, [*discover_cases(), *audit_cases()])
    case_count = Counter(
        cap_id for case in cases for cap_id in case.get("capabilities", [])
    )

    summary = {
        "capabilities": len(caps),
        "complete": sum(c["completion"] == "complete" for c in caps),
        "effectMatchedSourcePartial": sum(
            c["completion"] == "effect-matched-source-partial" for c in caps
        ),
        "sourceExactEffectPending": sum(
            c["completion"] == "source-exact-effect-pending" for c in caps
        ),
        "partial": sum(c["completion"] == "partial" for c in caps),
        "sourceStatus": dict(Counter(c["source"]["status"] for c in caps)),
        "effectStatus": dict(Counter(c["effect"]["status"] for c in caps)),
        "categories": dict(Counter(c["category"] for c in caps)),
        "cases": {
            "total": len(cases),
            "provided": sum(c["origin"] == "provided" for c in cases),
            "derived": sum(c["origin"] == "derived" for c in cases),
            "mapped": sum(bool(c["capabilities"]) for c in cases),
            "unmapped": sum(not c["capabilities"] for c in cases),
        },
        "dossiers": {
            "total": len(caps),
            "noCase": sum(case_count[c["id"]] == 0 for c in caps),
            "noSourceRefs": sum(not c["source"]["refs"] for c in caps),
            "noEffectRefs": sum(not c["effect"]["refs"] for c in caps),
        },
        "backlog": len(backlog),
    }

    CAP_DIR.mkdir(parents=True, exist_ok=True)
    index = {
        "schemaVersion": 1,
        "generatedAt": date.today().isoformat(),
        "sources": [
            "state.json#features",
            "capabilities/case-manifest.json",
            "corpus/**/case.json",
            "evidence/audit/*.json",
        ],
        "summary": summary,
        "capabilities": caps,
        "backlog": backlog,
    }
    (CAP_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "schemaVersion": 1,
        "generatedAt": date.today().isoformat(),
        "mappingNote": (
            "case-manifest is merged from corpus/**/case.json, evidence/audit/*.json "
            "and the previous manifest. Existing manifest entries win by id."
        ),
        "summary": summary["cases"],
        "cases": cases,
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for cap in caps:
        by_cat[cap["category"]].append(cap)
    lines = [
        "# 能力账本",
        "",
        f"Generated {index['generatedAt']} from `state.json`, "
        "`corpus/**/case.json` and `capabilities/case-manifest.json` by "
        "`tools/capabilities/build_capability_index.py`.",
        "",
        "## 汇总",
        "",
        f"- capabilities: {summary['capabilities']}",
        f"- complete (source EXACT + effect MATCH): {summary['complete']}",
        f"- effect matched, source partial: {summary['effectMatchedSourcePartial']}",
        f"- source exact, effect pending: {summary['sourceExactEffectPending']}",
        f"- partial: {summary['partial']}",
        f"- backlog: {summary['backlog']}",
        f"- cases: {summary['cases']['total']} "
        f"({summary['cases']['provided']} provided, "
        f"{summary['cases']['derived']} derived; "
        f"{summary['cases']['unmapped']} unmapped)",
        f"- dossiers: {summary['dossiers']['total']} "
        f"(no case {summary['dossiers']['noCase']}, "
        f"no source refs {summary['dossiers']['noSourceRefs']}, "
        f"no effect refs {summary['dossiers']['noEffectRefs']})",
        "",
        "Source and effect are separate axes. `complete` means both axes are "
        "closed; a case can be effect-matched while its source is still PARTIAL.",
        "",
        "## 按分类列出能力",
        "",
    ]
    for cat in sorted(by_cat):
        lines.append(f"### {cat or '(未分类)'}")
        lines.append("")
        for cap in sorted(by_cat[cat], key=lambda c: c["id"]):
            lines.append(
                f"- [`{cap['id']}`]({cap['id']}/README.md) — {cap['name']} "
                f"(source {cap['source']['status']}, "
                f"effect {cap['effect']['status']})"
            )
        lines.append("")
    (CAP_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
