---
name: <domain>
source_roots:
  - <source-root>
reference_runtime:
  commands:
    - <reference-command>
  outputs:
    - <comparison>
target_runtime:
  commands:
    - <target-command>
comparison:
  method: <comparison>
required_evidence:
  source:
    - file
    - symbol/address
    - control-flow notes
  effect:
    - reference input
    - reference output
    - target output
    - comparison verdict
acceptance_rules:
  require_source_exact: true
  require_effect_match: true
  allow_approximation_as_complete: false
verification_commands:
  - <target-command>
---

## Domain rules

- 参考端、目标端和产物形式由本文件决定。
- 只有本领域要求时才引入额外宿主或截图。
- 无法打开的参考输入记录为 `REFERENCE_DEFECT` / `INPUT_INVALID`。
- 领域特有的差异归因写在这里，不写进 core。
