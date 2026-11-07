# runs/regress-current

最近一次定向/全量回归的临时输出，可覆盖。

- `run.json`：mode / 日期 / case 列表
- `lists/`：本次 case 清单
- `baseline.json` / `current.json`：指标对比（按领域约定）

具体产物（截图/帧/trace）写回 `corpus/**/reference/` 或 `runs/<run-id>/`。
长期记录放 `runs/<run-id>/`，不要只留在 `regress-current/`。
