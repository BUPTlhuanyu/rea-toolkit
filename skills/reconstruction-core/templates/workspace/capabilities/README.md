# 能力账本

由 `tools/capabilities/build_capability_index.py` 从 `state.json`、
`corpus/**/case.json` 和 `capabilities/case-manifest.json` 生成。

每个能力的档案在 `capabilities/<feature-id>/README.md`。

命令：

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/build_feature_dossiers.py
python3 tools/capabilities/validate_capability_ids.py
python3 tools/capabilities/show_capability.py <feature-id>
```
