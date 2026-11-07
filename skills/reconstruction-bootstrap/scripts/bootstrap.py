#!/usr/bin/env python3
"""用一条命令初始化复刻工作区。

负责：
  1. 解析 profile（JSON 优先，MD 兼容）
  2. 生成工作区（reconstruction-scaffold）
  3. 检查工具链（check_tools.py），可选修复 rea MCP 配置
  4. 确认工作区（ensure_workspace.py）
  5. 初始化能力账本并校验

用法：
  python3 bootstrap.py --domain wps-chart --root . --profile wps-chart
  python3 bootstrap.py --domain android-native --root . \
      --source-root decompiled --profile android-native
  python3 bootstrap.py --profile wps-chart --check-only
  python3 bootstrap.py --profile wps-chart --fix-mcp

退出码：
  0  完整成功
  1  初始化/账本失败
  2  工作区已生成，但工具链缺失
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TOOLKIT = SKILL_DIR.parents[1]
CORE = TOOLKIT / "skills" / "reconstruction-core"
SCAFFOLD = TOOLKIT / "skills" / "reconstruction-scaffold" / "scripts" / "scaffold.py"
ENSURE = CORE / "scripts" / "ensure_workspace.py"
CHECK = Path(__file__).resolve().parent / "check_tools.py"


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


def flag(args: list[str], name: str) -> bool:
    return name in args


def expand(value: str) -> str:
    return os.path.expanduser(os.path.expandvars(value))


def profile_dirs(root: Path) -> list[Path]:
    env = os.environ.get("RECONSTRUCTION_PROFILES")
    candidates = [
        Path(env).expanduser() if env else None,
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
    return None


def run(command: list[str], cwd: Path) -> tuple[int, str, str]:
    process = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )
    if process.stdout:
        print(process.stdout.rstrip())
    if process.stderr:
        print(process.stderr.rstrip(), file=sys.stderr)
    return process.returncode, process.stdout, process.stderr


def backup_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.name}.bak-{stamp}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.bak-{stamp}-{counter}")
        counter += 1
    return candidate


def deep_expand(value):
    if isinstance(value, str):
        return expand(value)
    if isinstance(value, list):
        return [deep_expand(item) for item in value]
    if isinstance(value, dict):
        return {key: deep_expand(item) for key, item in value.items()}
    return value


def has_unresolved(value) -> bool:
    if isinstance(value, str):
        return "${" in value
    if isinstance(value, list):
        return any(has_unresolved(item) for item in value)
    if isinstance(value, dict):
        return any(has_unresolved(item) for item in value.values())
    return False


def fix_mcp(profile: dict) -> None:
    """把 profile 里的 mcp_server 补进 MCP 配置；已存在时不覆盖。"""
    for tool in profile.get("toolchains", []):
        server = tool.get("mcp_server")
        config = tool.get("mcp_config")
        tool_id = tool.get("id")
        if not server or not config or not tool_id:
            continue
        path = Path(expand(config))
        data = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                print(f"MCP_CONFIG_INVALID {path}", file=sys.stderr)
                continue
        servers = data.setdefault("mcpServers", {})
        if tool_id in servers:
            print(f"MCP_CONFIG_PRESENT {path} mcpServers.{tool_id}")
            continue
        resolved = deep_expand(server)
        if has_unresolved(resolved):
            print(
                f"MCP_CONFIG_NEEDS_MANUAL {path} mcpServers.{tool_id}: "
                "存在未展开的 ${VAR}，请先在环境中设置对应变量",
                file=sys.stderr,
            )
            continue
        servers[tool_id] = resolved
        if path.exists():
            backup = backup_path(path)
            shutil.copy2(path, backup)
            print(f"MCP_CONFIG_BACKUP {backup}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print(f"MCP_CONFIG_UPDATED {path} mcpServers.{tool_id}")


def parse_toolchecks(output: str) -> list[dict]:
    checks: list[dict] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "TOOLCHECK":
            checks.append({"id": parts[1], "ok": parts[2] == "OK"})
    return checks


def main() -> int:
    args = sys.argv[1:]
    root = Path(option(args, "--root", ".") or ".").expanduser().resolve()
    profile_arg = option(args, "--profile") or option(args, "--domain") or ""
    profile_path = resolve_profile(profile_arg, root)
    check_only = flag(args, "--check-only")
    fix = flag(args, "--fix-mcp")

    if option(args, "--profile") and profile_path is None:
        print(f"PROFILE_NOT_FOUND {option(args, '--profile')}", file=sys.stderr)
        return 1

    if check_only:
        if not profile_path or profile_path.suffix != ".json":
            print(
                "CHECK_FAILED: --check-only 需要 JSON profile（--profile <name|path>）",
                file=sys.stderr,
            )
            return 1
        code, output, _ = run([sys.executable, str(CHECK), str(profile_path)], cwd=root)
        if code != 0 and fix:
            fix_mcp(json.loads(profile_path.read_text(encoding="utf-8")))
            code, output, _ = run([sys.executable, str(CHECK), str(profile_path)], cwd=root)
        return 0 if code == 0 else 2

    profile: dict | None = None
    if profile_path and profile_path.suffix == ".json":
        profile = json.loads(profile_path.read_text(encoding="utf-8"))

    domain = option(args, "--domain") or (profile or {}).get("name") or (
        profile_path.stem if profile_path else ""
    )
    if not domain:
        print(
            "用法: bootstrap.py --domain <名称> [--profile <名称|路径>] "
            "[--source-root <目录>] [--root <项目根>]",
            file=sys.stderr,
        )
        return 1

    workspace_rel = option(args, "--workspace", f".comate/reconstruction-{domain}")
    config_rel = option(args, "--config", f".comate/reconstruction-{domain}.json")
    workspace = (root / workspace_rel).resolve()
    config_path = (root / config_rel).resolve()

    if workspace.exists() and any(workspace.iterdir()):
        if (workspace / "state.json").exists():
            print(f"WORKSPACE_EXISTS {workspace}")
            if profile is not None and not (workspace / "profile.json").exists():
                (workspace / "profile.json").write_text(
                    json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                print(f"PROFILE_COPIED {workspace / 'profile.json'}")
        else:
            print(
                f"WORKSPACE_NOT_INITIALIZED {workspace}: 非空但没有 state.json；"
                "请换 --workspace 或先清理该目录",
                file=sys.stderr,
            )
            return 1
    else:
        command = [
            sys.executable,
            str(SCAFFOLD),
            "--domain",
            domain,
            "--root",
            str(root),
            "--workspace",
            workspace_rel,
            "--config",
            config_rel,
        ]
        if profile_path:
            command += ["--profile", str(profile_path)]
        for value in options(args, "--source-root"):
            command += ["--source-root", value]
        for value in options(args, "--reference-runtime"):
            command += ["--reference-runtime", value]
        for value in options(args, "--target-runtime"):
            command += ["--target-runtime", value]
        comparison = option(args, "--comparison")
        if comparison:
            command += ["--comparison", comparison]
        code, _, _ = run(command, cwd=root)
        if code != 0:
            print("BOOTSTRAP_FAILED scaffold", file=sys.stderr)
            return 1

    check_profile: Path | None = None
    if (workspace / "profile.json").exists():
        check_profile = workspace / "profile.json"
    elif profile_path and profile_path.suffix == ".json":
        check_profile = profile_path

    toolchecks: list[dict] = []
    tool_ok = True
    if check_profile is not None:
        code, output, _ = run([sys.executable, str(CHECK), str(check_profile)], cwd=root)
        if code != 0 and fix:
            fix_mcp(json.loads(check_profile.read_text(encoding="utf-8")))
            code, output, _ = run([sys.executable, str(CHECK), str(check_profile)], cwd=root)
        toolchecks = parse_toolchecks(output)
        tool_ok = code == 0
    else:
        print("TOOLCHECK none SKIPPED (profile 不是 JSON)")

    code, _, _ = run(
        [
            sys.executable,
            str(ENSURE),
            "--config",
            config_rel,
            "--workspace",
            workspace_rel,
        ],
        cwd=root,
    )
    if code != 0:
        print("BOOTSTRAP_FAILED ensure_workspace", file=sys.stderr)
        return 1

    ledger_ok = True
    for script in (
        "build_capability_index.py",
        "build_feature_dossiers.py",
        "validate_capability_ids.py",
    ):
        code, _, _ = run(
            [sys.executable, str(workspace / "tools" / "capabilities" / script)],
            cwd=workspace,
        )
        if code != 0:
            ledger_ok = False
            break

    summary = {"capabilities": 0, "cases": 0}
    index_path = workspace / "capabilities" / "index.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            summary["capabilities"] = index.get("summary", {}).get("capabilities", 0)
            summary["cases"] = index.get("summary", {}).get("cases", {}).get("total", 0)
        except ValueError:
            pass

    record = {
        "schemaVersion": 1,
        "domain": domain,
        "platform": (profile or {}).get("platform", "unknown"),
        "profile": str(profile_path) if profile_path else None,
        "workspace": str(workspace),
        "config": str(config_path),
        "initializedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "toolchains": toolchecks,
        "ledger": summary,
    }
    (workspace / "bootstrap.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print()
    print(f"WORKSPACE {workspace}")
    print(f"CONFIG {config_path}")
    print(f"DOMAIN_MD {workspace / 'domain.md'}")
    if check_profile is not None:
        print(f"PROFILE {check_profile}")
    print(f"LEDGER {summary['capabilities']} capabilities, {summary['cases']} cases")
    print("NEXT 阅读 PIPELINE.md，从 Stage 0 建第一个 feature 档案")

    if not ledger_ok:
        print("BOOTSTRAP_FAILED ledger", file=sys.stderr)
        return 1
    if not tool_ok:
        print("BOOTSTRAP_PARTIAL 工具链缺失；补齐后重新运行 --check-only", file=sys.stderr)
        return 2
    print("BOOTSTRAP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
