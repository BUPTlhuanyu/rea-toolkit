#!/usr/bin/env python3
"""Patch chart XML and sheet cells inside an .xlsx without Excel.

用法：
  python3 xlsx_patch.py in.xlsx out.xlsx \
      --sub '<c:varyColors val="0"/>=> <c:varyColors val="1"/>' \
      --fill A1=100 --fill B2=hello

默认：
  --part  xl/charts/chart1.xml
  --sheet xl/worksheets/sheet1.xml

`--fill` 的数字写成 <v>，其他值写成 inlineStr。`--sub` 在 chart part 上做
字符串替换；找不到 old 会报错，避免静默写错文件。
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


def cell_key(ref: str) -> tuple[int, int]:
    match = re.match(r"([A-Z]+)(\d+)$", ref.upper())
    if not match:
        raise SystemExit(f"非法单元格引用: {ref}")
    col = 0
    for char in match.group(1):
        col = col * 26 + ord(char) - 64
    return int(match.group(2)), col


def parse_sub(value: str) -> tuple[str, str]:
    if "=>" not in value:
        raise argparse.ArgumentTypeError("--sub 必须是 old=>new")
    old, new = value.split("=>", 1)
    return old.strip(), new.strip()


def parse_fill(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--fill 必须是 A1=value")
    return tuple(value.split("=", 1))  # type: ignore[return-value]


def patch(
    source: Path,
    target: Path,
    fills: dict[str, str],
    subs: list[tuple[str, str]],
    part: str,
    sheet: str,
) -> None:
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == part and subs:
                text = data.decode("utf-8")
                for old, new in subs:
                    if old not in text:
                        raise SystemExit(f"--sub: {old!r} 不在 {part}")
                    text = text.replace(old, new)
                data = text.encode("utf-8")
            if item.filename == sheet and fills:
                text = data.decode("utf-8")
                cells = {
                    match.group(1): match.group(0)
                    for match in re.finditer(
                        r'<c r="([A-Z]+\d+)".*?</c>', text, re.S
                    )
                }
                for ref, value in fills.items():
                    ref = ref.upper()
                    if re.fullmatch(r"-?\d+(\.\d+)?", value):
                        cells[ref] = f'<c r="{ref}"><v>{value}</v></c>'
                    else:
                        cells[ref] = (
                            f'<c r="{ref}" t="inlineStr"><is>'
                            f'<t xml:space="preserve">{escape(value)}</t></is></c>'
                        )
                rows: dict[int, list[tuple[int, str]]] = {}
                for ref, xml in cells.items():
                    row, col = cell_key(ref)
                    rows.setdefault(row, []).append((col, xml))
                body = "".join(
                    f'<row r="{row}">'
                    + "".join(xml for _, xml in sorted(rows[row]))
                    + "</row>"
                    for row in sorted(rows)
                )
                text = re.sub(
                    r"<sheetData>.*</sheetData>",
                    lambda _: f"<sheetData>{body}</sheetData>",
                    text,
                    flags=re.S,
                )
                data = text.encode("utf-8")
            dst.writestr(item, data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--sub", type=parse_sub, action="append", default=[])
    parser.add_argument("--fill", type=parse_fill, action="append", default=[])
    parser.add_argument("--part", default="xl/charts/chart1.xml")
    parser.add_argument("--sheet", default="xl/worksheets/sheet1.xml")
    args = parser.parse_args()

    source = Path(args.source)
    target = Path(args.target)
    if not source.is_file():
        print(f"找不到输入: {source}", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    patch(
        source,
        target,
        dict(args.fill),
        list(args.sub),
        args.part,
        args.sheet,
    )
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
