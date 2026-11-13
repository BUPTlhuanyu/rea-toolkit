# 文件说明（File Map）

[中文](FILES.ZH.md) | [English](FILES.md)

这个文档回答四个问题：

1. 每个文件是干什么的？
2. 它是谁生成的？
3. 哪些文件可以手改，哪些不要手改？
4. 想新增/修改一个能力时，最短路径是什么？

> 下面的 JSON 代码块只用于文档展示，使用 `javascript` 高亮；实际 JSON 文件不能带注释。

路径约定：

- `skills/...`、`profiles/...`、`toolkits/...` 相对 `rea-toolkit` 仓库根。
- `<workspace>/...` 指项目里的 `.comate/reconstruction-<domain>/`。
- `<workspace>` 由 `reconstruction-scaffold` / `reconstruction-bootstrap` 生成。

---

## 1. 一页看懂

```text
rea-toolkit/
├── README.md                  # 英文仓库入口
├── README.ZH.md               # 中文仓库入口
├── docs/
│   ├── FILES.md               # 英文逐文件说明
│   ├── FILES.ZH.md            # 中文逐文件说明
│   ├── README.md              # 英文文档索引
│   ├── README.ZH.md           # 中文文档索引
│   ├── WORKSPACE-TEMPLATE.md  # 英文工作区模板流程
│   ├── WORKSPACE-TEMPLATE.ZH.md # 中文工作区模板流程
│   └── diagrams/              # archify 架构图 / 流程图
├── package.json               # npx 包元数据
├── bin/rea-toolkit.js         # npx 安装器（install/doctor/list）
├── profiles -> skills/reconstruction-bootstrap/profiles
├── skills/
│   ├── reconstruction-bootstrap/   # 自然语言入口 + 工具链检查 + profiles
│   ├── reconstruction-core/        # 通用流程 + 工作区模板 + 账本工具
│   └── reconstruction-scaffold/    # 生成工作区 + domain.md/profile.json
└── toolkits/                  # 通用截图/指标/对照/回归/Frida/rea/覆盖工具
```

工作区：

```text
<workspace>/
├── PIPELINE.md                # 流程唯一入口
├── README.md                  # 工作区地图
├── state.json                 # 机器状态：能力、状态、队列、backlog
├── domain.md                  # 人类可读领域配置
├── profile.json               # 机器可读领域配置（可选）
├── bootstrap.json             # 初始化记录（bootstrap 生成）
├── capabilities/              # 能力账本 + 每能力档案（重点）
├── corpus/                    # 输入语料 / 派生 case
├── evidence/                  # 源码/运行时/审计证据
├── runs/                      # 回归与实验产物
├── tools/                     # 账本工具 + 项目专用工具
└── history/                   # 冻结归档
```

---

## 2. `capabilities/` 目录（重点）

这是最容易混淆的目录。它同时包含**能力账本**、**case 映射**和**每能力档案**。

### 2.1 数据流

```text
state.json#features ─────────────┐
corpus/**/case.json ─────────────┼─> build_capability_index.py
evidence/audit/*.json ───────────┘        │
                                          ├─> capabilities/index.json
                                          ├─> capabilities/case-manifest.json
                                          └─> capabilities/README.md
                                                    │
                                                    v
                                     build_feature_dossiers.py
                                                    │
                                                    v
                          capabilities/<feature-id>/README.md
                                                    │
                                                    v
                                     validate_capability_ids.py
```

一句话：

- `index.json` 是**能力视角**：每个能力现在什么状态。
- `case-manifest.json` 是**case 视角**：每个 case 覆盖哪些能力。
- `capabilities/<feature-id>/README.md` 是**叙事视角**：这个能力是怎么还原出来的。
- `README.md` 是**目录视角**：按分类列出所有能力。

### 2.2 `capabilities/index.json`

**作用**：规范化能力表，是机器读的主索引。

每个 capability 大致包含：

