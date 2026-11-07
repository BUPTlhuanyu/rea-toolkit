# WPS 图表还原 profile

> 机器可读配置以 `wps-chart.json` 为准（工具链检查、bootstrap、scaffold 都读它）。
> 本文件保留人类可读的领域说明。

`reconstruction-core` 的领域配置。具体工作区和领域 skill 仍在项目中：

- 工作区：`.comate/wps-pc-chart-reconstruction/`
- 项目配置：`.comate/wps-chart-reconstruction.json`
- 领域 skill：`.comate/skills/wps-chart-source-reconstruction/`

```yaml
name: wps-chart
source_roots:
  - wps-pc/kso
  - wps-pc/ts-impl/src
reference_runtime:
  commands:
    - python3 .comate/wps-pc-chart-reconstruction/tools/run_case.py ...
  outputs:
    - screenshot
    - runtime jsonl
target_runtime:
  commands:
    - cd wps-pc/ts-impl && npm run build
    - cd wps-pc/ts-impl && npm test
comparison:
  method: wps-vs-ts-screenshot
required_evidence:
  source:
    - function address
    - callers/callees
    - formula/boundaries
  effect:
    - wps.png
    - ts.png
    - cmp.png
    - mae/verdict
acceptance_rules:
  require_source_exact: true
  require_effect_match: true
  allow_approximation_as_complete: false
  office_out_of_scope: true
```

领域规则：

- WPS 桌面版是唯一参考端；Microsoft Office 不在范围内。
- 源码证据来自 `wps-pc/kso` 的 Ghidra/rea/objdump。
- 效果证据是 WPS vs TS 截图 + 定向回归。
- 图表能力使用 `<chart>.<feature>` 语义 ID。
