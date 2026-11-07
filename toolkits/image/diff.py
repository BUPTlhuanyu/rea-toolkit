#!/usr/bin/env python3
"""Compare two images and mark differing pixels.

用法：
  python3 diff.py a.png b.png --out diff.png
  python3 diff.py a.png b.png --threshold 40 --json

输出 JSON：
  {"bbox": [x0,y0,x1,y1], "pixels": 123, "total": 100000, "ratio": 0.00123}

尺寸不一致时默认把 b 缩放到 a；`--on-size error` 改为报错。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference")
    parser.add_argument("target")
    parser.add_argument("--threshold", type=int, default=40)
    parser.add_argument("--out", default=None, help="差异标注图")
    parser.add_argument("--on-size", choices=("resize", "error"), default="resize")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    reference = Image.open(args.reference).convert("RGB")
    target = Image.open(args.target).convert("RGB")
    if reference.size != target.size:
        if args.on_size == "error":
            raise SystemExit(
                f"尺寸不一致: {reference.size} vs {target.size}"
            )
        target = target.resize(reference.size, Image.LANCZOS)

    diff = ImageChops.difference(reference, target).convert("L")
    diff = diff.point(lambda value: 255 if value > args.threshold else 0)
    pixels = sum(1 for value in diff.getdata() if value)
    total = reference.width * reference.height
    result = {
        "bbox": list(diff.getbbox()) if diff.getbbox() else None,
        "pixels": pixels,
        "total": total,
        "ratio": round(pixels / total, 6) if total else 0,
    }

    if args.out:
        marked = target.copy()
        marked.paste((255, 0, 255), mask=diff)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        marked.save(out)
        result["out"] = str(out)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(
            f"bbox={result['bbox']} pixels={pixels} "
            f"ratio={result['ratio']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
