# 证据与状态契约

## 两轴

- source：`UNKNOWN / LOCATED / DECODED / EXACT / PARTIAL / NONPORTABLE`
- effect：`PENDING / MATCH / DIFF / NO_REFERENCE / ACCEPTED_NONPORTABLE`

只有两轴都闭合且回归通过，能力才算完成。

## 证据文件

功能级结论：

```
evidence/source/<feature-id>-<YYYY-MM-DD>.md
evidence/runtime/<feature-id>-<YYYY-MM-DD>.jsonl
```

会话级原始产物：

```
evidence/source/raw/<YYYY-MM-DD>/MANIFEST.md
evidence/runtime/raw/<YYYY-MM-DD>/MANIFEST.md
```

规则：

- feature-id 是主键，日期只用于溯源。
- 原始 dump 放 `raw/<date>/`，不要复制到每个功能笔记。
- `raw/` 下每个文件都要在 MANIFEST 中有映射。
- 否定结果也是证据。

## Case

- case id：`<group>/<case>`
- 每个 case 目录放 `case.json`，声明 `origin`（`provided` / `derived`）、
  `capabilities` 列表和输入签名。
- 一个 case 可以覆盖多个 capability；一个 capability 至少有一个 case。
- 账本生成器只读显式映射，不按目录名猜能力。

## Run

```
runs/<run-id>/
├── run.json
├── result.json
├── shots/          # 或 frames/、traces/，按领域约定
└── logs/
```

`runs/regress-current/` 是可覆盖的临时输出；`runs/archive/` 是冻结历史。

## Dossier

每个 capability 必须有 `capabilities/<feature-id>/README.md`：

- observed behavior
- source 地址/公式/边界
- cases
- effect refs
- 实现文件
- run / regression
- 残留 / 下一步

结论不能只存在于对话里，必须写进 dossier 或 evidence 文件。
