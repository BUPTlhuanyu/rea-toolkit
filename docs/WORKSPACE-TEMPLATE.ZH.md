# 复刻工作区模板：运转流程与文件说明

[中文](WORKSPACE-TEMPLATE.ZH.md) | [English](WORKSPACE-TEMPLATE.md)

本文只讲一个对象：

```text
skills/reconstruction-core/templates/workspace/
```

它是 `reconstruction-scaffold` / `reconstruction-bootstrap` 复制到项目里的工作区模板。
本文严格按模板当前内容说明；`domain.md`、`profile.json`、`bootstrap.json`、
`capabilities/<feature-id>/README.md` 等是初始化或使用过程中才生成的，不在模板里。

配套图：

- [架构图：组件与数据流](diagrams/workspace-template-architecture.html)
- [运转流程图：6 阶段](diagrams/workspace-template-workflow.html)

> 流程图中 Stage 5-6 合并为一个收口节点；本文仍按 Stage 5 / Stage 6 分开说明。

---

## 1. 模板到底解决什么问题

复刻/还原任务最容易失控的地方不是写代码，而是：

1. 不知道一个功能到底还原到哪一步；
2. 不知道某个结论来自哪个函数、哪个 case、哪次运行；
3. 换个模型/隔一周继续时，找不到之前的证据；
4. 产物散落在 `tmp/`、`runs/foo-001/`、`cases2/`，无法回归。

模板用固定目录 + 固定状态 + 固定证据契约解决这四件事：

```text
输入 -> 证据 -> case -> 实现 -> 运行 -> 结论
```

每个环节都必须落到固定路径，并且能被下一个人重新找到。

---

## 2. 模板目录逐文件说明

当前模板的完整内容：

```text
templates/workspace/
├── PIPELINE.md
├── README.md
├── state.json
├── capabilities/
│   ├── README.md
│   ├── _TEMPLATE/
│   │   └── README.md
│   ├── index.json
│   └── case-manifest.json
├── corpus/
│   ├── provided/
│   │   └── README.md
│   └── derived/
│       └── README.md
├── evidence/
│   ├── source/
│   │   └── README.md
│   ├── runtime/
│   │   └── README.md
│   └── audit/
│       └── README.md
├── runs/
│   ├── _TEMPLATE/
│   │   ├── README.md
│   │   └── run.json
│   ├── regress-baseline/
│   │   └── README.md
│   └── regress-current/
│       └── README.md
├── tools/
│   ├── INDEX.md
│   └── capabilities/
│       ├── build_capability_index.py
│       ├── build_feature_dossiers.py
│       ├── show_capability.py
│       └── validate_capability_ids.py
└── history/
    ├── legacy-probes/
    │   └── README.md
    ├── plans/
    │   └── README.md
    ├── rounds/
    │   └── README.md
    ├── source-backups/
    │   └── README.md
    └── state-backups/
        └── README.md
```

### 2.1 根目录文件

| 文件 | 作用 | 谁写 | 是否手改 |
|---|---|---|---|
| `PIPELINE.md` | 流程唯一入口：6 阶段、目录契约、Gate、硬规则 | scaffold 复制模板 | 只在改流程时改 |
| `README.md` | 工作区地图：目录、case.json、最短上手路径 | scaffold 复制模板 | 可以补充 |
| `state.json` | 机器状态：features / backlog / queue / runScope | 人工 + 工具 | **可以，是状态源头** |

#### `PIPELINE.md`

它是“怎么做”的契约，不是项目记录。内容包括：

- 目录契约：哪些目录放输入、证据、运行产物；
- 命名：feature-id、case-id、run-id、evidence 文件名；
- 两轴状态：source / effect；
- 6 阶段和每阶段 Gate；
- 能力档案（dossier）模板：`capabilities/_TEMPLATE/README.md`；
- 防“换个模型就换一套思路”的硬规则；
- 常用命令和上下文效率规则。

> dossier 是单个能力的档案/故事，不是代码模板。每个能力最终有一份
> `capabilities/<feature-id>/README.md`。

读工作区时**先读它**，不要凭记忆。

#### `README.md`

