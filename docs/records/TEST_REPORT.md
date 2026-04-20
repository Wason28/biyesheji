# 测试报告

## 文档定位

本文档记录当前项目测试范围、测试策略和已发生的测试事实。
当前项目已完成第一阶段骨架代码、统一入口扩展与多轮单元 / 集成测试，本文件同时保留测试基线与真实执行结果。

## 测试范围

- 感知层 MCP 工具
- 决策层 LangGraph 主流程
- 执行层原子工具与 `run_smolvla`
- 前端交互与配置联动
- 实物分拣任务

## 测试分层策略

### 1. 单元测试

目标：
- 验证 MCP 工具的输入输出与异常处理
- 验证状态结构和配置读取逻辑

### 2. 集成测试

目标：
- 验证 LangGraph 主图流转
- 验证决策层与感知层、执行层的调用关系
- 验证前端配置对后端模型选择的影响

### 3. 实物测试

目标：
- 验证机械臂闭环分拣能力
- 记录连续成功次数、失败原因和环境条件

## 当前测试状态

当前真实状态：
- 已完成文档级测试范围梳理
- 已完成 44 个 pytest 测试并通过最近一次全量回归
- 已完成决策、感知、执行三个子域的最小功能验证
- 已完成统一启动入口的装配、配置加载、frontend 回退、原子执行工具透传与失败闭环验证
- 已补齐 perception 层统一 envelope 回归测试
- 已补 perception provider 工厂注册与 execution runtime 工厂注入测试
- 已开始第二阶段决策主线改造，并新增 capability/action 选择测试
- 已补最小前端占位合同测试，覆盖 `bootstrap/config/run snapshot` 与失败态错误回传
- 已补前端运行 facade 回归与执行合同深化相关测试
- 统一入口 CLI 已恢复可运行，可再次作为当前命令行验证基线的一部分
- 尚未开始实物测试

## 当前风险

- 如果后续替换真实模型或真实机械臂时不复用当前接口，现有测试会失去约束价值
- 如果 Ubuntu 环境配置没有先落地，实物测试阶段会延后
- 当前测试全部基于 mock 实现，无法代表真实时延、真实视觉噪声和真实执行误差

## 首批测试建议

1. 在当前最近一次全量回归为 44 个通过的基础上继续补充 `--config` 失败路径、更多 `release` / 放置场景以及 perception/execution 合同回归与 Ubuntu 实机验证事实。
2. 继续增加错误码一致性和接口契约测试。
3. 继续把前端运行 facade 映射到真实后端接口，并补相应回归测试。
4. 为真实适配器预留可复用测试夹具与模拟输入。
5. 完成 Ubuntu 实机运行记录后，再进入实际部署与联调。

## 已记录测试事实

### 2026-04-20 最近一次全量测试回归（phase2 主线持续推进后）

- 类型：代码级全量回归测试
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：44 个测试全部通过
- 覆盖范围：
  - phase-1 基线、phase2 决策主线、感知接口、执行合同、前端接口占位 API / facade 与相关回归测试全部通过
- 备注：当前 44 个测试主要证明 mock-first 合同、配置装配、错误边界、执行合同与前端占位 facade 的稳定性；统一入口 CLI 也已恢复可运行，但这仍不代表 Ubuntu 实机、真实硬件或真实模型链路已验证

### 2026-04-20 前端运行 facade 回归

- 类型：代码级合同测试 / phase-2 前端运行占位接口收敛
- 执行命令：`uv run pytest -q E:/lwj/biyesheji/tests/test_app_phase1.py`
- 结果：通过
- 汇总：15 个测试全部通过
- 覆盖范围：
  - `FrontendRuntimeFacade` 的 `bootstrap / config / runtime_api / run_api / error`
  - 前端运行快照中的 `selected_capability`、`selected_action`、`last_node_result`
  - bootstrap 中的 `execution_capabilities` 与 `execution_safety`
  - 前端 facade 相关阻塞修复后回归
