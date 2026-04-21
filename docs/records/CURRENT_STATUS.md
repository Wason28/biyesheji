# 当前状态

## 项目基准

- 唯一权威来源：`# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- docs 导航：`docs/README.md`
- 目标部署环境：`Ubuntu`
- 最近更新时间：2026-04-21

## 当前阶段判断

当前项目已完成第一阶段骨架实现与第二阶段主线收敛。第三阶段当前已推进到“前端完整规范功能已补齐、后端配置/工具合同已完成一轮收口、浏览器联调截图与 live 验证事实已补入”的状态。与此同时，第四阶段前置的“本地最小端到端闭环”也已补齐：现有 `mock runtime + backend/http + frontend workbench` 已能稳定完成初始化、配置保存、工具刷新、run 提交、`snapshot/events` 回放与终态留痕，并可通过 smoke 脚本重复验收。当前可将第四阶段推进口径写成“本地最小闭环完成，等待 Ubuntu / 真实链路扩展”，但这仍不等于真实硬件、真实视频流、生产级流式服务或端到端实体闭环已完成。

## 当前里程碑

- 当前阶段：第三阶段已完成，当前处于“完整规范功能、后端配置写回与工具刷新、浏览器联调截图与 live 验证事实已补齐”的状态
- 当前主线：冻结第三阶段完成口径，补测试与论文记录，准备转入第四阶段端到端闭环与论文撰写

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
- 已补任务面板可选 `run_id` 输入、错误码回显与事件流错误提示
- 已完成后端 `PUT /api/v1/runtime/config` 与 `POST /api/v1/runtime/tools/refresh` 合同收口，并补入对应 phase3 回归测试
- 已完成配置面板可写化：支持模型选择、API Key、本地路径、机械臂初始位校准、速度缩放与最大迭代次数提交/回滚
- 已补模型部署助手与系统载入助手提示信息，并在运行态面板承接 `current_image` 图像展示
- 已执行 `uv run pytest tests/test_backend_phase3.py tests/test_backend_http_phase3.py tests/test_backend_run_stream_phase3.py -q`，结果 `16 passed`
- 已执行 `npm --prefix "/e/lwj/biyesheji/frontend" run build`，结果通过
- 已完成 live 联调验证：`bootstrap / config / tools / runs / snapshot / events` 在本地后端与前端开发服务器下可用，并生成工作台截图 `docs/records/phase3_workbench_2026-04-21.png` 与 `docs/records/phase3_workbench_2026-04-21_live.png`
- 已新增本地最小闭环 smoke 脚本 `scripts/phase4_local_e2e_smoke.py`，并生成结果 `docs/records/phase4_local_e2e_smoke_result_2026-04-21.json`
- 已执行 `uv run python scripts/phase4_local_e2e_smoke.py`，结果通过，证明本地 mock-first 前后端闭环可重复验收

## 当前实现状态

- 决策层：可基于用户指令驱动 `task_planner -> scene_analyzer -> action_decider -> executor -> verifier` 固定流程
- 感知层：保持 mock-first 能力，已收敛结构化 `scene_observations`、provider 元数据与错误边界
- 执行层：可在 mock 运行时中执行 `move_to`、`move_home`、`grasp`、`release`、`run_smolvla`
- 后端层：最小 HTTP / SSE 合同、`run_id` 生命周期、终态会话清理与非负事件游标约束已形成可测试基线；`PUT /config` 与 `POST /tools/refresh` 已完成一轮收口并通过 focused tests，但后端长期仍为同步 WSGI + 进程内线程骨架
- 前端层：`App.tsx` 组合五块工作区；`ConfigPanel` 已升级为可编辑工作区，支持模型选择、API Key、本地路径、机械臂初始位校准、速度缩放与最大迭代次数提交/回滚，并承接模型部署助手/系统载入助手提示；`ControlPanel` 已提供初始化失败重试与可选 `run_id` 输入；`workbench.ts` 在 run 受理后和 SSE 异常时都会尝试 `snapshot_url` 兜底同步，并区分错误码；事件面板继续按 `version` 去重并显式展示续连状态与事件流错误提示；运行态面板已承接 `current_image` 图像展示
- 验证层：历史全量基线仍为 67 个 pytest 通过；本轮新增 focused tests 使用 `uv run pytest ...` 通过，前端构建通过，且已完成浏览器级工作台截图、live HTTP 流程验证与本地最小闭环 smoke 脚本验证

## 主要缺口

- 当前仍为 mock-first 骨架，尚未接入真实 VLM、真实 LLM、真实 `SmolVLA` 权重与真实机械臂
- `backend/http.py` 仍采用标准库同步 WSGI 传输，`RunRegistry` 仍为进程内实现；真实 SSE / WebSocket、主动取消、持久化与跨进程会话治理尚未实现
- 当前已完成浏览器级截图、live HTTP 验证与本地最小闭环 smoke 验证，但前端自动化测试、真实后端长生命周期流式验证与 Ubuntu 实机留痕仍待补齐
- 运行态视频区当前已能承接 `current_image` 图像字段，但真实摄像头视频流与媒体资源治理尚未开始实现
- Ubuntu 实机、前端联动、真实模型与真实硬件链路仍未验证
- 端到端实体分拣测试、数据采集与微调流程尚未开始

## 当前阻塞项

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
