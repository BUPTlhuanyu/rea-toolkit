# corpus/provided

用户、上游或参考实现提供的输入语料。只读，不改名、不移动。

每个 case 一个目录，建议放 `case.json` 声明能力映射：

```json
{
  "id": "<group>/<case>",
  "origin": "provided",
  "kind": "fixture",
  "capabilities": ["<domain>.<feature>"],
  "effect": { "status": "PENDING" },
  "source": { "status": "PENDING" }
}
```

参考端输出放在该 case 目录的 `reference/` 下。
