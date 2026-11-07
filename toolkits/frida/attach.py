#!/usr/bin/env python3
"""Attach a Frida script to a running process or launch a macOS app and attach.

用法：
  python3 attach.py --pid 1234 --script hook.js --log out.jsonl
  python3 attach.py --launch-app /Applications/Some.app --doc file.bin \
      --script hook.js --log out.jsonl

说明：
  - `--launch-app` 用 `open -n -g -a <app> <doc>` 启动，轮询新 pid 后 attach。
  - 默认从 app bundle 的 Contents/MacOS 下找可执行文件；可用 `--exe` 覆盖。
  - 需要 frida；GUI 应用需要相应权限。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path

import frida


def pids(exe: str) -> set[int]:
    out = subprocess.run(
        ["pgrep", "-f", f"^(/private)?{exe}"],
        capture_output=True,
        text=True,
    ).stdout
    return {int(pid) for pid in out.split() if pid.isdigit()}


def find_executable(app: str) -> str:
    macos = Path(app) / "Contents" / "MacOS"
    if macos.is_dir():
        for candidate in sorted(macos.iterdir()):
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, default=None)
    parser.add_argument("--launch-app", default=None)
    parser.add_argument("--doc", default=None)
    parser.add_argument("--exe", default=None, help="启动时用于匹配新 pid 的可执行文件")
    parser.add_argument("--script", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--launch-wait", type=float, default=30)
    args = parser.parse_args()

    start = time.time()
    if args.pid:
        pid = args.pid
    else:
        if not args.launch_app or not args.doc:
            raise SystemExit("需要 --pid 或 --launch-app + --doc")
        exe = args.exe or find_executable(args.launch_app)
        before = pids(exe)
        subprocess.Popen(["open", "-n", "-g", "-a", args.launch_app, args.doc])
        pid = None
        while time.time() - start < args.launch_wait and pid is None:
            new = pids(exe) - before
            pid = min(new) if new else None
            time.sleep(0.01)
        if pid is None:
            raise SystemExit(f"launch: 没有发现新进程 ({exe})")

    session = None
    while session is None:
        try:
            session = frida.get_local_device().attach(pid)
        except frida.ProcessNotRespondingError:
            if time.time() - start > args.launch_wait:
                raise
            time.sleep(0.05)

    script = session.create_script(open(args.script, encoding="utf-8").read())
    with open(args.log, "a", encoding="utf-8") as log:
        def on_message(message, _data):
            log.write(json.dumps(message.get("payload", message)) + "\n")
            log.flush()

        script.on("message", on_message)
        script.load()
        print(f"attached pid {pid} after {time.time() - start:.2f}s", flush=True)
        end = time.time() + args.seconds
        while time.time() < end:
            time.sleep(0.5)

    try:
        script.unload()
    except frida.InvalidOperationError:
        pass
    session.detach()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
