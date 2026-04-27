# 13 汉诺塔任务 Skill 规范

## 1. 文档目的

本文档定义项目内“汉诺塔任务技能”的最小边界，用于支持论文材料、数据采集说明和后续长程任务规划扩展。

## 2. 当前定位

- 当前 `汉诺塔任务 skill` 是项目内新增的任务技能资产。
- 它当前不直接替换执行层现有 `run_smolvla` 或原子动作工具。
- 它的作用是把“汉诺塔”从一个抽象长程目标，收敛成可验证的步骤序列与可引用 prompt 资产。

## 3. 技能目标

- 识别汉诺塔类任务指令
- 把目标拆解为合法的单步移动序列
- 生成中文步骤提示词，便于数据采集与人工执行
- 为后续接入 LangGraph 长程规划节点保留标准化输入输出

## 4. 技能实现位置

- 代码模块：
  [hanoi.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/skills/hanoi.py)
- Prompt 资产：
  [prompts.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/shared/prompts.py)

## 5. 技能输入输出

### 输入

- `num_disks`
- `source_peg`
- `target_peg`
- `auxiliary_peg`

### 输出

- `HanoiMove` 列表
- 中文步骤提示词列表
- skill 卡片描述对象

## 6. 默认问题设定

- 默认圆环数量：3
- 默认源柱：`A`
- 默认目标柱：`C`
- 默认辅助柱：`B`
- 默认圆环标识：
  - `pink_small`
  - `yellow_medium`
  - `red_large`

## 7. 约束规则

- 一次只允许移动一个圆环
- 大圆环不能放在更小的圆环上方
- 每一步必须显式给出源柱和目标柱
- 默认使用三柱三环桌面任务场景

## 8. 与项目现有资产的关系

- 与 `collection/hanoi_demo_collection.py` 的关系：
  - 该文件面向示教采集与模板化任务提示
  - 新 skill 面向任务规划资产与论文可追溯材料
- 与决策层的关系：
  - 当前尚未直接接入 LangGraph 节点
  - 后续可作为 `task_planning` 的长程子技能引入
- 与执行层的关系：
  - 当前不直接调用硬件
  - 后续可映射为 `move_to / grasp / release / move_home` 的步骤级组合

## 9. 论文建议写法

- 可在“任务技能扩展”或“长程任务能力设计”小节中描述为：系统已新增汉诺塔任务 skill 作为复杂序列任务的标准化资产，能够把三柱三环目标转化为合法步骤序列，并与提示词工程、数据采集材料和后续规划扩展保持一致。

## 10. 后续扩展方向

- 接入 LangGraph 中的专用 Hanoi 规划节点
- 将步骤级输出映射为真实机械臂抓取/放置动作
- 为不同初始摆放状态生成自适应规划
- 将 skill 输出接入数据采集和评测流程