工作区地图，回答“东西放哪”：

- 目录树；
- `case.json` 结构；
- 账本生成/校验命令；
- 最短路径。

它不替代 `PIPELINE.md`；`PIPELINE.md` 是流程，`README.md` 是地图。

#### `state.json`

模板里是空状态：

```javascript
{
  // 状态文件 schema 版本
  "schemaVersion": 1,
  // 当前工作区阶段/模式；模板初始 BOOTSTRAP
  "currentState": "BOOTSTRAP",
  // 已执行的工作轮次/迭代计数
  "iteration": 0,
  // 能力盘点状态；模板初始 INCOMPLETE
  "inventoryStatus": "INCOMPLETE",
  // 当前任务批次/本次运行选中的范围；不是总能力表
  // 总表是下面的 features（或 capabilities/index.json）
  "runScope": {
    // 本轮要处理的能力 ID
    "features": [],
    // 本轮必须跑/确认的 case ID
    "requiredCases": [],
    // 本轮必须通过的回归/命令
    "requiredRegressions": []
  },
  // 当前选中的单个能力 ID；null=未选
  "selectedFeature": null,
  // 执行状态：IDLE / RUNNING / BLOCKED / DONE
  "executionStatus": "IDLE",
  // 断点续跑说明：下次恢复时先做什么
  "resumeAction": "",
  // 尚未完成的 task/agent 任务 ID
  "pendingTaskIds": [],
  // 当前状态是否适合直接恢复
  "safeToResume": true,
  // 待处理能力队列；队首优先
  "queue": [],
  // 队列来源/生成依据
  "queueSource": "",
  // 被阻塞项：能力 ID + 原因 + 解除条件
  "blocked": [],
  // 上一轮实际做了什么
  "lastAction": "",
  // 上一轮验证结论：测试/构建/回归
  "lastVerdict": "",
  // 总能力账本：所有能力；不是 runScope
  "features": [],
  // 环境快照：参考端/目标端/二进制/版本等
  "environment": {},
  // 候选能力/缺口清单
  "backlog": []
}
```

`features` 是能力状态源头。每个元素大致：

```javascript
{
  // 语义能力 ID：<domain>.<feature>[.<variant>]
  "key": "<domain>.<feature>",
  // 人读名称
  "featureName": "...",
  // 分类/分组
  "category": "...",
  // 源码轴：UNKNOWN / LOCATED / DECODED / EXACT / PARTIAL / NONPORTABLE
  "sourceStatus": "UNKNOWN",
  // 效果轴：PENDING / MATCH / DIFF / NO_REFERENCE / ACCEPTED_NONPORTABLE
  "effectStatus": "PENDING",
  // 源码证据引用：evidence/source/... 或函数地址
  "sourceRefs": [],
  // 效果证据引用：截图/cmp/run
  "effectImageRefs": [],
  // 关联 case ID
  "caseRefs": [],
  // 源码判定摘要
  "sourceVerdict": "",
  // 源码残留/未闭合点
  "sourceGap": "",
  // 效果判定摘要
  "effectVerdict": "",
  // 回归状态：PASS / FAIL / REGRESSION / NOT_RUN
  "regressionStatus": "",
  // 下一步动作
  "nextState": "",
  // 最近一次变更摘要
  "lastChange": ""
}
```

规则：

- `key` 必须是语义 ID，例如 `pie3d.flat-import-inset`；
- 不要用 `ext-47`、`case-42` 这类批次号当能力 ID；
- `sourceStatus` 和 `effectStatus` 是两条独立轴；
- `index.json` 是从这里生成的，**不要反过来改 index 再期望 state 更新**。

`runScope` 是“这次任务选中的能力/case/回归”的工作单，不是总表：

- `features`：总能力账本（所有能力）
- `runScope`：当前任务批次选中的子集
- `queue`：待处理的优先级队列
- `selectedFeature`：当前正在做的那一个能力

> 下面代码块是文档展示，用 `javascript` 高亮；实际 JSON 文件不能带注释。

### 2.2 `capabilities/`

这是模板里最容易被误解的目录。它同时有：

