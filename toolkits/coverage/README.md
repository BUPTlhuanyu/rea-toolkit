# coverage

分支覆盖辅助工具。回答三个不同的问题：

1. **源码分支盘点**：反编译代码里到底有哪些分支？
2. **目标实现映射**：每个源码分支对应目标代码的哪一处？
3. **case 覆盖确认**：哪个 case 实际走到了这个分支？

`branch_coverage.py` 只负责把这三件事画出来，不替你判断“分支是否穷尽”。
分支是否穷尽取决于盘点方法和运行时证据。

## 输入

`inventory.json`：

```json
{
  "project": "example-chart",
  "functions": [
    {
      "id": "pieBestFit",
      "address": "0xf5cfd0",
      "target": "src/layout/pie-bestfit.ts:42",
      "branches": [
        {
          "id": "b1",
          "condition": "count == 0",
          "source": "0xf5cff0",
          "target": "src/layout/pie-bestfit.ts:48",
          "true": "return-empty",
          "false": "b2",
          "status": "covered",
          "cases": ["pie/empty"],
          "note": ""
        }
      ]
    }
  ]
}
```

`status`：

- `covered`：有 case，且参考端/目标端都观察到了该分支
- `partial`：有 case，但只验证了 true/false 一侧，或目标端未确认
- `uncovered`：分支已盘点，但没有 case
- `unknown`：源码里看到了疑似分支，但语义/边界未确认

如果 true/false 两侧的 case 不同，用 `trueCases` / `falseCases` 精确标注；
不写时退化为 `cases`。

## 用法

```bash
python3 branch_coverage.py branches.json --out-html coverage.html
python3 branch_coverage.py branches.json --out-mermaid coverage.mmd
python3 branch_coverage.py branches.json --markdown
```

HTML 用 Mermaid CDN 渲染流程图；离线环境可以直接用 `.mmd` 文件在任意
Mermaid 渲染器里打开。

## 图的含义

- 绿色：已覆盖
- 黄色：部分覆盖
- 红色：未覆盖
- 灰色：未知

边上的 `true` / `false` 后面会带上 case id。图只是**盘点结果的投影**：
如果源码分支本身漏了，图上不会自动出现红色节点。要减少漏项，必须配合：

- 反编译/反汇编交叉检查（Ghidra、IDA、objdump、rea）
- 运行时 trace（Frida/断点）确认实际走过的分支
- 目标端覆盖率工具（c8/istanbul、coverage.py、gcov/llvm-cov）
- 对复合条件做 condition/MC-DC 级别的拆分
- 对未知分支显式标 `unknown`，不要默认标 `covered`
