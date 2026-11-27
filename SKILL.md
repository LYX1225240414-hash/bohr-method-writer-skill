---
name: method-writer
description: 从真实的实验记录、配置、日志、代码与数据说明中抽取方法步骤、实验设置、参数、数据集划分、对照与复现 limitation 六类要素，生成字段齐备、数值有源、正文与参数表一致、缺口显式追问的可编辑方法与实验章节草稿；当用户要求撰写或补写方法与实验章节、核对参数与来源、整理复现清单或标注材料缺口时使用，支持中英文科研材料。
---

# 方法与实验章节：写得全、写得准、做得着、说得住

把散落的实验记录变成**可直接进入论文、能被第三方复做和复核**的方法与实验章节，而不是一段读得通却缺条件、缺来源的流畅叙述。本 Skill 锁定四个可验证性质：**写得全**（六类要素齐备）、**写得准**（每个数值可回到配置/日志/代码）、**做得着**（版本、环境、种子、命令可复做）、**说得住**（缺口与限制落到具体失效场景）。

## 何时使用

- 起草或补写论文/报告的方法与实验章节，材料为零散的实验记录、配置、日志、代码、数据说明。
- 需要生成带名称、取值、单位、作用对象与来源的参数表，并让正文数值与表格逐项对齐。
- 需要区分训练/验证/测试条件，写清数据集版本、划分方式与随机种子、重复次数。
- 需要核查“与基线比较”是否同预算、指标与统计方式是否明确，并把材料缺口交给作者确认。

不适用：无原始材料、要求凭空补造数值或实验结果、只需一句话大纲的场景。

## 运行环境与输出路径（重要）

- 平台把本 Skill 安装到 `/skills/weekly-skill`，用固定的 3 个案例运行。先读真实输入 `/input/case.json` 与 `/input/task.md`；`case.json` 可能含 `case_id`、`output_contract`、材料路径、目标文体与约束。**以实际字段为准，不从题目标签、文件名或示例推断材料内容**。
- 中间文件写在 `/app/work`，不污染输入目录；资源从 `/skills/weekly-skill/resources/` 读取，均为 UTF-8 文本。
- 最终产物写到 `/app/output/result.json`（UTF-8 合法 JSON），并同时保存**可编辑章节草稿** `/app/output/method_experiment_draft.md`、**参数与来源表** `/app/output/parameter_table.md`、**复现与追问清单** `/app/output/reproduction_checklist.md`，供人工继续编辑与复核。若 `output_contract` 指定其他产物路径，以合同为准。
- `result.json` 必须原样回填 `case_id`，完整包含 `output_contract` 的全部字段（不得改名、不得遗漏），再补充本 Skill 的扩展字段；合同字段与本表同名时以合同为准。
- 预算内**尽早写入诚实的部分结果**再增量完善；3 个案例、每条件 3 次运行由平台安排，参赛者不提供测试案例或白板。
- 禁止提交预制答案、正式案例答案、假造的运行日志或评测成绩；本 Skill 包内不应含任何 `result.json`。

## 输入输出

输入：任务说明与科研材料（文件或路径）：实验记录、配置文件、训练/评测日志、代码、数据说明、已有稿件片段；可选约束：文体、语言、目标期刊格式、关注方向。

输出 `result.json` 字段如下（`output_contract` 优先）：

| 字段 | 要求 |
|---|---|
| case_id | 从 case.json 原样回填；确实没有才填 `N/A` |
| status | `success` / `partial` / `unable` / `refused`；部分完成须写明未完成范围与人工接管位置 |
| method_experiment_draft | 对象，含 `steps` / `setup` / `parameters` / `datasets` / `baselines` / `reproduce_and_limits` 六段**完整可编辑正文**；每段按 `resources/method_template.md` 组织，缺处标 `[材料未述]`，不编造 |
| procedure_steps | 数组，每项含 `step_id` / `input` / `operation` / `output` / `decision` / `anchor`；每步可执行，判断条件单独写出 |
| parameter_table | 数组，每项含 `name` / `value` / `unit` / `applies_to` / `source` / `anchor` / `consistent_with_text`；`source` 只能是配置文件、日志、代码或作者确认，取值原样保留 |
| experiment_setup | 对象，分别给出 `training` / `validation` / `testing` 的硬件、软件与版本、运行环境、随机种子、重复次数；材料未述的字段留空并写入 uncertainties |
| dataset_splits | 数组，每项含 `dataset` / `version` / `size` / `preprocessing` / `split_ratio` / `random_method` / `seed` / `used_for` / `anchor` |
| baseline_comparison | 数组，每项含 `baseline` / `version` / `same_budget` / `metrics` / `statistics` / `evidence` / `anchor`；断言必须可被比较条件支撑 |
| reproduction_checklist | 数组，每项含 `item` / `value_or_command` / `source` / `anchor`；覆盖代码版本、环境依赖、数据获取、训练/评测命令与输出位置 |
| limitations | 数组，每项含 `condition` / `failure_scenario` / `boundary` / `anchor`；限制必须落到具体失效场景，不写套话 |
| evidence_map | 数组，每项含 `claim` / `value` / `source_type` / `evidence` / `anchor` / `change_record`；数字、术语、图表和关键论断均可逐条回查 |
| verification | 对象，逐项给 `result`（pass/fail/na）与 `evidence`（**带具体计数或抽查片段**）：`element_coverage`、`source_traceability`、`value_consistency`、`anchor_spotcheck`、`reproducibility`、`limitation_specificity`、`no_new_facts` |
| uncertainties | 数组，每项含 `item` / `reason` / `anchor` / `question_for_author`；材料缺失、冲突、无来源参数、版本不明分别说明 |
| sources | 使用的输入文件与页码/段号/配置键/日志行范围，界定输入边界 |
| change_log | 自检回修记录：问题、修正、位置、时间顺序 |

