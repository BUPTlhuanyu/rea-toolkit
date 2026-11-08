#!/usr/bin/env python3
"""基于 reconstruction-core 生成领域复刻工作区。

用法：
  python3 scaffold.py --domain wps-chart --root .
  python3 scaffold.py --domain unity-3d --root . --profile unity-game
  python3 scaffold.py --domain my-parser --root . \
      --source-root decompiled --reference-runtime "./run-ref.sh" \
      --target-runtime "npm run build" --comparison screenshot

生成：
  <root>/.comate/reconstruction-<domain>/
  <root>/.comate/reconstruction-<domain>.json
  <root>/.comate/reconstruction-<domain>/domain.md
  <root>/.comate/reconstruction-<domain>/profile.json   # profile 为 JSON 时
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TOOLKIT = SKILL_DIR.parents[1]
CORE_TEMPLATE = SKILL_DIR.parent / "reconstruction-core" / "templates" / "workspace"
DOMAIN_TEMPLATE = SKILL_DIR / "templates" / "domain.md"


def option(args: list[str], name: str, default: str | None = None) -> str | None:
    if name in args:
        index = args.index(name)
        if index + 1 < len(args):
            return args[index + 1]
    return default


def options(args: list[str], name: str) -> list[str]:
    out: list[str] = []
    for index, arg in enumerate(args):
        if arg == name and index + 1 < len(args):
            out.append(args[index + 1])
    return out


def profile_dirs(root: Path) -> list[Path]:
    env = os.environ.get("RECONSTRUCTION_PROFILES")
    candidates = [
        Path(env).expanduser() if env else None,
        SKILL_DIR.parent / "reconstruction-bootstrap" / "profiles",
        TOOLKIT / "profiles",
        SKILL_DIR.parent / "profiles",
        root / ".comate" / "profiles",
        root / "profiles",
        Path.cwd() / "profiles",
    ]
    return [path for path in candidates if path and path.is_dir()]


def resolve_profile(value: str, root: Path) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    candidates: list[Path] = []
    if path.is_absolute() or "/" in value:
        candidates += [path, root / value]
    else:
        candidates += [root / value, TOOLKIT / value]
        for directory in profile_dirs(root):
            candidates += [directory / value]
            if not path.suffix:
                candidates += [directory / f"{value}.json", directory / f"{value}.md"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise SystemExit(f"找不到 profile: {value}")


def yaml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def yaml_lines(value, indent: int = 0) -> list[str]:
    pad = "  " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(yaml_lines(item, indent + 1))
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(yaml_lines(item, indent + 1))
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
    else:
        lines.append(f"{pad}{yaml_scalar(value)}")
    return lines


def as_runtime(value, default_commands: list[str]) -> dict:
    if isinstance(value, dict):
        return {
            "commands": value.get("commands") or default_commands,
            "outputs": value.get("outputs") or [],
        }
    return {"commands": default_commands, "outputs": []}


def as_comparison(value) -> dict:
    if isinstance(value, dict):
        return value
    return {"method": str(value)}


def profile_to_markdown(
    profile: dict, domain: str, overrides: dict, workspace_rel: str
) -> str:
    source_roots = overrides["source_roots"]
    reference = as_runtime(
        profile.get("reference_runtime"), overrides["reference_commands"]
    )
    target = as_runtime(profile.get("target_runtime"), overrides["target_commands"])
    comparison = as_comparison(
        overrides.get("comparison")
        or profile.get("comparison")
        or "screenshot"
    )

    front = {
        "name": domain,
        "platform": profile.get("platform", "unknown"),
        "source_roots": source_roots,
        "reference_runtime": reference,
        "target_runtime": target,
        "comparison": comparison,
        "required_evidence": profile.get("required_evidence", {}),
        "acceptance_rules": profile.get(
            "acceptance_rules",
            {
                "require_source_exact": True,
                "require_effect_match": True,
                "allow_approximation_as_complete": False,
            },
        ),
        "verification_commands": profile.get(
            "verification_commands", target["commands"]
        ),
    }
    if profile.get("id_domains"):
        front["id_domains"] = profile["id_domains"]

    lines = ["---", *yaml_lines(front), "---", ""]
    lines += [
        f"# {profile.get('title', domain)}",
        "",
        profile.get("description", "领域配置由 `reconstruction-bootstrap` 生成。"),
        "",
        "## 机器配置",
        "",
        "- `profile.json`：本目录的机器可读版本，供工具检查和重新初始化使用。",
        "- 工具链检查：",
        "",
        "```bash",
        "python3 <toolkit>/skills/reconstruction-bootstrap/scripts/check_tools.py \\",
        f"  {workspace_rel}/profile.json",
        "```",
        "",
    ]

    toolchains = profile.get("toolchains") or []
    if toolchains:
        lines += ["## 工具链", ""]
        for tool in toolchains:
            tool_id = tool.get("id", "?")
            lines += [f"### `{tool_id}`", ""]
            if tool.get("purpose"):
                lines += [f"- 用途：{tool['purpose']}"]
            if tool.get("mcp_config"):
                lines += [f"- MCP 配置：`{tool['mcp_config']}`"]
            for key, label in (
                ("required_env", "必需环境变量"),
                ("required_files", "必需文件"),
                ("required_commands", "必需命令"),
                ("optional_commands", "可选命令"),
            ):
                values = tool.get(key) or []
                if values:
                    lines += [f"- {label}：" + "、".join(f"`{v}`" for v in values)]
            notes = tool.get("notes") or []
            if notes:
                lines += ["- 说明："]
                lines += [f"  - {note}" for note in notes]
            setup = tool.get("setup") or []
            if setup:
                lines += ["- 安装/配置："]
                lines += [f"  - {step}" for step in setup]
            lines += [""]

    lines += [
        "## 参考端与目标端",
        "",
        "- 参考端命令：",
        *[f"  - `{command}`" for command in reference["commands"]],
        "",
        "- 目标端命令：",
        *[f"  - `{command}`" for command in target["commands"]],
        "",
        f"- 对照方式：`{comparison.get('method', 'screenshot')}`",
    ]
    if comparison.get("metrics"):
        lines += [
            "- 指标：" + "、".join(f"`{m}`" for m in comparison["metrics"])
        ]
    if comparison.get("artifacts"):
        lines += [
            "- 产物：" + "、".join(f"`{a}`" for a in comparison["artifacts"])
        ]
    lines += [""]

    rules = profile.get("domain_rules") or []
    if rules:
        lines += ["## 领域规则", ""]
        lines += [f"- {rule}" for rule in rules]
        lines += [""]

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = sys.argv[1:]
    domain = option(args, "--domain")
    if not domain:
        print(
            "用法: scaffold.py --domain <名称> [--profile <名称|路径>] [--root <目录>]",
            file=sys.stderr,
        )
        return 1

    root = Path(option(args, "--root", ".") or ".").expanduser().resolve()
    workspace_rel = option(args, "--workspace", f".comate/reconstruction-{domain}")
    config_rel = option(args, "--config", f".comate/reconstruction-{domain}.json")
    workspace = (root / workspace_rel).resolve()
    config_path = (root / config_rel).resolve()

    if not CORE_TEMPLATE.exists():
        print(f"找不到 core 模板: {CORE_TEMPLATE}", file=sys.stderr)
        return 1
    if workspace.exists() and any(workspace.iterdir()):
        print(f"工作区已存在且非空: {workspace}", file=sys.stderr)
        return 2

    workspace.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(CORE_TEMPLATE, workspace, dirs_exist_ok=True)
    for name in ("PIPELINE.md", "README.md"):
        path = workspace / name
        if path.exists():
            text = path.read_text(encoding="utf-8").replace("<workspace>", workspace_rel)
            path.write_text(text, encoding="utf-8")

    profile_path = resolve_profile(option(args, "--profile") or "", root)
    profile: dict | None = None
    if profile_path and profile_path.suffix == ".json":
        profile = json.loads(profile_path.read_text(encoding="utf-8"))

    overrides = {
        "source_roots": options(args, "--source-root")
        or (profile or {}).get("source_roots")
        or ["<source-root>"],
        "reference_commands": options(args, "--reference-runtime")
        or ["<reference-command>"],
        "target_commands": options(args, "--target-runtime") or ["<target-command>"],
        "comparison": option(args, "--comparison"),
    }

    if profile is not None:
        domain_text = profile_to_markdown(profile, domain, overrides, workspace_rel)
        effective = dict(profile)
        effective["name"] = domain
        effective["source_roots"] = overrides["source_roots"]
        effective["reference_runtime"] = as_runtime(
            profile.get("reference_runtime"), overrides["reference_commands"]
        )
        effective["target_runtime"] = as_runtime(
            profile.get("target_runtime"), overrides["target_commands"]
        )
        effective["comparison"] = as_comparison(
            overrides.get("comparison")
            or profile.get("comparison")
            or "screenshot"
        )
        (workspace / "profile.json").write_text(
            json.dumps(effective, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    elif profile_path:
        domain_text = profile_path.read_text(encoding="utf-8")
        domain_text = domain_text.replace("<domain>", domain)
    else:
        domain_text = DOMAIN_TEMPLATE.read_text(encoding="utf-8")
        replacements = {
            "<domain>": domain,
            "<source-root>": overrides["source_roots"][0],
            "<reference-command>": overrides["reference_commands"][0],
            "<target-command>": overrides["target_commands"][0],
            "<comparison>": overrides.get("comparison") or "screenshot",
        }
        for old, new in replacements.items():
            domain_text = domain_text.replace(old, new)

    domain_path = workspace / "domain.md"
    domain_path.write_text(domain_text, encoding="utf-8")

    config = {
        "schemaVersion": 1,
        "domain": domain,
        "platform": (profile or {}).get("platform", "unknown"),
        "workspace": workspace_rel,
        "domainProfile": str(domain_path.relative_to(root)),
        "profileSource": str(profile_path) if profile_path else None,
        "profileData": "profile.json" if profile is not None else None,
        "projectRoot": ".",
        "createdBy": "reconstruction-scaffold",
        "createdAt": date.today().isoformat(),
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"SCAFFOLDED {workspace}")
    print(f"CONFIG {config_path}")
    print(f"DOMAIN {domain_path}")
    if profile is not None:
        print(f"PROFILE {workspace / 'profile.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
