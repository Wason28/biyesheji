# 硬件集成待办事项与步骤 (Hardware Integration Todos & Steps)

本文档聚焦当前项目从“本地软件级 demo”继续推进到“真实硬件 + 真实 MCP 闭环”时的待办项。当前代码基线已经具备感知层 `get_image / get_robot_state / describe_scene` 与执行层 `move_to / move_home / grasp / release / servo_rotate / run_smolvla` 的 mock-first 合同，因此后续工作应优先围绕真实适配器、MCP 工具扩展和安全校验展开，而不是重写既有 contract。

## 当前基线与扩展原则

- 当前已存在的感知 MCP 工具：`get_image`、`get_robot_state`、`describe_scene`
- 当前已存在的执行 MCP 工具：`move_to`、`move_home`、`grasp`、`release`、`servo_rotate`、`run_smolvla`
- 当前缺口：真实摄像头数据流、真实 LeRobot 执行链路、真实 SmolVLA 推理链路、硬件安全与运维级工具尚未落地
- 扩展原则：优先补“真实世界接入”能力，再补“场景理解增强”能力，最后补“运维/数据闭环”能力

## 建议新增 MCP 工具清单

### P0：真实链路打通

这些工具直接决定项目能否从 mock execution 进入真实硬件联调阶段，应最优先实现。

- [ ] `stream_camera_frame`
  - 职责：从 USB/RealSense 等真实设备采集单帧或低频采样帧，输出标准化图像、时间戳、分辨率与相机参数
  - 归属：感知层 / Camera
  - 优先级：P0
  - 说明：用于替换当前 mock 图像输入，是 `describe_scene`、`run_smolvla` 和前端实时画面展示的上游依赖

- [ ] `get_depth_frame`
  - 职责：采集深度图或 RGB-D 配准结果，输出深度矩阵引用、深度尺度和相机内参
  - 归属：感知层 / Camera
  - 优先级：P0
  - 说明：若后续要做抓取定位、障碍规避和桌面几何建模，该工具是比纯 RGB 更关键的第二入口

- [ ] `get_robot_telemetry`
  - 职责：读取真实机器人关节状态、末端位姿、夹爪开合、错误码与通信健康状态
  - 归属：执行层 / LeRobot
  - 优先级：P0
  - 说明：用于替换当前 mock `robot_state`，并为前端遥测展示、SmolVLA 输入拼接与安全校验提供真实反馈

- [ ] `dispatch_lerobot_action`
  - 职责：把统一动作合同转换成 LeRobot 可执行指令，支持 move / grasp / release / home 等动作分发
  - 归属：执行层 / LeRobot
  - 优先级：P0
  - 说明：这是执行层从“本地 contract”走向“真实控制接口”的核心桥接工具，建议保持与现有 action contract 对齐

- [ ] `safety_precheck`
  - 职责：在真实动作下发前校验工作空间边界、关节限位、速度阈值、碰撞风险和急停状态
  - 归属：执行层 / Safety
  - 优先级：P0
  - 说明：真实链路一旦接通，该工具应成为所有动作工具的前置依赖，避免直接将模型输出送入物理设备

### P1：感知与定位增强

这些工具用于把“能看见”推进到“能定位、能理解、能约束动作”。

- [ ] `detect_objects`
  - 职责：从当前图像中输出候选目标框、类别、置信度与实例 id
  - 归属：感知层 / Scene Grounding
  - 优先级：P1
  - 说明：适合为“抓取红色杯子”“定位桌面方块”等自然语言任务提供结构化目标候选

- [ ] `ground_target_pose`
  - 职责：融合 RGB/RGB-D、相机参数和机械臂基座坐标，输出目标物体在机器人坐标系下的抓取位姿候选
  - 归属：感知层 / Scene Grounding
  - 优先级：P1
  - 说明：它连接感知和执行，是比纯场景描述更接近动作生成的中间工具

- [ ] `calibrate_camera_to_robot`
  - 职责：执行手眼标定，输出外参矩阵、标定误差和可复用的标定配置
  - 归属：感知层 / Calibration
  - 优先级：P1
  - 说明：没有稳定标定，`ground_target_pose` 与 SmolVLA 输出都无法可靠落到真实世界

- [ ] `estimate_workspace_occupancy`
  - 职责：生成桌面占用图、可达区域和禁入区域摘要
  - 归属：感知层 / Safety
  - 优先级：P1
  - 说明：适合为安全预检和动作规划提供环境级约束，而不仅是目标级识别

### P1：VLA 执行增强

这些工具用于把 SmolVLA 从“单次推理能力”扩展到“可观测、可验证、可回退”的执行链路。

- [ ] `plan_smolvla_action`
  - 职责：基于图像、文本指令和机器人状态生成结构化动作计划，而不直接落硬件
  - 归属：执行层 / SmolVLA
  - 优先级：P1
  - 说明：建议把“规划”和“执行”拆开，先得到可审计的 action plan，再决定是否调用真实机器人

- [ ] `decode_action_tokens`
  - 职责：将 SmolVLA 输出 token 解码为位姿增量、关节轨迹或夹爪控制序列
  - 归属：执行层 / SmolVLA
  - 优先级：P1
  - 说明：有助于把当前黑箱式 `run_smolvla` 改造成可检查、可回放的中间层

- [ ] `preview_trajectory`
  - 职责：对即将执行的动作轨迹做几何预览，输出关键点、风险点与预计执行时长
  - 归属：执行层 / Safety
  - 优先级：P1
  - 说明：适合在前端工作台中展示“执行前预览”，也便于人工确认高风险动作