- 备注：本组测试证明前端运行占位接口已进一步收口成 facade 形态，但仍不代表真实 HTTP/SSE/WebSocket 服务已实现

### 2026-04-20 全量测试回归（phase2 感知合同深化后）

- 类型：代码级全量回归测试
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：43 个测试全部通过
- 覆盖范围：
  - phase-1 基线、phase2 决策主线、感知合同深化、执行合同、前端占位 API 与相关回归测试全部通过
- 备注：当前 43 个测试主要证明 mock-first 合同、配置装配、错误边界与前端占位 API 的稳定性，不代表真实硬件、真实模型或实物实验已验证

### 2026-04-20 phase2 感知合同深化回归

- 类型：代码级合同测试 / perception phase2 合同深化
- 执行命令：`uv run pytest -q E:/lwj/biyesheji/tests/test_perception_phase1.py E:/lwj/biyesheji/tests/test_app_phase1.py`
- 结果：通过
- 汇总：29 个测试全部通过
- 覆盖范围：
  - 感知层：结构化 `structured_observations` 校验、runtime summary 透传、provider metadata 摘要、VLM auth/rate-limit/invalid-response 错误边界、`vlm_local_path` 配置映射
  - 统一入口：扩展 perception 配置字段继续稳定装配到 runtime
- 备注：本轮仍主要证明 mock-first 合同、配置边界与错误边界稳定，不代表真实相机、真实 ROS/LeRobot 状态源或真实 VLM SDK 已联通

### 2026-04-20 最近一次全量测试回归（phase2 主线持续推进后）

- 类型：代码级全量回归测试
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：38 个测试全部通过
- 覆盖范围：
  - phase-1 基线、phase2 决策主线、感知接口、执行合同、前端接口占位 API 与相关回归测试全部通过
- 备注：当前 38 个测试主要证明 mock CLI 之外的合同、装配与回归稳定性；同一时间点下，统一入口 CLI 因 `_build_parser` 未定义暂不可运行，因此不能再把“CLI 可运行”作为当前基线事实的一部分

### 2026-04-20 全量测试回归（phase2 前端占位 API 后）

- 类型：代码级全量回归测试
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：37 个测试全部通过
- 覆盖范围：
  - phase-1 基线、phase2 决策主线、感知接口、执行合同、前端接口占位 API 与相关回归测试全部通过
- 备注：当前 37 个测试仍主要证明 mock CLI、统一入口、跨层合同、provider/adapter 工厂、capability/action 选择与前端占位 API 的稳定性，不代表真实硬件、真实模型或实物实验已验证

### 2026-04-20 前端接口占位合同回归

- 类型：代码级合同测试 / phase-2 前置接口收敛
- 执行命令：`uv run pytest -q E:/lwj/biyesheji/tests/test_app_phase1.py`
- 结果：通过
- 汇总：11 个测试全部通过
- 覆盖范围：
  - 前端配置快照 `build_frontend_config_payload`
  - 前端启动快照 `build_frontend_bootstrap`
  - 运行态快照 `build_frontend_run_snapshot`
  - 失败态错误消息回传
  - 统一入口配置装配对 `llm_local_path`、`vlm_local_path`、`home_pose` 的映射
- 备注：本组测试只证明占位合同和状态字段已固定，不代表真实 HTTP/SSE/WebSocket 接口已实现

### 2026-04-20 全量测试回归（phase2 感知接口后）

- 类型：代码级全量回归测试
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：28 个测试全部通过
- 覆盖范围：
  - phase-1 与 phase2 当前感知 / 决策 / 执行改造相关测试全部通过
  - 感知层新增 runtime config、adapter 工厂注入、非法 base64 与扩展配置装配回归通过
- 备注：当前 28 个测试仍主要证明 mock CLI、统一入口与跨层合同稳定，不代表真实硬件、真实模型或实物实验已验证

### 2026-04-20 phase2 感知接口 focused tests

