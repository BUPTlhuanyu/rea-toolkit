# 流程参考

工作区里的 `<workspace>/PIPELINE.md` 是唯一流程入口。本文件只解释设计理由和
扩展点，避免在 core skill 里重复整份目录契约。

## 为什么固定目录

- 全局目录按产物类型：输入在 `corpus/`，证据在 `evidence/`，运行结果在 `runs/`。
- 能力档案按能力组织：`capabilities/<feature-id>/README.md` 串起 source、case、
  effect、run。
- 换模型、换会话时，只读 dossier 就能知道“这个能力怎么还原出来的”。

## 固定契约

- feature-id：`<domain>.<feature>[.<variant>]`
- case-id：`<group>/<case>`，映射写在 `corpus/**/case.json`
- run-id：`YYYY-MM-DD-<feature-id>-NN`
- source 证据：`evidence/source/<feature-id>-<date>.md`
- runtime 证据：`evidence/runtime/<feature-id>-<date>.jsonl`
- 原始产物：`evidence/*/raw/<date>/` + `MANIFEST.md`

## 六阶段

1. Intake：建 feature 档案，登记 case。
2. Source：定位函数/字段/分支/常量/边界，产出证据。
3. Case：每个分支一个最小 case，登记能力映射。
4. Reference：运行参考端，保存原始与归一化产物。
5. Implement：只改目标实现和测试。
6. Verify/Close：对照、定向回归、更新账本和 dossier。

每个阶段的门禁见工作区 `PIPELINE.md`。

## 领域扩展点

- 参考端如何启动、如何采集。
- 目标端如何构建、如何测试。
- 对照用什么指标和产物。
- 工具链如何检查。
- 哪些差异属于平台/环境不可移植。

这些全部写在 `domain.md` / `profile.json`；不要改 core 流程。
