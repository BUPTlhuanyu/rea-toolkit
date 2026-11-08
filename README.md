# rea-toolkit

用于集中管理复刻/还原相关 Skill 的仓库。

## 目录结构

```
rea-toolkit/
├── skills/
│   ├── reconstruction-bootstrap/   # 自然语言入口 + profiles/
│   ├── reconstruction-core/        # 通用流程、证据契约、工作区模板
│   └── reconstruction-scaffold/    # 生成工作区 + 领域配置
├── profiles -> skills/reconstruction-bootstrap/profiles   # 兼容软链
├── toolkits/                       # 通用工具：截图、裁剪、对照、回归、Frida、rea
├── bin/rea-toolkit.js              # npx 安装器
├── package.json
└── README.md
```

`profiles/` 的**规范位置**是 `skills/reconstruction-bootstrap/profiles/`。
这样 `npx skills add` 复制 bootstrap skill 时会自动带上 profiles；顶层
`profiles` 只是兼容软链。

每个 Skill 仍遵循：

```
skills/<skill-name>/
├── SKILL.md
├── scripts/
├── references/
└── templates/
```

## 安装

Comate 通过 `SKILL.md` 发现 skill，所以安装的本质是：把
`reconstruction-bootstrap` / `reconstruction-core` / `reconstruction-scaffold`
三个目录放到 Comate 能找到的目录。三者必须一起安装。

### 方式一：`npx skills`（通用 CLI）

`npx skills` 是 skills.sh 生态的通用安装器，支持本地路径、GitHub repo 和 skill 包。
它会安装到 `.agents/skills/`（项目级）或 `~/.agents/skills/`（全局级）；
Comate 同时扫描 `.comate/skills/` 和 `.agents/skills/`。

```bash
# 全局：~/.agents/skills/
npx --yes skills add /path/to/rea-toolkit -g -y -a universal

# 项目级：<project>/.agents/skills/
npx --yes skills add /path/to/rea-toolkit -y -a universal

# 发布到 GitHub 后
npx --yes skills add <owner/repo> -g -y -a universal
```

说明：

- `-g` 是全局，不加是项目级。
- `-a universal` 是通用 agent；`npx skills` 目前不支持 `-a comate`。
- 它只安装 `SKILL.md` 目录。因为 `profiles/` 已经放在
  `skills/reconstruction-bootstrap/profiles/`，三个 skill 会一起带上 profiles。
- `toolkits/` 不会被 `npx skills` 安装。需要通用工具时用下面的完整安装，
  或直接 clone 本仓库。

### 方式二：`npx rea-toolkit`（完整安装）

仓库自带 `bin/rea-toolkit.js`，会安装 **skills + profiles + toolkits**：

```bash
# 项目级：装到 <project>/.comate
npx --yes /path/to/rea-toolkit install --project <project>

# 全局：装到 ~/.comate
npx --yes /path/to/rea-toolkit install --global

# 开发时用软链而不是复制
npx --yes /path/to/rea-toolkit install --project <project> --link

# 检查
npx --yes /path/to/rea-toolkit doctor --project <project>
npx --yes /path/to/rea-toolkit doctor --global
```

如果发布到了 npm registry，可以省略路径：

```bash
npx rea-toolkit install --global
```

当前 `package.json` 是 `private: true`，发布到 registry 前需要先改掉。

注意：`npx` 本身只负责下载/执行包，**不会自动把 skill 注册到全局**。
“全局”是安装器的 `--global` 决定的：它把文件复制到 `~/.comate/skills/`。
默认用复制，避免 npx 缓存被清理后留下坏软链；开发时用 `--link`。

### 方式三：手动复制/软链

项目级：

```bash
mkdir -p <project>/.comate/skills
ln -s /path/to/rea-toolkit/skills/reconstruction-bootstrap \
  <project>/.comate/skills/reconstruction-bootstrap
ln -s /path/to/rea-toolkit/skills/reconstruction-core \
  <project>/.comate/skills/reconstruction-core
ln -s /path/to/rea-toolkit/skills/reconstruction-scaffold \
  <project>/.comate/skills/reconstruction-scaffold
```

全局：

```bash
mkdir -p ~/.comate/skills
ln -s /path/to/rea-toolkit/skills/reconstruction-bootstrap \
  ~/.comate/skills/reconstruction-bootstrap
ln -s /path/to/rea-toolkit/skills/reconstruction-core \
  ~/.comate/skills/reconstruction-core
ln -s /path/to/rea-toolkit/skills/reconstruction-scaffold \
  ~/.comate/skills/reconstruction-scaffold
```

`profiles/` 已经在 `reconstruction-bootstrap/profiles/` 里，手动软链 skill
时不需要再单独链 profiles；如果其他工具需要顶层 `profiles/`，可以额外：

```bash
ln -s /path/to/rea-toolkit/profiles <project>/.comate/profiles
```

profile 也可以放在以下任一位置（按顺序查找）：

