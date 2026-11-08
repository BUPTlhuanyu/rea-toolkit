# profiles

> 规范位置：`skills/reconstruction-bootstrap/profiles/`。这样 `npx skills add`
> 复制 bootstrap skill 时会自动带上全部 profile；顶层 `profiles/` 只是兼容软链。

`reconstruction-core` 的领域配置。每个 profile 声明：

- 平台与领域
- 源码/反编译根
- 参考端运行与采集方式
- 目标端构建/测试方式
- 对照方式和产物
- 必需证据
- 验收规则
- 工具链检查与安装步骤

core 保持领域无关；profile 提供具体命令和门禁。

## 已有 profile

| profile | 平台 | 参考端 | 典型效果证据 |
|---|---|---|---|
| `wps-chart` | 桌面端 | WPS 桌面版 | 截图 + 定向回归 |
| `desktop-native` | 桌面端 | 原生程序 | UI 截图/树 |
| `android-native` | Android | 真机/模拟器 | adb 截图 + uiautomator + logcat |
| `ios-native` | iOS | 真机/模拟器 | 设备截图 + syslog |
| `unity-game` | 3D 游戏 | Unity 游戏 | 帧序列 + 场景状态 |
| `unreal-game` | 3D 游戏 | Unreal 游戏 | 帧序列 + 场景状态 |
| `game-2d` | 2D 游戏 | Cocos/Laya/Unity 2D 等 | 帧序列 + 游戏状态 |
| `web-app` | Web | 浏览器 | 截图 + DOM/网络 |

`comparison.metrics` 只声明该领域实际使用的指标族。像素指标（`mae` /
`maxBlock` / `focusBlocks` / ΔE）不是所有领域的默认答案：

- 静态 UI/文档/图表：像素 + 感知 + 结构指标
- 游戏/动画：帧序列、时间对齐、场景/物理状态 diff；像素指标只做辅助
- 协议/解析器/数据：结构化 diff，不用像素指标
- 音频：波形/频谱指标

## 怎么用

不需要手动执行命令。直接对模型说：

- “帮我构建一个反编译 WPS 桌面端软件的工程”
- “初始化一个 Android App 逆向还原项目，参考端是这台手机”
- “搭一个 Unity 游戏复刻工作区，反编译产物在 `decompiled/`”
- “从零还原这个 Web 应用，先建工程”

模型会调用 `reconstruction-bootstrap`：

1. 根据描述选择 profile；
2. 只问缺失的阻塞信息；
3. 生成 `.comate/reconstruction-<domain>/`；
4. 检查 rea/adb/frida 等工具链；
5. 初始化能力账本；
6. 交接给 `reconstruction-core`。

只想检查工具链：

```bash
python3 skills/reconstruction-bootstrap/scripts/bootstrap.py \
  --profile android-native --check-only
```

## JSON 与 Markdown

- `<name>.json`：机器可读，bootstrap/scaffold/check_tools 优先使用。
- `<name>.md`：人类可读说明，兼容旧用法。
- 新 profile 建议直接写 JSON；需要解释时再补 MD。

JSON 最小结构见 `_TEMPLATE.json`；文字模板见 `_TEMPLATE.md`。

关键字段：

```json
{
  "name": "<domain>",
  "platform": "<desktop-native|mobile-android|mobile-ios|web|game-2d|game-3d>",
  "source_roots": ["<decompiled-dir>", "<target-src>"],
  "reference_runtime": { "commands": ["..."], "outputs": ["screenshot"] },
  "target_runtime": { "commands": ["..."], "outputs": ["dist"] },
  "comparison": { "method": "...", "metrics": ["..."], "artifacts": ["..."] },
  "required_evidence": { "source": ["..."], "effect": ["..."] },
  "acceptance_rules": { "require_source_exact": true, "require_effect_match": true },
  "verification_commands": ["..."],
  "id_domains": ["app", "ui"],
  "toolchains": [
    {
      "id": "rea",
      "mcp_config": "~/.comate/mcp.json",
      "required_env": ["JAVA_HOME", "REA_JADX_MCP_JAR"],
      "required_files": ["${REA_JADX_MCP_JAR}", "${JAVA_HOME}/bin/java"],
      "required_commands": ["python3", "node", "npx"],
      "setup": ["..."]
    }
  ],
  "domain_rules": ["..."]
}
```

- `id_domains`：能力 ID 第一段的白名单；新增能力域时同步追加。
- `toolchains`：CLI 工具用 `required_commands`；GUI 工具用
  `optional_commands` + `notes`；MCP 工具用 `mcp_config` +
  `required_env/files`。
- `${VAR}` 会从 MCP server 的 `env` 或当前进程环境展开。

## 扩展新领域

1. 复制 `_TEMPLATE.json` 为 `<domain>.json`。
2. 先判断平台：
   - 桌面原生 → `desktop-native`
   - Android → `android-native`
   - iOS → `ios-native`
   - Web → `web-app`
   - 2D 游戏 → `game-2d`
   - 3D 游戏 → `unity-game` / `unreal-game`
   - 其他引擎 → 新建平台 profile
3. 填参考端、目标端、对照方式、证据和验收规则。
4. 在 `toolchains` 里声明工具检查：
   - CLI 工具用 `required_commands`
   - GUI 工具用 `optional_commands` + `notes`
   - MCP 工具用 `mcp_config` + `required_env/files`
5. 用 `--profile <domain> --check-only` 验证。
6. 用 `bootstrap.py --domain <domain> --profile <domain>` 建一个临时工作区验证。

不需要改 `reconstruction-core` 或 `reconstruction-bootstrap` 的代码。
同一平台的不同软件优先复用平台 profile + CLI 覆盖。
