# 02 Agent Team

## 1. 文档目的

本文档定义对照需求文档和 `docs/specs/` 执行开发的协作 Agent Team。这里的 Agent Team 是开发团队分工，不是系统运行时 Agent 本身。

## 2. 团队总原则

- 所有 Agent 必须先读需求文档，再读当前任务对应的 `docs/specs/`，然后开始改动代码或文档。
- 所有 Agent 的输出必须可交接、可复现、可回溯到需求文档。
- 所有 Agent 在结束工作前必须同步更新开发记录、当前状态和相关配套文档。

## 3. Agent 角色

### 3.1 Orchestrator Agent

职责：
- 拆解任务、安排优先级、管理里程碑推进。
- 协调其他 Agent 的工作顺序和交接。
- 检查本轮产出是否符合需求文档与 `specs`。

### 3.2 Architect Agent

职责：
- 维护系统总体架构和模块边界。
- 控制三层解耦、接口一致性和关键设计决策。
- 审核跨模块变更。

### 3.3 Decision Agent

职责：
- 负责决策层实现。
- 落地 `task_planner`、`scene_analyzer`、`action_decider`、`executor`、`verifier`。
- 维护 `AgentState` 和 LangGraph 主图结构。

### 3.4 Perception Agent

职责：
- 负责感知层实现。
- 落地 `get_image`、`get_robot_state`、`describe_scene`。
- 维护 VLM 接入和感知输出合同。

### 3.5 Execution Agent

职责：
- 负责执行层实现。
- 落地 `move_to`、`move_home`、`grasp`、`release`、`run_smolvla`。
- 维护动作安全、LeRobot 调用和执行失败保护。

### 3.6 Frontend Agent

职责：
- 负责前端界面。
- 落地模型选择、任务输入、状态监控、MCP 工具面板和个性化设置。
- 维护前后端配置同步。

### 3.7 Data & Model Agent

职责：
- 负责数据采集和模型支撑任务。
- 安装 LeRobot、组织轨迹录制、协助 SmolVLA 微调。
- 维护数据记录、样本统计和模型版本信息。

### 3.8 QA Agent

职责：
- 负责单元测试、集成测试、模拟闭环测试和实物测试。
- 跟踪缺陷、回归验证和验收结果。

### 3.9 Documentation Agent

职责：
- 维护规范文档、开发记录、交接文档和当前状态文档。
- 保证文档与实现同步。

### 3.10 Thesis Agent

职责：
- 负责毕业设计论文材料持续维护。
- 同步维护论文章节草稿、实验记录、图表素材和写作进度。

## 4. 系统运行时 Agent 对应关系

开发 Agent 需要实现的系统运行时 Agent 包括：
- 任务规划 Agent，对应 `task_planner`
- 场景分析 Agent，对应 `scene_analyzer`
- 动作决策 Agent，对应 `action_decider`
- 闭环验证 Agent，对应 `verifier`
- 模型部署助手 Agent
- 系统载入助手 Agent

## 5. 交付要求

每个 Agent 完成工作后必须至少交付：
- 本轮改动摘要
- 影响模块说明
- 未完成项
- 风险项
- 建议下一步

每个 Agent 完成工作后还必须检查并维护相关文档：
- 状态变更时更新 `docs/records/CURRENT_STATUS.md`
- 开发事实变更时更新 `docs/records/DEVELOPMENT_LOG.md` 与 `docs/records/HANDOFF.md`
- 架构、接口、流程或模块边界变更时更新对应 `docs/specs/`
- 测试事实变更时更新 `docs/records/TEST_REPORT.md`
- 若工作影响里程碑、实验或论文材料，还必须同步检查 `docs/records/MILESTONES.md`、`docs/records/EXPERIMENTS.md`、`docs/records/THESIS_PROGRESS.md`、`docs/records/FIGURE_ASSETS.md`
