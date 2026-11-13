# 复刻流程与目录契约

> 模板：把 `<workspace>` / `<project>` 替换成实际路径。领域差异写在
> `domain.md` 和 `profile.json`，不要改本文的流程骨架。

本文是 `<workspace>` 的唯一流程入口。目的：无论换哪个模型、隔多久继续，
都能按同一套步骤、同一套路径回答“这个能力是怎么还原出来的”，而不是靠会话记忆
或临时目录。

---

## 1. 目录契约

```
<workspace>/
├── PIPELINE.md                 # 本文，流程唯一入口
├── README.md                   # 项目地图
├── domain.md                   # 领域配置（人类可读）
├── profile.json                # 领域配置（机器可读，可选）
├── state.json                  # 机器状态（features / backlog / queue）
│
├── capabilities/               # 能力账本 + 每能力档案
│   ├── index.json              # 规范化能力表（source/effect/refs/status）
│   ├── case-manifest.json      # case -> capability 映射
│   ├── README.md               # 能力索引（生成）
│   └── <feature-id>/
│       └── README.md           # 该能力“怎么还原出来”的一页档案
│
├── corpus/                     # 输入语料，只读
│   ├── provided/               # 用户/上游提供的参考输入
│   ├── derived/                # 从源码证据派生的最小 case
│   └── **/case.json            # 可选：每个 case 的声明文件
│
├── evidence/                   # 结论与原始证据
│   ├── source/                 # 静态反编译结论、公式、地址、补丁说明
│   │   └── raw/<date>/         # 原始 dump/反编译产物（冻结）
│   ├── runtime/                # 运行时探针、hook、日志
│   │   ├── <feature-id>-<date>.jsonl
│   │   └── raw/<date>/         # 会话级原始日志（冻结，附 MANIFEST）
│   └── audit/                  # 逐 case 的 source/effect 判定（可选）
│
├── runs/                       # 可重建的运行产物
│   ├── regress-baseline/       # 当前回归基线（只读）
│   ├── regress-current/        # 最近一次定向/全量回归输出
│   ├── archive/                # 冻结的历史产物
│   ├── _TEMPLATE/
│   └── <run-id>/               # 一次实验/回归
│       ├── run.json
│       ├── result.json
│       ├── shots/
│       └── logs/
│
├── tools/                      # 所有可执行脚本
│   ├── capabilities/           # 账本生成/校验/查询
│   └── INDEX.md
│
└── history/                    # 冻结归档：过程/协调/备份
    ├── rounds/
    ├── plans/
    ├── legacy-probes/
    ├── source-backups/
    └── state-backups/
```

### 全局目录 vs 能力档案

- **全局目录按“产物类型”组织**：输入在 `corpus/`，证据在 `evidence/`，运行结果在
  `runs/`。
- **能力档案按“能力”组织**：`capabilities/<feature-id>/README.md` 把散落在全局
  目录里的 source、runtime、case、run 串起来。
- 不把大文件复制进能力档案；档案里只放**链接、结论、状态、下一步**。

### runs/regress-current 与 archive

`runs/regress-current/` 是最近一次回归的临时输出，可随时覆盖，不是长期证据。
需要正式留档时写入 `runs/<run-id>/`；退休的 run 整体移入
`runs/archive/<date>-<purpose>/`。

`runs/archive/` 存运行产物；`history/` 存过程/协调/备份。两者都只读。

---

## 2. 命名

### 2.1 feature-id

```
<domain>.<subfeature>[.<variant>]
```

示例：

```
parser.element.attribute-fallback
renderer.text.vertical-metrics
network.retry.backoff
scene.lighting.shadow-bias
```

要求：

- 全小写、点分、短横线分词。
- 一个 feature 对应一个可独立判定的行为，不要用“杂项”“其他”。
- ID 一旦写入 `capabilities/index.json`，不再改名；必须改名时保留旧 ID 的档案并
  在 dossier 里写迁移说明。
- 不要用 `ext-NN`、`case-42` 这类批次号当能力 ID。

白名单（可选）写在 `profile.json` 的 `id_domains`，校验器会检查第一段。

### 2.2 case-id

```
<group>/<case>
```

case 路径相对 `corpus/`。新 case 放进 `corpus/derived/<group>/<case>/`，并在目录里
放 `case.json`：

