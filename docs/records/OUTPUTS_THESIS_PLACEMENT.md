# outputs 材料与论文章节对应表

## 文档定位

本文档用于把 `outputs/` 目录下已经生成的训练材料逐项映射到论文正文、图表和附录位置。以下映射只包含当前已经完成并可直接引用的产物。

## 总体结论

`outputs/` 目录当前对应的是一轮已完成的 SmolVLA 训练实验材料，最适合放入论文第 8 章“系统测试与实验分析”中，作为训练结果与数据统计证据使用。

## 正文落点总览

- 第 8 章 `8.5 SmolVLA 训练实验与结果分析`
  - 训练摘要
  - 训练曲线
  - checkpoint 记录
  - 数据集动作统计
- 第 8 章 `8.6 结果汇总`
  - 引用训练完成事实与核心数值
- 附录
  - 放训练日志、CSV 原始表和图表索引

## 文件级映射

| 文件 | 论文位置 | 用法 | 建议写法 |
| --- | --- | --- | --- |
| [report.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/report.md) | 第 8 章 `8.5` | 训练实验主摘要 | 用于概述训练时间、步数、loss、数据集规模与图表说明 |
| [summary.json](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/summary.json) | 第 8 章 `8.5` 中的表 4 | 训练摘要数据源 | 可整理为“数据集规模 / 步数 / 最终 loss / 最优 loss / checkpoint 数量”表 |
| [training_metrics.csv](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/training_metrics.csv) | 第 8 章 `8.5` | 曲线原始数据 | 作为损失、梯度、学习率、耗时四张图的原始数据来源 |
| [checkpoints.csv](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/checkpoints.csv) | 第 8 章 `8.5` 或附录 | checkpoint 时间点记录 | 可写“训练过程中共保存 10 个 checkpoint，覆盖 1000 至 10000 步” |
| [loss_vs_step.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/loss_vs_step.svg) | 第 8 章 `8.5` 图 5 | 损失曲线 | 图题建议：`SmolVLA 训练损失曲线` |
| [grad_norm_vs_step.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/grad_norm_vs_step.svg) | 第 8 章 `8.5` 图 6 | 梯度范数曲线 | 图题建议：`SmolVLA 梯度范数变化曲线` |
| [learning_rate_vs_step.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/learning_rate_vs_step.svg) | 第 8 章 `8.5` 图 7 | 学习率曲线 | 图题建议：`SmolVLA 学习率衰减曲线` |
| [timing_vs_step.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/timing_vs_step.svg) | 第 8 章 `8.5` 图 8 | 训练耗时曲线 | 图题建议：`SmolVLA 训练耗时构成曲线` |
| [action_quantiles.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/action_quantiles.svg) | 第 8 章 `8.5` 图 9 | 数据集动作统计图 | 图题建议：`汉诺塔示教数据关节动作分位统计图` |
| [figure_manifest.json](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/figure_manifest.json) | 附录 | 图表元数据索引 | 适合作为“图表来源说明”附录材料 |
| [thesis_figure_index.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/thesis_figure_index.md) | 写作辅助材料 | 图号与位置建议 | 可直接辅助排版，不建议在正文引用 |
| [hanoi_smolvla_v1_train.log](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/records/hanoi_smolvla_v1_train.log) | 附录 | 训练日志节选 | 可作为训练过程留痕 |
| [hanoi_smolvla_v1_full_train.log](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/records/hanoi_smolvla_v1_full_train.log) | 附录 | 完整训练日志 | 可作为完整日志留档，不建议正文大段展开 |

## 建议插入位置

### 第 8 章 `8.5 SmolVLA 训练实验与结果分析`

建议按以下顺序组织：

1. 先引用 [summary.json](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/summary.json) 和 [report.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/report.md)，写训练摘要。
2. 再插入 [loss_vs_step.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/loss_vs_step.svg)、[grad_norm_vs_step.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/grad_norm_vs_step.svg)、[learning_rate_vs_step.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/learning_rate_vs_step.svg)、[timing_vs_step.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/timing_vs_step.svg)。
3. 最后插入 [action_quantiles.svg](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/action_quantiles.svg)，用于说明示教动作分布。

### 附录建议

- 把 [hanoi_smolvla_v1_full_train.log](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/records/hanoi_smolvla_v1_full_train.log) 作为“训练日志附录”。
- 把 [training_metrics.csv](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/training_metrics.csv) 与 [checkpoints.csv](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/checkpoints.csv) 作为“原始指标附表”。
- 把 [figure_manifest.json](/home/liuwenjie/lerobot/biyesheji/biyesheji/outputs/reports/hanoi_smolvla_v1_full/figure_manifest.json) 作为“图表元数据说明”。
