# 使用增益对照协议（质量增益 / 效率增益 / 增益可验证性）

本题"使用增益"占 25 分，其中"增益可验证性 5 分"要求**用证据说明改善**，不能只写"效果更好"。本协议给出可在单次运行内完成的对照记录方法。

## 1. 对照条件（必须一致）

| 项目 | 要求 |
|---|---|
| 材料 | 同一份输入材料目录，同一批文件，不改内容 |
| 任务要求 | 同一份 task.md 与输出字段要求 |
| 预算 | 同一模型、同一次运行预算（64 请求 / 900 秒） |
| 度量 | 同一组指标与同一判定口径（见第 3 节） |

不满足以上任一项，增益结论无效，应写 `uncertainties` 说明对照不成立。

## 2. 两种记录方式（按可得性择一）

### 方式 A：同材料两次产出的可对比指标（首选）
若平台提供基础 Agent 的产出或可复跑一次不加载 Skill 的条件，分别计算第 3 节指标，填入下表并写进 `result.json` 的 `gain_record.conditions`。

### 方式 B：单次运行内的机械检查对照（无基础产出时）
在没有对照产出时，用 `param_lint.py` 的机械检查作为可复核证据：
1. 先按"只看材料直接写"的方式产出第一版草稿（`/app/work/draft_blind.md`）；
2. 再按本 Skill 的六步流程产出第二版（最终草稿）；
3. 对两版分别跑 `param_lint.py check`，比较 `conflict_count` 与 `orphan_count` 的下降，以及 `missing_count` 的收敛。

这种对照不是"跑两次模型"，而是**同一运行内的两版草稿**，成本低、可复核，且直接对应"是否减少了作者追问实验细节和返工"的效率增益。

## 3. 指标与口径（只报能算出来的）

| 指标 | 定义 | 采集方式 |
|---|---|---|
| 要素覆盖 | 六类要素（步骤/设置/参数/数据/对照/复现与限制）已写段数 / 6 | 人工按 method_template 核对 |
| 有来源参数占比 | 有材料锚点的参数数 / 参数表总项数 | `lint_report.json.source_coverage` |
| 数值冲突数 | 正文与材料不一致的数值条数 | `lint_report.json.conflict_count`，越低越好 |
| 无来源数值数 | 正文出现但材料查不到的数值条数 | `lint_report.json.orphan_count`，应为 0 |
| 未覆盖参数数 | 材料有但正文未写的数值型参数 | `lint_report.json.missing_count` |
| 返工轮次 | 从初稿到定稿的人工修正轮数 | 记录 change_log 的条目数 |
| 耗时 | 从读材料到产出定稿的 wall time | 运行日志时间戳 |

## 4. 记录格式（写入 result.json）

```json
"gain_record": {
  "conditions": {"same_materials": true, "same_budget": true, "same_task": true},
  "mode": "B_single_run_two_drafts",
  "baseline": {"draft": "/app/work/draft_blind.md", "conflict_count": 0, "orphan_count": 0,
               "missing_count": 0, "element_coverage": "3/6"},
  "with_skill": {"draft": "/app/output/method_experiment_draft.md", "conflict_count": 0,
                 "orphan_count": 0, "missing_count": 0, "element_coverage": "6/6"},
  "delta_note": "冲突数由 0 降至 0；未覆盖参数由 N 降至 M；要素覆盖 3/6 → 6/6",
  "verifiable_artifacts": ["/app/work/lint_report.json", "/app/work/change_log.jsonl"]
}
```

## 5. 诚实性红线

- 不得编造对照数据、耗时或返工轮次；无法测量就写 `na` 并说明原因。
- 不得把平台提供的白板或官方结果写成自己的对照产出。
- 增益结论必须能由 `verifiable_artifacts` 里的文件复算出来；只写结论不附产物，视为不可验证。