- 能力索引（`index.json`）；
- case 映射（`case-manifest.json`）；
- 能力目录（`README.md`）；
- 新建能力模板（`_TEMPLATE/README.md`）。

#### `capabilities/index.json`

模板里是空账本：

```javascript
{
  // 账本 schema 版本
  "schemaVersion": 1,
  // 生成日期（YYYY-MM-DD）
  "generatedAt": "",
  // 生成来源列表
  "sources": [],
  // 汇总统计
  "summary": {
    // 能力总数
    "capabilities": 0,
    // case 统计
    "cases": {
      // case 总数
      "total": 0,
      // 提供的 case 数
      "provided": 0,
      // 派生的 case 数
      "derived": 0,
      // 已映射到能力的 case 数
      "mapped": 0,
      // 未映射的 case 数
      "unmapped": 0
    }
  },
  // 能力表：每个能力的状态、证据引用、case 引用
  "capabilities": [],
  // 候选能力/缺口
  "backlog": []
}
```

使用后由 `build_capability_index.py` 覆盖，内容：

- 每个 capability 的 `id/name/category/kind/tags`；
- `completion`；
- `source.status`、`source.refs`、`source.verdict`、`source.gap`；
- `effect.status`、`effect.refs`、`effect.verdict`；
- `cases.refs`、`cases.verdicts`；
- `regressionStatus`、`nextState`、`lastChange`、`details`。

**不要手改。** 改 `state.json` / `case.json` 后重新生成。

#### `capabilities/case-manifest.json`

模板里是空清单：

```javascript
{
  // 清单 schema 版本
  "schemaVersion": 1,
  // 生成日期（YYYY-MM-DD）
  "generatedAt": "",
  // 映射说明：capabilities 是候选集，编辑 case 时可细化
  "mappingNote": "capabilities is a candidate set; refine per case when editing it.",
  // case 汇总
  "summary": {
    // case 总数
    "total": 0,
    // 提供的 case 数
    "provided": 0,
    // 派生的 case 数
    "derived": 0,
    // 已映射到能力的 case 数
    "mapped": 0,
    // 未映射的 case 数
    "unmapped": 0
  },
  // case 列表：每个 case 覆盖哪些能力
  "cases": []
}
```

使用后由 `build_capability_index.py` 合并：

1. `corpus/**/case.json`；
2. `evidence/audit/*.json` 中带 `id` 的 case；
3. 上一次的 `case-manifest.json`（人工条目按 `id` 优先保留）。

每个 case 记录：

```javascript
{
  // case ID：<group>/<case>
  "id": "<group>/<case>",
  // 来源：provided=用户/上游提供，derived=源码派生
  "origin": "provided|derived",
  // 类型：fixture / screenshot / trace 等
  "kind": "fixture",
  // case 名称
  "name": "...",
  // 相对工作区的路径
  "path": "corpus/...",
  // 该 case 覆盖的能力 ID
  "capabilities": ["<domain>.<feature>"],
  // 映射来源：declared / audit / manual / unmapped
  "mapping": "declared|audit|manual|unmapped",
  // 效果判定
  "effect": { "status": "PENDING", "notes": "" },
  // 源码判定
  "source": { "status": "PENDING", "notes": "" }
}
```

新增 case 优先写 `corpus/**/case.json`，不要直接手改 `case-manifest.json`。

#### `capabilities/README.md`

模板里是空索引说明。使用后由 `build_capability_index.py` 覆盖，按 `category` 列出：

```text
### <分类>
- [`<feature-id>`](<feature-id>/README.md) — <name> (source ..., effect ...)
```

**不要手改。**

#### `capabilities/_TEMPLATE/README.md`

新建能力的模板。复制成：

```text
capabilities/<feature-id>/README.md
```

包含：

- 观察到的行为；
- 源码/协议证据（地址/函数/公式/边界）；
- case 表；
- 实现文件；
- 验证 / run；
- 缺口 / 下一步。

#### `capabilities/<feature-id>/README.md`（使用后生成）

单个能力的 dossier，是“这个功能怎么还原出来的”唯一叙事入口。

- 生成块：

  ```markdown
  <!-- GENERATED:START -->
  ...
  <!-- GENERATED:END -->
  ```

  由 `build_feature_dossiers.py` 维护，不要手改。

