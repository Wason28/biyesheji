# 第8章图表索引

本目录用于整理 SmolVLA 训练实验在论文《第8章 系统测试与实验分析》中的插图材料。

建议引用顺序如下：

1. 图 8-1 SmolVLA 训练损失曲线
文件：
`thesis_figures/fig8_1_smolvla_training_loss_curve.svg`
建议位置：
第8章训练过程分析小节，用于说明 loss 随训练步数整体下降。

2. 图 8-2 SmolVLA 梯度范数变化曲线
文件：
`thesis_figures/fig8_2_smolvla_gradient_norm_curve.svg`
建议位置：
紧接图8-1之后，用于说明优化过程未出现明显梯度爆炸。

3. 图 8-3 SmolVLA 学习率衰减曲线
文件：
`thesis_figures/fig8_3_smolvla_learning_rate_curve.svg`
建议位置：
训练配置说明段落，用于解释 cosine decay with warmup 调度策略。

4. 图 8-4 SmolVLA 训练耗时构成曲线
文件：
`thesis_figures/fig8_4_smolvla_training_timing_curve.svg`
建议位置：
实验效率分析小节，用于说明参数更新耗时和数据加载耗时。

5. 图 8-5 汉诺塔示教数据关节动作分位统计图
文件：
`thesis_figures/fig8_5_hanoi_action_quantile_chart.svg`
建议位置：
数据集描述或实验设置小节，用于说明 6 维关节动作分布特征。

建议在正文中统一使用以下中文图题：

- 图 8-1 SmolVLA 训练损失曲线
- 图 8-2 SmolVLA 梯度范数变化曲线
- 图 8-3 SmolVLA 学习率衰减曲线
- 图 8-4 SmolVLA 训练耗时构成曲线
- 图 8-5 汉诺塔示教数据关节动作分位统计图

本轮实验摘要可引用：

- 数据集规模：90 条 episode，33801 帧
- 训练步数：10000
- 最终 loss：0.042
- 最优 loss：0.038
- 最终 checkpoint：10000 步
