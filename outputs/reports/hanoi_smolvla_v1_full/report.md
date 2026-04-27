# SmolVLA Training Report

## Experiment Summary

- Generated at: `2026-04-27T02:55:48.491294`
- Training start: `2026-04-27 02:09:06`
- Training end: `2026-04-27 02:47:18`
- Final step: `10000`
- Final loss: `0.042`
- Best loss: `0.038`
- Final grad norm: `0.84`
- Final learning rate: `2.5e-06`
- Mean update time per step: `0.22711000000000003` s
- Mean data loading time per step: `0.00201` s
- Dataset frames: `33801`
- Dataset episodes: `90`
- Learnable parameters: `99880992`
- Total parameters: `450046176`
- Checkpoints: `[1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]`

## Dataset Action Statistics

| Joint | Mean | Std |
| --- | ---: | ---: |
| shoulder_pan | -4.8363 | 14.3804 |
| shoulder_lift | -24.1100 | 59.2800 |
| elbow_flex | 26.4463 | 39.6687 |
| wrist_flex | 87.0475 | 12.0366 |
| wrist_roll | -92.9808 | 9.2109 |
| gripper | 35.4857 | 29.0250 |

## Figures

### SmolVLA Training Loss vs Step

- File: `loss_vs_step.svg`
- Caption: 训练损失随步数下降，反映策略在示教数据上的拟合过程。

### Gradient Norm vs Step

- File: `grad_norm_vs_step.svg`
- Caption: 梯度范数曲线用于观察优化过程是否平稳，是否出现梯度爆炸或异常抖动。

### Learning Rate vs Step

- File: `learning_rate_vs_step.svg`
- Caption: 学习率衰减曲线，对应本次训练使用的 cosine decay with warmup 调度策略。

### Training Timing vs Step

- File: `timing_vs_step.svg`
- Caption: 展示每步参数更新耗时和数据加载耗时，可用于分析训练吞吐和 I/O 开销。

### Dataset Action Quantiles by Joint

- File: `action_quantiles.svg`
- Caption: 展示各关节动作在数据集中的 q10 / q50 / q90 分位值，用于说明示教动作分布。
