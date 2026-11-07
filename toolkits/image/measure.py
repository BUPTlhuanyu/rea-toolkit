#!/usr/bin/env python3
"""Generic image measurement: connected components, text/line boxes, ink runs.

用法：
  python3 measure.py image.png --box 0,0,1600,1200 --mode components
  python3 measure.py image.png --box 0,0,1600,1200 --mode lines --json
  python3 measure.py image.png --mode ink --axis rows

输出：
  components: [{x0,y0,x1,y1,pixels,cx,cy,w,h}, ...]
  lines:      [{x0,y0,x1,y1,pixels}, ...]（把相邻 component 合并成行）
  ink:        [[start,end], ...]

依赖：Pillow、numpy。
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


def load_rgb(path: str | Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int16)


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--box 必须是 x0,y0,x1,y1")
    return tuple(parts)  # type: ignore[return-value]


def components(
    image: np.ndarray,
    box: tuple[int, int, int, int] | None = None,
    threshold: int = 140,
    min_pixels: int = 5,
) -> list[dict]:
    """Dark-pixel connected components inside box (8-neighbour)."""
    height, width = image.shape[:2]
    x0, y0, x1, y1 = box or (0, 0, width, height)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)
    sub = image[y0:y1, x0:x1]
    mask = (
        (sub[:, :, 0] < threshold)
        & (sub[:, :, 1] < threshold)
        & (sub[:, :, 2] < threshold)
    )
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    out: list[dict] = []
    for yy in range(h):
        for xx in range(w):
            if not mask[yy, xx] or seen[yy, xx]:
                continue
            queue = deque([(yy, xx)])
            seen[yy, xx] = True
            ys: list[int] = []
            xs: list[int] = []
            while queue:
                cy, cx = queue.popleft()
                ys.append(cy)
                xs.append(cx)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
            if len(xs) < min_pixels:
                continue
            out.append(
                {
                    "x0": x0 + min(xs),
                    "y0": y0 + min(ys),
                    "x1": x0 + max(xs),
                    "y1": y0 + max(ys),
                    "pixels": len(xs),
                    "cx": round(x0 + float(np.mean(xs)), 2),
                    "cy": round(y0 + float(np.mean(ys)), 2),
                    "w": max(xs) - min(xs) + 1,
                    "h": max(ys) - min(ys) + 1,
                }
            )
    return sorted(out, key=lambda item: (item["y0"], item["x0"]))


def merge_lines(components_list: list[dict], y_gap: int = 3, x_gap: int = 14) -> list[dict]:
    """Merge components that sit on the same horizontal band."""
    lines: list[dict] = []
    for comp in sorted(components_list, key=lambda item: (round(item["y0"] / 8), item["x0"])):
        placed = False
        for line in lines:
            same_band = not (
                comp["y1"] < line["y0"] - y_gap or comp["y0"] > line["y1"] + y_gap
            )
            near = comp["x0"] - line["x1"] <= x_gap and comp["x0"] >= line["x0"] - x_gap
            if same_band and near:
                line["x0"] = min(line["x0"], comp["x0"])
                line["y0"] = min(line["y0"], comp["y0"])
                line["x1"] = max(line["x1"], comp["x1"])
                line["y1"] = max(line["y1"], comp["y1"])
                line["pixels"] += comp["pixels"]
                placed = True
                break
        if not placed:
            lines.append(
                {
                    "x0": comp["x0"],
                    "y0": comp["y0"],
                    "x1": comp["x1"],
                    "y1": comp["y1"],
                    "pixels": comp["pixels"],
                }
            )
    return sorted(lines, key=lambda item: (item["y0"], item["x0"]))


def runs(mask: np.ndarray, min_length: int = 1) -> list[list[int]]:
    """Return [start, end] runs of True values in a 1-D mask."""
    out: list[list[int]] = []
    start: int | None = None
    for index, value in enumerate(mask):
        if value and start is None:
            start = index
        elif not value and start is not None:
            if index - start >= min_length:
                out.append([start, index - 1])
            start = None
    if start is not None and len(mask) - start >= min_length:
        out.append([start, len(mask) - 1])
    return out


def ink_rows(image: np.ndarray, threshold: int = 200) -> np.ndarray:
    gray = image.mean(axis=2)
    return (gray < threshold).sum(axis=1)


def ink_cols(image: np.ndarray, threshold: int = 200) -> np.ndarray:
    gray = image.mean(axis=2)
    return (gray < threshold).sum(axis=0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--box", type=parse_box, default=None)
    parser.add_argument("--mode", choices=("components", "lines", "ink"), default="components")
    parser.add_argument("--threshold", type=int, default=140)
    parser.add_argument("--min-pixels", type=int, default=5)
    parser.add_argument("--y-gap", type=int, default=3)
    parser.add_argument("--x-gap", type=int, default=14)
    parser.add_argument("--axis", choices=("rows", "cols"), default="rows")
    parser.add_argument("--min-length", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    image = load_rgb(args.image)
    if args.mode == "ink":
        profile = ink_rows(image, args.threshold) if args.axis == "rows" else ink_cols(image, args.threshold)
        result = runs(profile > 0, args.min_length)
    else:
        comps = components(image, args.box, args.threshold, args.min_pixels)
        result = merge_lines(comps, args.y_gap, args.x_gap) if args.mode == "lines" else comps

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in result:
            print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