- 类型：代码级合同测试 / perception phase2 边界补强
- 执行命令：`uv run pytest -q E:/lwj/biyesheji/tests/test_perception_phase1.py E:/lwj/biyesheji/tests/test_app_phase1.py`
- 结果：通过
- 汇总：19 个测试全部通过
- 覆盖范围：
  - 感知层：非法 base64、扩展 runtime config 映射、adapter factory 注入、unsupported backend 错误映射、provider 工厂路径
  - 统一入口：扩展 perception 配置字段从 YAML 装配到 runtime
- 备注：本轮仍只验证 mock-first 合同与 phase-2 接口边界，不代表真实相机、真实 ROS/LeRobot 状态源或真实 VLM SDK 已联通

### 2026-04-20 P0 合同收敛与 focused tests 回归

- 类型：代码级合同测试 / 统一入口与感知执行回归
- 执行命令：`uv run pytest -q tests/test_app_phase1.py tests/test_perception_phase1.py tests/test_execution_phase1.py`
- 结果：通过
- 汇总：17 个测试全部通过
- 覆盖范围：
  - 统一入口：单任务成功、多任务成功、配置装配、未知工具失败、原子执行工具暴露、执行失败闭环透传、感知失败闭环透传
  - 感知层：`describe_scene` 成功、`get_image` 失败、`get_robot_state` 成功/失败、未知工具 envelope
  - 执行层：`run_smolvla` 成功、`move_to` 校验失败、未知工具统一 envelope
- 备注：本轮回归验证了 capability contract 雏形、结构化 `ee_pose`、perception/execution envelope 与 focused tests 的兼容性

### 2026-04-20 全量测试回归（P0 第二批后）

- 类型：代码级全量回归测试
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：21 个测试全部通过
- 覆盖范围：
  - 决策层：单任务完成路径、多任务循环路径
  - 感知层：`describe_scene` 成功路径、`get_image` / `get_robot_state` 失败错误封套、未知工具统一错误封套
  - 执行层：`run_smolvla` 成功路径、`move_to` 校验失败急停、未知工具统一错误封套
  - 统一入口：单任务 / 多任务闭环、配置文件加载、frontend `max_iterations` 回退、未知工具稳定信封、原子执行工具透传、感知失败闭环、执行失败闭环
- 备注：当前 21 个测试仍主要证明 mock CLI、统一入口和跨层合同的稳定性，不代表真实硬件、真实模型或实物实验已验证

### 2026-04-20 phase2 决策主线首轮回归

- 类型：代码级决策与统一入口回归测试
- 执行命令：`uv run pytest -q tests/test_decision_phase1.py tests/test_app_phase1.py`
- 结果：通过
- 汇总：12 个测试全部通过
- 覆盖范围：
  - decision 层：能力选择不再固定为单一路径，新增 `return_home` / `release_object` 的 capability/action 选择测试
  - 统一入口：多任务路径在 phase2 决策主线下仍保持可回归验证
- 备注：本轮验证的是第二阶段主线第一步的 capability/action 选择增强，不代表真实模型推理或真实执行链路已接入

### 2026-04-20 全量测试回归（phase2 决策主线首轮后）

- 类型：代码级全量回归测试
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：22 个测试全部通过
- 覆盖范围：
  - phase-1 与 phase2 首轮决策主线改造相关测试全部通过
- 备注：当前 22 个测试仍主要证明 mock CLI、统一入口、跨层合同和 capability/action 选择的稳定性，不代表真实硬件、真实模型或实物实验已验证

### 2026-04-20 全量测试回归（P0 第三批后）

- 类型：代码级全量回归测试
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：21 个测试全部通过
- 覆盖范围：
  - 决策层：单任务完成路径、多任务循环路径
  - 感知层：`describe_scene` 成功路径、`get_image` / `get_robot_state` 失败错误封套、未知工具统一错误封套、provider 工厂注册路径
  - 执行层：`run_smolvla` 成功路径、`move_to` 校验失败急停、未知工具统一错误封套、runtime 工厂注入路径
  - 统一入口：单任务 / 多任务闭环、配置文件加载、frontend `max_iterations` 回退、未知工具稳定信封、原子执行工具透传、感知失败闭环、执行失败闭环
