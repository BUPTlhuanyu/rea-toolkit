#!/usr/bin/env python3
"""Crop / resize an image.

用法：
  python3 crop.py in.png --box x0,y0,x1,y1 --out out.png
  python3 crop.py in.png --box 78,432,1898,1500 --resize 1820x1068 --out out.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--box 必须是 x0,y0,x1,y1")
    return tuple(parts)  # type: ignore[return-value]


def parse_size(value: str) -> tuple[int, int]:
    parts = [int(part) for part in value.lower().split("x")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("--resize 必须是 WxH")
    return parts[0], parts[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--box", type=parse_box, required=True,
                        help="x0,y0,x1,y1（原图像素）")
    parser.add_argument("--resize", type=parse_size, default=None,
                        help="裁剪后缩放，例如 1820x1068")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    image = Image.open(args.image).convert("RGB")
    x0, y0, x1, y1 = args.box
    if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
        raise SystemExit(
            f"crop box {args.box} 超出图像范围 {image.width}x{image.height}"
        )
    image = image.crop(args.box)
    if args.resize:
        image = image.resize(args.resize, Image.LANCZOS)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
