#!/usr/bin/env python3
"""Stack a reference and a target image into one comparison image, with MAE.

用法：
  python3 make_compare.py --reference wps.png --target ts.png --out cmp.png
  python3 make_compare.py --reference a.png --target b.png --out cmp.png \
      --labels WPS,TS --layout horizontal --mae

输出 JSON：
  {"out": "...", "mae": 1.23, "size": [w,h], "reference": "...", "target": "..."}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

TOOLKITS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLKITS))
from metrics.focus import focus_metrics  # noqa: E402


def parse_labels(value: str) -> tuple[str, str]:
    parts = [part.strip() for part in value.split(",", 1)]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("--labels 必须是 reference,target")
    return parts[0], parts[1]


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--crop-reference 必须是 x0,y0,x1,y1")
    return tuple(parts)  # type: ignore[return-value]


def mae(reference: Image.Image, target: Image.Image) -> float:
    a = np.asarray(reference.convert("RGB")).astype(int)
    b = np.asarray(target.convert("RGB")).astype(int)
    if a.shape != b.shape:
        b = np.asarray(
            target.convert("RGB").resize(reference.size, Image.LANCZOS)
        ).astype(int)
    return round(float(np.abs(a - b).mean()), 3)


def fit_width(image: Image.Image, width: int) -> Image.Image:
    if image.width == width:
        return image
    height = max(1, round(image.height * width / image.width))
    return image.resize((width, height), Image.LANCZOS)


def stack(
    reference: Image.Image,
    target: Image.Image,
    label_reference: str,
    label_target: str,
    layout: str = "vertical",
    pad: int = 8,
    bar: int = 26,
    background: str = "white",
) -> Image.Image:
    if layout == "horizontal":
        width = max(reference.width, target.width)
        reference = fit_width(reference, width)
        target = fit_width(target, width)
        height = max(reference.height, target.height)
        out = Image.new("RGB", (width * 2 + pad, bar + height), background)
        draw = ImageDraw.Draw(out)
        draw.text((6, 6), label_reference, fill=(180, 0, 0))
        draw.text((width + pad + 6, 6), label_target, fill=(0, 0, 160))
        out.paste(reference, (0, bar))
        out.paste(target, (width + pad, bar))
        return out

    width = max(reference.width, target.width)
    reference = fit_width(reference, width)
    target = fit_width(target, width)
    height = bar + reference.height + pad + bar + target.height + pad
    out = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(out)
    draw.text((6, 6), label_reference, fill=(180, 0, 0))
    out.paste(reference, (0, bar))
    y = bar + reference.height + pad
    draw.text((6, y + 4), label_target, fill=(0, 0, 160))
    out.paste(target, (0, y + bar))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--labels", type=parse_labels, default=("REFERENCE", "TARGET"))
    parser.add_argument("--layout", choices=("vertical", "horizontal"), default="vertical")
    parser.add_argument("--crop-reference", type=parse_box, default=None)
    parser.add_argument("--pad", type=int, default=8)
    parser.add_argument("--bar", type=int, default=26)
    parser.add_argument("--background", default="white")
    parser.add_argument("--mae", dest="mae", action="store_true", default=True,
                        help="计算 MAE（默认）")
    parser.add_argument("--no-mae", dest="mae", action="store_false")
    parser.add_argument("--focus", dest="focus", action="store_true", default=True,
                        help="计算 focus 指标（默认）")
    parser.add_argument("--no-focus", dest="focus", action="store_false",
                        help="只输出旧版 MAE")
    parser.add_argument("--block", type=int, default=32,
                        help="block 指标的分块大小")
    parser.add_argument("--focus-threshold", type=float, default=15.0,
                        help="block 分数超过该值计为 focus block")
    parser.add_argument("--edges", action="store_true", help="计算边缘结构差")
    parser.add_argument("--clusters", action="store_true", help="计算 CIELAB ΔE 局部簇")
    parser.add_argument("--crop-dir", default=None, help="ΔE 簇裁剪图输出目录")
    args = parser.parse_args()

    reference = Image.open(args.reference).convert("RGB")
    if args.crop_reference:
        reference = reference.crop(args.crop_reference)
    target = Image.open(args.target).convert("RGB")

    result = {
        "reference": args.reference,
        "target": args.target,
        "size": list(reference.size),
    }
    if args.focus:
        metrics = focus_metrics(
            np.asarray(reference).astype(np.int16),
            np.asarray(target).astype(np.int16),
            block=args.block,
            focus_threshold=args.focus_threshold,
            include_edges=args.edges,
            include_clusters=args.clusters,
            crop_dir=Path(args.crop_dir) if args.crop_dir else None,
        )
        if not args.mae:
            metrics.pop("mae", None)
        result.update(metrics)
    elif args.mae:
        result["mae"] = mae(reference, target)
    out_image = stack(
        reference,
        target,
        args.labels[0],
        args.labels[1],
        args.layout,
        args.pad,
        args.bar,
        args.background,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out_image.save(out)
    result["out"] = str(out)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
