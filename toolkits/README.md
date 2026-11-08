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
├── metrics/
│   └── focus.py             # 全局 MAE + block/focus + 边缘/ΔE 局部簇
├── compare/
│   └── make_compare.py      # 参考/目标上下或左右拼接 + 指标
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

## 为什么不是只看 MAE

全局 MAE 会把只占画面一小部分的差异稀释掉：一个错误的图例色块、缺失的引导线、
小标签的边框，可能在两百万像素里只占几百像素，MAE 仍然很低。

`metrics/focus.py` 提供三层指标：

- 全局 `mae`：兼容旧结果
- block 指标：`32x32` 分块，输出 `maxBlock`、`focusBlocks`、`focusAreaPct`
  - `maxBlock`：最差块的平均绝对差
  - `focusBlocks`：块分数 `> 15` 的块数（默认阈值，可按领域调整）
- 可选：
  - `--edges`：边缘结构差（missing / extra）
  - `--clusters`：CIELAB ΔE 局部簇，先估计整体平移，再用局部最小 ΔE 抑制字形 AA

阈值是 triage 辅助，不是最终判定。WPS 图表对齐里 `maxBlock`/`focusBlocks`
用的就是 block 32 + focus threshold 15。

## 适用性

focus 指标适合**静态、可复现、像素对齐、差异局部化**的视觉对照，不是所有
应用类型的默认答案。

| 类型 | 是否适合 | 建议 |
|---|---|---|
| WPS/Office 文档、图表渲染 | 很适合 | `mae + maxBlock + focusBlocks + ΔE clusters + edges` |
| 桌面端窗口/UI | 适合 | 先裁到 client area，固定 DPI/字体，再算 block/ΔE |
| Android/iOS 静态页面 | 适合 | 固定设备/分辨率/主题/locale；截图 + UI 树一起看 |
| Web 静态页面 | 适合 | 固定 viewport/DPR、冻结动画、mock 网络；再加 DOM/network diff |
| 2D/3D 游戏 | 只能作为辅助 | 必须做帧序列 + 输入回放 + 时间对齐 + 场景/物理状态 diff |
| 动画/视频 | 不完全适合 | 单帧 block 会漏时序问题；用帧序列 + 时间聚合指标 |
| 协议/解析器/CLI/数据 | 不适合 | 用 JSON/文本/结构化 diff，不要用像素指标 |
| 音频 | 不适合 | 用波形/频谱/PSNR 等音频指标 |

参数也不是通用的：`block=32 / focus threshold=15` 是针对 1820x1068 图表帧
标定的。4K、游戏帧、移动端截图需要按分辨率缩放 block，并重新标定阈值。

各领域应在 `profiles/*.json` 的 `comparison.metrics` 里声明实际使用的指标族：

- `pixel`：`mae`、`maxBlock`、`focusBlocks`
- `perceptual`：`delta-e-clusters`、`ssim`
- `structure`：`edges`、`ui-tree-diff`、`dom-diff`
- `semantic`：`network-diff`、`state-diff`、协议/JSON diff
- `temporal`：`frame-sequence`、`timeline`

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

# 对照 + 指标（默认包含 maxBlock/focusBlocks）
python3 toolkits/compare/make_compare.py \
  --reference wps.png --target ts.png --out cmp.png --labels WPS,TS

# 只算指标，不拼图
python3 toolkits/metrics/focus.py --reference wps.png --target ts.png
python3 toolkits/metrics/focus.py --reference wps.png --target ts.png \
  --edges --clusters --crop-dir crops

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

# 回归（默认算全局 MAE + block 指标）
python3 toolkits/regress/runner.py --cases cases.json \
  --out-dir runs/current --baseline-dir runs/baseline \
  --shoot 'node shoot.mjs --case {case} --out {target}'

# 全局 MAE 通过、但局部块很差时标 PIXEL_DIFF
python3 toolkits/regress/runner.py --cases cases.json \
  --out-dir runs/current --max-block-threshold 25 --focus-blocks-threshold 20

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
- numpy（`image/measure.py`、`metrics/focus.py`、`compare/make_compare.py`、`regress/runner.py`）
- opencv-python（可选，仅 `metrics/focus.py --clusters` 的 CIELAB ΔE 局部簇需要）
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
| `metrics/focus.py` | `tools/audit_xlsx_visual_clusters.py`、`tools/audit_xlsx_structure.py`，以及 gallery alignment 的 `maxBlock`/`focusBlocks` |
| `compare/make_compare.py` | `tools/render/make-cmp.py` 的 `stack()` + 指标 |
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
