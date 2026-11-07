---
name: reconstruction-core
description: 通用源码驱动复刻与行为对齐流水线。用于任何“有参考实现、有源码/反编译证据、需要逐项证明源码一致且效果一致”的还原任务。提供能力账本、case/证据/run 契约、6 阶段流程、状态机、多 agent 协作和上下文效率规则；具体源码位置、参考端运行方式、目标端构建和领域术语由项目 domain profile 提供。
---

# 通用复刻核心

目标不是“看起来差不多”，而是同时证明：

1. 实现结构与参考源码的关键路径一致；
2. 可观测效果与参考实现一致；
3. 每个差异都有证据支持的归因。

任一条件缺失，不能标记完成。

## 启动检查（每轮先做）

```bash
python3 <skill-dir>/scripts/ensure_workspace.py
```

解析顺序：

1. `--workspace <path>`
2. `RECONSTRUCTION_WORKSPACE`
3. `<project>/.comate/reconstruction.json`
4. 已存在的 `.comate/*/state.json` + `PIPELINE.md`
5. `.comate/reconstruction`

输出：

- `WORKSPACE_READY <path>`：读 `state.json` 继续
- `WORKSPACE_CREATED <path>`：读 `PIPELINE.md` 开始
- `CONFIG <path>`：项目配置

**新项目**先用 `reconstruction-bootstrap` 初始化（选 profile、查工具链、建工作区、
建账本），不要手工复制模板。

## 领域配置

领域差异不写进本 skill。项目提供：

```
.comate/reconstruction-<domain>/domain.md     # 人类可读
.comate/reconstruction-<domain>/profile.json  # 机器可读（可选）
```

至少声明：

- `name`
- `platform`
- `source_roots`
- `reference_runtime`
- `target_runtime`
- `comparison`
- `required_evidence`
- `acceptance_rules`
- `verification_commands`

没有领域配置时先创建，再开始实现。新建工作区用 `reconstruction-bootstrap`。

## 工作区

默认结构见 `templates/workspace/PIPELINE.md`：

```
<workspace>/
├── PIPELINE.md
├── domain.md / profile.json
├── state.json
├── capabilities/       # index + case-manifest + <feature-id>/README.md
├── corpus/             # provided / derived / **/case.json
├── evidence/           # source / runtime / audit
├── runs/               # _TEMPLATE / current / archive
├── tools/
└── history/
```

所有结论必须能回指文件、方法、地址、case、run 或截图。

case 与能力的映射写在 `corpus/**/case.json`：

```json
{
  "id": "<group>/<case>",
  "origin": "provided|derived",
  "kind": "fixture",
  "capabilities": ["<domain>.<feature>"]
}
```

账本生成器不按目录名猜能力。

## 六阶段

### 0. Intake / 建档

- 分配语义 feature-id：`<domain>.<feature>[.<variant>]`
- 建 `capabilities/<feature-id>/README.md`
- 登记 case（origin / capability / XML/协议签名）
- 运行 `validate_capability_ids.py`

### 1. Source / 源码

- 定位源码/反编译函数、分支、常量、默认值、边界
- 产出 `evidence/source/<feature-id>-<date>.md`
- 明确 EXACT / PARTIAL / FITTED

### 2. Case / 构造

- 每个分支一个最小 case：默认、显式覆盖、边界
- 交互项只做 pairwise
- 登记到 `capabilities/case-manifest.json`

### 3. Reference / 参考

- 运行参考实现并采集输出
- 保存 raw + cropped 产物及 manifest
- 记录参考端版本、采集方式、有效性

### 4. Implement / 实现

- 只改目标实现和对应测试
- 记录文件/函数/公式
- 通过 typecheck / 单测

### 5. Verify / 验证

- 目标输出 + 对照图 + MAE/判定
- 定向回归，收口时再全量
- 结果写入 `runs/<run-id>/` 或 `runs/regress-current/`

### 6. Close / 收口

- 更新 `capabilities/index.json`
- 刷新 dossier
- 运行 `validate_capability_ids.py`
- 记录残留、next step、blocked

## 状态

source：`UNKNOWN / LOCATED / DECODED / EXACT / PARTIAL / NONPORTABLE`

effect：`PENDING / MATCH / DIFF / NO_REFERENCE / ACCEPTED_NONPORTABLE`

完成 = source EXACT/NONPORTABLE + effect MATCH/ACCEPTED_NONPORTABLE/NO_REFERENCE + 回归通过 + dossier 更新。

## 参考文件（按需加载）

- `references/pipeline.md`：目录、命名、阶段细节
- `references/evidence.md`：证据/状态/dossier 契约
- `references/multi-agent.md`：多 agent ownership
- `references/efficiency.md`：上下文与 token 经济

## 硬规则

1. 先读 `capabilities/index.json` 和 dossier，再动手。
2. 新产物只写 `PIPELINE.md` 定义的路径。
3. 结论必须有 evidence + case + run。
4. 源码优先，效果兜底；拟合值标 PARTIAL。
5. 一次只改一个 feature。
6. 回归按 XML/协议特征 + 代码路径筛集合。
7. 历史目录只读。
8. 每次改 capabilities/case-manifest 后跑校验。
9. 子 agent 只在 disjoint 文件上并行；共享文件走 patch；参考端只允许一个 agent 操作。
