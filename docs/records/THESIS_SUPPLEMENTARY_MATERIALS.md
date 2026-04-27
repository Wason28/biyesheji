# 论文补充材料整理

## 文档定位

本文档用于收口除正文架构图之外，最值得加入论文的补充材料，包括运行证据、接口材料、配置材料、提示词材料和待补采模板。

## 一、已具备且建议直接纳入论文的材料

### 1. 前端真实运行证据

- 首页截图：
  [frontend_video_home_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_home_2026-04-27.png)
- 运行中截图：
  [frontend_video_running_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_running_2026-04-27.png)
- 完成态截图：
  [frontend_video_completed_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_completed_2026-04-27.png)
- 左上角视频流特写：
  [frontend_video_panel_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_panel_2026-04-27.png)

建议论文用途：
- 系统实现与验证
- 前端工作台设计
- 具身智能运行界面展示

### 2. 架构与流程图材料

- Mermaid 图总稿：
  [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
- 章节分配表：
  [THESIS_CHAPTER_ASSET_MAP.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_CHAPTER_ASSET_MAP.md)
- 论文附录现成材料：
  [THESIS_APPENDIX_READY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_APPENDIX_READY.md)
- 论文证据索引：
  [THESIS_EVIDENCE_INDEX.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_EVIDENCE_INDEX.md)

建议论文用途：
- 第 3 章总体架构
- 第 4 到第 6 章分层设计
- 第 7 章前后端通信与状态管理
- 附录与答辩证据组织

### 3. Prompt 材料

- Prompt 整理文档：
  [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
- Prompt 代码资产：
  [prompts.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/shared/prompts.py)
- 汉诺塔任务 skill：
  [13-hanoi-task-skill.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/13-hanoi-task-skill.md)
- 汉诺塔 skill 代码资产：
  [hanoi.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/skills/hanoi.py)

建议论文用途：
- 系统实现细节
- 提示词工程与结构化输出约束
- 附录中的关键 Prompt 列表
- 长程任务技能扩展示例

### 4. 测试与闭环验证材料

- 测试报告：
  [TEST_REPORT.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/TEST_REPORT.md)
- 实验记录：
  [EXPERIMENTS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/EXPERIMENTS.md)
- 当前状态：
  [CURRENT_STATUS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/CURRENT_STATUS.md)
- 本地最小闭环 smoke 结果：
  [phase4_local_e2e_smoke_result_2026-04-21.json](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/phase4_local_e2e_smoke_result_2026-04-21.json)

建议论文用途：
- 系统验证章节
- 测试覆盖说明
- 完成边界与真实性声明

### 5. 配置与接口材料

- 真实链路配置模板：
  [phase4_real_opencv_lerobot_local.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/phase4_real_opencv_lerobot_local.example.yaml)
- 运行说明：
  [12-phase4-real-chain-runbook.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/12-phase4-real-chain-runbook.md)
- HTTP 路由实现：
  [http.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/backend/http.py)

建议论文用途：
- 系统部署说明
- 前后端接口设计
- 实验环境配置说明

## 二、建议补采但尚未形成文件的材料

### 1. 硬件平台实物照片

建议至少采集：
- 机械臂 + 摄像头 + 桌面任务区总览图
- 机械臂侧视图
- 桌面俯视任务区图

建议论文用途：
- 实验平台介绍
- 硬件环境说明
- 答辩展示

### 2. 真实任务证据包

建议每次真实演示都留存：
- 用户指令文本
- 前端运行中截图
- 前端完成态截图
- `run_id`
- 最终 `assistant_response`
- 若有动作执行，再附动作日志

建议论文用途：
- 案例分析
- 运行过程说明
- 闭环演示证据

### 3. 失败案例材料

优先采集三类：
- 摄像头无输入
- 用户手动结束任务
- 视觉感知降级或 provider 异常

建议论文用途：
- 鲁棒性分析
- 异常处理设计
- 系统边界说明

## 三、建议直接写成表格放入论文的内容

### 1. 实验平台配置表

| 项目 | 内容 | 状态 |
| --- | --- | --- |
| 机械臂型号 | 待补实物信息 | 待填写 |
| 摄像头设备 | `/dev/video0` | 已有运行证据 |
| 后端地址 | `127.0.0.1:7864` | 已验证 |
| 前端地址 | `127.0.0.1:5173` | 已验证 |
| 决策模型 | `gpt-4o-mini` | 已验证 |
| 感知模型 | `MiniMax-VL-01` | 已验证 |
| 汉诺塔任务 skill | 已加入项目 | 已有代码、Prompt 与规范文档 |

### 2. 系统完成边界表

| 能力 | 当前状态 | 论文表述建议 |
| --- | --- | --- |
| 前端工作台 | 已完成 | 可本地运行、可观测、可截图留痕 |
| 后端合同与运行时 | 已完成 | 支持 `config / tools / runs / snapshot / events / video-stream` |
| 感知层真实 provider 接入 | 已完成装配 | 已具备真实 VLM 接入能力 |
| 决策层真实 LLM 接入 | 已完成装配 | 已具备真实 LLM 规划能力 |
| 汉诺塔任务 skill | 已加入项目 | 已形成可追溯的任务技能资产，但尚未直连真实硬件执行 |
| 执行层真实硬件闭环 | 已完成核心链路接入 | 已具备 SmolVLA 实体执行事实，后续继续补重复性实验 |
| 生产级流式服务 | 未完成 | 当前为本地软件级验证骨架 |

### 3. Prompt 资产表

| 层级 | Prompt 名称 | 当前状态 | 备注 |
| --- | --- | --- | --- |
| 感知层 | `PERCEPTION_DEFAULT_SCENE_PROMPT` | 已接入 | 默认任务提示词 |
| 感知层 | `PERCEPTION_VISION_RESPONSE_SYSTEM_PROMPT` | 已接入 | 结构化输出约束 |
| 决策层 | `DECISION_PLANNING_SYSTEM_PROMPT` | 已接入 | JSON 规划约束 |
| 决策技能层 | `DECISION_HANOI_SKILL_SYSTEM_PROMPT` | 已建档 | 汉诺塔长程任务技能 Prompt |
| 执行层 | `EXECUTION_SMOLVLA_SYSTEM_PROMPT` | 已建档 | 供后续真实执行接入 |

## 四、建议新增到论文附录的材料

- 关键 Prompt 完整文本
- HTTP 接口表
- 配置模板节选
- 一次完整 `run_id` 生命周期时序图
- 测试覆盖摘要表
- 失败案例截图或日志摘录

## 五、后续补采时的最小登记模板

### 真实演示记录模板

| 字段 | 内容 |
| --- | --- |
| 日期 |  |
| 指令 |  |
| 前端截图 |  |
| run_id |  |
| 最终状态 |  |
| assistant_response |  |
| 是否调用执行动作 |  |
| 备注 |  |

### 失败案例记录模板

| 字段 | 内容 |
| --- | --- |
| 日期 |  |
| 场景 |  |
| 触发条件 |  |
| 错误现象 |  |
| 页面回显 |  |
| 日志位置 |  |
| 结论 |  |