1. `$RECONSTRUCTION_PROFILES`
2. `<bootstrap-skill>/profiles/`（`npx skills` 安装后自动带上）
3. `<rea-toolkit>/profiles/`
4. `<project>/.comate/profiles/`
5. `<project>/profiles/`
6. `<cwd>/profiles/`

安装/重载后，当前会话的 skill 列表里应出现：

- `reconstruction-bootstrap`
- `reconstruction-core`
- `reconstruction-scaffold`

已有 WPS 项目继续使用它自己的 `.comate/skills/wps-chart-source-reconstruction/`
和工作区，不需要改动。

### 方式三：直接运行（不安装 skill）

只想跑脚本时，可以不安装：

```bash
python3 /path/to/rea-toolkit/skills/reconstruction-bootstrap/scripts/bootstrap.py \
  --profile wps-chart --check-only
```

但这种方式不会让模型自动触发 skill，只适合手动执行。

## 推荐用法：直接说目标

不需要手动执行命令。对模型说：

- “帮我构建一个反编译 WPS 桌面端软件的工程”
- “初始化一个 Android App 逆向还原项目”
- “搭一个 Unity 游戏复刻工作区”
- “从零还原这个 Web 应用，先建工程”

`reconstruction-bootstrap` 会：

1. 根据描述选择平台 profile；
2. 只问缺失的阻塞信息；
3. 生成 `.comate/reconstruction-<domain>/`；
4. 检查 rea/adb/frida 等工具链；
5. 初始化能力账本；
6. 把后续交给 `reconstruction-core`。

## 通用工具

从 WPS 图表还原工程里抽出的、去掉领域常量的工具在 `toolkits/`：

- `toolkits/image/`：裁剪、差异、拼 sheet、连通域/文字行测量
- `toolkits/metrics/`：全局 MAE + `maxBlock` / `focusBlocks` + ΔE 局部簇 + 边缘结构
- `toolkits/compare/`：参考/目标拼接 + focus 指标
- `toolkits/capture/`：macOS 按窗口 ID 截图
- `toolkits/ooxml/`：xlsx chart XML / 单元格 patch
- `toolkits/regress/`：通用回归驱动
- `toolkits/frida/`：spawn/attach + JSONL
- `toolkits/rea/`：rea MCP 批处理

用法和依赖见 `toolkits/README.md`。WPS 专用封装仍留在 WPS 工作区。

## 平台矩阵

| 平台 | profile | 源码证据 | 效果证据 |
|---|---|---|---|
| 桌面原生 | `desktop-native` | 反汇编/反编译/调试器 | UI 截图/树 |
| Android | `android-native` | rea/jadx、smali、Frida | adb 截图 + UI 树 + logcat |
| iOS | `ios-native` | Mach-O、class-dump、LLDB | 设备截图 + syslog |
| 3D 游戏 | `unity-game` / `unreal-game` | IL2CPP/pak/资产 | 帧序列 + 场景状态 |
| 2D 游戏 | `game-2d` | 脚本包/资产/引擎元数据 | 帧序列 + 游戏状态 |
| Web | `web-app` | 构建产物/source map/网络 | 截图 + DOM/网络 |
| WPS 图表 | `wps-chart` | kso.framework 反编译 | WPS 截图 + 回归 |

## 手动使用

### 已有项目，只缺工作区

```bash
python3 skills/reconstruction-core/scripts/ensure_workspace.py
```

### 新领域，先生成脚手架

```bash
python3 skills/reconstruction-scaffold/scripts/scaffold.py \
  --domain unity-3d \
  --root /path/to/project \
  --profile unity-game \
  --source-root src \
  --reference-runtime "./run-ref.sh" \
  --target-runtime "npm run build" \
  --comparison screenshot
```

`--profile` 可以是 `profiles/` 下的名字，也可以是文件路径；优先 `.json`。
JSON profile 会同时生成 `profile.json` 和 `domain.md`，并支持工具链检查。

### 只检查工具链

```bash
python3 skills/reconstruction-bootstrap/scripts/bootstrap.py \
  --profile wps-chart --check-only
```

### rea 配置

`rea` 依赖 `JAVA_HOME`、`REA_JADX_MCP_JAR` 和 `~/.comate/mcp.json` 里的
`mcpServers.rea`。缺失时：

```bash
python3 skills/reconstruction-bootstrap/scripts/bootstrap.py \
  --profile wps-chart --check-only --fix-mcp
```

`--fix-mcp` 只补缺失项、先备份，不覆盖已有配置。未展开的 `${VAR}` 会输出
`MCP_CONFIG_NEEDS_MANUAL`。

## 新增 Skill

1. 在 `skills/` 下创建以 Skill 名命名的目录（小写字母、数字和连字符）。
2. 编写 `SKILL.md`，开头使用如下 frontmatter：

```markdown
---
name: <skill-name>
description: 说明这个 Skill 做什么、什么时候使用
---
```

`description` 决定 Skill 何时被触发，应写清楚使用场景。