- 备注：当前 21 个测试仍主要证明 mock CLI、统一入口和跨层合同的稳定性，不代表真实硬件、真实模型或实物实验已验证

### 2026-04-20 Ubuntu mock 运行链路验证

- 类型：运行验证 / Ubuntu runbook 对齐验证
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：21 个测试全部通过
- 说明：确认当前项目级测试入口在仓库现有环境下可运行

- 执行命令：`uv run python -m embodied_agent.app --instruction "抓取桌面方块"`
- 结果：通过
- 输出摘要：`全部任务完成`
- 说明：确认统一入口可完成单任务 mock 闭环

- 执行命令：`uv run python -m embodied_agent.app --instruction "抓取桌面方块" --dump-final-state`
- 结果：通过
- 输出摘要：最终状态 JSON 中包含 `action_result: success`
- 说明：确认统一入口支持最终状态导出

- 执行命令：`uv run python -m embodied_agent.app --instruction "抓取桌面方块" --list-tools`
- 结果：通过
- 输出摘要：返回 8 个工具：`describe_scene`、`get_image`、`get_robot_state`、`grasp`、`move_home`、`move_to`、`release`、`run_smolvla`
- 说明：确认统一入口已装配感知与执行层的最小工具集合，并可被直接检查

- 备注：本轮仅验证当前 mock CLI 可运行链路，不代表 Ubuntu 实机安装、前端联动、真实 MCP 传输、真实 `LeRobot`、真实 `SmolVLA` 权重或实物链路已验证


### 2026-04-19 文档基线检查

- 类型：文档结构与路径一致性检查
- 范围：`docs/` 目录结构、spec 路径引用、交接文档阅读顺序
- 结果：通过
- 说明：作为项目初始文档基线保留

### 2026-04-20 统一启动入口跨层集成测试

- 类型：代码级集成测试 / mock 闭环装配验证
- 执行命令：`uv run pytest -q tests/test_app_phase1.py`
- 结果：通过
- 汇总：1 个测试通过
- 覆盖范围：
  - 统一入口 `src/embodied_agent/app.py` 的配置加载、mock MCP 服务接线与决策图装配
  - 单任务指令下的 `task_planner -> scene_analyzer -> action_decider -> executor -> verifier` mock 闭环
  - 关键工具调用 `get_image`、`get_robot_state`、`describe_scene`、`run_smolvla` 的跨层接线事实
- 备注：该测试验证的是 mock integration validation fact，不代表真实 MCP 传输、前端联动、Ubuntu 部署或真实硬件链路已验证

### 2026-04-20 本地环境修复后 pytest 验证

- 类型：代码级单元测试 / 环境可用性验证
- 执行命令：`uv run pytest -q`
- 结果：通过
- 汇总：6 个测试全部通过
- 覆盖范围：
  - 决策层：验证单任务完成路径与多任务循环路径
  - 感知层：验证场景描述成功路径与相机采集失败错误返回
  - 执行层：验证 `run_smolvla` 成功路径与 `move_to` 参数越界后的急停保护
- 备注：本次验证同时确认本地 Python 环境、依赖安装和测试入口已可正常使用

### 2026-04-19 第一阶段骨架 pytest 回归

- 类型：代码级单元测试
- 执行命令：`python -m pytest tests -q`
- 结果：通过
- 汇总：6 个测试全部通过
- 覆盖范围：
  - 决策层：验证单任务完成路径与多任务循环路径
  - 感知层：验证场景描述成功路径与相机采集失败错误返回
  - 执行层：验证 `run_smolvla` 成功路径与 `move_to` 参数越界后的急停保护
- 备注：测试运行过程中出现第三方依赖告警摘要，但未导致失败，退出码为 0
