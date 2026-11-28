# 最小调用示例（示意，非正式案例）

本示例仅演示接口与字段结构，不代表任何真实科研案例的方法与实验章节。

## 输入
```json
{
  "case_id": "示意-case-001",
  "task": "根据实验记录与配置补写方法与实验章节，保留每条数值的来源",
  "materials": ["config.yaml", "train.log", "methods_notes.md"],
  "output_contract": {"case_id": "string", "status": "string"}
}
```
实际评测时输入为 `/input/case.json` 与 `/input/task.md`，材料路径以其中字段为准。

## 调用
1. 在 Agent 中加载本 Skill（安装位置 `/skills/weekly-skill`）。
2. 按 SKILL.md 第 0–6 步执行；先写骨架到 `/app/output/result.json`。
3. 用 `resources/method_template.md` 抽取六类要素，用 `resources/checklist.md` 做带计数自检。
4. 输出 `/app/output/result.json` 及 `method_experiment_draft.md`、`parameter_table.md`、`reproduction_checklist.md`。

## 调用脚本（第 3 步参数对齐）

```bash
L=/skills/weekly-skill/resources/scripts/param_lint.py
python3 "$L" init  --out /app/output/method_experiment_draft.md
python3 "$L" scan  --materials /app/work/materials --out /app/work/materials.json
python3 "$L" check --materials-json /app/work/materials.json \
                   --draft /app/output/method_experiment_draft.md --out /app/work
cat /app/work/lint_report.md
```

`check` 的输出里，`conflict` 必须按材料改正，`orphan` 必须找到出处或删除，`missing` 建议补写；`verification_hint` 直接给出四项自检计数。

## 示意输出
字段结构见 `../resources/output_example.json`；其中取值均为占位示例，`status` 为 `partial`，不得当作正式案例答案或评测结果。
