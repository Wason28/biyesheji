# 当前状态

## 项目基准

- 唯一权威来源：`# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- docs 导航：`docs/README.md`
- 目标部署环境：`Ubuntu`
- 最近更新时间：2026-04-20

## 当前阶段判断

当前项目已完成第一阶段骨架实现与第二阶段主线收敛。第三阶段当前已从“前端工程骨架已落地并构建通过”进一步收敛到“前端已补齐 config 消费、`snapshot_url` 兜底同步、初始化重试入口，并保持构建通过”的状态。当前前端已能够围绕既有 `bootstrap / config / tools / runs / events` 合同完成初始化、配置展示、任务提交、快照同步和 SSE 订阅占位；但这仍不等于真实浏览器联调、生产级流式服务或端到端闭环已完成。

## 当前里程碑

- 当前阶段：第三阶段已启动，当前处于“前端消费边界已补强，第三轮文档再次同步完成”的状态
- 当前主线：冻结前端消费合同，优先补浏览器联调记录、最小验收闭环与截图证据

## 已完成

- 已建立 `src/embodied_agent/` 三层骨架目录：`perception/`、`decision/`、`execution/`
- 已完成第二阶段主线收敛：决策层状态流转、感知/执行合同与前端展示合同边界稳定
- 已落地独立 backend 模块：`contracts.py`、`presenters.py`、`service.py`、`run_registry.py`、`http.py`
- 已落地最小后端接口：`bootstrap / config / tools / run / runs / events`
- 已新增 `src/embodied_agent/adapters/mcp_gateway.py`，统一感知层与执行层工具响应 envelope
- 已将 `src/embodied_agent/app.py` 收口为组合根与 CLI 入口
- 已创建 `frontend/` 前端工程，技术栈为 `React 19 + TypeScript + Vite + Zustand`
- 已建立前端工作台主页面与 5 个面板模块：任务输入、配置展示、运行态快照、事件订阅、工具面板
- 已完成前端 config 消费补强：优先读取 `GET /api/v1/runtime/config`，失败或未返回时回退到 `bootstrap.config`
- 已完成前端初始化失败兜底：任务面板在初始化失败时显式提示，并提供“重试初始化”入口
- 已完成运行态快照兜底同步：run 受理后先通过 `snapshot_url` 主动同步一次快照，SSE 出错时再次尝试用 `snapshot_url` 对齐最新状态
- 已建立 `frontend/src/lib/api.ts` 与 `frontend/src/lib/sse.ts`，支持同源 `/api` 代理或 `VITE_RUNTIME_BASE_URL`
- 已执行 `python -m pytest tests -q`，当前为 67 个测试全部通过
- 已执行 `npm run build`（目录：`frontend/`），结果通过，证明前端骨架在本轮补强后仍可完成静态构建

## 当前实现状态

- 决策层：可基于用户指令驱动 `task_planner -> scene_analyzer -> action_decider -> executor -> verifier` 固定流程
- 感知层：保持 mock-first 能力，已收敛结构化 `scene_observations`、provider 元数据与错误边界
- 执行层：可在 mock 运行时中执行 `move_to`、`move_home`、`grasp`、`release`、`run_smolvla`
- 后端层：最小 HTTP / SSE 合同、`run_id` 生命周期、终态会话清理与非负事件游标约束已形成可测试基线，但仍是同步 WSGI + 进程内线程骨架
- 前端层：`App.tsx` 组合五块工作区；`ConfigPanel` 已消费 `bootstrap + config` 双读取合同；`ControlPanel` 已提供初始化失败重试；`workbench.ts` 在 run 受理后和 SSE 异常时都会尝试 `snapshot_url` 兜底同步；事件面板继续按 `version` 去重并显式展示续连状态
- 验证层：当前已有 67 个 pytest 测试通过；前端侧当前已完成构建验证，但尚未形成浏览器级自动化回归或手工联调留痕

## 主要缺口

- 当前仍为 mock-first 骨架，尚未接入真实 VLM、真实 LLM、真实 `SmolVLA` 权重与真实机械臂
- `backend/http.py` 仍采用标准库同步 WSGI 传输，`RunRegistry` 仍为进程内实现；真实 SSE / WebSocket、主动取消、持久化与跨进程会话治理尚未实现
- 前端虽已补齐 config 消费、`snapshot_url` 兜底同步与初始化重试，但当前仍缺少浏览器手工联调记录、前端自动化测试与真实后端启动截图
- 运行态视频区当前仅展示 `current_image` 占位；真实摄像头视频流与媒体资源治理尚未开始实现
- Ubuntu 实机、前端联动、真实模型与真实硬件链路仍未验证
- 端到端实体分拣测试、数据采集与微调流程尚未开始

## 当前阻塞项

- 当前前端虽已具备更完整的消费与兜底逻辑，但尚未产出浏览器级联调证据；若不尽快补充真实后端启动、页面初始化、run 提交、SSE 中断与终态收口记录，第三阶段仍会停留在“代码可构建、逻辑可兜底，但交互事实未留痕”的状态
- 当前虽已有最小 WSGI HTTP + SSE 回放骨架，但长期服务栈尚未最终选定
- `docs/reference/INTERFACES.md` 当前不存在；在未显式新增接口参考文档前，只能以 `docs/specs/07-frontend-spec.md`、backend tests、frontend 代码与 records 作为临时合同基线
- 本地 PowerShell 仍未识别 `uv` 命令；后续若继续依赖 `uv run ...`，需先确认环境变量与安装路径

## 当前优先级栈

- P0：按 `docs/specs/07-frontend-spec.md` 执行前端最小验收清单，并补页面初始化、run 提交、`snapshot_url` 兜底同步、失败回显与事件断开场景的验证记录
- P0：补浏览器级运行截图或录屏证据，避免“仅构建通过”与“实际联调通过”继续混淆
- P1：在不突破展示合同边界的前提下补空态、错误态、加载态与事件续连提示的细节打磨
- P1：后端仅评估长连接服务栈演进方案与现有 WSGI 边界，不提前展开生产级流式重构

## 下一步建议

1. 先用当前前端骨架与既有后端接口完成首轮浏览器联调，并把“初始化成功 / 初始化失败重试 / run 受理 / `snapshot_url` 同步成功 / 终态收口”事实补入记录文档。
2. 按 `docs/specs/07-frontend-spec.md` 的 9 项最小验收清单逐项打勾，优先覆盖重复 `run_id`、非法游标、事件流中断与空态/错误态。
3. 在未完成浏览器联调前，不把“前端已补 config 消费、`snapshot_url` 兜底同步和初始化重试”扩写成“前后端闭环已完成”或“流式订阅已稳定生产可用”。
4. 若后续补充前端运行或浏览器验证结果，同步检查 `TEST_REPORT.md`、`FIGURE_ASSETS.md` 与 `THESIS_PROGRESS.md` 是否需要更新。
