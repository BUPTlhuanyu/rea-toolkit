# 复刻工作区

把本目录复制到项目的 `.comate/<workspace>/`，然后：

0. 推荐用 `reconstruction-bootstrap` skill 自动完成初始化（生成工作区、检查工具链、
   初始化账本）。
1. 在 `PIPELINE.md` 和 `README.md` 中替换 `<workspace>` / `<project>`。
2. 补齐 `domain.md`（人类可读）和 `profile.json`（机器可读，可选）。
3. 填写 `state.json`：
   - `features`：每个能力一个语义 ID（`<domain>.<feature>`）
   - `backlog` / `queue`
   - `runScope`
4. 把输入语料放到 `corpus/provided/`，源码派生的 case 放到 `corpus/derived/`。
5. 运行：

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/build_feature_dossiers.py
python3 tools/capabilities/validate_capability_ids.py
```

## 目录

```
<workspace>/
├── PIPELINE.md
├── README.md
├── domain.md
├── profile.json
├── state.json
├── capabilities/
├── corpus/
├── evidence/
├── runs/
├── history/
└── tools/
```

只复制这个脚手架，不要复制参考工作区的 `corpus/`、`evidence/`、`runs/`。

## case.json

每个 case 目录放一个 `case.json`，显式声明它覆盖哪些能力：

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

账本生成器会扫描 `corpus/**/case.json`，不会按目录名猜能力。
