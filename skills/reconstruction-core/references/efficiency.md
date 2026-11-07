# 上下文与效率

## 先查索引，不读大文件

不要把大段 state/index 读进上下文。用辅助脚本：

```bash
python3 tools/capabilities/show_capability.py <feature-id>
python3 tools/capabilities/show_capability.py --grep <关键字>
```

需要机器数据时，用 `python3 -c` 或 `jq` 精确取字段，不要 `cat`。

## 一次只读一个功能

按 dossier 链接读：

```
capabilities/<feature-id>/README.md
  -> source refs
  -> case paths
  -> effect refs
  -> run
```

不要为了重建上下文重扫整个 evidence 目录。

## 先看 MANIFEST

```
evidence/source/raw/<date>/MANIFEST.md
evidence/runtime/raw/<date>/MANIFEST.md
```

定位到 1–2 个文件，再 `rg` / `sed` 读片段。

## 批量工具

- 静态：一次 dump 多个地址。
- 运行时：一次会话多个 hook。
- 截图：一次浏览器/进程批量处理多个 case。
- 回归：分片并行，已生成的 shot 可复用。

## 探针预算

- 一次探针只回答一个问题；
- 同一次运行同时记录输入和输出；
- 连续两次拿不到结论，停止深挖，改 effect-diff 或换入口；
- 否定结论也要落盘。

## 回归分层

```
单 case -> 定向集合（特征 + 代码路径） -> 全量
```

全量只在收口或大改后跑。

## 输出摘要，不输出流水

- 脚本写 `run.json` / `result.json`；
- 终端只打印汇总；
- 长日志写文件，回复只给路径和关键数字。

## 构建缓存

- 快构建与昂贵资源重建分开；
- 输入没变时复用已有截图/产物。

## 交接

新会话只读：

1. `PIPELINE.md`
2. `capabilities/<feature-id>/README.md`
3. 当前 `state.json` 的 queue/backlog 摘要（用脚本取）
