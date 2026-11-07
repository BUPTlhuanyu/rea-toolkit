# toolkits

从 WPS 图表还原工程里抽出来的通用工具。它们**不含 WPS/图表常量**，可以用于
桌面端、移动端、游戏、Web 等领域的参考截取、图像对照和回归。

WPS 专用封装仍留在 `.comate/wps-pc-chart-reconstruction/tools/`，不要把这些
通用工具再写回 WPS 工作区。

## 目录

```
toolkits/
├── image/
│   ├── crop.py              # 裁剪/缩放
│   ├── diff.py              # 差异 bbox + 洋红标注
│   ├── contact_sheet.py     # 多图拼 sheet
│   └── measure.py           # 连通域/文字行/ink runs
├── compare/
│   └── make_compare.py      # 参考/目标上下或左右拼接 + MAE
├── capture/
│   ├── macos_window.py      # macOS 按窗口 ID 截图
│   └── list_windows.swift   # CGWindowList 窗口列表
├── ooxml/
│   └── xlsx_patch.py        # 改 chart XML / 填单元格
├── regress/
│   └── runner.py            # 通用回归驱动
├── frida/
│   ├── run.py               # spawn + script + JSONL
│   └── attach.py            # attach / launch + script + JSONL
└── rea/
    └── rea_batch.mjs        # rea MCP 批处理
```

## 快速用法

```bash
# 裁剪
python3 toolkits/image/crop.py raw.png --box 78,432,1898,1500 \
  --resize 1820x1068 --out crop.png

# 差异
python3 toolkits/image/diff.py reference.png target.png --out diff.png --json

# 多图拼 sheet
python3 toolkits/image/contact_sheet.py --glob 'shots/*.wps.png' \
  --columns 2 --scale 0.5 --out sheet.png

# 对照 + MAE
python3 toolkits/compare/make_compare.py \
  --reference wps.png --target ts.png --out cmp.png --labels WPS,TS --mae

# macOS 窗口截图
python3 toolkits/capture/macos_window.py list --app wpsoffice
python3 toolkits/capture/macos_window.py capture \
  --app /Applications/wpsoffice.app --doc case.xlsx \
  --size 1512x944 --crop 78,432,1898,1500 --resize 1820x1068 \
  --out case.wps.png --close

# xlsx patch
python3 toolkits/ooxml/xlsx_patch.py in.xlsx out.xlsx \
  --sub '<c:varyColors val="0"/> => <c:varyColors val="1"/>' \
  --fill A1=100 --fill B2=hello

# 回归
python3 toolkits/regress/runner.py --cases cases.json \
  --out-dir runs/current --baseline-dir runs/baseline \
  --shoot 'node shoot.mjs --case {case} --out {target}'

# Frida
python3 toolkits/frida/run.py --exe ./app --script hook.js --log out.jsonl
python3 toolkits/frida/attach.py --pid 1234 --script hook.js --log out.jsonl

# rea
node toolkits/rea/rea_batch.mjs --target ./binary --out out.jsonl \
  --procedures 0x1000,0x2000
```

## 依赖

- Python 3.9+
- Pillow
- numpy（`image/measure.py`、`compare/make_compare.py`、`regress/runner.py`）
- frida（`frida/*`）
- Node 18+（`rea/rea_batch.mjs`）
- macOS + Xcode command line tools（`capture/*`，`swift` 和 `screencapture`）

## 来源

| toolkit | 来源 |
|---|---|
| `image/crop.py` | `tools/crop_image.py` |
| `image/diff.py` | `tools/img_diff.py` |
| `image/contact_sheet.py` | `tools/contact_sheet.py`（路径/列数参数化） |
| `image/measure.py` | `tools/measure/blobs.py`、`tools/measure/measure.py`、`tools/measure/txtbox.py` |
| `compare/make_compare.py` | `tools/render/make-cmp.py` 的 `stack()` + MAE |
| `capture/macos_window.py` | `tools/run_case.py` 的窗口查找/截图 + `tools/capture_wps_preview.py` 的窗口调整/关闭 |
| `ooxml/xlsx_patch.py` | `tools/capture_r4.py` 的 `patch_xlsx` |
| `regress/runner.py` | `tools/regress.py`、`tools/render/deck-regress.py`、`tools/shard_regress.py` 的回归模式 |
| `frida/run.py` | `tools/frida/frida_run.py` |
| `frida/attach.py` | `tools/frida/frida_attach.py`（`wpsoffice` 参数化） |
| `rea/rea_batch.mjs` | `tools/drivers/rea-batch.mjs`（target/Ghidra/JDK 参数化） |

## 没有抽出来的部分

这些仍属于 WPS/图表领域，留在原工作区：

- WPS 固定窗口尺寸、crop、`/tmp/wps-dbg.app`、`workarea.cfg` 清理
- 图表对象检测（`chartbox.py`）、`909x533` 逻辑框、capture class
- PPTX `graphicFrame` 映射、239 deck 回归
- TS 截图页、gallery、SDK 专用截图
- `gen_*.py` 图表 case 生成器（作为 case 溯源保留）
- 大部分 Frida 图表探针（作为源码证据保留）

## 注意

- `capture/macos_window.py` 需要「屏幕录制」授权；`list_windows.swift` 不需要
  「辅助功能」授权。
- `regress/runner.py` 的 `--shoot` / `--compare` 用 `shell=True` 执行模板，
  只接受可信输入。
- `xlsx_patch.py` 的 `--sub` 找不到 old 字符串会报错，避免静默写错文件。
- 这些工具只处理“参考输出 vs 目标输出”的通用层；源码取证、能力账本和验收
  规则仍由 `reconstruction-core` 及各领域 profile 提供。