```javascript
{
  // 语义能力 ID
  "id": "pie3d.flat-import-inset",
  // 人读名称
  "name": "3D 饼图平面导入内缩",
  // 分类/分组
  "category": "饼图",
  // 类型/对象
  "kind": "pie3D",
  // 标签/协议字段
  "tags": ["c:pie3DChart"],
  // 完成度：complete / effect-matched-source-partial / partial
  "completion": "complete",
  // 源码轴
  "source": {
    // UNKNOWN / LOCATED / DECODED / EXACT / PARTIAL / NONPORTABLE
    "status": "EXACT",
    // 源码证据引用
    "refs": ["evidence/source/..."],
    // 源码判定摘要
    "verdict": "...",
    // 残留/未闭合点
    "gap": null
  },
  // 效果轴
  "effect": {
    // PENDING / MATCH / DIFF / NO_REFERENCE / ACCEPTED_NONPORTABLE
    "status": "MATCH",
    // 效果证据引用
    "refs": ["runs/.../shots/cmp.png"]
  },
  // case 引用
  "cases": {
    // 关联 case ID
    "refs": ["pie/pie3d-01"],
    // 逐 case 判定
    "verdicts": {}
  }
}
```

- **谁生成**：`tools/capabilities/build_capability_index.py`
- **输入**：`state.json#features`、`corpus/**/case.json`、`evidence/audit/*.json`、已有的 `case-manifest.json`
- **是否手改**：不要手改；改 `state.json` / `case.json` 后重新生成
- **用途**：校验、统计、dossier 生成、快速查询

### 2.3 `capabilities/case-manifest.json`

**作用**：case → capability 的映射表，是 case 视角的索引。

每个 case 大致包含：

```javascript
{
  // case ID：<group>/<case>
  "id": "pie/pie3d-01",
  // 来源：provided / derived
  "origin": "derived",
  // 类型：fixture / screenshot / trace 等
  "kind": "fixture",
  // 相对工作区的路径
  "path": "corpus/derived/pie/pie3d-01",
  // 该 case 覆盖的能力 ID
  "capabilities": ["pie3d.flat-import-inset"],
  // 映射来源：declared / audit / manual / unmapped
  "mapping": "declared",
  // 效果判定
  "effect": { "status": "MATCH" },
  // 源码判定
  "source": { "status": "EXACT" }
}
```

- **谁生成**：`build_capability_index.py`
- **来源**：
  1. `corpus/**/case.json`（推荐，显式声明）
  2. `evidence/audit/*.json` 中带 `id` 的 case
  3. 上一次的 `case-manifest.json`（人工维护优先）
- **是否手改**：可以，但新增 case 更推荐写 `corpus/**/case.json`；手工条目按 `id` 优先保留
- **用途**：回答“这个 case 验证了哪些能力”“这个能力有哪些 case”

### 2.4 `capabilities/README.md`

**作用**：按分类列出所有能力的可读索引，由生成器覆盖。

- **谁生成**：`build_capability_index.py`
- **是否手改**：不要手改；改 `state.json` 后重新生成

### 2.5 `capabilities/_TEMPLATE/README.md`

**作用**：新建能力档案的模板。

内容包含：

- 观察到的行为
- 源码/协议证据
- case 表
- 实现文件
- 验证 / run
- 缺口 / 下一步

**怎么用**：

```bash
mkdir -p capabilities/<feature-id>
cp capabilities/_TEMPLATE/README.md capabilities/<feature-id>/README.md
```

然后：

1. 在 `state.json#features` 增加该能力；
2. 在 `corpus/.../case.json` 里声明 case；
3. 运行 `build_capability_index.py`；
4. 运行 `build_feature_dossiers.py`；
5. 运行 `validate_capability_ids.py`。

### 2.6 `capabilities/<feature-id>/README.md`

**作用**：单个能力的 dossier，是“这个功能怎么还原出来的”唯一叙事入口。

结构：

```markdown
# <能力名> (`<feature-id>`)

- 分类 / 类型 / 标签
- Source / Effect / Completion

## 1. 观察到的行为
## 2. 源码/协议证据
## 3. Case
## 4. 实现
## 5. 验证 / run
## 6. 缺口 / 下一步
```

生成器只维护这个块：

```markdown
<!-- GENERATED:START -->
...
<!-- GENERATED:END -->
```

- **块内**：由 `build_feature_dossiers.py` 更新，不要手改
- **块外**：人工笔记，生成器不会覆盖

这是“换个模型也能知道怎么还原的”关键文件。

### 2.7 `feature-id` 和 `case-id` 的区别

| | feature-id | case-id |
|---|---|---|
| 回答 | 还原了哪个可观察行为/规则 | 用哪个输入验证 |
| 例子 | `pie3d.flat-import-inset` | `pie/pie3d-01` |
| 存放 | `state.json#features`、`index.json`、dossier 目录 | `corpus/**/case.json`、`case-manifest.json` |
| 关系 | 一个能力可以有多个 case | 一个 case 可以覆盖多个能力 |

