# Prompt 素材与系统提示词整理

## 文档定位

本文档用于把项目中与论文相关的 prompt 资产收口为可引用材料，避免论文中写“系统使用了 Prompt”但无法追溯到代码。

## 当前结论

- 项目已经存在感知层与决策层的系统提示词，但此前分散在实现文件中。
- 当前已新增统一 prompt 资产文件：
  [prompts.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/shared/prompts.py)
- 执行层此前没有成体系的 system prompt；现已补充 `EXECUTION_SMOLVLA_SYSTEM_PROMPT`，作为当前 SmolVLA 实体执行链路的配套提示词资产。

## Prompt 资产清单

### 1. 感知层默认任务提示词

- 常量名：`PERCEPTION_DEFAULT_SCENE_PROMPT`
- 文件位置：
  [prompts.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/shared/prompts.py)
- 用途：约束 VLM 输出桌面场景描述，强调物体类别、相对位置、遮挡关系、抓取状态与安全风险。
- 当前调用位置：
  [providers.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/perception/providers.py)
- 论文可写法：感知层通过统一任务提示词，把视觉问题约束到桌面操作场景而非开放式聊天描述。

### 2. 感知层系统提示词

- 常量名：`PERCEPTION_VISION_RESPONSE_SYSTEM_PROMPT`
- 文件位置：
  [prompts.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/shared/prompts.py)
- 用途：强制 VLM 输出 `scene_description / confidence / structured_observations` 三段结构，并约束 `structured_observations` 的字段。
- 当前调用位置：
  [providers.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/perception/providers.py)
- 论文可写法：采用结构化 system prompt，降低自由文本输出对下游决策层的解析压力。

### 3. 决策层系统提示词

- 常量名：`DECISION_PLANNING_SYSTEM_PROMPT`
- 文件位置：
  [prompts.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/shared/prompts.py)
- 用途：约束 LLM 只返回 JSON 规划结果，限定 `selected_capability / selected_action / selected_action_args / assistant_response` 等字段，并对舵机控制、归位、场景问答三类任务做强约束。
- 当前调用位置：
  [providers.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/decision/providers.py)
- 论文可写法：决策层并非直接依赖开放式自然语言，而是通过受限 JSON 规划提示词约束可执行动作空间。

### 4. 执行层系统提示词

- 常量名：`EXECUTION_SMOLVLA_SYSTEM_PROMPT`
- 文件位置：
  [prompts.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/shared/prompts.py)
- 当前状态：新增的项目 Prompt 资产，可作为当前 SmolVLA 实体执行链路的可追溯提示词基线。
- 用途：为真实 `SmolVLA` 或 MCP 执行代理提供统一的动作生成 system prompt 资产。
- 论文可写法：执行层已建立标准动作生成提示词资产，可与当前实体执行链路形成一致的工程材料。

### 5. 汉诺塔任务技能系统提示词

- 常量名：`DECISION_HANOI_SKILL_SYSTEM_PROMPT`
- 文件位置：
  [prompts.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/shared/prompts.py)
- 当前状态：已新增并归档为项目 Prompt 资产。
- 用途：将汉诺塔类长程任务收敛为合法、可执行、可追踪的步骤规划约束。
- 对应 skill 模块：
  [hanoi.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/skills/hanoi.py)
- 论文可写法：除通用决策提示词外，系统还补充了面向长程序列任务的领域化 task skill prompt。

## Prompt 与系统层级映射

| 层级 | Prompt | 当前状态 | 代码落点 |
| --- | --- | --- | --- |
| 感知层 | `PERCEPTION_DEFAULT_SCENE_PROMPT` | 已接入 | `perception/providers.py` |
| 感知层 | `PERCEPTION_VISION_RESPONSE_SYSTEM_PROMPT` | 已接入 | `perception/providers.py` |
| 决策层 | `DECISION_PLANNING_SYSTEM_PROMPT` | 已接入 | `decision/providers.py` |
| 决策技能层 | `DECISION_HANOI_SKILL_SYSTEM_PROMPT` | 已建档 | `skills/hanoi.py` |
| 执行层 | `EXECUTION_SMOLVLA_SYSTEM_PROMPT` | 已建档，可作为实体执行链路配套资产 | `shared/prompts.py` |

## 论文建议写法

### 可直接写入正文的点

- 系统提示词不是临时拼接字符串，而是跨层集中管理的提示词资产。
- 感知层提示词强调结构化输出，服务于下游状态图节点消费。
- 决策层提示词强调动作空间受限与 JSON 输出，降低大模型自由生成导致的越权规划风险。
- 执行层提示词已形成标准资产；在论文中可表述为“已形成与 SmolVLA 实体执行链路相配套的提示词材料”，但若具体某次实体执行未直接消费该提示词，也不应夸大为“所有真实执行均由该 Prompt 直接驱动”。

### 更适合附录的点

- 每个 Prompt 的完整文本
- Prompt 与代码文件的映射关系
- Prompt 修改记录与实验版本

## 可直接引用的完整 Prompt 文本

### 感知层默认任务提示词

```text
请稳定输出桌面场景描述，覆盖物体类别、相对位置、遮挡关系、抓取状态与安全风险。
```

### 感知层系统提示词

```text
你是桌面具身智能系统的视觉感知模块。请只返回一个 json 对象，字段必须包含 scene_description、confidence、structured_observations。structured_observations 必须包含 objects、relations、robot_grasp_state、risk_flags。
```

### 决策层系统提示词

```text
你是桌面具身智能体的任务规划器。请只返回一个 json 对象，字段可以包含 task_queue、selected_capability、selected_action、selected_action_args、reason、assistant_response。assistant_response 必须是面向最终用户的简短中文回复，要说明你看到了什么、准备做什么。如果当前任务是单舵机旋转，只能选择 servo_control / servo_rotate。如果当前任务是归位或回零，只能选择 return_home / move_home。如果当前任务是在问你看到什么、描述场景或查看画面，只能选择 scene_understanding / describe_scene。不要把舵机任务、归位任务规划成 pick_and_place 或 run_smolvla。不要输出 markdown，不要输出解释性前缀。
```

### 执行层系统提示词

```text
你是桌面机械臂的动作生成模块。请在严格遵守安全边界的前提下，把上层任务拆成可执行的原子动作序列。动作只允许从 move_to、move_home、grasp、release 中选择。若视觉输入为空、机器人状态缺失或安全边界不明确，应拒绝生成危险动作。优先输出保守、安全、可验证的短序列，动作结束后默认回到安全 home 位姿。
```

### 汉诺塔任务技能系统提示词

```text
你是桌面具身智能体中的汉诺塔任务规划技能。你的职责是把汉诺塔目标拆成严格合法的原子移动步骤。一次只能移动一个圆环，大圆环不能放在更小的圆环上方。输出必须显式包含 step_index、ring、source_peg、target_peg。若用户只说“完成汉诺塔”而未说明目标柱，默认从 A柱 移动到 C柱，并使用 B柱 作为辅助柱。回复应优先保证动作合法性、步骤完整性与可执行性，而不是语言花哨。
```
