#!/usr/bin/env python3
"""确保当前项目存在复刻工作区。

解析顺序：
  1. --workspace
  2. RECONSTRUCTION_WORKSPACE
  3. --config（默认 <project>/.comate/reconstruction.json）
  4. 已存在的 .comate/*/state.json + PIPELINE.md（迁移）
  5. .comate/reconstruction（新默认）

工作区不存在时，把 templates/workspace 复制过去并写项目配置。
已有非空工作区不会被覆盖。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "templates" / "workspace"
DEFAULT_CONFIG = ".comate/reconstruction.json"
DEFAULT_WORKSPACE = ".comate/reconstruction"


def find_project_root(start: Path) -> Path:
    env = os.environ.get("RECONSTRUCTION_PROJECT_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    # 项目配置优先；不要因为子目录有 .git 就提前停止。
    for parent in [start, *start.parents]:
        if (parent / ".comate" / "reconstruction.json").exists():
            return parent
    for parent in [start, *start.parents]:
        if any(
            (state.parent / "PIPELINE.md").exists()
            for state in (parent / ".comate").glob("*/state.json")
        ):
            return parent
    for parent in [start, *start.parents]:
        if (parent / ".comate").is_dir():
            return parent
    return start


def read_config(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise SystemExit(f"配置无效 {path}: {error}")


def existing_workspaces(root: Path) -> list[Path]:
    found: list[Path] = []
    for state in sorted((root / ".comate").glob("*/state.json")):
        workspace = state.parent
        if (workspace / "PIPELINE.md").exists():
            found.append(workspace)
    return found


def resolve_workspace(
    root: Path, cli: str | None, config_path: Path
) -> tuple[Path, str]:
    if cli:
        return (root / cli).resolve(), "cli"
    env = os.environ.get("RECONSTRUCTION_WORKSPACE")
    if env:
        return (root / env).resolve(), "env"
    config = read_config(config_path)
    if config and config.get("workspace"):
        return (root / config["workspace"]).resolve(), "config"
    candidates = existing_workspaces(root)
    if len(candidates) == 1:
        return candidates[0].resolve(), "existing"
    if len(candidates) > 1:
        return max(candidates, key=lambda p: (p / "state.json").stat().st_mtime).resolve(), "existing"
    return (root / DEFAULT_WORKSPACE).resolve(), "default"


def write_config(path: Path, root: Path, workspace: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        relative = workspace.relative_to(root)
    except ValueError:
        relative = workspace
    # 保留 scaffold 写入的 domain/profile 等字段，只补齐/修正工作区信息。
    data = read_config(path) or {}
    data.setdefault("schemaVersion", 1)
    data["workspace"] = str(relative)
    data.setdefault("projectRoot", ".")
    data.setdefault("createdBy", "reconstruction-core")
    data.setdefault("createdAt", date.today().isoformat())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def populate(workspace: Path, root: Path, force: bool = False) -> None:
    if not TEMPLATE.is_dir():
        raise SystemExit(f"找不到工作区模板: {TEMPLATE}")
    if workspace.exists() and any(workspace.iterdir()):
        if (workspace / "state.json").exists():
            return
        if not force:
            raise SystemExit(
                f"工作区 {workspace} 已存在但没有 state.json；"
                "拒绝覆盖（如果只是空脚手架，使用 --force）"
            )
        shutil.rmtree(workspace)
    workspace.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE, workspace, dirs_exist_ok=True)
    rel = workspace.relative_to(root) if workspace.is_relative_to(root) else workspace
    for name in ("PIPELINE.md", "README.md"):
        path = workspace / name
        if path.exists():
            text = path.read_text(encoding="utf-8").replace("<workspace>", str(rel))
            path.write_text(text, encoding="utf-8")


def main() -> int:
    args = sys.argv[1:]
    cli = None
    force = False
    config_arg = DEFAULT_CONFIG
    for index, arg in enumerate(args):
        if arg == "--workspace" and index + 1 < len(args):
            cli = args[index + 1]
        elif arg == "--config" and index + 1 < len(args):
            config_arg = args[index + 1]
        elif arg == "--force":
            force = True

    root = find_project_root(Path.cwd().resolve())
    config_path = (root / config_arg).resolve()
    workspace, _source = resolve_workspace(root, cli, config_path)
    existed = (workspace / "state.json").exists()
    populate(workspace, root, force=force)
    config = write_config(config_path, root, workspace)

    if existed:
        print(f"WORKSPACE_READY {workspace}")
    else:
        print(f"WORKSPACE_CREATED {workspace}")
    print(f"CONFIG {config}")
    print(f"PROJECT_ROOT {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
