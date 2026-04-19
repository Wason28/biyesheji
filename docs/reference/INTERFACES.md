# 接口参考

## 文档定位

本文档汇总当前项目的核心接口、MCP 工具、决策状态结构和配置基线，作为开发和联调时的稳定参考。

基准来源：
- `docs/specs/04-perception-spec.md`
- `docs/specs/05-decision-spec.md`
- `docs/specs/06-execution-spec.md`
- `docs/specs/07-frontend-spec.md`

## 一、感知层 MCP 工具

### 1. `get_image`

- 功能：采集当前相机图像
- 输入：无
- 输出：图像 `base64`
- 调用方：决策层 `scene_analyzer` / `verifier`

### 2. `get_robot_state`

- 功能：获取当前关节角和末端位姿
- 输入：无
- 输出：`{joint_positions, ee_pose}`
- 调用方：决策层 `scene_analyzer`

### 3. `describe_scene`

- 功能：调用当前配置的 VLM 生成场景描述
- 输入：`image`、可选 `prompt`
- 输出：场景描述文本
- 调用方：决策层 `scene_analyzer` / `verifier`
- 约束：VLM 供应商从配置读取，不允许写死厂商

## 二、执行层 MCP 工具

### 1. `move_to`

- 功能：移动到指定空间位置
- 输入：`x`, `y`, `z`, `orientation`
- 输出：执行结果状态

### 2. `move_home`

- 功能：返回预设初始位姿
- 输入：无
- 输出：执行结果状态

### 3. `grasp`

- 功能：闭合夹爪
- 输入：`force`
- 输出：执行结果状态

### 4. `release`

- 功能：打开夹爪
- 输入：无
- 输出：执行结果状态

### 5. `run_smolvla`

- 功能：执行基于 SmolVLA 的抓取技能
- 输入：`task_description`, `current_image`, `robot_state`
- 输出：执行结果状态和必要日志
- 约束：固定核心技能，不提供前端替换

## 三、决策层状态结构

当前决策主状态至少包含：

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

状态使用约束：
- `iteration_count` 用于闭环次数控制
- `conversation_history` 用于调试与追溯
- `current_image`、`robot_state`、`scene_description` 由感知阶段刷新
- `action_result` 由执行阶段和验证阶段共同影响

## 四、LangGraph 节点接口关系

固定主图：
- `task_planner -> scene_analyzer -> action_decider -> executor -> verifier`

节点职责摘要：
- `task_planner`：生成任务序列
- `scene_analyzer`：刷新场景信息
- `action_decider`：决定动作或技能
- `executor`：执行工具调用
- `verifier`：判断结束或继续

## 五、前端配置基线

前端至少需要维护以下配置能力：
- 决策 `LLM` 供应商选择：`MiniMax / OpenAI / Ollama`
- 感知 `VLM` 供应商选择：`MiniMax MCP Vision / OpenAI GPT-4o / Ollama Vision`
- API Key 输入
- 本地模型路径输入能力
- 最大闭环迭代次数
- 机械臂初始位姿校准参数
- 执行速度缩放系数

## 六、配置文件参考结构

```yaml
decision:
  llm_provider: minimax
  llm_model: MiniMax-M2.1
  llm_api_key: ${MINIMAX_API_KEY}

perception:
  vlm_provider: minimax_mcp_vision
  vlm_api_key: ${MINIMAX_API_KEY}

execution:
  vla_model_path: ./models/smolvla_finetuned
  robot_config: ./lerobot_configs/my_robot.yaml

frontend:
  port: 7860
  max_iterations: 10
```

## 七、接口变更原则

- 变更 MCP 工具名时，必须同步更新 spec、参考文档和测试文档
- 新增状态字段时，必须同步更新 LangGraph 状态说明和测试用例
- 新增模型配置项时，必须同步更新前端配置说明
- 所有接口变更必须记录到 `docs/records/DEVELOPMENT_LOG.md`

## 八、当前状态

当前接口已完成文档基线整理，但尚未进入真实联调阶段。
因此本文件目前属于接口参考定版，后续一旦代码落地，应优先维护此文件与实际实现一致。