**锚点格式**：`p<页>:<段>` / `<章节>:<段>` / `fig<号>` / `tab<号>` / `eq<号>` / `config:<键路径>` / `log:<日志行或片段>` / `code:<文件:行>`，必须指向输入材料的真实位置。

## 工作流

### 第 0 步：落盘骨架（先保底）
读取 `/input/case.json` 与 `/input/task.md`，在 `/app/work` 建立工作副本，立即向 `/app/output/result.json` 写入含 `case_id`、`status: partial`、各扩展字段空数组的骨架；后续每完成一段就增量更新，避免超时只留下空结果。

### 第 1 步：确认输入边界与规则表
打开材料实际文件（配置、日志、代码、数据说明、既有稿件），不用文件名或领域标签推断内容；记录 `sources`。从任务说明抽取文体、语言、术语、禁止改动项、目标输出字段，形成规则表，后续每步重读。缺文件 → `status: unable` 并写明具体路径；扫描件尝试 OCR，失败写入 `uncertainties`。

### 第 2 步：六类要素抽取（写得全）
按 `resources/method_template.md` 逐项抽取：

1. **方法步骤**：把零散记录整理为有序步骤，每步写清输入、操作、输出与判断条件，多步不得压成一句。
2. **实验设置**：训练/验证/测试分别描述，硬件、软件版本、环境、种子、重复次数分开写，避免条件串台。
3. **参数与来源**：每个参数给出名称、取值、单位、作用对象、来源（配置键、日志片段、代码行或作者确认）；无来源的参数不得补值，写入 `uncertainties`。
4. **数据集与划分**：名称、版本、规模、预处理、划分比例与随机方式、各子集用途；版本含混处显式标注。
5. **对照实验**：基线对象与版本、是否同预算、评价指标、统计方式；缺一项即不能写成“显著优于”。
6. **可复现性与限制**：代码版本、环境依赖、数据获取、命令与输出位置；限制落到具体失效场景与适用范围。

抽取结果同时写入 `procedure_steps` / `experiment_setup` / `parameter_table` / `dataset_splits` / `baseline_comparison` / `reproduction_checklist` / `limitations`，每条带 `anchor`。

### 第 3 步：数值对齐与证据台账（写得准）
逐条比对正文数值与参数表、配置、日志、代码：`value`、`unit`、`applies_to` 原样保留，限定词与否定关系不改变；正文每处数值都能在 `evidence_map` 找到对应条目。发现冲突时并列两份取值与各自锚点，写入 `uncertainties` 并请作者确认，不擅自择一。对图表为图片、数字无法读取的情况保留占位与锚点，不猜内容。

### 第 4 步：生成可编辑章节草稿（做得着）
按六段结构写 `method_experiment_draft`：步骤可直接照做，设置按训练/验证/测试分列，参数表与正文数值一致，数据集版本与划分无歧义，对照条件可比，复现清单给全命令与版本。所有缺口用 `[材料未述，待作者确认]` 标注，并在 `uncertainties` 给出 `question_for_author`。同时写出三个可编辑 Markdown 产物。

### 第 5 步：带计数的自检与回修（说得住）
逐项核对 `resources/checklist.md`，把**计数**写进 `verification`：
- `element_coverage`：六类要素已写/应为 6；`source_traceability`：有来源参数数/参数总数；
- `value_consistency`：正文—参数表—原始材料一致数/抽查数；`anchor_spotcheck`：按锚点回查成功数/抽查数；
- `reproducibility`：复现清单齐备项数/应填项数；`limitation_specificity`：具体到失效场景的限制数/限制总数；
- `no_new_facts`：材料外新增事实数（必须为 0，并说明抽查方式）。
失败项回到第 2–4 步修正并记入 `change_log`；仍无法解决则 `status: partial`、列出人工接管位置，不得把失败写成通过。

### 第 6 步：输出与复核
写 `/app/output/result.json` 与三个可编辑产物，确认 `case_id` 已回填、`output_contract` 字段齐全、`verification` 含计数、`uncertainties` 与 `change_log` 如实填写，草稿中无未标注的推断数值。

## 异常处理

| 情况 | 处理 |
|---|---|
| 配置/日志/代码缺失或无权限 | 写明缺失路径与影响范围，`status: partial` 或 `unable`，不代编参数 |
| 参数无来源或数值冲突 | 并列记录各来源与锚点，写入 `uncertainties`，交作者确认 |
| 数据集版本/划分不明 | 不推断版本与比例，标 `[材料未述]` 并追问 |
| 图表公式为图片 | 保留占位与锚点，说明无法读取，不猜内容 |
| 语言切换 / 中英混排 | 草稿语言随任务要求，专有名词、命令与版本号保留原文写法 |
| 超长输入 / 预算紧张 | 分块处理、尽早落盘，宁可 `partial` 也不编造 |

## 资源

- `resources/method_template.md`：六类要素抽取与章节草稿模板。
- `resources/checklist.md`：带计数的自检清单。
- `resources/field_dict.md`：字段字典与锚点格式。
- `resources/output_example.json`：输出结构示意（非答案）。
- `examples/README.md`：最小调用示例（示意）。

## 最小示例

见 `examples/README.md`。示意输出仅展示字段结构，不代表任何真实科研案例的章节草稿。