```json
{
  "id": "<group>/<case>",
  "origin": "derived",
  "kind": "fixture",
  "capabilities": ["<domain>.<feature>"],
  "effect": { "status": "PENDING", "notes": "" },
  "source": { "status": "PENDING", "notes": "" }
}
```

`case.json` 是 case 与能力的显式映射；没有它时，账本不会按目录名猜能力。

### 2.3 run-id

```
YYYY-MM-DD-<feature-id>-NN
```

例如：

```
runs/2026-11-07-parser.element.attribute-fallback-01/
```

### 2.4 evidence 文件

**结论/笔记：feature 在前，日期在后。**

```
evidence/source/<feature-id>-<YYYY-MM-DD>.md
evidence/runtime/<feature-id>-<YYYY-MM-DD>.jsonl
```

**会话级原始 dump/日志：按日期分桶，并附 `MANIFEST.md`。**

```
evidence/source/raw/<YYYY-MM-DD>/
evidence/runtime/raw/<YYYY-MM-DD>/
```

原始 dump 往往一次覆盖多个功能，不适合按 feature 拆；必须在同目录
`MANIFEST.md` 里写清每个文件对应的函数/feature/case。

禁止再用 `dump.txt`、`probe.jsonl`、`tmp-xxx` 这类无法检索的名字。

---

## 3. 状态模型

source 与 effect 分开记录，互不替代。

### source

| 状态 | 含义 |
|---|---|
| `UNKNOWN` | 还没定位 |
| `LOCATED` | 找到函数/地址/协议字段，但语义未解 |
| `DECODED` | 分支/公式已解，边界未完全验证 |
| `EXACT` | 公式、默认值、边界、分支均有源码/运行时证据 |
| `PARTIAL` | 有拟合常量或未闭合分支 |
| `NONPORTABLE` | 参考实现行为无法/不需要复刻，且有理由 |

### effect

| 状态 | 含义 |
|---|---|
| `PENDING` | 还没有对照 |
| `MATCH` | 与参考实现对照通过 |
| `DIFF` | 有可复现差异 |
| `NO_REFERENCE` | 无法获得参考输出（仅 source 结论） |
| `ACCEPTED_NONPORTABLE` | 差异已判定为平台/环境/采集不可移植 |

### 完成判定

一个 feature 只有同时满足以下条件才能标 `complete`：

1. `source = EXACT` 或 `NONPORTABLE`（有理由）；
2. `effect = MATCH` 或 `ACCEPTED_NONPORTABLE` / `NO_REFERENCE`；
3. 定向回归无新增 regression；
4. `capabilities/<feature-id>/README.md` 已更新；
5. `capabilities/index.json` 已由生成器重建；
6. `validate_capability_ids.py` 通过。

---

## 4. 标准流程（每个能力都走这 6 步）

### Step 0 — Intake / 建档

输入：用户 case、源码线索、或 backlog 项。

动作：

1. 分配 `feature-id`；
2. 从 `capabilities/_TEMPLATE/` 创建 `capabilities/<feature-id>/README.md`；
3. 在 `state.json#features` 登记，状态先写 `UNKNOWN` / `PENDING`；
4. 如有 case，在 `corpus/` 放 `case.json` 并写 `capabilities`。

产出：

```
capabilities/<feature-id>/README.md
state.json#features
```

