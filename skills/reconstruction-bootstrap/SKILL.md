---
name: reconstruction-bootstrap
description: 用自然语言初始化一个逆向复刻/还原工程。用户说“帮我构建一个反编译 WPS 桌面端软件的工程”“初始化一个 Android 逆向还原项目”“搭一个 Unity 游戏复刻工作区”“从零开始还原某个软件/协议/渲染引擎”时使用。负责识别平台、选择领域 profile、检查 rea 等反编译/采集工具链、生成 .comate 工作区、初始化能力账本，并把后续交给 reconstruction-core。
---

# 复刻工程初始化

用户只描述目标和平台，**由你完成初始化**：选择 profile、检查工具链、生成工作区、
初始化账本。不要把命令丢给用户说“请手动执行”。

初始化完成后，后续功能还原遵循 `reconstruction-core` 和工作区里的 `PIPELINE.md`。

## 什么时候用

- “帮我构建一个反编译 WPS 桌面端软件的工程”
- “初始化一个 Android App 逆向还原项目”
- “搭一个 Unity / Unreal 游戏复刻工作区”
- “我要从零还原某个软件/协议/渲染引擎，先建工程”
- 项目里还没有 `.comate/reconstruction-*` 工作区

如果工作区已存在，不要重复初始化；直接进入 `reconstruction-core`。

## 第一步：解析用户意图

从自然语言里提取这些槽位：

| 槽位 | 说明 | 默认 |
|---|---|---|
| `goal` | 还原对象/目标 | 必填，缺失才问 |
| `platform` | 桌面端/Android/iOS/Web/2D 游戏/3D 游戏 | 从描述推断 |
| `domain` | 工作区名，kebab-case | 由目标推断 |
| `root` | 项目根 | 当前工作目录 |
| `source_root` | 反编译产物/源码根 | profile 默认值 |
| `reference_runtime` | 参考端启动/采集命令 | profile 默认值 |
| `target_runtime` | 目标端构建/测试命令 | profile 默认值 |
| `comparison` | 对照方式 | profile 默认值 |

平台到默认 profile：

| 用户描述 | `--profile` | 参考端 | 常见效果证据 |
|---|---|---|---|
| WPS 桌面端（图表/文档渲染） | `wps-chart` | WPS 桌面版 | 截图 + 定向回归 |
| WPS 桌面端其他模块 | `desktop-native` | WPS 桌面版 | 截图/UI 树 |
| Windows/macOS/Linux 原生软件 | `desktop-native` | 原程序 | 截图/UI 树 |
| Android APK/AAB | `android-native` | 真机/模拟器 | adb 截图 + uiautomator + logcat |
| iOS IPA/Mach-O | `ios-native` | 真机/模拟器 | 设备截图 + syslog |
| Unity 游戏/3D 应用 | `unity-game` | 原游戏 | 帧序列 + 场景状态 |
| Unreal 游戏 | `unreal-game` | 原游戏 | 帧序列 + 场景状态 |
| 2D 游戏 | `game-2d` | 原游戏 | 帧序列 + 游戏状态 |
| Web 应用/前端渲染 | `web-app` | 浏览器 | 截图 + DOM/网络 |

没有匹配的 profile 时：

1. 先找最接近的平台 profile；
2. 用 `--source-root` / `--reference-runtime` / `--target-runtime` / `--comparison`
   覆盖；
3. 把领域差异写进生成的 `domain.md`；
4. 如果这是一个会反复使用的领域，再新增 `profiles/<domain>.json`。

平台识别信号：

- Android：`apk`、`aab`、`dex`、`smali`、`jadx`、`adb`、`frida-server`
- iOS：`ipa`、`Mach-O`、`class-dump`、`otool`、`idevice*`
- Unity：`global-metadata.dat`、`GameAssembly.dll`、`libil2cpp.so`、
  `Assembly-CSharp.dll`、`Il2CppDumper`
- Unreal：`pak`、`utoc`、`ucas`、`FModel`、`UE4SS`、`Blueprint`
- 2D 游戏：`Cocos`、`Laya`、`GameMaker`、`jsb`、`atlas`、`plist`
- Web：URL、HTML/JS、DOM、source map、CDP、Playwright
- 桌面原生：`exe`、`dll`、`so`、`dylib`、`Mach-O`、`PE`、Ghidra/IDA

## 第二步：只问阻塞问题

最多问 3 个问题，且只在缺了就无法初始化时问：

- 还原对象是什么（软件/游戏/引擎/协议）？
- 反编译产物或源码在哪？
- 参考端怎么启动、目标端怎么构建？

能从上下文推断的不要问。用户说“先按默认/你看着办”时，用 profile 默认值继续，
把未确认项写进 `domain.md` 的待确认清单。

