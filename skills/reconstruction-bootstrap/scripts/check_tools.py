#!/usr/bin/env python3
"""检查 domain profile 声明的工具链是否可用。

读取 JSON profile 的 toolchains，检查：
  - mcp_config 是否存在且对应 server 未禁用
  - required_env 是否在 MCP env 或当前环境中
  - required_files 是否存在（支持 ${ENV} 展开）
  - required_commands 是否在 PATH 中

用法：
  python3 check_tools.py profiles/wps-chart.json
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def expand(value: str, env: dict[str, str]) -> str:
    for key, val in env.items():
        value = value.replace(f"${{{key}}}", str(val))
    return os.path.expanduser(os.path.expandvars(value))


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: check_tools.py <profile.json>", file=sys.stderr)
        return 1
    profile_path = Path(sys.argv[1]).expanduser()
    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    failed = 0
    for tool in profile.get("toolchains", []):
        tool_id = tool.get("id", "?")
        missing: list[str] = []
        mcp_env: dict[str, str] = {}

        mcp_config = tool.get("mcp_config")
        if mcp_config:
            config_path = Path(expand(mcp_config, {})).expanduser()
            if not config_path.exists():
                missing.append(f"mcp_config 不存在: {config_path}")
            else:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                server = data.get("mcpServers", {}).get(tool_id, {})
                if not server:
                    missing.append(f"mcpServers.{tool_id} 不存在")
                if server.get("disabled"):
                    missing.append(f"mcpServers.{tool_id} 已禁用")
                mcp_env = server.get("env", {}) or {}
                command = server.get("command")
                if command:
                    expanded = expand(command, {**os.environ, **mcp_env})
                    if "/" in command or command.startswith("~"):
                        if not Path(expanded).exists():
                            missing.append(
                                f"mcpServers.{tool_id}.command 不存在: {expanded}"
                            )
                    elif shutil.which(command) is None:
                        missing.append(
                            f"mcpServers.{tool_id}.command 不在 PATH: {command}"
                        )

        for key in tool.get("required_env", []):
            if key not in mcp_env and not os.environ.get(key):
                missing.append(f"缺少环境变量: {key}")

        env = {**os.environ, **mcp_env}
        for pattern in tool.get("required_files", []):
            path = Path(expand(pattern, env)).expanduser()
            if not path.exists():
                missing.append(f"文件不存在: {path}")

        for command in tool.get("required_commands", []):
            if shutil.which(command) is None:
                missing.append(f"命令不在 PATH: {command}")

        if missing:
            failed += 1
            print(f"TOOLCHECK {tool_id} MISSING")
            for item in missing:
                print(f"  - {item}")
        else:
            print(f"TOOLCHECK {tool_id} OK")

    if failed:
        print(f"工具链检查失败: {failed} 项")
        return 2
    print("工具链检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