- [ ] `verify_grasp_result`
  - 职责：基于执行后图像、夹爪状态与位姿变化判断抓取是否成功
  - 归属：执行层 / Verification
  - 优先级：P1
  - 说明：可显著提升闭环质量，避免仅依赖执行成功返回值误判任务完成

### P2：数据闭环与运维能力

这些工具不阻塞首次真实联调，但会显著提升系统可维护性、可复现性与论文材料产出效率。

- [ ] `record_episode`
  - 职责：记录指令、图像、机器人状态、动作序列和结果标签，形成训练/复盘样本
  - 归属：平台层 / Data Ops
  - 优先级：P2
  - 说明：适合为 SmolVLA 微调、案例回放和实验复现实验提供统一数据落盘入口

- [ ] `replay_episode`
  - 职责：回放历史任务的关键帧、事件流和动作轨迹，用于故障分析与答辩演示
  - 归属：平台层 / Data Ops
  - 优先级：P2
  - 说明：与前端现有 snapshot / events 机制天然兼容，适合补强演示与调试能力

- [ ] `hardware_health_check`
  - 职责：探测摄像头、机械臂、串口/网口、模型服务与 GPU 推理环境是否就绪
  - 归属：平台层 / Ops
  - 优先级：P2
  - 说明：建议作为启动前检查和论文实验前检查工具，减少“环境没准备好却开始联调”的排障成本

- [ ] `export_run_artifacts`
  - 职责：导出运行日志、关键截图、配置快照和错误报告
  - 归属：平台层 / Ops
  - 优先级：P2
  - 说明：适合答辩材料整理、实验记录归档和跨会话交接

## 按模块整理的待办事项

### 1. 摄像头集成 (Camera Integration)

#### 待办事项 (Todos)

- [ ] 评估并选择合适的物理摄像头设备，优先确认 USB RGB 摄像头与 RealSense 两条路线的驱动稳定性
- [ ] 在 `src/embodied_agent/perception/adapters.py` 中落地真实 CameraAdapter，先支持 `stream_camera_frame`
- [ ] 补 `get_depth_frame` 所需的深度流读取、时间同步和 RGB-D 配准逻辑
- [ ] 将相机输出统一转为与现有 `get_image` / `describe_scene` 兼容的 payload 格式
- [ ] 在前端 Workbench 验证单帧刷新、关键帧展示与延迟情况

#### 实施步骤 (Steps)

1. **硬件连接与测试**：在宿主机环境（Windows/Ubuntu）连接摄像头，用 OpenCV 或官方 SDK 验证图像读取。
2. **真实采集工具落地**：优先补 `stream_camera_frame`，保证输出字段与现有感知合同兼容。
3. **深度流补齐**：若设备支持深度，继续补 `get_depth_frame` 与 RGB-D 对齐逻辑。
4. **前端联调**：将真实帧接入 Workbench，验证刷新稳定性、分辨率和画面延迟。

---

### 2. LeRobot 集成 (LeRobot Integration)

#### 待办事项 (Todos)

- [ ] 在 `execution` 模块中引入或配置 LeRobot 作为真实机器人控制底座
- [ ] 以 `dispatch_lerobot_action` 为核心，建立统一动作合同到 LeRobot API 的映射
- [ ] 以 `get_robot_telemetry` 替换 mock 状态回传，补齐夹爪状态、错误码和心跳信息
- [ ] 将 `safety_precheck` 接入动作执行前链路，覆盖限位、禁入区、速度和急停校验
- [ ] 在独立脚本与前端工作台两条路径上验证真实动作调度和状态回读

#### 实施步骤 (Steps)

1. **环境准备**：安装 LeRobot 依赖并确认串口、局域网或控制总线可用。
2. **动作桥接开发**：在 `src/embodied_agent/execution/robot_adapter.py` 中先打通 `dispatch_lerobot_action`。
3. **遥测回读接线**：补齐 `get_robot_telemetry`，确保执行前后都能拿到真实状态。
4. **安全前置化**：把 `safety_precheck` 置于所有真实动作调用前，并记录失败原因。

---

### 3. SmolVLA 集成 (SmolVLA Integration)

#### 待办事项 (Todos)

- [ ] 将 SmolVLA 从“单工具调用”扩展为“规划、解码、预览、执行、验证”链路
- [ ] 落地 `plan_smolvla_action` 与 `decode_action_tokens`，拆分黑箱推理步骤
- [ ] 让 `preview_trajectory` 在真实执行前给出几何与风险摘要
- [ ] 使用 `verify_grasp_result` 判断任务是否真正完成，而非只看动作返回值
- [ ] 持续优化模型推理延迟，确保感知-决策-执行闭环满足实时性要求

#### 实施步骤 (Steps)

1. **模型加载与推理环境搭建**：在 `src/embodied_agent/execution/smolvla.py` 保持现有接口不破坏的前提下补可拆分的规划/解码入口。
2. **Prompt 与数据工程**：统一图像、文本和机器人状态输入格式，优先与 `stream_camera_frame`、`get_robot_telemetry` 对齐。
3. **动作中间层建设**：先输出结构化 action plan 与 token 解码结果，再决定是否下发真实硬件。
4. **闭环验证**：接入 `verify_grasp_result`，形成“执行结果可验证”的最小真实闭环。

## 推荐实现顺序

1. **第一批 P0**：`stream_camera_frame`、`get_robot_telemetry`、`dispatch_lerobot_action`、`safety_precheck`
2. **第二批 P0/P1**：`get_depth_frame`、`calibrate_camera_to_robot`、`ground_target_pose`
3. **第三批 P1**：`plan_smolvla_action`、`decode_action_tokens`、`preview_trajectory`、`verify_grasp_result`
4. **第四批 P2**：`record_episode`、`replay_episode`、`hardware_health_check`、`export_run_artifacts`