---

## 3. 工作区根目录

| 文件 | 作用 | 谁生成 | 是否手改 |
|---|---|---|---|
| `PIPELINE.md` | 6 阶段流程、目录契约、硬规则 | scaffold/bootstrap | 只在改流程时改 |
| `README.md` | 工作区地图和最短上手路径 | scaffold/bootstrap | 可以补充 |
| `state.json` | 能力状态机：features/backlog/queue/runScope | 人工 + 工具 | **可以，是状态源头** |
| `domain.md` | 人类可读领域配置 | scaffold | 可以，补参考端/目标端/验收 |
| `profile.json` | 机器可读领域配置 | scaffold（JSON profile） | 可以，工具检查读它 |
| `bootstrap.json` | 初始化记录（profile、工具检查、账本数量） | bootstrap | 不要手改 |

### `state.json`

最重要的字段：

```javascript
{
  // 总能力账本
  "features": [
    {
      // 语义能力 ID
      "key": "domain.feature",
      // 人读名称
      "featureName": "...",
      // 分类/分组
      "category": "...",
      // 源码轴
      "sourceStatus": "UNKNOWN",
      // 效果轴
      "effectStatus": "PENDING",
      // 源码证据引用
      "sourceRefs": [],
      // 效果证据引用
      "effectImageRefs": [],
      // 关联 case ID
      "caseRefs": []
    }
  ],
  // 候选能力/缺口
  "backlog": [],
  // 待处理能力队列
  "queue": [],
  // 当前任务批次选中的范围
  "runScope": { "features": [], "requiredCases": [], "requiredRegressions": [] }
}
```

- `key` 必须是语义 ID（`<domain>.<feature>`），不要用 `ext-47` 这类批次号。
- `sourceStatus` / `effectStatus` 是两条独立的轴，不能互相替代。
- `runScope` 是当前任务批次的工作单，不是总表；总表是 `features` / `capabilities/index.json`。
- `queue` 是待处理的优先级队列；`selectedFeature` 是当前正在做的那一个能力。
- `index.json` 是从这里生成的，**不要反过来手改 index 再期望 state 更新**。

---

## 4. `corpus/`

| 路径 | 作用 |
|---|---|
| `corpus/provided/` | 用户/上游提供的真实输入，覆盖真实使用场景，不要求最小 |
| `corpus/derived/` | 从源码/协议证据派生的**最小可归因 case** |
| `corpus/**/case.json` | 每个 case 的能力映射声明 |
| `corpus/**/reference/` | 参考端输出（截图/日志/帧） |
| `<group>/<case>/` | 一组 case 目录，名字稳定、可检索 |

`case.json` 最小结构：

```javascript
{
  // case ID：<group>/<case>
  "id": "<group>/<case>",
  // 来源：provided / derived
  "origin": "provided|derived",
  // 类型：fixture / screenshot / trace 等
  "kind": "fixture",
  // 该 case 覆盖的能力 ID
  "capabilities": ["<domain>.<feature>"],
  // 效果判定
  "effect": { "status": "PENDING" },
  // 源码判定
  "source": { "status": "PENDING" }
}
```

---

## 5. `evidence/`

| 路径 | 作用 |
|---|---|
| `evidence/source/` | 静态反编译/协议结论：函数、地址、公式、默认值、边界 |
| `evidence/source/raw/<date>/` | 原始反编译 dump/裁图，冻结，附 `MANIFEST.md` |
| `evidence/runtime/` | 运行时探针、hook、trace、日志 |
| `evidence/runtime/raw/<date>/` | 会话级原始日志，冻结，附 `MANIFEST.md` |
| `evidence/audit/` | 逐 case 的 source/effect 判定 JSON（可选） |

命名：

```text
evidence/source/<feature-id>-<YYYY-MM-DD>.md
evidence/runtime/<feature-id>-<YYYY-MM-DD>.jsonl
```

规则：feature-id 是主键，日期只用于溯源；原始 dump 放 `raw/`，不要把结论放进 `raw/`。

---

## 6. `runs/`

