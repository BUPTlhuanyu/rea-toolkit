---
name: reconstruction-scaffold
description: 为新的复刻/还原项目生成领域工作区与领域配置。用于用户要启动一个新的源码复刻任务（桌面端、移动端、Web、3D 游戏、2D 游戏、非游戏应用等），需要一份带 capability 账本、case/evidence/run 目录、PIPELINE 和初始化脚本的脚手架时。通常由 reconstruction-bootstrap 自动调用；用户直接要求“只生成脚手架”时也可单独使用。
---

# Reconstruction scaffold

这个 skill 只负责**生成脚手架**，不负责具体领域的取证和实现。生成后的执行
遵循 `reconstruction-core` 和工作区里的 `PIPELINE.md`。

> 推荐入口是 `reconstruction-bootstrap`：它会调用本 skill，并继续做工具链检查、
> 工作区确认和账本初始化。只有想跳过这些步骤时才直接运行 `scaffold.py`。

## 什么时候用

- 新项目还没有 `.comate/reconstruction-*`
- 要开始一个 WPS 之外的领域：桌面端、PC 端、3D/2D 游戏、非游戏应用
- 想把现有项目的流程复制成一个标准工作区

## 输入

至少需要：

- `--domain`：领域名，例如 `wps-chart`、`unity-3d`、`desktop-app`
- `--root`：项目根
- `--source-root`：源码/反编译/协议根（可重复）
- `--reference-runtime`：参考实现运行命令（可重复）
- `--target-runtime`：目标实现构建/运行命令（可重复）
- `--comparison`：对照方式，例如 `screenshot`、`layout-json`、`trace`

## 生成

```bash
python3 <skill-dir>/scripts/scaffold.py \
  --domain <domain> \
  --root <project-root> \
  --profile <profile-name|profile-path> \
  --source-root <src> \
  --reference-runtime "<command>" \
  --target-runtime "<command>" \
  --comparison <method>
```

`--profile` 可以是 `profiles/` 下的名字（如 `wps-chart`、`android-native`），
也可以是文件路径。解析时优先 `.json`，其次 `.md`：

- JSON profile：生成 `profile.json`（机器可读）+ `domain.md`（人类可读），
  工具检查读 `profile.json`。
- Markdown profile：内容复制为 `domain.md`，不做工具链检查。

CLI 参数（`--source-root` / `--reference-runtime` / `--target-runtime` /
`--comparison`）会覆盖 JSON profile 里的对应字段。

输出：

```
<project>/.comate/reconstruction-<domain>/
<project>/.comate/reconstruction-<domain>.json
<project>/.comate/reconstruction-<domain>/domain.md
<project>/.comate/reconstruction-<domain>/profile.json   # JSON profile
```

不会覆盖已存在的非空工作区。

## 生成后

1. 打开 `domain.md` / `profile.json`，补齐参考端/目标端/验收规则。
2. 运行 `reconstruction-core` 的 `ensure_workspace.py` 确认 `READY`：
   ```bash
   python3 <core-skill-dir>/scripts/ensure_workspace.py \
     --config .comate/reconstruction-<domain>.json
   ```
3. 填 `state.json` 的 features/backlog/queue。
4. 每个 case 目录放 `case.json`，显式声明覆盖哪些能力。
5. 按 `PIPELINE.md` 的 6 阶段开始。

推荐用 `reconstruction-bootstrap` 一次完成 1–4 步。

## 领域适配

不同领域只改领域配置 `domain.md` 和工作区的 `corpus/`，不要复制 core 流程：

- 3D/2D 游戏：source roots、engine runtime、scene capture、frame diff
- 桌面端/PC：native binary、UI automation、screenshot/DOM tree
- 非游戏应用：API/protocol、fixture replay、response diff

core 不硬编码任何领域命令。