- 块外：人工笔记，生成器不会覆盖。

### 2.3 `corpus/`

模板里只有两个 README，没有实际 case。

| 路径 | 作用 | 模板里有什么 |
|---|---|---|
| `corpus/provided/` | 用户/上游提供的真实输入，覆盖真实场景，不要求最小 | `README.md` |
| `corpus/derived/` | 从源码/协议证据派生的**最小可归因 case** | `README.md` |

使用后每个 case 目录放 `case.json`：

```javascript
{
  // case ID：<group>/<case>
  "id": "<group>/<case>",
  // 来源：provided=用户/上游提供，derived=源码派生
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

“最小”指变量最少、能稳定触发一个分支、结果可观察，不是文件/输入最小。交互项只做 pairwise。

### 2.4 `evidence/`

模板里只有三个 README，没有实际证据。

| 路径 | 作用 | 使用后的典型文件 |
|---|---|---|
| `evidence/source/` | 静态反编译/协议结论 | `<feature-id>-<date>.md` |
| `evidence/source/raw/<date>/` | 原始 dump/裁图，冻结 | `MANIFEST.md` + 原始文件 |
| `evidence/runtime/` | 运行时探针/hook/trace/日志 | `<feature-id>-<date>.jsonl` |
| `evidence/runtime/raw/<date>/` | 会话级原始日志，冻结 | `MANIFEST.md` + 原始日志 |
| `evidence/audit/` | 逐 case 的 source/effect 判定（可选） | `*.json` |

规则：

- feature-id 是主键，日期只用于溯源；
- 原始 dump 放 `raw/`，结论不要放 `raw/`；
- `raw/` 下每个文件都要在 `MANIFEST.md` 里有映射；
- 否定结论也是证据。

### 2.5 `runs/`

| 路径                       | 作用              | 模板里有什么                   |
| ------------------------ | --------------- | ------------------------ |
| `runs/_TEMPLATE/`        | 新 run 模板        | `README.md` + `run.json` |
| `runs/regress-baseline/` | 当前回归基线，只读       | `README.md`              |
| `runs/regress-current/`  | 最近一次回归的临时输出，可覆盖 | `README.md`              |
| `runs/<run-id>/`         | 一次实验/回归的正式记录    | 使用后创建                    |
| `runs/archive/`          | 冻结历史            | 使用后创建                    |

`_TEMPLATE/run.json`：

```javascript
{
  // run ID：YYYY-MM-DD-<feature-id>-NN
  "runId": "YYYY-MM-DD-<feature-id>-NN",
  // 本次 run 对应的能力 ID
  "feature": "<feature-id>",
  // 运行日期
  "date": "YYYY-MM-DD",
  // 复现命令
  "command": "<reproduction command>",
  // baseline 路径
  "baseline": "runs/regress-baseline",
  // 本次运行的 case 列表
  "cases": [],
  // 总体结果：PENDING / MATCH / DIFF / REGRESSION
  "result": "PENDING",
  // 回归列表
  "regressions": [],
  // 备注
  "notes": ""
}
```

正式 run 目录：

```text
runs/<run-id>/
├── run.json
├── result.json
├── shots/          # 或 frames/、traces/
└── logs/
```

`regress-baseline` 只由基线刷新流程更新；`regress-current` 不作为长期证据。

### 2.6 `tools/`

| 文件 | 作用 | 输入 | 输出 |
|---|---|---|---|
| `INDEX.md` | 工具索引 | 无 | 文档 |
| `capabilities/build_capability_index.py` | 生成能力账本 | `state.json`、`corpus/**/case.json`、`evidence/audit/*.json`、旧 manifest | `index.json`、`case-manifest.json`、`README.md` |
| `capabilities/build_feature_dossiers.py` | 生成/刷新 dossier | `index.json`、`case-manifest.json` | `capabilities/<feature-id>/README.md` |
| `capabilities/show_capability.py` | 紧凑查看一个能力 | `index.json`、`case-manifest.json` | 终端摘要 |
| `capabilities/validate_capability_ids.py` | 校验 ID/状态/case/dossier | 上述 + `state.json` + `profile.json` | `OK` / 错误列表 |

标准顺序：

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/build_feature_dossiers.py
python3 tools/capabilities/validate_capability_ids.py
```

### 2.7 `history/`

冻结归档，不作为新工作输入：

| 路径 | 内容 |
|---|---|
| `history/legacy-probes/` | 旧探针，可能依赖已删除 build |
| `history/plans/` | 旧计划、验证记录、一次性清单 |
| `history/rounds/` | 并行轮次规则、patch、请求结果 |
| `history/source-backups/` | `.orig` / 被拒绝的源码备份 |
| `history/state-backups/` | 重大迁移前的 1–2 份 state 快照 |

---

## 3. 模板是怎么被实例化的

模板本身不是工作区，它只是被复制过去。实际初始化有两层：

### 3.1 `reconstruction-scaffold`

`skills/reconstruction-scaffold/scripts/scaffold.py`：

1. 校验 `--domain`；
2. 复制 `reconstruction-core/templates/workspace` 到
   `<project>/.comate/reconstruction-<domain>/`；
3. 把 `PIPELINE.md` / `README.md` 里的 `<workspace>` 替换成实际路径；
4. 解析 profile：
   - JSON profile → 生成 `domain.md` + `profile.json`；
   - Markdown profile → 复制为 `domain.md`；
   - 无 profile → 用 `templates/domain.md` 生成；
5. 写项目配置 `<project>/.comate/reconstruction-<domain>.json`。

### 3.2 `reconstruction-bootstrap`

`skills/reconstruction-bootstrap/scripts/bootstrap.py`：

1. 解析 profile；
2. 调 `scaffold.py` 建工作区；
3. 调 `check_tools.py` 检查 rea/adb/frida 等工具；
4. 调 `ensure_workspace.py` 确认工作区；
5. 跑：
   - `build_capability_index.py`
   - `build_feature_dossiers.py`
   - `validate_capability_ids.py`
6. 写 `bootstrap.json`（初始化记录：profile、工具检查、账本数量）。

### 3.3 `ensure_workspace.py`

`skills/reconstruction-core/scripts/ensure_workspace.py`：

- 解析顺序：`--workspace` → `RECONSTRUCTION_WORKSPACE` → 项目配置 → 已有 `.comate/*/state.json` → `.comate/reconstruction`；
- 工作区不存在时复制模板；
- 已有工作区不覆盖；
- 输出 `WORKSPACE_READY` / `WORKSPACE_CREATED` / `CONFIG`。

---

## 4. 6 阶段运转流程

### Stage 0 — Intake

**输入**：用户 case、源码线索、backlog。

**动作**：

1. 分配 feature-id；
2. 从 `capabilities/_TEMPLATE/README.md` 复制
   `capabilities/<feature-id>/README.md`；
3. 在 `state.json#features` 增加该能力；
4. 在 `corpus/.../case.json` 声明 capability；
5. 运行 build + validate。

