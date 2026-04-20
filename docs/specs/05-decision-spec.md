# 05 决策层详细规范

## 1. 职责

决策层负责：
- 接收用户自然语言指令。
- 编排多 Agent 协作流程。
- 调用感知层和执行层工具。
- 维护闭环反馈控制。

## 2. 状态定义

决策层主状态必须至少包含以下字段：

```python
class AgentState(TypedDict):
    user_instruction: str
    task_queue: List[str]
    current_task: str
    current_image: str
    robot_state: dict
    scene_description: str
    action_result: str
    iteration_count: int
    conversation_history: List
```

## 3. 节点定义

### 3.1 `task_planner`

职责：
- 解析用户指令
- 生成任务序列

模型依赖：
- 前端选定的 `LLM`

### 3.2 `scene_analyzer`

职责：
- 调用感知层工具获取场景描述和机器人状态

工具依赖：
- `describe_scene`
- `get_robot_state`

### 3.3 `action_decider`

职责：
- 结合当前任务和场景决定动作

工具依赖：
- `run_smolvla` 或基础原子工具

### 3.4 `executor`

职责：
- 执行动作调用
- 接收执行结果

### 3.5 `verifier`

职责：
- 在动作执行后验证任务完成状态

工具依赖：
- `describe_scene`
- `get_image`

## 4. 图结构约束

主图固定结构：
- `task_planner -> scene_analyzer -> action_decider -> executor -> verifier`

入口：
- `task_planner`

条件分支：
- 若 `action_result == in_progress`，则返回 `scene_analyzer`
- 否则结束

## 5. 模型切换要求

- 决策层必须支持前端选择 `MiniMax`、`OpenAI`、`Ollama`。
- 决策层必须从配置读取模型供应商、模型名、密钥或本地路径。
- 模型切换不得改变 LangGraph 状态结构和节点职责。

## 6. 闭环控制要求

- 必须记录 `iteration_count`。
- 必须设置最大闭环迭代次数。
- 必须保留对话历史，便于调试和回溯。

## 7. 测试要求

- 主流程至少覆盖正常结束、循环继续、异常中止三类路径。
- 节点逻辑应可在模拟工具下独立验证。
- `AgentState` 新增字段时必须同步更新测试。
