# 多子 agent 协作模式

一个 skill、一个工作区、多个 agent。skill 仍是唯一行为契约；子 agent 只是
执行单元，不各自发明流程。

## 什么时候拆

适合拆：

- 多个独立能力/模块并行
- 静态取证、运行时取证、实现、回归可以并行
- 批量 case 核对

不适合拆：

- 单个能力、强耦合的模块改动
- 需要频繁改共享文件（`state.json`、账本、核心布局/渲染文件）
- 还没有清晰 ownership 边界

## 角色

| 角色 | 职责 | 写权限 |
|---|---|---|
| Coordinator | 维护 skill/state/账本，分派任务，合并 patch，跑全量回归 | `state.json`、`capabilities/index.json`、`case-manifest.json`、`PIPELINE.md`、dossier |
| Source agent | 反编译/反汇编/协议静态取证 | 只能写 `evidence/source/<feature-id>-<date>.md` |
| Runtime agent | 参考端/运行时采集（全局唯一） | 只能写 `evidence/runtime/...`、`corpus/**/reference` |
| Impl agent | 按模块实现 + 单测 | 只能改分配的文件 |
| Verify agent | 对照、指标、定向回归 | 只能写 `runs/<run-id>/` |

**Coordinator 是唯一能改共享文件和最终状态的人。** 子 agent 不写
`state.json`、`capabilities/index.json`、`case-manifest.json`。

## Ownership 规则

1. 每个文件同一时间只有一个 writer。
2. 共享文件改动走 patch：
   ```
   runs/<run-id>/patches/<from>-to-<to>-<topic>.patch
   ```
   由目标 owner 或 coordinator 应用，应用后加 `.APPLIED`。
3. 参考端/运行时资源（真机、模拟器、浏览器、调试器、截图进程）只允许一个 agent
   占用；其他 agent 把请求写到 `runs/<run-id>/requests.md`，由 runtime agent
   串行执行。
4. Impl agent 不得修改别人 ownership 的文件；需要时写 patch 或请求。
5. 子 agent 不再 spawn 子 agent（深度限制 1），避免上下文失控。

## 任务 brief

每个子 agent 只给最小上下文：

```
feature-id：
目标：
只读输入：PIPELINE.md、capabilities/<id>/README.md、指定 evidence/case
允许修改：
禁止修改：
预期输出：
停止条件：
```

禁止让子 agent “自己去看整个工作区”。

## 报告格式

每个子 agent 返回结构化报告：

```
status: DONE | PARTIAL | BLOCKED
源码地址 / 函数 / 字段：
修改文件：
测试 / 命令：
效果 / 指标：
账本行：
共享文件 patch：
请求（运行时/采集）：
gaps / next step:
```

Coordinator 只把报告写进 dossier/state，不把整段对话塞回主上下文。

## 推荐并行方式

```
Coordinator
├── Source agent A (模块 A)
├── Source agent B (模块 B)
├── Source agent C (模块 C)
├── Runtime agent (唯一)
├── Impl agent (按模块)
└── Verify agent
```

实际分工按**文件/模块 ownership** 切，保证同一文件只有一个 writer。

- Source agents 先并行取证，产出 evidence。
- Runtime agent 按请求队列串行采集。
- Impl agents 在 disjoint 文件上并行实现。
- Verify agent 跑单 case / 定向回归。
- Coordinator 合并 patch、更新账本、跑全量回归。

## 回归边界

- 子 agent 只跑自己 case 的定向回归和单测。
- 全量回归、baseline 刷新、状态收口只由 coordinator 执行。
- 子 agent 不修改 `runs/regress-baseline`。

## 上下文预算

- 每个子 agent 只读：`PIPELINE.md` + 自己的 dossier + 分配的文件。
- 不重扫 `evidence/`、`runtime/`、`corpus/`。
- 长日志写文件，报告只给路径和关键数字。
- 两次探针拿不到结论就停止，写 `BLOCKED`/`PARTIAL` 并给出下一步。

## 冲突处理

- 两个 agent 改同一文件：后写者停止，改为 patch 交给 owner。
- 两个 agent 得出冲突结论：以源码 + 参考效果证据为准，coordinator 裁决。
- 共享资源冲突：runtime 请求排队，禁止并发启动参考端/调试器。
