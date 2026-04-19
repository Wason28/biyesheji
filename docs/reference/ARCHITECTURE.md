# 系统架构参考

## 文档定位

本文档是项目当前架构参考文档，用于帮助开发 Agent、测试 Agent 和交接 Agent 快速理解系统分层、主流程、模块边界和扩展点。

基准来源：
- 需求文档：`# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- 详细规范：`docs/specs/03-system-architecture.md`
- 项目基线：`docs/specs/01-project-baseline.md`

## 当前总体架构

项目采用三层主架构加一个前端交互层：
- 前端界面层：负责任务输入、模型配置、状态展示和工具面板
- 决策层：负责 LangGraph 编排、多 Agent 状态流转和闭环控制
- 感知层：负责相机图像、机器人状态和 VLM 场景理解
- 执行层：负责原子动作、SmolVLA 技能执行和 LeRobot 控制

目标部署环境：`Ubuntu`

## 分层说明

### 1. 前端界面层

职责：
- 接收用户自然语言任务
- 配置决策层 LLM 和感知层 VLM
- 展示当前任务、场景描述、动作状态和视频流
- 展示已注册的 MCP 工具

边界：
- 只负责交互、展示和配置
- 不承担核心业务决策逻辑

### 2. 决策层

技术基线：
- `LangGraph + MCP Client`

职责：
- 解析用户任务
- 驱动 `task_planner -> scene_analyzer -> action_decider -> executor -> verifier` 主流程
- 维护状态字段、闭环次数和对话历史
- 决定调用感知层还是执行层工具

边界：
- 不直接访问硬件
- 不直接替代执行层做动作控制

### 3. 感知层

技术基线：
- `MCP Server + VLM`

职责：
- 获取 RGB 图像
- 获取机器人状态
- 基于配置的 VLM 生成场景描述

边界：
- 对外只暴露标准化 MCP 工具
- 不与前端或执行层直接耦合内部实现

### 4. 执行层

技术基线：
- `MCP Server + SmolVLA + LeRobot`

职责：
- 提供 `move_to`、`move_home`、`grasp`、`release`
- 提供 `run_smolvla` 作为核心抓取技能
- 将动作下发给机械臂控制接口

边界：
- `SmolVLA` 固定，不允许在前端热切换
- 新能力通过新增 MCP 工具扩展，不直接替换核心技能

## 主流程

1. 用户在前端输入自然语言任务。
2. 决策层 `task_planner` 调用选定的 LLM 生成任务序列。
3. 决策层 `scene_analyzer` 调用感知层获取场景描述和机器人状态。
4. 决策层 `action_decider` 结合任务、场景和状态决定动作。
5. `executor` 调用执行层原子工具或 `run_smolvla`。
6. `verifier` 再次调用感知工具，判断任务是否完成。
7. 若未完成，则回到 `scene_analyzer` 进入下一轮闭环；若完成，则结束。

## 当前系统对象

系统运行时 Agent：
- 任务规划 Agent，对应 `task_planner`
- 场景分析 Agent，对应 `scene_analyzer`
- 动作决策 Agent，对应 `action_decider`
- 闭环验证 Agent，对应 `verifier`
- 模型部署助手 Agent
- 系统载入助手 Agent

开发协作 Agent Team：
- 见 `docs/specs/02-agent-team.md`

## 当前实现边界

当前文档体系已经明确：
- 目标问题：桌面级物体分拣
- 目标平台：`PC + 单机械臂 + 臂上摄像头`
- 目标部署环境：`Ubuntu`
- 当前不覆盖：多机械臂协同、分布式部署、执行层核心模型热切换

## 扩展点

允许扩展：
- 新感知工具
- 新执行技能工具
- 新模型供应商适配器
- 新前端展示模块

扩展原则：
- 优先通过 `MCP` 增量扩展
- 不破坏主闭环流程
- 同步更新 `docs/reference/INTERFACES.md` 和 `docs/records/TEST_REPORT.md`

## 当前文档状态判断

当前处于架构已固化、代码待按架构落地的阶段。
架构方向明确，后续开发应围绕本架构推进，不再重复讨论大范围边界问题。