**产物**：

```text
capabilities/<feature-id>/README.md
state.json#features
corpus/.../case.json
```

**Gate**：`validate_capability_ids.py` 通过，且能回答“要还原哪个可观察行为”。

### Stage 1 — Source

**输入**：反编译、调试器、协议抓包、运行时 hook。

**动作**：

1. 定位函数/分支/常量/默认值/边界；
2. 记录地址、伪代码、调用链；
3. 区分 EXACT / PARTIAL / FITTED。

**产物**：

```text
evidence/source/<feature-id>-<date>.md
evidence/source/raw/<date>/（如适用）
```

**Gate**：`sourceStatus >= DECODED`，且至少能构造一个 case。

### Stage 2 — Case

**输入**：Stage 1 的分支表。

**动作**：

1. 每个分支至少一个 case：默认 / 显式覆盖 / 边界；
2. 交互项只做 pairwise；
3. case 放进 `corpus/derived/<group>/<case>/`；
4. `case.json` 声明 `capabilities`。

**产物**：

```text
corpus/derived/<group>/<case>/
corpus/derived/<group>/<case>/case.json
```

**Gate**：case 能被参考端打开/执行，输入可复现。

### Stage 3 — Reference

**输入**：Stage 2 的 case。

**动作**：

1. 用 `domain.md` 的参考端命令运行 case；
2. 保存原始输出和归一化产物；
3. 记录参考端版本、采集方式、有效性。

