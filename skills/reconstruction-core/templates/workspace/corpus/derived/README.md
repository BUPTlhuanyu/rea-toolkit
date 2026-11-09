# corpus/derived

从源码/协议证据派生的**最小可归因 case**。

这里的“最小”不是文件最小、输入最少，而是**变量最少、能稳定触发一个分支、
结果可观察**。一个 case 只回答一个规则问题；多个规则同时变化时，出现差异
无法判断是哪一条规则造成的。

每个分支至少一个：

- 默认值
- 显式覆盖
- 边界（0 / 最大 / 负值 / 缺省）

如果一个场景必须多个特性共同作用才能复现，它就不是“最小 case”：

- 放到 `corpus/provided/` 作为真实/集成输入
- 或用 pairwise 组合单独登记，不要把它当成单分支证据

每个 case 目录放 `case.json`：

```json
{
  "id": "<group>/<case>",
  "origin": "derived",
  "kind": "fixture",
  "capabilities": ["<domain>.<feature>"],
  "effect": { "status": "PENDING" },
  "source": { "status": "PENDING" }
}
```

交互项只做 pairwise，不做全排列。目标是覆盖分支，不是穷举输入空间。