| 路径 | 作用 | 生命周期 |
|---|---|---|
| `runs/_TEMPLATE/` | 新 run 的模板 | 只读 |
| `runs/_TEMPLATE/run.json` | run 元数据模板 | 只读 |
| `runs/regress-baseline/` | 当前回归基线 | 只由基线刷新流程更新 |
| `runs/regress-current/` | 最近一次回归的临时输出 | 可覆盖 |
| `runs/archive/` | 冻结的历史 run/回归 | 只读 |
| `runs/<run-id>/` | 一次实验/回归的正式记录 | 新工作写这里 |

`run-id`：

```text
YYYY-MM-DD-<feature-id>-NN
```

`run.json` 记录命令、feature、case 列表、baseline、result、notes；`result.json` 记录逐 case 指标/判定。

---

## 7. `tools/capabilities/`

| 脚本 | 作用 | 输入 | 输出 |
|---|---|---|---|
| `build_capability_index.py` | 生成能力账本 | `state.json`、`corpus/**/case.json`、`evidence/audit/*.json`、旧 manifest | `index.json`、`case-manifest.json`、`README.md` |
| `build_feature_dossiers.py` | 生成/刷新每能力档案 | `index.json`、`case-manifest.json` | `capabilities/<feature-id>/README.md` |
| `show_capability.py` | 紧凑查看一个能力 | `index.json`、`case-manifest.json` | 终端摘要 |
| `validate_capability_ids.py` | 校验 ID/状态/case/dossier | `index.json`、`case-manifest.json`、`state.json`、`profile.json` | 错误列表 / `OK` |

