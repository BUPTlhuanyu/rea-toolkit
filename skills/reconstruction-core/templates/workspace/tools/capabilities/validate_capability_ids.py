#!/usr/bin/env python3
"""校验能力 ID、状态键和档案。

规则：
  - id: <domain>.<feature>[.<variant>]，点后使用小写 kebab
  - profile.json 声明 id_domains 时，第一段必须在白名单内
  - state.json 的 feature key 和 runScope.features 必须是语义 ID
  - 活跃账本里不能有旧 ext-NN ID
  - case-manifest 引用的 capability 必须存在
  - 每个 capability 必须有 capabilities/<id>/README.md

用法：
  python3 tools/capabilities/validate_capability_ids.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "capabilities"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9-]*)+$")


def load(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_domains() -> set[str]:
    """从 workspace/profile.json 或项目配置读取 id 白名单。"""
    profile = load(ROOT / "profile.json", {}) or {}
    domains = profile.get("id_domains")
    if domains:
        return set(domains)

    for config in sorted((ROOT.parent).glob("reconstruction*.json")):
        data = load(config, {}) or {}
        workspace = data.get("workspace")
        if workspace and (ROOT.parent.parent / workspace).resolve() != ROOT:
            continue
        profile_data = data.get("profileData")
        if not profile_data:
            continue
        candidate = (ROOT / profile_data).resolve()
        profile = load(candidate, {}) or {}
        if profile.get("id_domains"):
            return set(profile["id_domains"])
    return set()


def main() -> int:
    index = load(CAP / "index.json")
    manifest = load(CAP / "case-manifest.json")
    state = load(ROOT / "state.json", {}) or {}
    if index is None or manifest is None:
        print(
            "FAILED: capabilities/index.json or case-manifest.json missing; "
            "run build_capability_index.py first",
            file=sys.stderr,
        )
        return 1

    domains = load_domains()
    ids = [cap["id"] for cap in index.get("capabilities", [])]
    errors: list[str] = []

    for cap_id in ids:
        if not ID_RE.match(cap_id):
            errors.append(f"bad id format: {cap_id}")
            continue
        if cap_id.startswith("ext-"):
            errors.append(f"legacy batch id in active ledger: {cap_id}")
        if domains and cap_id.split(".", 1)[0] not in domains:
            errors.append(f"unknown domain: {cap_id}")

    if len(ids) != len(set(ids)):
        errors.append("duplicate capability ids")

    active = set(ids)
    for feature in state.get("features", []):
        key = feature.get("key")
        if not key:
            errors.append(
                f"state feature without key: {feature.get('featureName', '?')}"
            )
        elif not ID_RE.match(key):
            errors.append(f"state feature key is not semantic: {key}")
        elif domains and key.split(".", 1)[0] not in domains:
            errors.append(f"state feature key has unknown domain: {key}")
        elif key not in active:
            errors.append(f"state feature key missing from index: {key}")

    for key in state.get("runScope", {}).get("features", []):
        if key not in active:
            errors.append(f"runScope feature missing from index: {key}")

    for case in manifest.get("cases", []):
        for cap_id in case.get("capabilities", []):
            if cap_id not in active:
                errors.append(f"case {case['id']} references unknown capability {cap_id}")

    for cap_id in ids:
        if not (CAP / cap_id / "README.md").exists():
            errors.append(f"missing dossier: {cap_id}")

    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for error in errors[:80]:
            print(" -", error)
        return 1
    print(f"OK: {len(ids)} capabilities, {len(manifest.get('cases', []))} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
