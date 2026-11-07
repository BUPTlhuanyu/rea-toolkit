# evidence/audit

可选的逐 case source/effect 判定。每个文件一个 case 组，case 必须显式写 `id`：

```json
{
  "cases": [
    {
      "id": "<group>/<case>",
      "capabilities": ["<domain>.<feature>"],
      "source": { "status": "EXACT", "notes": "" },
      "effect": { "status": "MATCH", "notes": "" }
    }
  ]
}
```

`tools/capabilities/build_capability_index.py` 会合并这里的显式条目。
