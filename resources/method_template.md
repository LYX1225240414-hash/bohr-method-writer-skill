# 六类要素抽取与章节草稿模板（结构示意，非答案）

## 1. steps｜方法步骤
| step_id | input | operation | output | decision | anchor |
|---|---|---|---|---|---|
| S1 | 原始材料中的输入对象与文件 | 可执行动作，逐条写 | 该步产出 | 通过/失败判断条件 | config:… / log:… / pX:Y |

正文写法：按 S1、S2… 顺序成段，不把多步压成一句；判断条件单独成句。

## 2. setup｜实验设置
| 条件 | 硬件 | 软件与版本 | 运行环境 | 随机种子 | 重复次数 | anchor |
|---|---|---|---|---|---|---|
| training | … | … | … | … | … | … |
| validation | … | … | … | … | … | … |
| testing | … | … | … | … | … | … |

未述字段写 `[材料未述，待作者确认]`，不得用其他条件的值代替。

## 3. parameters｜参数与来源
| name | value | unit | applies_to | source | anchor | consistent_with_text |
|---|---|---|---|---|---|---|
| 学习率 | 原样取值 | 原样单位 | 作用对象 | config / log / code / 作者确认 | config:… | yes/no |

正文中所有数值必须能在该表找到同值条目；无来源的参数不写数值，只进 uncertainties。

## 4. datasets｜数据集与划分
| dataset | version | size | preprocessing | split_ratio | random_method | seed | used_for | anchor |
|---|---|---|---|---|---|---|---|---|

## 5. baselines｜对照实验
| baseline | version | same_budget | metrics | statistics | evidence | anchor |
|---|---|---|---|---|---|---|

“优于基线”必须同时具备同预算说明、评价指标与统计方式；缺项则改写为描述性比较并写入 uncertainties。

## 6. reproduce_and_limits｜复现与限制
复现清单：代码版本 → 环境依赖 → 数据获取 → 训练命令 → 评测命令 → 输出位置（每项给 source / anchor）。

限制写法：当 `<condition>` 时，在 `<failure_scenario>` 场景下会 `<具体后果>`，因此结论仅适用于 `<boundary>`；不明确处交作者确认。

## 草稿段落顺序
`steps` → `setup` → `parameters` → `datasets` → `baselines` → `reproduce_and_limits`，每段之后附“证据短引 + 锚点”索引。
