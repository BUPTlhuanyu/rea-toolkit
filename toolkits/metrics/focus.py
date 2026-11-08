#!/usr/bin/env python3
"""Focus-aware comparison metrics.

Global MAE 会把只占画面一小部分的差异稀释掉：一个错误的图例色块、缺失的引导线、
小标签的边框，可能在两百万像素里只占几百像素。这个模块提供三层指标：

1. 全局 MAE（兼容旧结果）
2. block 指标：把图像切成 NxN 块，报告最差块 `maxBlock` 和超阈值块数 `focusBlocks`
3. 可选：
   - 边缘结构：WPS 边缘未被目标边缘覆盖的比例（missing / extra）
   - CIELAB ΔE 局部簇：先估计整体平移，再用局部最小 ΔE 抑制字形 AA，
     输出每个差异簇的 bbox / 面积 / 峰值 ΔE / 两侧颜色

阈值是 triage 辅助，不是最终判定。是否把 `PIXEL_DIFF` 判为 DIFF，应由领域规则
或人工复核决定。

用法：
  python3 focus.py --reference wps.png --target ts.png
  python3 focus.py --reference wps.png --target ts.png --edges
  python3 focus.py --reference wps.png --target ts.png --clusters --crop-dir crops
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

DEFAULT_BLOCK = 32
DEFAULT_FOCUS_THRESHOLD = 15.0
DEFAULT_EDGE_THRESHOLD = 24
DEFAULT_DILATE = 5
DEFAULT_DELTA_E = 8.0
DEFAULT_BLUR_DELTA = 4.0
DEFAULT_MIN_AREA = 24
DEFAULT_CLOSE_PX = 3
DEFAULT_SHIFT_RANGE = 4
DEFAULT_BORDER_MARGIN = 6


def load_rgb(path: str | Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int16)


def fit(reference: np.ndarray, target: np.ndarray) -> np.ndarray:
    if reference.shape == target.shape:
        return target
    image = Image.fromarray(target.astype(np.uint8))
    image = image.resize((reference.shape[1], reference.shape[0]), Image.LANCZOS)
    return np.asarray(image).astype(np.int16)


def mae(reference: np.ndarray, target: np.ndarray) -> float:
    target = fit(reference, target)
    return round(float(np.abs(reference.astype(np.int16) - target.astype(np.int16)).mean()), 3)


def block_metrics(
    reference: np.ndarray,
    target: np.ndarray,
    block: int = DEFAULT_BLOCK,
    focus_threshold: float = DEFAULT_FOCUS_THRESHOLD,
    include_scores: bool = False,
) -> dict:
    """Worst NxN block and count of blocks above focus_threshold.

    解决“关注点只占视图一小部分时全局 MAE 被稀释”的问题。block 分数是该块内
    三通道平均绝对差，和全局 MAE 同一量纲。
    """
    if block < 2:
        raise ValueError("block 必须 >= 2")
    target = fit(reference, target)
    diff = np.abs(reference.astype(np.int16) - target.astype(np.int16)).mean(axis=2)
    height, width = diff.shape
    rows = math.ceil(height / block)
    cols = math.ceil(width / block)
    scores = np.zeros((rows, cols), dtype=np.float64)
    for row in range(rows):
        y0, y1 = row * block, min((row + 1) * block, height)
        for col in range(cols):
            x0, x1 = col * block, min((col + 1) * block, width)
            scores[row, col] = float(diff[y0:y1, x0:x1].mean())

    flat = int(np.argmax(scores))
    row, col = divmod(flat, cols)
    worst = {
        "x": col * block,
        "y": row * block,
        "w": min(block, width - col * block),
        "h": min(block, height - row * block),
        "score": round(float(scores[row, col]), 3),
    }
    focus = scores > focus_threshold
    focus_blocks = int(focus.sum())
    focus_area = 0
    for row in range(rows):
        for col in range(cols):
            if focus[row, col]:
                focus_area += min(block, height - row * block) * min(block, width - col * block)
    result = {
        "block": block,
        "blockRows": rows,
        "blockCols": cols,
        "maxBlock": round(float(scores.max()), 3),
        "focusBlocks": focus_blocks,
        "focusBlockRatio": round(focus_blocks / max(1, rows * cols), 4),
        "focusAreaPct": round(focus_area / max(1, height * width), 4),
        "focusThreshold": focus_threshold,
        "worstBlock": worst,
    }
    if include_scores:
        result["blockScores"] = [[round(float(value), 3) for value in line] for line in scores]
    return result


def _edges(image: np.ndarray, threshold: int) -> np.ndarray:
    gray = np.asarray(Image.fromarray(image.astype(np.uint8)).convert("L")).astype(np.int16)
    dx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    dy = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    return np.maximum(dx, dy) > threshold


def _dilate(mask: np.ndarray, size: int) -> np.ndarray:
    if size < 3 or size % 2 == 0:
        raise ValueError("dilate 必须是 >=3 的奇数")
    return np.asarray(
        Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(size))
    ) > 0


def edge_metrics(
    reference: np.ndarray,
    target: np.ndarray,
    edge_threshold: int = DEFAULT_EDGE_THRESHOLD,
    dilate: int = DEFAULT_DILATE,
) -> dict:
    """Structural diff: edges present in one image but not near the other."""
    target = fit(reference, target)
    reference_edges = _edges(reference, edge_threshold)
    target_edges = _edges(target, edge_threshold)
    reference_count = int(reference_edges.sum())
    target_count = int(target_edges.sum())
    if reference_count == 0 or target_count == 0:
        return {
            "referenceEdges": reference_count,
            "targetEdges": target_count,
            "missing": 0,
            "extra": 0,
            "missingRatio": 0.0,
            "extraRatio": 0.0,
        }
    missing = reference_edges & ~_dilate(target_edges, dilate)
    extra = target_edges & ~_dilate(reference_edges, dilate)
    missing_count = int(missing.sum())
    extra_count = int(extra.sum())
    return {
        "referenceEdges": reference_count,
        "targetEdges": target_count,
        "missing": missing_count,
        "extra": extra_count,
        "missingRatio": round(missing_count / reference_count, 4),
        "extraRatio": round(extra_count / target_count, 4),
        "edgeThreshold": edge_threshold,
        "dilate": dilate,
    }


def _cv2():
    try:
        import cv2  # noqa: F401
    except ImportError as error:
        raise RuntimeError(
            "ΔE 局部簇需要 opencv-python：pip install opencv-python"
        ) from error
    return cv2


def _to_lab(bgr: np.ndarray):
    cv2 = _cv2()
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] *= 100.0 / 255.0
    lab[..., 1] -= 128.0
    lab[..., 2] -= 128.0
    return lab


def _delta_e(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.linalg.norm(a - b, axis=2)


def _estimate_shift(reference: np.ndarray, target: np.ndarray, shift_range: int) -> tuple[int, int, float]:
    cv2 = _cv2()
    a = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY).astype(np.float32)[::3, ::3]
    b = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)[::3, ::3]
    height, width = a.shape
    margin = shift_range + 2
    if height <= margin * 2 or width <= margin * 2:
        return 0, 0, 0.0
    best = (float("inf"), 0, 0)
    for dy in range(-shift_range, shift_range + 1):
        for dx in range(-shift_range, shift_range + 1):
            aa = a[margin:height - margin, margin:width - margin]
            bb = b[margin + dy:height - margin + dy, margin + dx:width - margin + dx]
            score = float(np.mean(np.abs(aa - bb)))
            if score < best[0]:
                best = (score, dx, dy)
    return best[1], best[2], best[0]


def _translate(image: np.ndarray, dx: int, dy: int) -> np.ndarray:
    cv2 = _cv2()
    matrix = np.float32([[1, 0, -dx], [0, 1, -dy]])
    return cv2.warpAffine(
        image,
        matrix,
        (image.shape[1], image.shape[0]),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _local_min_delta(a_lab: np.ndarray, b_lab: np.ndarray, radius: int) -> np.ndarray:
    cv2 = _cv2()
    best = np.full(a_lab.shape[:2], np.inf, dtype=np.float32)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                shifted = b_lab
            else:
                matrix = np.float32([[1, 0, -dx], [0, 1, -dy]])
                shifted = cv2.warpAffine(
                    b_lab,
                    matrix,
                    (b_lab.shape[1], b_lab.shape[0]),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REPLICATE,
                )
            np.minimum(best, _delta_e(a_lab, shifted), out=best)
    return best


def _hex_colour(bgr: np.ndarray, mask: np.ndarray) -> str:
    if not mask.any():
        return "-"
    values = bgr[mask].reshape(-1, 3).mean(axis=0)
    blue, green, red = [int(round(value)) for value in values]
    return f"#{red:02x}{green:02x}{blue:02x}"


def _classify(bbox: tuple[int, int, int, int], area: int, fill: float, solid: int) -> str:
    _, _, width, height = bbox
    thin = min(width, height)
    long_side = max(width, height)
    if thin <= 4 and long_side >= 12 and area <= long_side * 6:
        return "line"
    if solid == 0:
        return "aa"
    if area >= 2000 and fill < 0.08:
        return "shape"
    if width >= 10 and height >= 10 and fill < 0.35:
        return "outline"
    if area <= 500:
        return "small"
    return "region"


def _crop_panel(reference, target, heat, bbox, out: Path) -> None:
    cv2 = _cv2()
    x, y, width, height = bbox
    pad = 12
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1 = min(reference.shape[1], x + width + pad)
    y1 = min(reference.shape[0], y + height + pad)
    panels = [
        Image.fromarray(cv2.cvtColor(reference[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)),
        Image.fromarray(cv2.cvtColor(target[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)),
    ]
    heat_image = cv2.applyColorMap(
        np.clip(heat[y0:y1, x0:x1] * 4, 0, 255).astype(np.uint8),
        cv2.COLORMAP_JET,
    )
    panels.append(Image.fromarray(cv2.cvtColor(heat_image, cv2.COLOR_BGR2RGB)))
    gap = 8
    sheet = Image.new(
        "RGB",
        (sum(panel.width for panel in panels) + gap * 2, max(panel.height for panel in panels)),
        "white",
    )
    offset = 0
    for panel in panels:
        sheet.paste(panel, (offset, 0))
        offset += panel.width + gap
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def delta_e_clusters(
    reference: np.ndarray,
    target: np.ndarray,
    delta_threshold: float = DEFAULT_DELTA_E,
    blur_threshold: float = DEFAULT_BLUR_DELTA,
    min_area: int = DEFAULT_MIN_AREA,
    close_px: int = DEFAULT_CLOSE_PX,
    shift_range: int = DEFAULT_SHIFT_RANGE,
    border_margin: int = DEFAULT_BORDER_MARGIN,
    crop_dir: Path | None = None,
    max_clusters: int = 12,
) -> dict:
    """CIELAB ΔE local clusters, robust to 1-3 px global/local shifts."""
    cv2 = _cv2()
    target = fit(reference, target)
    # 统一转 BGR 供 cv2 使用。
    wps = cv2.cvtColor(reference.astype(np.uint8), cv2.COLOR_RGB2BGR)
    ts = cv2.cvtColor(target.astype(np.uint8), cv2.COLOR_RGB2BGR)

    dx, dy, shift_score = _estimate_shift(wps, ts, shift_range)
    aligned = _translate(ts, dx, dy) if (dx or dy) else ts
    wps_lab = _to_lab(wps)
    ts_lab = _to_lab(aligned)
    delta = _local_min_delta(wps_lab, ts_lab, 2)
    wps_blur = cv2.GaussianBlur(wps, (0, 0), 0.7)
    ts_blur = cv2.GaussianBlur(aligned, (0, 0), 0.7)
    blur_delta = _local_min_delta(_to_lab(wps_blur), _to_lab(ts_blur), 2)

    mask = ((delta > delta_threshold) & (blur_delta > blur_threshold)).astype(np.uint8)
    mask[:border_margin, :] = 0
    mask[-border_margin:, :] = 0
    mask[:, :border_margin] = 0
    mask[:, -border_margin:] = 0
    if close_px > 1:
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (close_px, close_px)),
        )
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    clusters = []
    for index in range(1, count):
        x, y, width, height, area = [int(value) for value in stats[index]]
        if area < min_area:
            continue
        component = labels == index
        peak = float(delta[component].max())
        mean = float(delta[component].mean())
        blur_peak = float(blur_delta[component].max())
        if peak < delta_threshold or blur_peak < blur_threshold:
            continue
        fill = area / max(1, width * height)
        sub = component[y:y + height, x:x + width].astype(np.uint8)
        solid = int(cv2.erode(sub, np.ones((3, 3), np.uint8)).sum())
        clusters.append(
            {
                "kind": _classify((x, y, width, height), area, fill, solid),
                "bbox": [x, y, width, height],
                "area": area,
                "solidArea": solid,
                "fill": round(fill, 3),
                "peakDeltaE": round(peak, 2),
                "meanDeltaE": round(mean, 2),
                "referenceColor": _hex_colour(wps, component),
                "targetColor": _hex_colour(aligned, component),
                # sqrt(area) * peak 让小而实的色块排在巨大但稀疏的轮廓差前面。
                "score": round(math.sqrt(max(solid, 1)) * peak * fill, 1),
            }
        )

    clusters.sort(key=lambda item: -item["score"])
    for rank, cluster in enumerate(clusters[:max_clusters]):
        if crop_dir is None:
            continue
        path = Path(crop_dir) / f"{rank:02d}-{cluster['kind']}.png"
        _crop_panel(wps, aligned, delta, tuple(cluster["bbox"]), path)
        cluster["crop"] = str(path)

    focus_area = int(mask.sum())
    focus_delta = float(delta[mask > 0].mean()) if focus_area else 0.0
    return {
        "shift": [dx, dy],
        "shiftScore": round(shift_score, 3),
        "focusArea": focus_area,
        "focusAreaPct": round(focus_area / max(1, mask.shape[0] * mask.shape[1]), 4),
        "focusMeanDeltaE": round(focus_delta, 2),
        "maxPeakDeltaE": round(float(delta.max()), 2),
        "clusters": clusters[:max_clusters],
    }


def focus_metrics(
    reference: np.ndarray,
    target: np.ndarray,
    block: int = DEFAULT_BLOCK,
    focus_threshold: float = DEFAULT_FOCUS_THRESHOLD,
    include_edges: bool = False,
    include_clusters: bool = False,
    crop_dir: Path | None = None,
    **cluster_options,
) -> dict:
    result = {
        "mae": mae(reference, target),
        **block_metrics(reference, target, block, focus_threshold),
    }
    if include_edges:
        result["edges"] = edge_metrics(reference, target)
    if include_clusters:
        result["clusters"] = delta_e_clusters(reference, target, crop_dir=crop_dir, **cluster_options)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--block", type=int, default=DEFAULT_BLOCK)
    parser.add_argument("--focus-threshold", type=float, default=DEFAULT_FOCUS_THRESHOLD)
    parser.add_argument("--edges", action="store_true")
    parser.add_argument("--clusters", action="store_true")
    parser.add_argument("--crop-dir", default=None)
    parser.add_argument("--delta-threshold", type=float, default=DEFAULT_DELTA_E)
    parser.add_argument("--blur-threshold", type=float, default=DEFAULT_BLUR_DELTA)
    parser.add_argument("--min-area", type=int, default=DEFAULT_MIN_AREA)
    parser.add_argument("--shift-range", type=int, default=DEFAULT_SHIFT_RANGE)
    parser.add_argument("--border-margin", type=int, default=DEFAULT_BORDER_MARGIN)
    parser.add_argument("--max-clusters", type=int, default=12)
    parser.add_argument("--blocks", action="store_true", help="输出每个 block 的分数")
    args = parser.parse_args()

    reference = load_rgb(args.reference)
    target = load_rgb(args.target)
    result = focus_metrics(
        reference,
        target,
        args.block,
        args.focus_threshold,
        args.edges,
        args.clusters,
        Path(args.crop_dir) if args.crop_dir else None,
        delta_threshold=args.delta_threshold,
        blur_threshold=args.blur_threshold,
        min_area=args.min_area,
        shift_range=args.shift_range,
        border_margin=args.border_margin,
        max_clusters=args.max_clusters,
    )
    if args.blocks:
        result["blockScores"] = block_metrics(
            reference, target, args.block, args.focus_threshold, include_scores=True
        )["blockScores"]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