**产物**：

```text
corpus/.../reference/
evidence/runtime/<feature-id>-<date>.jsonl
```

**Gate**：参考输出状态 `ok`；无效采集必须标 `INVALID`。

### Stage 4 — Implement

**输入**：Stage 1 源码结论 + Stage 3 参考。

**动作**：

1. 只改目标实现和对应测试；
2. 在 dossier 记录文件/函数/公式/源码对应关系。

**Gate**：类型检查、单测、构建通过。

### Stage 5 — Verify

**输入**：Stage 4 代码。

**动作**：

1. 单 case：重跑目标端、生成对照产物、记录判定；
2. 定向回归：用输入特征/代码路径筛集合；
3. 必要时全量回归；
4. 结果写入 `runs/<run-id>/`。

**产物**：

```text
runs/<run-id>/
├── run.json
├── result.json
├── shots/
└── logs/
```

**Gate**：

- `effect = MATCH` 或 `ACCEPTED_NONPORTABLE`；
- 无新增 regression；
- 有 diff 的 case 在 dossier 写明原因和状态。

### Stage 6 — Close

**动作**：

1. 更新 `state.json#features` 的 source/effect/nextState；
2. 重建 `capabilities/index.json`；
3. 刷新 dossier；
4. 更新 dossier 的判定/证据/下一步；
5. 回归暴露的旧问题写 `evidence/source/` 并在 backlog 留一条。

**Gate**：

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/build_feature_dossiers.py
python3 tools/capabilities/validate_capability_ids.py
```

必须通过，且 dossier 能独立回答：

- 观察到的行为是什么？
- 源码/协议依据是什么？
- 用了哪些 case？
- 参考输出在哪？
- 目标实现改了哪里？
- 最终判定是什么？残留是什么？

---

## 5. 数据流：谁生成谁

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

关键点：

- `state.json` 是能力状态源头；
- `case.json` 是 case → capability 的显式映射；
- `index.json` / `case-manifest.json` / `README.md` 是派生文件；
- dossier 是结论的叙事入口；
- `validate` 是最后一道门。

---

## 6. 哪些文件不要手改

| 文件 | 原因 |
|---|---|
| `capabilities/index.json` | 由 `build_capability_index.py` 覆盖 |
| `capabilities/case-manifest.json` | 会被重新合并；新增 case 写 `case.json` |
| `capabilities/README.md` | 生成器覆盖 |
| dossier 的 `GENERATED` 块 | `build_feature_dossiers.py` 维护 |
| `runs/regress-baseline/` | 只由基线刷新流程更新 |
| `history/` | 冻结归档 |

## 7. 可以手改

- `state.json#features` / `backlog` / `queue`
- `corpus/**/case.json`
- dossier 的 `GENERATED` 块外
- `domain.md` / `profile.json`
- `PIPELINE.md`（只在改流程时）
- 项目专用 `tools/` 和 `tools/INDEX.md`

---

## 8. 最短路径

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
3. 用 bootstrap 生成一个临时工作区验证
```

---

## 9. 常见反模式

1. **直接改 `index.json`**：下次 build 会被覆盖，state 仍然没变。
2. **把结论只写在对话里**：下次会话找不到。
3. **把原始 dump 和结论混在 `evidence/source/`**：无法检索。
4. **每个分支只跑一个“大而全”的 case**：差异无法归因。
5. **不写 `case.json`，靠目录名猜能力**：生成器不做猜测。
6. **回归产物写在 `runs/regress-current/` 当长期证据**：它随时会被覆盖。
7. **把历史目录当输入**：`history/` 和 `runs/archive/` 是冻结的。

---

## 10. 一句话总结

**模板把“输入、证据、case、实现、运行、结论”固定成一套可回指的路径；
`state.json` 记状态，`capabilities/` 记账本和故事，`PIPELINE.md` 记流程。**
