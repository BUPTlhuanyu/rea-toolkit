# rea-toolkit

用于集中管理复刻/还原相关 Skill 的仓库。

## 目录结构

```
rea-toolkit/
├── skills/
│   ├── reconstruction-bootstrap/   # 自然语言入口：初始化工程 + 工具链检查
│   ├── reconstruction-core/        # 通用流程、证据契约、工作区模板
│   └── reconstruction-scaffold/    # 生成工作区 + 领域配置
├── profiles/                       # 领域配置：wps-chart、android-native、unity-game ...
└── README.md
```

每个 Skill 仍遵循：

```
skills/<skill-name>/
├── SKILL.md
├── scripts/
├── references/
└── templates/
```

## 安装到项目

模型只有在能发现 `SKILL.md` 时才会触发。把需要的 skill 放进项目的
`.comate/skills/`（复制或软链）：

```bash
mkdir -p <project>/.comate/skills
ln -s /Users/liaohuanyu/projects/ai/idea/rea-toolkit/skills/reconstruction-bootstrap \
  <project>/.comate/skills/reconstruction-bootstrap
ln -s /Users/liaohuanyu/projects/ai/idea/rea-toolkit/skills/reconstruction-core \
  <project>/.comate/skills/reconstruction-core
ln -s /Users/liaohuanyu/projects/ai/idea/rea-toolkit/skills/reconstruction-scaffold \
  <project>/.comate/skills/reconstruction-scaffold
```

profile 可以放在以下任一位置（按顺序查找）：

1. `$RECONSTRUCTION_PROFILES`
2. `<rea-toolkit>/profiles/`
3. `skills/profiles/`
4. `<project>/.comate/profiles/`
5. `<project>/profiles/`
6. `<cwd>/profiles/`

最省事的是软链：

```bash
ln -s /Users/liaohuanyu/projects/ai/idea/rea-toolkit/profiles <project>/.comate/profiles
```

已有 WPS 项目继续使用它自己的 `.comate/skills/wps-chart-source-reconstruction/`
和工作区，不需要改动。

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