Gate：

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/validate_capability_ids.py
```

必须通过；同时能回答“要还原哪个可观察行为”。

---

### Step 1 — Source / 源码取证

输入：反编译结果、调试器、协议抓包、运行时 hook、符号/字符串。

动作：

1. 定位函数/分支/常量/协议字段；
2. 记录地址、伪代码、调用链、默认值、边界；
3. 明确哪些是 EXACT，哪些是 FITTED/PARTIAL。

产出：

```
evidence/source/<feature-id>-<date>.md
evidence/source/raw/<date>/（如适用）
```

Gate：`sourceStatus >= DECODED`，且能列出至少一个可构造的 case。

禁止：只看效果猜公式；拟合常量必须写进证据文件并标 `PARTIAL`。

---

### Step 2 — Case construction / 构造 case

输入：Step 1 的分支表。

动作：

1. 每个分支至少一个 case：默认、显式覆盖、边界（0/最大/负值）；
2. 交互项只做 pairwise，不做全排列；
3. case 放进 `corpus/derived/<group>/<case>/`；
4. 在 `case.json` 记录 `capabilities` 和预期行为。

产出：

```
corpus/derived/<group>/<case>/
corpus/derived/<group>/<case>/case.json
```

Gate：case 能被参考端打开/执行，且输入可复现。

---

### Step 3 — Reference / 参考采集

输入：Step 2 的 case。

动作：

1. 用 `domain.md` 里的参考端命令运行 case；
2. 保存原始输出（截图/日志/trace/帧）和裁剪/归一化产物；
3. 记录参考端版本、采集方式、有效性。

产出（按领域选择）：

```
corpus/derived/<group>/<case>/reference/
evidence/runtime/<feature-id>-<date>.jsonl
```

Gate：参考输出状态 `ok`；无效采集必须标 `INVALID` 并说明原因，不能当有效参考。

---

### Step 4 — Implementation / 实现

输入：Step 1 源码结论 + Step 3 参考。

动作：

1. 只改目标实现和对应测试；
2. 在 `capabilities/<feature-id>/README.md` 记录：
   - 改了哪些文件/函数
   - 关键公式/规则
   - 与源码的对应关系。

Gate：

```bash
# 使用 domain.md 里 target_runtime / verification_commands
```

类型检查、单测、构建必须通过。

---

### Step 5 — Verification / 效果与回归

输入：Step 4 代码。

动作：

1. 单 case：重跑目标端、生成对照产物、记录判定；
2. 定向回归：用输入特征/协议字段/代码路径筛受影响 case；
3. 必要时全量回归；
4. 结果写入新的 `runs/<run-id>/`。

产出：

```
runs/<run-id>/
├── run.json          # 命令、feature、case 列表、baseline
├── result.json       # 每 case 判定/指标
├── shots/            # 目标端/对照产物
└── logs/             # stdout / stderr
```

`run.json` 最小结构：

```json
{
  "runId": "2026-11-07-parser.element.attribute-fallback-01",
  "feature": "parser.element.attribute-fallback",
  "date": "2026-11-07",
  "command": "<reproduction command>",
  "baseline": "runs/regress-baseline",
  "cases": ["<group>/<case>"],
  "result": "MATCH",
  "notes": ""
}
```

Gate：

- `effect = MATCH` 或 `ACCEPTED_NONPORTABLE`；
- 无新增 regression（阈值按 domain.md 约定）；
- 有 diff 的 case 必须在 dossier 里写明原因和状态。

---

### Step 6 — Close / 收口

动作：

1. 更新 `state.json#features` 的 source/effect/nextState；
2. 重建 `capabilities/index.json`；
3. 刷新 dossier；
4. 更新 `capabilities/<feature-id>/README.md` 的判定/证据/下一步；
5. 如果回归暴露旧问题，写入 `evidence/source/` 并在 backlog 留一条。

Gate：

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/build_feature_dossiers.py
python3 tools/capabilities/validate_capability_ids.py
```

必须通过，且 dossier 能独立回答：

- 这个能力观察到的行为是什么？
- 源码/协议依据是什么（地址/公式/边界）？
- 用了哪些 case？
- 参考输出在哪？
- 目标实现改了哪里？
- 最终判定是什么？残留是什么？

---

## 5. 能力档案（dossier）模板：`capabilities/<feature-id>/README.md`

dossier 是**单个能力的档案/故事**，不是代码模板。模板文件在
`capabilities/_TEMPLATE/README.md`；新建能力时复制它到
`capabilities/<feature-id>/README.md`。

模板保证每个能力都回答同一组问题：观察到什么、源码依据是什么、用了哪些 case、
改了哪里、怎么验证、还差什么。

```markdown
# <能力名> (`<feature-id>`)

- 分类：<category>
- 类型/对象：<kind>
- 标签/协议：<tags>
- Source：<status>
- Effect：<status>
- Completion：<complete / effect-matched-source-partial / partial>

## 1. 观察到的行为

<参考实现的实际表现；贴对照产物路径>

## 2. 源码/协议证据

- 地址/函数/字段：
- 公式/规则：
- 默认值/边界：
- 证据文件：`evidence/source/...`
- 确定性：EXACT / PARTIAL / FITTED

## 3. Case

| case | origin | 参考输出 | 目标输出 | 状态 |
|---|---|---|---|---|
| ... | provided/derived | path | path | MATCH/DIFF |

## 4. 实现

