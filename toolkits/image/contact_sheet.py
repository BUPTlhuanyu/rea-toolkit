#!/usr/bin/env python3
"""Tile images into a contact sheet.

用法：
  python3 contact_sheet.py --glob 'corpus/**/shots/*.wps.png' --out sheet.png
  python3 contact_sheet.py a.png b.png c.png --columns 2 --scale 0.5 --out sheet.png

默认按输入顺序排版，每格左上角写文件名。所有图会缩放到第一张图的尺寸；
用 `--tile WxH` 可以显式指定统一格子尺寸。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def parse_size(value: str) -> tuple[int, int]:
    parts = [int(part) for part in value.lower().split("x")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("--tile 必须是 WxH")
    return parts[0], parts[1]


def expand_inputs(args: argparse.Namespace) -> list[Path]:
    out: list[Path] = [Path(item) for item in args.inputs]
    for pattern in args.glob:
        out.extend(sorted(Path().glob(pattern)))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in out:
        resolved = path.resolve()
        if resolved not in seen and path.is_file():
            seen.add(resolved)
            unique.append(path)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", help="图片路径")
    parser.add_argument("--glob", action="append", default=[], help="相对当前目录的 glob")
    parser.add_argument("--out", required=True)
    parser.add_argument("--columns", type=int, default=2)
    parser.add_argument("--scale", type=float, default=0.5)
    parser.add_argument("--tile", type=parse_size, default=None)
    parser.add_argument("--label", action="store_true", default=True)
    parser.add_argument("--no-label", dest="label", action="store_false")
    args = parser.parse_args()

    paths = expand_inputs(args)
    if not paths:
        raise SystemExit("没有输入图片")
    if args.columns < 1:
        raise SystemExit("--columns 必须 >= 1")

    tiles: list[Image.Image] = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        if args.tile:
            size = args.tile
        else:
            size = (
                max(1, int(image.width * args.scale)),
                max(1, int(image.height * args.scale)),
            )
        image = image.resize(size, Image.LANCZOS)
        if args.label:
            draw = ImageDraw.Draw(image)
            draw.text((6, 6), path.name, fill=(200, 0, 200))
        tiles.append(image)

    width, height = tiles[0].size
    rows = (len(tiles) + args.columns - 1) // args.columns
    sheet = Image.new("RGB", (width * args.columns, height * rows), "white")
    for index, tile in enumerate(tiles):
        sheet.paste(tile, ((index % args.columns) * width, (index // args.columns) * height))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"{out} {len(tiles)} tiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