建议顺序：

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/build_feature_dossiers.py
python3 tools/capabilities/validate_capability_ids.py
```

`tools/INDEX.md` 是项目专用工具的索引，新增工具时同步更新。

---

## 8. `history/`

冻结归档，不作为新工作输入：

| 路径 | 内容 |
|---|---|
| `history/rounds/` | 并行轮次规则、patch、请求结果 |
| `history/plans/` | 旧计划、验证记录、一次性清单 |
| `history/legacy-probes/` | 旧探针，可能依赖已删除的 build |
| `history/source-backups/` | `.orig` / 被拒绝的源码备份 |
| `history/state-backups/` | 重大迁移前的 1–2 份 state 快照 |

---

## 9. `skills/`

### `skills/reconstruction-bootstrap/`

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 自然语言入口：识别平台、选 profile、执行初始化 |
| `scripts/bootstrap.py` | 编排 scaffold + 工具检查 + ensure_workspace + 账本初始化 |
| `scripts/check_tools.py` | 检查 profile 声明的 MCP/env/file/command |
| `profiles/*.json` | 规范 profile 位置；`npx skills add` 会随 bootstrap 一起复制 |

### `skills/reconstruction-core/`

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 通用流程契约：两轴状态、6 阶段、硬规则 |
| `scripts/ensure_workspace.py` | 解析/创建/确认工作区 |
| `references/pipeline.md` | 流程设计理由和扩展点 |
| `references/evidence.md` | 证据/状态/dossier 契约 |
| `references/multi-agent.md` | 多 agent ownership 和并行规则 |
| `references/efficiency.md` | 上下文/token 经济 |
| `templates/workspace/` | 工作区脚手架（见第 2–8 节） |

### `skills/reconstruction-scaffold/`

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 只生成脚手架时的使用说明 |
| `scripts/scaffold.py` | 复制 core 模板、生成 `domain.md`/`profile.json`、写项目配置 |
| `templates/domain.md` | 没有 profile 时的领域配置模板 |

---

## 10. `profiles/`

规范位置：`skills/reconstruction-bootstrap/profiles/`。

| 文件 | 作用 |
|---|---|
| `README.md` | profile 列表、schema、扩展方法 |
| `_TEMPLATE.json` | 新平台 profile 的机器可读模板 |
| `_TEMPLATE.md` | 只写文字说明时的模板 |
| `wps-chart.json/.md` | WPS 图表领域 |
| `desktop-native.json` | 桌面原生 |
| `android-native.json` | Android |
| `ios-native.json` | iOS |
| `unity-game.json` | Unity 3D |
| `unreal-game.json` | Unreal |
| `game-2d.json` | 2D 游戏 |
| `web-app.json` | Web |

profile 里的 `toolchains` 决定 `check_tools.py` 检查什么；`comparison.metrics` 决定该领域用哪些指标。

---

## 11. `toolkits/`

| 路径 | 作用 |
|---|---|
| `image/crop.py` | 裁剪/缩放 |
| `image/diff.py` | 差异 bbox + 洋红标注 |
| `image/contact_sheet.py` | 多图拼 sheet |
| `image/measure.py` | 连通域/文字行/ink runs |
| `metrics/focus.py` | 全局 MAE + `maxBlock`/`focusBlocks` + 边缘/ΔE 局部簇 |
| `compare/make_compare.py` | 参考/目标拼接 + focus 指标 |
| `capture/macos_window.py` | macOS 按窗口 ID 截图 |
| `capture/list_windows.swift` | CGWindowList 窗口枚举 |
| `ooxml/xlsx_patch.py` | 改 chart XML / 填单元格 |
| `regress/runner.py` | 通用回归驱动 |
| `frida/run.py` | spawn + Frida script + JSONL |
| `frida/attach.py` | attach/launch + Frida script + JSONL |
| `rea/rea_batch.mjs` | rea MCP 批处理 |
| `coverage/branch_coverage.py` | 分支覆盖清单 → Mermaid/HTML |
| `coverage/branches.example.json` | 分支覆盖输入示例 |
| `README.md` | 工具用法、依赖、适用性 |

---

## 12. `bin/` 和 `package.json`

| 文件 | 作用 |
|---|---|
| `bin/rea-toolkit.js` | 安装器：`install --project/--global`、`doctor`、`list` |
| `package.json` | npx 包元数据；`bin` 指向安装器；`files` 决定打包内容 |

安装器默认复制，`--link` 用软链，`--force` 覆盖已存在项。

## 12.5 `docs/`

| 文件 | 作用 |
|---|---|
| `docs/FILES.ZH.md` | 本文：仓库逐文件说明 |
| `docs/FILES.md` | 英文版：仓库逐文件说明 |
| `docs/README.ZH.md` | 中文文档索引 |
| `docs/README.md` | 英文文档索引 |
| `docs/WORKSPACE-TEMPLATE.ZH.md` | 工作区模板的详细运转流程、逐文件说明、Gate、最短路径 |
| `docs/WORKSPACE-TEMPLATE.md` | 英文版：工作区模板详细流程 |
| `docs/diagrams/workspace-template-architecture.html` | archify 生成的组件与数据流架构图 |
| `docs/diagrams/workspace-template-workflow.html` | archify 生成的 6 阶段运转流程图 |
| `docs/.archify/...` | archify 的 candidate 与 review 记录 |

---

## 13. 哪些文件不要手改

| 文件 | 原因 |
|---|---|
| `capabilities/index.json` | 由 `build_capability_index.py` 覆盖 |
| `capabilities/case-manifest.json` | 会被重新合并；新增 case 请写 `corpus/**/case.json` |
| `capabilities/README.md` | 生成器覆盖 |
| `capabilities/<feature-id>/README.md` 的 GENERATED 块 | `build_feature_dossiers.py` 维护 |
| `bootstrap.json` | bootstrap 生成 |
| `runs/regress-baseline/` | 只由基线刷新流程更新 |
| `history/` | 冻结归档 |

## 14. 可以手改

- `state.json#features` / `backlog` / `queue`
- `corpus/**/case.json`
- `capabilities/<feature-id>/README.md` 的 GENERATED 块外
- `domain.md` / `profile.json`
- `PIPELINE.md`（只在改流程时）
- 项目专用 `tools/` 和 `tools/INDEX.md`

---

## 15. 最短路径

### 新增一个能力

```text
1. state.json#features 增加 key
2. cp capabilities/_TEMPLATE/README.md capabilities/<feature-id>/README.md
3. corpus/derived/<group>/<case>/case.json 声明 capabilities
4. python3 tools/capabilities/build_capability_index.py
5. python3 tools/capabilities/build_feature_dossiers.py
6. python3 tools/capabilities/validate_capability_ids.py
```

### 新增一个 case

```text
1. 在 corpus/derived/<group>/<case>/ 放输入
2. 写 case.json，声明 capabilities
3. 运行 build_capability_index.py
4. 在 dossier 的 Case 表里补参考/目标输出
```

### 修改一个能力的判定

```text
1. 改 state.json#features 的 sourceStatus/effectStatus/refs
2. 改 dossier 的 GENERATED 块外笔记
3. 重新 build + validate
```

### 新增一个平台

```text
1. 复制 profiles/_TEMPLATE.json
2. 填 platform/source_roots/reference_runtime/target_runtime/comparison/toolchains
3. npx /path/to/rea-toolkit doctor --profile <name>
4. 用 bootstrap 生成一个临时工作区验证
```
