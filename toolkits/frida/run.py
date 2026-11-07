#!/usr/bin/env python3
"""Spawn an executable with a Frida script and log send() payloads to JSONL.

用法：
  python3 run.py --exe /path/to/binary --script hook.js --log out.jsonl
  python3 run.py --exe /path/to/binary --script hook.js --log out.jsonl --seconds 60 --arg doc.bin

说明：
  - 需要 Python 环境安装 frida（版本与目标平台匹配）。
  - macOS 上如果 spawn 失败，尝试用系统 Python 或与 frida-server/协议匹配的版本。
"""

from __future__ import annotations

import argparse
import json
import time

import frida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--arg", action="append", default=[], help="传给目标的参数")
    args = parser.parse_args()

    device = frida.get_local_device()
    pid = device.spawn([args.exe] + args.arg)
    session = device.attach(pid)
    script = session.create_script(open(args.script, encoding="utf-8").read())
    with open(args.log, "a", encoding="utf-8") as log:
        def on_message(message, _data):
            log.write(json.dumps(message.get("payload", message)) + "\n")
            log.flush()

        script.on("message", on_message)
        script.load()
        device.resume(pid)
        print(f"spawned pid {pid}", flush=True)
        time.sleep(args.seconds)
    session.detach()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
