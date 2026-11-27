# 自检清单（必须带计数写入 verification）

## 第 0/1 步：输入与规则
- [ ] 已读取 `/input/case.json` 与 `/input/task.md`，`case_id` 与 `output_contract` 已记录
- [ ] 已打开全部真实材料文件，`sources` 覆盖所用文件与范围
- [ ] 未用文件名/领域标签推断材料内容
- [ ] 规则表（文体、语言、术语、禁止改动、输出字段）已建立并在每步重读
- [ ] 骨架 `result.json` 已在早期落盘，后续增量更新

## 第 2 步：六类要素齐全（element_coverage）
- [ ] 方法步骤：每步有 input / operation / output / decision / anchor
- [ ] 实验设置：training / validation / testing 分开，硬件/版本/环境/种子/重复次数逐项填写
- [ ] 参数：每项有 name / value / unit / applies_to / source / anchor
- [ ] 数据集：名称/版本/规模/预处理/划分比例/随机方式/子集用途
- [ ] 对照实验：基线版本/同预算/指标/统计方式
- [ ] 复现与限制：代码版本/环境/数据获取/命令 + 限制落到具体失效场景
- [ ] 计数：已写要素数 / 6

## 第 3 步：来源与数值（source_traceability / value_consistency）
- [ ] 每个数值、单位与限定词与配置/日志/代码/原文一致
- [ ] 参数表取值与正文逐项一致；无材料外补值
- [ ] 冲突取值并列并写入 uncertainties，未擅自择一
- [ ] 每条 claim 在 evidence_map 中有 evidence 与 anchor
- [ ] 计数：有来源参数数 / 参数总数；正文—表格—原始材料一致数 / 抽查数

## 第 4 步：草稿与追问（reproducibility / limitation_specificity）
- [ ] 六段可编辑草稿齐全，步骤可直接照做
- [ ] 复现清单覆盖代码版本、依赖、数据获取、训练/评测命令与输出位置
- [ ] 每条限制给出 condition、failure_scenario、boundary
- [ ] 每处材料缺口标注 `[材料未述，待作者确认]` 并有 `question_for_author`
- [ ] 计数：复现清单齐备项 / 应填项；具体失效场景限制数 / 限制总数

## 第 5 步：回查与诚实性（anchor_spotcheck / no_new_facts）
- [ ] 抽查 anchor 能回到原材料的真实位置（记录成功数 / 抽查数）
- [ ] 材料外新增事实数为 0，并写明抽查方式
- [ ] 失败项已回修并记入 change_log；未解决项保留在 uncertainties
- [ ] status 与实际完成度一致（success / partial / unable / refused）
- [ ] 三个可编辑产物与 result.json 均已写入 /app/output

## 提交前检查
- [ ] 包内不含 result.json、正式案例答案或预制输出
- [ ] 所有资源为 UTF-8 文本、相对路径、无符号链接，单文件 ≤500KB、总量 ≤2MB
