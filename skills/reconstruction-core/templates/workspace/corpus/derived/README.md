# corpus/derived

从源码/协议证据派生的最小 case。每个分支至少一个：

- 默认值
- 显式覆盖
- 边界（0 / 最大 / 负值 / 缺省）

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

交互项只做 pairwise，不做全排列。