- 文件：
- 关键函数：
- 测试：

## 5. 验证 / run

- run-id：
- 命令：
- 结果：
- 回归：

## 6. 缺口 / 下一步

<剩余工作、负责人、下一个具体动作>
```

生成器会从 `capabilities/index.json` + `case-manifest.json` 自动生成骨架；
人工补充“观察到的行为 / 关键函数 / 缺口”。

---

## 6. 防止“换个模型就换一套思路”的硬规则

1. **先读 `capabilities/index.json` 和对应 dossier，再动手。** 没有档案先建档案。
2. **每次改 `capabilities/`、`case-manifest.json` 或 `state.json#features` 后必须跑**
   `python3 tools/capabilities/build_capability_index.py` 和
   `validate_capability_ids.py`；不允许带着校验错误继续。
3. **新产物只能写到本文定义的路径。** 不新建 `runs/foo-001`、`tmp/xxx`、`cases2/`。
4. **每个结论必须有 evidence 文件 + case + run 三件套。** 只有截图/日志不算证据。
5. **源码优先，效果兜底。** 不能为了指标静默调常量；拟合值必须标 `PARTIAL`。
6. **一次只改一个 feature。** 跨 feature 的改动必须拆成多个 run。
7. **回归用输入特征 + 代码路径筛集合。** 不做无边界的全量重跑，除非收口。
8. **历史目录只读。** `runs/archive/`、`history/`、`evidence/*/raw/` 不作为新工作的
   输入或输出。
9. **dossier 是唯一叙事入口。** 任何人想知道“怎么还原的”，只读
   `capabilities/<feature-id>/README.md` 及其链接。
10. **领域差异只写 `domain.md` / `profile.json`。** 不改 core 流程和目录骨架。

---

## 7. 常用命令

```bash
# 重建能力账本（会合并 corpus/**/case.json）
python3 tools/capabilities/build_capability_index.py

# 校验 ID/case/dossier
python3 tools/capabilities/validate_capability_ids.py

# 不读大账本，直接看一个能力
python3 tools/capabilities/show_capability.py <feature-id>
python3 tools/capabilities/show_capability.py --grep <关键字>

# 生成/刷新每能力 dossier 骨架
python3 tools/capabilities/build_feature_dossiers.py

# 参考端 / 目标端命令见 domain.md
```

---

## 8. 上下文与效率

目标：不要因为目录大、日志长、case 多，把上下文耗在重复读取上。

### 8.1 先查索引，不读大文件

- 不要全文读 `state.json` 或 `capabilities/index.json`。
- 用 `show_capability.py`；需要机器数据时用 `python3 -c` / `jq` 精确取字段。

### 8.2 一次只读一个能力的文件集

```
capabilities/<feature-id>/README.md
  -> source refs
  -> case paths
  -> effect refs
  -> run
```

### 8.3 原始证据看 MANIFEST，不逐个打开

```
evidence/source/raw/<date>/MANIFEST.md
evidence/runtime/raw/<date>/MANIFEST.md
```

### 8.4 批量工具优先于逐条操作

- 反编译/调试器一次 dump 多个地址，不每个函数重启一次。
- 运行时 hook 一次会话跑多个 hook，结果写一个 JSONL。
- 截图/回归一次批量处理，不每个 case 启一次进程。

### 8.5 探针预算

- 一次探针只回答一个问题。
- 同一次运行同时记录输入和输出。
- 连续两次拿不到规则，停止静态深挖，改效果 diff 或换入口。
- 否定结论也写进 evidence，避免下一个人重走。

### 8.6 回归分层

```
单 case -> 定向集合（输入特征 + 代码路径） -> 全量
```

不要每改一行都跑全量；全量只在收口或大改后跑。

### 8.7 输出摘要，不输出原始流水

- 脚本写 `run.json` / `result.json`，终端只打印汇总。
- 长日志写文件，回复里只引用路径和关键数字。

### 8.8 交接只读三样

1. `PIPELINE.md`
2. `capabilities/<feature-id>/README.md`
3. `state.json` 的当前 queue/backlog（用脚本取摘要，不全文读）

---

## 9. 一句话总结

**全局目录存“证据和产物”，`capabilities/<feature-id>/` 存“这个能力的故事”。**

领域差异只写在 `domain.md` / `profile.json`；流程、目录、状态和证据契约保持稳定。
