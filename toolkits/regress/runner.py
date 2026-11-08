#!/usr/bin/env python3
"""Generic regression runner: cases -> shoot -> metrics -> baseline diff.

指标默认包含全局 MAE + block 指标（`maxBlock` / `focusBlocks`），避免小范围
差异被整图 MAE 稀释。也可用 `--max-block-threshold` / `--focus-blocks-threshold`
把“MAE 通过但局部很差”的 case 标成 `PIXEL_DIFF`。

cases.json：
[
  {
    "case": "pie/pie-01",
    "reference": "corpus/pie/pie-01/reference.png",
    "target": "out/pie-01.target.png",
    "shoot": "node shoot.mjs --case {case} --out {target}",
    "compare": "python3 make_compare.py --reference {reference} --target {target} --out {cmp}",
    "meta": {"feature": "pie.default"}
  }
]

用法：
  python3 runner.py --cases cases.json --out-dir runs/current \
      --shoot "node shoot.mjs --case {case} --out {target}" \
      --baseline-dir runs/baseline

模板占位符：
  {case} {reference} {target} {cmp} {out_dir} {root}

状态：
  MATCH / PIXEL_DIFF / DIFF / REGRESSION / NO_REFERENCE / MISSING

默认有 regression 时退出码 1；`--allow-regression` 改为 0。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

TOOLKITS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLKITS))
from metrics.focus import focus_metrics, load_rgb  # noqa: E402


def load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("cases", [])
    if not isinstance(data, list):
        raise SystemExit("cases.json 必须是数组或 {cases: [...]}")
    return data


def resolve(path: str | None, root: Path) -> Path | None:
    if not path:
        return None
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else (root / candidate).resolve()


def format_command(template: str, values: dict[str, str]) -> str:
    class Safe(dict):
        def __missing__(self, key):  # type: ignore[override]
            return "{" + key + "}"

    return template.format_map(Safe(values))


def run_command(command: str, cwd: Path) -> tuple[int, str, str]:
    process = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        text=True,
        capture_output=True,
    )
    return process.returncode, process.stdout, process.stderr


def safe_name(case: str) -> str:
    return case.replace("/", "__").replace("\\", "__")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True, help="cases.json")
    parser.add_argument("--root", default=".", help="相对路径基准")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--shoot", default=None, help="截图命令模板")
    parser.add_argument("--compare", default=None, help="对照图命令模板")
    parser.add_argument("--baseline-dir", default=None)
    parser.add_argument("--match-mae", type=float, default=2.0)
    parser.add_argument("--block", type=int, default=32,
                        help="focus 指标的 block 大小")
    parser.add_argument("--focus-threshold", type=float, default=15.0,
                        help="block 分数超过该值计为 focus block")
    parser.add_argument("--max-block-threshold", type=float, default=None,
                        help="全局 MAE 通过但 maxBlock 超过该值时标 PIXEL_DIFF")
    parser.add_argument("--focus-blocks-threshold", type=int, default=None,
                        help="全局 MAE 通过但 focusBlocks 超过该值时标 PIXEL_DIFF")
    parser.add_argument("--baseline-metric", choices=("mae", "maxBlock", "focusBlocks"),
                        default="mae", help="baseline delta 使用哪个指标")
    parser.add_argument("--fail-delta", type=float, default=0.05)
    parser.add_argument("--allow-regression", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    out_dir = (root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir = (root / args.baseline_dir).resolve() if args.baseline_dir else None
    cases = load_cases((root / args.cases).resolve() if not Path(args.cases).is_absolute() else Path(args.cases))

    rows: list[dict] = []
    regressions = 0
    for item in cases:
        case = item.get("case") or item.get("id")
        if not case:
            print("skip case without id", file=sys.stderr)
            continue
        reference = resolve(item.get("reference"), root)
        target = resolve(item.get("target"), root) or (out_dir / f"{safe_name(case)}.target.png")
        cmp_path = out_dir / f"{safe_name(case)}.cmp.png"

        values = {
            "case": case,
            "reference": str(reference) if reference else "",
            "target": str(target),
            "cmp": str(cmp_path),
            "out_dir": str(out_dir),
            "root": str(root),
        }

        shoot = item.get("shoot") or args.shoot
        if shoot and not args.dry_run:
            code, stdout, stderr = run_command(format_command(shoot, values), root)
            if code != 0:
                rows.append(
                    {
                        "case": case,
                        "status": "SHOOT_FAILED",
                        "command": format_command(shoot, values),
                        "stderr": stderr[-2000:],
                    }
                )
                continue

        if reference is None or not reference.exists():
            rows.append({"case": case, "status": "NO_REFERENCE", "reference": str(reference) if reference else None})
            continue
        if not target.exists():
            rows.append({"case": case, "status": "MISSING", "target": str(target)})
            continue

        reference_pixels = load_rgb(reference)
        target_pixels = load_rgb(target)
        metrics = focus_metrics(
            reference_pixels,
            target_pixels,
            block=args.block,
            focus_threshold=args.focus_threshold,
        )
        score = metrics["mae"]
        old = None
        baseline = baseline_dir / f"{safe_name(case)}.png" if baseline_dir else None
        if baseline and baseline.exists():
            baseline_metrics = focus_metrics(
                reference_pixels,
                load_rgb(baseline),
                block=args.block,
                focus_threshold=args.focus_threshold,
            )
            old = baseline_metrics[args.baseline_metric]
        current = metrics[args.baseline_metric]
        delta = round(current - old, 3) if old is not None else None
        status = "MATCH" if score <= args.match_mae else "DIFF"
        if status == "MATCH" and args.max_block_threshold is not None and metrics["maxBlock"] > args.max_block_threshold:
            status = "PIXEL_DIFF"
        if status == "MATCH" and args.focus_blocks_threshold is not None and metrics["focusBlocks"] > args.focus_blocks_threshold:
            status = "PIXEL_DIFF"
        if delta is not None and delta > args.fail_delta:
            status = "REGRESSION"
            regressions += 1

        compare = item.get("compare") or args.compare
        if compare and not args.dry_run:
            code, stdout, stderr = run_command(format_command(compare, values), root)
            if code != 0:
                rows.append(
                    {
                        "case": case,
                        "status": "COMPARE_FAILED",
                        "mae": score,
                        "stderr": stderr[-2000:],
                    }
                )
                continue

        row = {
            "case": case,
            "status": status,
            "mae": score,
            "maxBlock": metrics["maxBlock"],
            "focusBlocks": metrics["focusBlocks"],
            "focusAreaPct": metrics["focusAreaPct"],
            "worstBlock": metrics["worstBlock"],
            "baseline_mae": old if args.baseline_metric == "mae" else None,
            "baseline_metric": args.baseline_metric,
            "baseline_value": old,
            "delta": delta,
            "reference": str(reference),
            "target": str(target),
            "cmp": str(cmp_path) if compare else None,
            "meta": item.get("meta", {}),
        }
        rows.append(row)
        old_text = f"{old:.3f}" if old is not None else "-"
        delta_text = f"{delta:+.3f}" if delta is not None else "-"
        print(
            f"{case}\t{status}\tmae={score:.3f}\t"
            f"maxBlock={metrics['maxBlock']:.2f}\tfocus={metrics['focusBlocks']}\t"
            f"old={old_text}\tdelta={delta_text}"
        )

    summary = {
        "total": len(rows),
        "match": sum(row["status"] == "MATCH" for row in rows),
        "pixelDiff": sum(row["status"] == "PIXEL_DIFF" for row in rows),
        "diff": sum(row["status"] == "DIFF" for row in rows),
        "regression": sum(row["status"] == "REGRESSION" for row in rows),
        "noReference": sum(row["status"] == "NO_REFERENCE" for row in rows),
        "missing": sum(row["status"] == "MISSING" for row in rows),
        "failed": sum(
            row["status"] in ("SHOOT_FAILED", "COMPARE_FAILED") for row in rows
        ),
    }
    run = {
        "startedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": str(root),
        "outDir": str(out_dir),
        "casesFile": str(args.cases),
        "shoot": args.shoot,
        "compare": args.compare,
        "baselineDir": str(baseline_dir) if baseline_dir else None,
        "matchMae": args.match_mae,
        "block": args.block,
        "focusThreshold": args.focus_threshold,
        "maxBlockThreshold": args.max_block_threshold,
        "focusBlocksThreshold": args.focus_blocks_threshold,
        "baselineMetric": args.baseline_metric,
        "failDelta": args.fail_delta,
    }
    (out_dir / "run.json").write_text(
        json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "result.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    if regressions and not args.allow_regression:
        return 1
    if summary["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
