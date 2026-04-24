# 当前状态

## 项目基准

- 唯一权威来源：`# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- docs 导航：`docs/README.md`
- 目标部署环境：`Ubuntu`
- 最近更新时间：2026-04-24

## 当前阶段判断

当前项目已完成第一阶段骨架实现与第二阶段主线收敛。第三阶段现在可以按“本地软件级 embodied-agent demo 已完成”来定义：前端工作台、后端运行时、真实模型接入与工程化测试已经补齐到可本地运行、可观测、可回归、可通过真实 provider / model adapter 接入的完成口径。现有 `mock execution + backend/http + frontend workbench` 已能稳定完成初始化、配置保存、工具刷新、run 提交、`snapshot/events` 回放、终态留痕、浏览器 smoke 与 focused tests 回归。当前仍不等于真实硬件、真实视频流、MCP 执行闭环或生产级流式服务已完成。

## 当前里程碑

- 当前阶段：第三阶段已完成，当前进入“本地软件级 demo 收口 + 文档同步 + Ubuntu / 真实链路待验收”状态
- 当前主线：保持 contract 稳定，保留 mock execution 边界，继续把后续工作聚焦在 Ubuntu / 真实链路验证与论文材料整理

## 已完成

- 已建立 `src/embodied_agent/` 三层骨架目录：`perception/`、`decision/`、`execution/`
- 已完成第二阶段主线收敛：决策层状态流转、感知/执行合同与前端展示合同边界稳定
- 已落地独立 backend 模块：`contracts.py`、`presenters.py`、`service.py`、`run_registry.py`、`http.py`
- 已落地最小后端接口：`bootstrap / config / tools / run / runs / snapshot / events`，并补齐 `PUT /config` 与 `POST /tools/refresh`
- 已将 `src/embodied_agent/app.py` 收口为组合根与 CLI 入口
- 已创建 `frontend/` 前端工程，技术栈为 `React 19 + TypeScript + Vite + Tailwind CSS v4 + Zustand + lucide-react`
- 已建立前端面板化工作台：顶部状态栏、运行状态、阶段总览、实时画面/遥测、事件日志、控制中心与设置弹层
- 已完成前端 config / tools / runs / snapshot / events 真实接线，支持配置保存、草稿回滚、工具刷新、空指令校验、可选 `run_id`、断开订阅与运行错误提示
- 已完成前端运行诊断展示补强：`plan`、`last_node_result`、`execution_feedback`、`final_report`、`robot_state`、`scene_observations`、`current_image` 均可见
- 已完成 perception 真实 provider 接入：`minimax_mcp_vision`、`openai_gpt4o`、`ollama_vision` 走真实装配；未配置时显式回退 mock provider
- 已完成 decision 真实 LLM adapter 接入：`minimax`、`openai`、`ollama` 支持真实规划调用，并保留 `_split_into_tasks()` 与 `_select_capability_and_action()` heuristic fallback
- 已完成 backend runtime 生命周期补强：`run_id` 冲突、非法 `after_version` / `Last-Event-ID`、缺失 run、原子配置热更新与错误码收敛均已自动化验证
- 已完成工程化验证补强：focused pytest、前端构建与 Playwright smoke 已形成稳定回归门禁
- 已执行 `uv run python -m pytest tests/test_perception_phase1.py tests/test_decision_phase1.py tests/test_backend_phase3.py tests/test_backend_http_phase3.py tests/test_backend_run_stream_phase3.py`，结果 `51 passed`
- 已执行 `npm --prefix frontend run test:e2e`，结果 `3 passed`
- 已执行 `npm --prefix frontend run build`，结果通过；Node `20.18.0` 仍低于 Vite 7 推荐下限，但不阻塞当前构建

## 当前实现状态

- 决策层：LangGraph 主流程保持稳定，已支持真实 LLM provider 规划增强与 heuristic fallback 并存
- 感知层：已具备真实 VLM provider 装配、统一错误类型与 mock fallback；provider readiness 会如实回显到前端
- 执行层：保持 mock execution 边界，继续提供 `move_to`、`move_home`、`grasp`、`release`、`run_smolvla`
- 后端层：最小 HTTP / SSE 合同、`run_id` 生命周期、终态会话清理、非负事件游标约束、原子配置热更新与错误码收敛已形成可测试基线；长期仍为同步 WSGI + 进程内线程骨架
- 前端层：`App.tsx` 已收口为面板化工作台；`ControlPanel`、`RuntimePanel`、`EventPanel`、`ConfigPanel`、`ToolsPanel`、`SettingsModal` 全部接入真实 store 与 runtime contract；当前 smoke 锚点稳定
- 验证层：focused pytest `51 passed`、Playwright e2e `3 passed`、前端构建通过，已形成后续可重复回归门禁

## 主要缺口

- 当前仍以 mock execution 为边界，MCP 执行、真实机械臂动作、真实摄像头视频流与实体抓取闭环尚未实现
- `backend/http.py` 仍采用标准库同步 WSGI 传输，`RunRegistry` 仍为进程内实现；生产级 SSE / WebSocket、主动取消、持久化与跨进程会话治理尚未实现
- 虽已形成 focused pytest 与 Playwright smoke 门禁，但 Ubuntu 实机、真实模型长时运行与真实硬件联调仍未验证
- 文档与代码现已基本对齐，但论文材料、运行手册和更完整的验收记录仍可继续细化

## 当前阻塞项

- 当前虽已有最小 WSGI HTTP + SSE 回放骨架，但长期服务栈尚未最终选定
- `docs/reference/INTERFACES.md` 当前不存在；在未显式新增接口参考文档前，只能以 `docs/specs/07-frontend-spec.md`、backend tests、frontend 代码与 records 作为临时合同基线
- 本地 PowerShell 仍未识别 `uv` 命令；后续若继续依赖 `uv run ...`，需先确认环境变量与安装路径

## 当前优先级栈

- P0：按 `docs/specs/07-frontend-spec.md` 执行前端最小验收清单，并补页面初始化、run 提交、`snapshot_url` 兜底同步、失败回显与事件断开场景的验证记录
- P0：补浏览器级 smoke / e2e 留痕，避免“本地人工联调通过”与“自动化验证通过”继续混淆
- P1：在不突破展示合同边界的前提下补空态、错误态、加载态与事件续连提示的细节打磨
- P1：后端仅评估长连接服务栈演进方案与现有 WSGI 边界，不提前展开生产级流式重构

## 下一步建议

1. 继续把 Ubuntu / 真实链路验证做成独立验收批次，重点验证真实 provider 凭据、运行时配置切换和长时运行稳定性。
2. 若后续推进论文材料，优先同步 `TEST_REPORT.md`、运行截图、真实链路验证记录与完成边界表述，避免把“本地软件级 demo”误写成“真实硬件闭环完成”。
3. 若要继续扩工程化测试，优先补更细的失败态 e2e 与文档化手工验收记录，而不是提前重构服务栈。
