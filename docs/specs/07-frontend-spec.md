# 07 前端详细规范

## 1. 职责

前端负责：
- 任务输入
- 模型选择
- 状态监控
- MCP 工具扩展面板
- 个性化参数设置

## 2. 功能模块

### 2.1 任务交互区

必须包含：
- 用户自然语言输入框
- 当前任务显示
- 场景描述显示
- 动作日志显示
- 摄像头实时视频流展示

### 2.2 模型配置面板

必须包含：
- 决策 `LLM` 选择：`MiniMax / OpenAI / Ollama`
- 感知 `VLM` 选择：`MiniMax MCP Vision / OpenAI GPT-4o / Ollama Vision`
- API Key 输入
- 本地模型路径输入能力
- 执行层当前模型展示：`SmolVLA`

### 2.3 MCP 工具扩展面板

必须包含：
- 已注册工具列表展示
- 手动刷新工具列表能力

### 2.4 个性化设置

必须包含：
- 机械臂初始位置校准
- 执行速度缩放系数
- 最大闭环迭代次数

## 3. 辅助 Agent

### 3.1 模型部署助手 Agent

职责：
- 引导用户完成 API Key 配置或本地模型路径指定

### 3.2 系统载入助手 Agent

职责：
- 启动时检测可用模型
- 在前端自动填充可选模型列表

## 4. 前端边界

- 前端只负责交互、配置和状态展示。
- 前端不得承载核心决策逻辑。
- 执行层模型只展示，不允许替换。

## 5. 体验要求

- 当前状态必须可视化。
- 模型切换结果必须明确反馈。
- 工具刷新结果必须可见。
- 错误信息必须可提示给用户。

## 6. 第二阶段前置接口占位

在不进入第三阶段完整前端开发前，后端至少需要先沉淀以下最小接口占位和状态字段约束：

- `bootstrap` 占位载荷必须至少包含：
  - 当前配置快照：`decision / perception / execution / frontend`
  - 执行层展示模型：`SmolVLA`
  - 已注册工具列表
  - 运行态快照字段清单
- 配置快照最少覆盖：
  - `decision.provider / model / api_key_configured / local_path`
  - `perception.provider / model / api_key_configured / local_path`
  - `execution.display_name / model_path / home_pose / mutable`
  - `frontend.port / max_iterations / speed_scale`
- 运行态快照最少覆盖：
  - `run_id`
  - `status`
  - `current_node`
  - `current_task`
  - `scene_description`
  - `action_result`
  - `iteration_count`
  - `max_iterations`
  - `current_image`
  - `robot_state`
  - `last_execution`
  - `logs`
  - `error`

约束：
- 前端消费的运行态快照必须是显式适配后的展示合同，不直接暴露完整决策内部状态。
- 配置载荷默认不回传明文 API Key，只返回空字符串和 `api_key_configured` 标记。
- 工具面板依赖的工具列表合同必须兼容感知层与执行层当前已注册工具，并支持后续手动刷新。
- 第二阶段可继续把 `bootstrap / config / run / error` 组织成接近真实后端服务的 facade，但不得把该 facade 写成完整前端服务或真实 HTTP/SSE/WebSocket 接口已实现。
- 若需要补执行层展示信息，只能补稳定展示合同，如 `execution_capabilities` 与 `execution_safety`，不得让前端直接依赖执行层内部实现对象。
