#!/usr/bin/env python3
"""Capture a macOS application window by window id.

这个工具从 WPS 截图脚本里抽出来，去掉了 WPS/图表常量。适用于任何 macOS
桌面程序（WPS、Office、自研应用）。

用法：
  python3 macos_window.py list --app wpsoffice
  python3 macos_window.py capture \
      --app /Applications/wpsoffice.app \
      --doc case.xlsx \
      --title case.xlsx \
      --size 1512x944 \
      --crop 78,432,1898,1500 \
      --resize 1820x1068 \
      --out case.wps.png

说明：
  - `list` 用同目录的 `list_windows.swift` 读取 CGWindowList，不需要辅助功能授权。
  - `capture` 用 `screencapture -l <window-id>` 抓窗口自身图层，不要求窗口在前台。
  - 需要「屏幕录制」授权。
  - `--close` 会在截图后用 ⌘W 关闭文档窗口。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
LIST_SCRIPT = HERE / "list_windows.swift"


def parse_size(value: str) -> tuple[int, int]:
    parts = [int(part) for part in value.lower().split("x")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("--size/--resize 必须是 WxH")
    return parts[0], parts[1]


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--crop 必须是 x0,y0,x1,y1")
    return tuple(parts)  # type: ignore[return-value]


def run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True)


def list_windows(app: str) -> list[dict]:
    result = run(["swift", str(LIST_SCRIPT), app])
    if result.returncode != 0:
        raise SystemExit(
            "读取窗口列表失败（需要屏幕录制授权）:\n"
            + (result.stderr or result.stdout)
        )
    windows: list[dict] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 4)
        if len(parts) < 5:
            continue
        try:
            windows.append(
                {
                    "id": parts[0].strip(),
                    "onscreen": parts[1].strip() == "1",
                    "width": int(parts[2]),
                    "height": int(parts[3]),
                    "title": parts[4].strip(),
                }
            )
        except ValueError:
            continue
    return windows


def find_window(app: str, title: str) -> dict | None:
    candidates = [
        window
        for window in list_windows(app)
        if title.lower() in window["title"].lower()
        and window["width"] > 200
        and window["height"] > 200
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda window: (
            window["onscreen"],
            window["width"] * window["height"],
        ),
    )


def applescript_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def resize_window(process: str, title: str, size: tuple[int, int]) -> None:
    width, height = size
    script = f'''
tell application "System Events"
  tell process {applescript_string(process)}
    set target to first window whose name contains {applescript_string(title)}
    perform action "AXRaise" of target
    delay 0.2
    set position of target to {{0, 0}}
    set size of target to {{{width}, {height}}}
  end tell
end tell
'''
    run(["osascript", "-e", script])


def close_window(process: str, title: str, timeout: float = 8.0) -> None:
    script = f'''
tell application "System Events"
  tell process {applescript_string(process)}
    perform action "AXRaise" of (first window whose name contains {applescript_string(title)})
    delay 0.3
    keystroke "w" using {{command down}}
  end tell
end tell
'''
    run(["osascript", "-e", script])
    deadline = time.time() + timeout
    while time.time() < deadline:
        if find_window(process, title) is None:
            return
        time.sleep(0.5)


def capture(args: argparse.Namespace) -> dict:
    if sys.platform != "darwin":
        raise SystemExit("macos_window.py 只支持 macOS")
    if shutil.which("screencapture") is None:
        raise SystemExit("找不到 screencapture")
    if not LIST_SCRIPT.exists():
        raise SystemExit(f"找不到 {LIST_SCRIPT}")

    doc = Path(args.doc).expanduser().resolve()
    title = args.title or doc.name
    raw = Path(args.raw) if args.raw else Path(args.out).with_suffix(".raw.png")
    raw.parent.mkdir(parents=True, exist_ok=True)

    deadline = time.time() + args.wait
    window = None
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        run(["open", "-g", "-a", args.app, str(doc)])
        time.sleep(args.first_delay if attempt == 1 else args.retry_delay)
        window = find_window(args.app, title)
        if window:
            break
    if not window:
        raise SystemExit(
            f"没有找到窗口: app={args.app!r} title~={title!r}\n"
            f"windows={list_windows(args.app)}"
        )

    if args.size:
        resize_window(args.process or args.app, title, args.size)
        time.sleep(1.5)
        window = find_window(args.app, title) or window

    shot = run(["screencapture", "-x", "-o", "-l", window["id"], str(raw)])
    if shot.returncode != 0 or not raw.exists() or raw.stat().st_size == 0:
        raise SystemExit(f"screencapture 失败: {shot.stderr}")
    raw_size = list(Image.open(raw).size)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(raw).convert("RGB")
    if args.crop:
        image = image.crop(args.crop)
    if args.resize:
        image = image.resize(args.resize, Image.LANCZOS)
    image.save(out)

    if args.close:
        try:
            close_window(args.process or args.app, title)
        except Exception as error:  # noqa: BLE001 - close is best effort
            print(f"close failed: {error}", file=sys.stderr)

    return {
        "app": args.app,
        "doc": str(doc),
        "title": title,
        "window": window,
        "raw": str(raw),
        "raw_size": raw_size,
        "out": str(out),
        "out_size": list(image.size),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="列出窗口")
    list_parser.add_argument("--app", required=True, help="App 名或路径的子串")
    list_parser.add_argument("--json", action="store_true")

    capture_parser = sub.add_parser("capture", help="打开文档并截图")
    capture_parser.add_argument("--app", required=True, help="App 名或 .app 路径")
    capture_parser.add_argument("--doc", required=True, help="要打开的文档/输入")
    capture_parser.add_argument("--title", default=None, help="窗口标题子串，默认文档名")
    capture_parser.add_argument("--process", default=None, help="System Events 进程名")
    capture_parser.add_argument("--size", type=parse_size, default=None, help="窗口尺寸 WxH")
    capture_parser.add_argument("--crop", type=parse_box, default=None)
    capture_parser.add_argument("--resize", type=parse_size, default=None)
    capture_parser.add_argument("--raw", default=None)
    capture_parser.add_argument("--out", required=True)
    capture_parser.add_argument("--wait", type=float, default=40)
    capture_parser.add_argument("--first-delay", type=float, default=5)
    capture_parser.add_argument("--retry-delay", type=float, default=7)
    capture_parser.add_argument("--close", action="store_true")
    capture_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.command == "list":
        windows = list_windows(args.app)
        if args.json:
            print(json.dumps(windows, ensure_ascii=False, indent=2))
        else:
            for window in windows:
                print(
                    f"{window['id']}\t{int(window['onscreen'])}\t"
                    f"{window['width']}\t{window['height']}\t{window['title']}"
                )
        return 0

    result = capture(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
