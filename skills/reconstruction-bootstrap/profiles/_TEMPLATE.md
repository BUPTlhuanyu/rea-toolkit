# <domain> 领域 profile

> 机器可读版本优先使用同目录的 `<domain>.json`。本模板用于只需要文字说明的领域。

```yaml
name: <domain>
platform: <desktop-native|mobile-android|mobile-ios|web|game-2d|game-3d>
source_roots:
  - <decompiled-dir>
  - <target-src>
reference_runtime:
  commands:
    - <launch-reference>
    - <drive-input-and-capture>
  outputs:
    - screenshot
    - runtime-log
target_runtime:
  commands:
    - <build-target>
  outputs:
    - dist
comparison:
  method: <screenshot|frame-diff|dom-diff|protocol-diff>
  metrics:
    - <metric>
required_evidence:
  source:
    - <source evidence item>
  effect:
    - <effect evidence item>
acceptance_rules:
  require_source_exact: true
  require_effect_match: true
  allow_approximation_as_complete: false
verification_commands:
  - <test-command>
id_domains:
  - <domain-segment>
```

## 工具链

- 反编译/反汇编：
- 运行时探针：
- 参考端采集：
- 目标端构建：

## 领域规则

- 参考端版本/设备/环境必须固定并记录。
- 哪些差异属于平台/环境不可移植。
- 效果对照的固定条件和容差。
- 无法获得参考输出时如何标记 `NO_REFERENCE`。
