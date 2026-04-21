# 图表素材清单

## 文档定位

本文档用于追踪论文与答辩所需图表素材，避免后期集中返工。

- 素材名称：第三阶段完整规范工作台截图（2026-04-21）
  - 来源依据：`docs/records/phase3_workbench_2026-04-21.png`
  - 建议内容：完整配置工作区、工具面板、运行态快照与事件订阅的工作台首屏
  - 当前状态：已留档
  - 论文用途：系统实现与验证、前端交互设计、答辩展示
- 素材名称：第三阶段 live 联调工作台截图（2026-04-21）
  - 来源依据：`docs/records/phase3_workbench_2026-04-21_live.png`
  - 建议内容：本地 frontend dev server + isolated backend 联调时的实际页面截图
  - 当前状态：已留档
  - 论文用途：系统实现与验证、前后端联调留痕、答辩展示

## 第三轮前端骨架与合同消费落地后的新增素材

- 素材名称：前端工程骨架结构图
  - 来源依据：`frontend/package.json`、`frontend/src/App.tsx`、`frontend/src/components/*`
  - 建议内容：React 19 + Vite 7 + Zustand 5 的前端工程结构，任务输入 / 配置展示 / 运行态快照 / 事件订阅 / 工具面板五块布局关系
  - 当前状态：可基于现有代码直接出图，尚未绘制
  - 论文用途：系统架构设计、前端交互设计、系统实现与验证
- 素材名称：前端状态管理与接口接线图
  - 来源依据：`frontend/src/store/workbench.ts`、`frontend/src/lib/api.ts`、`frontend/src/lib/sse.ts`
  - 建议内容：`initialize -> bootstrap/config/tools`、`submitRun -> POST /runs -> accepted.run`、`syncRunSnapshot(snapshot_url)`、`EventSource(events_url) -> snapshot 回放 -> version 去重 -> terminal 收口` 的前端消费链路
  - 当前状态：可基于现有代码直接出图，尚未绘制
  - 论文用途：前后端接口设计、系统实现与验证、答辩讲解
- 素材名称：前端最小消费合同图
  - 来源依据：`src/embodied_agent/backend/contracts.py`、`frontend/src/types/runtime.ts`
  - 建议内容：`bootstrap / config / tools / run / runs / events` 六类接口、`status_fields`、`execution_*`、`snapshot_url / events_url` 与前端显式类型字段边界
  - 当前状态：可基于现有代码与类型定义绘制，尚未出图
  - 论文用途：系统架构设计、前后端接口设计、系统实现与验证
- 素材名称：`run_id` 生命周期时序图
  - 来源依据：`src/embodied_agent/backend/service.py`、`frontend/src/store/workbench.ts`、`tests/test_backend_run_stream_phase3.py`
  - 建议内容：`start_run -> version=1 running ack -> EventSource 订阅 -> snapshot 回放 -> terminal 收口` 的最小生命周期
  - 当前状态：可基于现有代码与测试绘制，尚未出图
  - 论文用途：系统实现与验证、接口语义说明、答辩口头讲解
- 素材名称：HTTP / SSE 路由总览图
  - 来源依据：`src/embodied_agent/backend/http.py`、`frontend/src/lib/api.ts`、`frontend/src/lib/sse.ts`
  - 建议内容：`GET /bootstrap / config / tools`、`POST /run / runs`、`GET /runs/{run_id}`、`GET /runs/{run_id}/events` 及前端调用入口映射
  - 当前状态：可基于现有代码与测试绘制，尚未出图
  - 论文用途：前后端接口设计、第三阶段实现说明
- 素材名称：前端主工作台首屏截图
  - 来源依据：`frontend/src/App.tsx` 与页面运行结果
  - 建议内容：任务输入区、模型配置面板、运行态快照区、事件订阅区、工具面板的首屏布局，以及 `Bootstrap / 事件流 / 当前状态` 顶部状态卡
  - 当前状态：前端骨架与合同消费已落地，可直接截图但尚未留档
  - 论文用途：系统实现与验证、答辩展示
- 素材名称：前端配置与工具面板截图
  - 来源依据：`frontend/src/components/config-panel.tsx`、`frontend/src/components/tools-panel.tsx` 与页面运行结果
  - 建议内容：`decision / perception / execution / frontend` 四分页、`config_status`、`config_source`、执行模型/安全字段、工具列表刷新与 layer 标识
  - 当前状态：已具备 `bootstrap fallback + GET /config` 的展示合同消费，可直接截图但尚未留档
  - 论文用途：前端交互设计、系统实现与验证
- 素材名称：前端运行态与事件订阅截图
  - 来源依据：`frontend/src/components/runtime-panel.tsx`、`frontend/src/components/event-panel.tsx` 与页面运行结果
  - 建议内容：`accepted.run` 首帧、`snapshot_url / events_url`、`robot_state / last_execution / scene_observations / logs`、事件时间线、`latest_version`、terminal 收口提示
  - 当前状态：已具备 `snapshot_url` 主动同步与 `events_url` 订阅展示，可直接截图但尚未留档
  - 论文用途：系统实现与验证、运行态说明、答辩展示
- 素材名称：前端错误态与空态截图
  - 来源依据：前端联调结果、`frontend/src/store/workbench.ts`、后端错误合同
  - 建议内容：空输入、重复 `run_id`、非法事件游标、初始化失败、手动同步快照失败、空态/加载态/失败态回显
  - 当前状态：展示位置已具备，可采集但需联调触发后生成
  - 论文用途：异常处理与鲁棒性说明

## 必备素材

### 1. 架构类

- 系统总体架构图
- 三层解耦结构图
- MCP 调用关系图
- 前端工程骨架结构图
- 前端状态管理与接口接线图

### 2. 决策层类

- LangGraph 主流程图
- `AgentState` 状态结构图
- 闭环验证流程图

### 3. 实现类

- 前端主界面截图
- 模型配置面板截图
- 工具面板截图
- 运行态与事件订阅截图
- 机械臂运行场景照片

### 4. 实验类

- 成功率统计图
- 失败原因分类图
- 分拣结果对比图
- 数据采集流程图
- 样本规模统计图
- 首条真实轨迹落盘截图
- 样本台账示例截图
- `SmolVLA` 微调训练曲线图（待真实训练后产出）

## 当前素材状态

已具备代码或构建证据，可先出图：
- 前端工程骨架结构图
- 前端状态管理与接口接线图
- 前端最小消费合同图
- `run_id` 生命周期时序图
- HTTP / SSE 路由总览图
- 系统架构逻辑图
- 接口与工具逻辑图

前端已落地且界面具备截图条件，但尚未留档：
- 前端主工作台首屏截图
- 前端配置与工具面板截图
- 前端运行态与事件订阅截图
- 前端错误态与空态截图
- 统一启动入口运行截图
- 集成测试通过截图

仍待后续实验或真实链路产出：
- 实验结果图表
- 机械臂运行场景照片
- 首条真实轨迹落盘截图
- 样本台账示例截图
- `SmolVLA` 微调训练曲线图

## 建议维护方式

- 每新增一张图，记录名称、来源、保存位置、用途
- 前端截图至少补记采集条件、后端提交指令、run_id 与页面状态，避免论文图注缺少上下文
- 每完成一次实验，同步登记可复用截图和图表
- 所有素材命名尽量统一，便于论文和答辩复用