## 第三步：执行初始化

不要只输出命令，直接运行：

```bash
python3 <skill-dir>/scripts/bootstrap.py \
  --profile <profile> \
  --domain <domain> \
  --root <project-root>
```

按需追加：

```bash
  --source-root <decompiled-dir> \
  --source-root <target-src> \
  --reference-runtime "<launch-and-capture>" \
  --target-runtime "<build-and-test>" \
  --comparison <method> \
  --workspace .comate/reconstruction-<domain> \
  --config .comate/reconstruction-<domain>.json
```

脚本会依次做：

1. 解析 profile（JSON 优先，Markdown 兼容）；
2. 复制 core 工作区模板到 `.comate/reconstruction-<domain>/`；
3. 生成 `domain.md`；JSON profile 同时生成 `profile.json`；
4. 运行工具链检查；
5. 运行 `ensure_workspace.py` 确认工作区；
6. 初始化 `capabilities/index.json` / `case-manifest.json`，并跑校验；
7. 写 `bootstrap.json`，打印 `BOOTSTRAP_OK` / `BOOTSTRAP_PARTIAL`。

只检查工具链，不建工作区：

```bash
python3 <skill-dir>/scripts/bootstrap.py --profile <profile> --check-only
```

## 第四步：处理工具链缺失

`bootstrap.py` 输出 `TOOLCHECK <id> OK/MISSING`。

- `OK`：继续。
- `MISSING`：把缺的项原样告诉用户，并给出安装/配置步骤。
- `BOOTSTRAP_PARTIAL`：工作区已经生成，不要回滚；补齐工具后重跑
  `--check-only`。

### rea / JADX 配置

`rea` 用于桌面端和 Android 的 JADX 反编译。它依赖：

- `JAVA_HOME`：JDK 17+
- `REA_JADX_MCP_JAR`：`jadx-headless-mcp-*-all.jar`
- `~/.comate/mcp.json` 里的 `mcpServers.rea`
- 可选 `JAVA_TOOL_OPTIONS=-Xmx8g`

检查：

```bash
python3 <skill-dir>/scripts/bootstrap.py --profile <profile> --check-only
```

如果 `~/.comate/mcp.json` 缺少 `rea`，可以：

```bash
python3 <skill-dir>/scripts/bootstrap.py --profile <profile> --check-only --fix-mcp
```

`--fix-mcp` 只补缺失的 server，不覆盖已有配置，并会先备份。若 profile 里的
`${VAR}` 无法展开，脚本会输出 `MCP_CONFIG_NEEDS_MANUAL`，此时先设置环境变量
或手动补配置。**不要在用户未同意时修改全局 MCP 配置。**

## 第五步：交接给 core

初始化成功后：

1. 读 `.comate/reconstruction-<domain>/PIPELINE.md`；
2. 读 `domain.md` / `profile.json` 确认参考端、目标端、验收规则；
3. 打开 `state.json`，按 Stage 0 建第一个 feature 档案；
4. 后续按 `reconstruction-core` 的 6 阶段执行。

回复用户时只给：

- 工作区、配置、profile 路径；
- 工具链检查结果；
- 账本初始数量；
- 下一步要做的第一件事（Stage 0 建档）。

不要把整个 `PIPELINE.md` 或 `state.json` 贴出来。

## 新增平台/领域

扩展不需要改脚本，只加一个 `profiles/<domain>.json`：

1. 复制 `profiles/_TEMPLATE.json`；
2. 填 `platform`、`source_roots`、`reference_runtime`、`target_runtime`、
   `comparison`、`required_evidence`、`acceptance_rules`；
3. 在 `toolchains` 里声明怎么检查工具（`required_env/files/commands`）；
4. 用 `--profile <domain>` 跑一次 bootstrap 验证；
5. 如果这个领域会长期使用，再补一份人类可读说明。

同一平台的不同软件优先复用平台 profile + CLI 覆盖，不要为每个软件复制一套流程。

## 硬规则

1. **能推断就不问。** 只在缺了无法初始化时问，最多 3 个问题。
2. **直接执行，不要只给命令。** 用户要的是工程，不是操作手册。
3. **工作区已存在就复用。** 有 `state.json` 时不覆盖，直接进入 core。
4. **工具缺失不回滚工作区。** 标记 `BOOTSTRAP_PARTIAL`，补齐后重查。
5. **不改全局 MCP 配置，除非用户同意。** `--fix-mcp` 必须先说明会改
   `~/.comate/mcp.json`。
6. **领域差异只写 profile/domain.md。** 不改 core 流程和目录骨架。
7. **一个工作区一个领域。** 多领域用 `.comate/reconstruction-<domain>` 分开。
