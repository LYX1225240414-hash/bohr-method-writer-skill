# 字段字典

`output_contract` 中的字段优先：同名时以合同为准，不得改名或遗漏；本表扩展字段补充在合同字段之后。

| 字段 | 类型 | 含义 |
|---|---|---|
| case_id | string | 从 case.json 原样回填；确实没有才填 `N/A` |
| status | string | `success` / `partial` / `unable` / `refused` |
| method_experiment_draft | object | 六段可编辑正文：steps / setup / parameters / datasets / baselines / reproduce_and_limits |
| procedure_steps | array | step_id / input / operation / output / decision / anchor |
| parameter_table | array | name / value / unit / applies_to / source / anchor / consistent_with_text |
| experiment_setup | object | training / validation / testing 各自的硬件、版本、环境、种子、重复次数 |
| dataset_splits | array | dataset / version / size / preprocessing / split_ratio / random_method / seed / used_for / anchor |
| baseline_comparison | array | baseline / version / same_budget / metrics / statistics / evidence / anchor |
| reproduction_checklist | array | item / value_or_command / source / anchor |
| limitations | array | condition / failure_scenario / boundary / anchor |
| evidence_map | array | claim / value / source_type / evidence / anchor / change_record |
| verification | object | 每项 result + 带计数的 evidence |
| uncertainties | array | item / reason / anchor / question_for_author |
| sources | array | 输入文件与页码/段号/配置键/日志行范围 |
| change_log | array | 问题 / 修正 / 位置 / 时间顺序 |

## source_type 允许值
`config` / `log` / `code` / `data_doc` / `manuscript` / `author_confirmation`；不写“推断”“常识”。

## 锚点格式
`p<页>:<段>` / `<章节>:<段>` / `fig<号>` / `tab<号>` / `eq<号>` / `config:<键路径>` / `log:<日志行或片段>` / `code:<文件:行>`。

## verification 计数项
`element_coverage`(x/6)、`source_traceability`、`value_consistency`、`anchor_spotcheck`、`reproducibility`、`limitation_specificity`、`no_new_facts`(必须为 0)。
