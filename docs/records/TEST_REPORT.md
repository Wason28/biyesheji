# 测试报告

## 文档定位

本文档记录当前里程碑的测试范围、执行命令、真实结果、剩余风险与回归事实。
当前口径以“项目已补齐为本地软件级 embodied-agent demo”为准。测试目标是证明前端工作台、后端运行时、真实模型接入层与工程化验证已经形成可重复回归依据，而不是证明 MCP 执行、真实硬件、真实视频流或生产级流式服务已经完成。

## 当前阶段测试范围

本阶段测试内容：
- 测试 `perception/providers.py` 的真实 provider 装配、mock fallback 与错误映射
- 测试 `decision/providers.py` 与 `decision/nodes.py` 的真实 LLM 规划接入与 heuristic fallback
- 测试 `backend/service.py`、`backend/http.py`、`backend/run_registry.py` 的运行时生命周期、原子配置热更新、错误码与 SSE 回放边界
- 测试前端工作台对 `bootstrap / config / tools / runs / snapshot / events` 的真实消费路径、设置弹窗、控制面板与事件日志
- 验证前端工程 `npm --prefix frontend run build` 可通过
- 验证前端 Playwright smoke / e2e 可通过

本阶段明确不测：
- 不测 MCP 执行、真实机械臂抓取、真实视频流或实体分拣闭环
- 不测生产级 WebSocket、跨进程会话治理、持久化恢复与高并发压测
- 不测 Ubuntu 实机、真实时延、真实摄像头噪声与真实 `SmolVLA` 权重表现

## 当前测试分层

### 1. 单元 / 合同测试

目标：
- 验证感知 provider、决策 provider 与回退策略保持稳定
- 验证后端合同字段、错误码与前端展示载荷保持稳定

### 2. 集成 / 传输测试

目标：
- 验证统一入口 runtime 装配、运行 facade、HTTP / SSE 与 run registry 生命周期边界
- 验证配置更新失败时不会污染当前 runtime

### 3. 前端构建 / 浏览器回归

目标：
- 验证前端工程可构建
- 验证工作台 smoke、设置弹窗、工具刷新、配置保存与本地输入校验

## 当前测试范围快照

| 模块 | 测试级别 | 当前结果 | 结论 |
| --- | --- | --- | --- |
| `tests/test_perception_phase1.py` | 单元 / 合同 | 19/19 通过 | 通过 |
| `tests/test_decision_phase1.py` | 单元 / 合同 | 10/10 通过 | 通过 |
| `tests/test_backend_phase3.py` | 集成 / 运行时 | 9/9 通过 | 通过 |
| `tests/test_backend_http_phase3.py` | 集成 / HTTP / SSE | 7/7 通过 | 通过 |
| `tests/test_backend_run_stream_phase3.py` | 集成 / stream | 6/6 通过 | 通过 |
| `frontend/tests/e2e/workbench-smoke.spec.ts` | 浏览器 e2e | 3/3 通过 | 通过 |
| `frontend` 构建 | 构建门禁 | 通过 | 通过 |

## 本轮执行命令与结果

- 命令：`uv run python -m pytest tests/test_perception_phase1.py tests/test_decision_phase1.py tests/test_backend_phase3.py tests/test_backend_http_phase3.py tests/test_backend_run_stream_phase3.py`
- 结果：通过
- 汇总：`51 passed in 1.25s`
- 说明：确认真实 provider 接入、heuristic fallback、后端生命周期与 HTTP / SSE 边界均可回归

- 命令：`uv run python -m compileall src/embodied_agent`
- 结果：通过
- 说明：确认当前 Python 包可完成语法级编译检查

- 命令：`npm --prefix frontend run build`
- 结果：通过
- 说明：Vite 7 提示当前 Node `20.18.0` 低于推荐下限 `20.19+`，但本轮构建仍成功

- 命令：`npm --prefix frontend run test:e2e`
- 结果：通过
- 汇总：`3 passed in 9.3s`
- 覆盖范围：
  - 工作台启动并完成一次 run
  - 设置弹窗中的配置刷新、工具刷新、助手显示与配置保存
  - 控制面板空指令本地校验

## 当前风险与缺口

- 当前自动化验证仍以本地软件级 demo 为边界，不覆盖 MCP 执行、真实硬件与真实视频流
- 当前 HTTP / SSE 传输仍为同步 WSGI + 进程内线程模型，未覆盖生产级并发与持久化恢复
- 前端 e2e 目前聚焦 smoke 与关键交互，尚未覆盖更长链路的失败态与断流恢复
- Ubuntu 实机、真实 provider 凭据与长时间运行留痕仍待后续验收

## 当前结论

- 当前项目已经具备“本地软件级 embodied-agent demo”的自动化验证基础：后端 focused pytest、前端构建和浏览器 e2e 均已通过
- 当前测试结果支持这样的表述：前端工作台、后端运行时、真实模型接入层与工程化测试已经补齐到可本地运行、可观测、可回归的状态
- 当前测试结果不支持把项目表述为：MCP 执行完成、真实机械臂闭环完成、真实视频流完成或生产级流式服务完成

## 当前阶段测试范围

本阶段测试内容：
- 测试 `backend/contracts.py`、`backend/presenters.py`、`backend/service.py`、`backend/http.py` 的最小后端合同与 HTTP 骨架
- 测试 `backend/run_registry.py` 与 `FrontendRuntimeFacade.start_run / get_run / iter_run_events` 的 run 状态推送骨架、事件版本、终态快照与终态清理
- 测试异步 run 生命周期边界：重复 `run_id` 冲突、`after_version / Last-Event-ID` 非负游标校验、终态 session 保留与清理
- 测试统一入口 `app.py` 作为组合根的 runtime 装配、配置映射、run snapshot 与 facade 兼容性
- 测试 `adapters/mcp_gateway.py` 对感知层与执行层响应 envelope 的统一桥接
- 评估 `frontend/src/App.tsx`、`store/workbench.ts`、`components/*`、`lib/api.ts`、`lib/sse.ts` 对 `bootstrap / config / tools / runs / snapshot / events` 的最小消费接线是否齐备
- 验证前端工程 `npm run build` 可通过，确保第三阶段最小工作台至少达到可构建、可交付静态产物的门禁
- 验证根目录 `npm run dev` 可启动前后端本地联调链路，并确认 execution flow 在真实事件输入下可见变化
- 回归决策层、感知层、执行层现有 mock-first 合同，确保第三阶段新增后端层未破坏前两阶段基线

本阶段明确不测：
- 不测真实浏览器自动化、生产级长连接治理、WebSocket、断线自动重连与 run 过程持续推送稳定性
- 不测真实浏览器联调录屏、端到端 UI 自动化、真实页面交互留痕与前后端联调实测
- 不测真实 `VLM / LLM / SmolVLA / 机械臂`、真实相机噪声、真实时延与实物分拣
- 不测生产级部署、鉴权、中间件、并发压测与持久化

## 当前测试分层

### 1. 单元 / 合同测试

目标：
- 验证决策、感知、执行原子能力的输入输出、错误封套与边界条件
- 验证后端合同字段、配置映射、错误码与展示载荷保持稳定

### 2. 集成 / 传输测试

目标：
- 验证统一入口 runtime 装配、MCP 桥接与 facade 组合行为
- 验证最小 HTTP 骨架的读接口、运行接口、状态码与错误返回

### 3. 前端构建 / 接线评估

目标：
- 验证前端工程可通过 `npm run build`，至少具备第三阶段最小交付物
- 依据当前实现映射 `FE-A01 ~ FE-A09`，确认页面初始化、run 提交、snapshot 同步、SSE 订阅、终态收口与错误提示均有明确代码落点
- 明确“代码接线已具备”与“浏览器联调已留痕”是两层不同结论，避免过度表述

### 4. 硬件 / 实物测试

目标：
- 当前里程碑未启动
- 待 simulation-first 与真实服务链路完成后，再进入 Ubuntu 实机与硬件验证

## 当前测试范围快照

| 模块 | 测试级别 | 测试数 | 当前覆盖目标 | 当前结果 | 结论 |
| --- | --- | ---: | --- | --- | --- |
| `tests/test_decision_phase1.py` | 单元 | 6 | 决策正常结束、循环继续、能力/动作选择 | 6/6 通过 | 通过 |
| `tests/test_perception_phase1.py` | 单元 / 合同 | 14 | 感知成功/失败、provider 边界、配置映射、统一 envelope | 14/14 通过 | 通过 |
| `tests/test_execution_phase1.py` | 单元 / 合同 | 9 | 原子工具、`run_smolvla`、安全边界、工厂注入 | 9/9 通过 | 通过 |
| `tests/test_app_phase1.py` | 集成 / 合同 | 15 | runtime 装配、配置加载、run snapshot、失败闭环、MCP 桥接 | 15/15 通过 | 通过 |
| `tests/test_backend_http_phase3.py` | 集成 / 传输 | 18 | `bootstrap / config / tools / run / runs / events / error` HTTP 路由、SSE 骨架、`run_id` 冲突与非负游标校验 | 18/18 通过 | 通过 |
| `tests/test_backend_run_stream_phase3.py` | 集成 / simulation-first | 5 | `start_run / get_run / iter_run_events` 状态推送骨架、事件版本过滤、终态快照与终态清理 | 5/5 通过 | 通过 |
| `frontend/src/App.tsx`、`store/workbench.ts`、`components/*`、`lib/api.ts`、`lib/sse.ts` | 构建 / 代码接线评估 | 9 项验收映射 | `FE-A01 ~ FE-A09` 最小联调口径、`npm run build` 门禁、`runs / snapshot / events` 消费路径 | 构建通过；9/9 项均有实现落点 | 通过（仅限代码/构建口径） |
| 全量回归 | 汇总 | 67 | 第三阶段 run 生命周期收口、状态推送骨架与 HTTP 路由不破坏既有主线 | 67/67 通过 | 通过 |

## 本轮最小测试增量

- 扩展 `tests/test_backend_http_phase3.py` 到 18 个测试，新增重复 `run_id` 返回 `409 RunAlreadyExists`、负数 `after_version` 返回 `400 InvalidAfterVersion`、非法 `Last-Event-ID` 返回 `400 InvalidLastEventId`
- 扩展 `tests/test_backend_run_stream_phase3.py` 到 5 个测试，新增终态 session 过期清理与运行中 session 保留，验证 `cleanup()` 只回收满足条件的终态 run
- 补充 SSE 事件载荷断言，确认事件类型、`version` 递增、`terminal` 终态标记、事件回放骨架与非负游标约束成立
- 保留同步 `POST /api/v1/runtime/run` 业务失败保持测试，确认失败态仍返回稳定快照，而不是被 HTTP 层误改写
- 延续 `tests/test_app_phase1.py` 回归，验证 backend contracts、run snapshot、runtime facade 与统一桥接行为未被新增推送骨架破坏
- 新增第三阶段前端最小联调口径文档评估，按 `FE-A01 ~ FE-A09` 核对当前 `React + Zustand + fetch + EventSource` 接线是否齐备，并把结论限定在代码/构建级

## 本轮执行命令与结果

- 命令：`python -m pytest .\tests\test_backend_run_stream_phase3.py .\tests\test_backend_http_phase3.py -q`
- 结果：通过
- 汇总：`23 passed, 1 warning in 0.45s`
- 说明：确认第三阶段新增 run 生命周期收口、HTTP 路由扩展、SSE 事件返回与终态清理策略可独立回归

- 命令：`python -m pytest tests -q`
- 结果：通过
- 汇总：`67 passed, 1 warning in 0.62s`
- 说明：确认第三阶段新增后端层、run registry、生命周期收口与推送骨架没有破坏第一、二阶段既有决策/感知/执行/统一入口基线

- 命令：`npm run build`
- 结果：通过
- 汇总：`tsc -b && vite build` 退出码 `0`，产出 `dist/index.html`、`dist/assets/index-*.css`、`dist/assets/index-*.js`
- 说明：确认第三阶段前端最小工作台工程在当前仓库下可构建，且静态资源产物可生成；该事实只证明构建门禁通过，不等于真实浏览器联调已留痕

## 本轮第三阶段完整规范补强（2026-04-21）

- 类型：focused backend tests + frontend build + live HTTP / 浏览器截图留痕
- 执行命令：`uv run pytest tests/test_backend_phase3.py tests/test_backend_http_phase3.py tests/test_backend_run_stream_phase3.py -q`
- 结果：通过
- 汇总：`16 passed in 1.64s`
- 覆盖范围：
  - `PUT /api/v1/runtime/config` 配置写回对称性
  - `POST /api/v1/runtime/tools/refresh` 工具刷新回归
  - phase3 bootstrap/config 中的助手元数据返回
  - `runs / snapshot / events` 生命周期与终态回放保持稳定
- 执行命令：`npm --prefix "/e/lwj/biyesheji/frontend" run build`
- 结果：通过
- 备注：Node 当前为 `20.18.0`，Vite 7 会提示建议升级到 `20.19+` 或 `22.12+`，但本轮构建仍成功
- live 验证：
  - isolated backend：`http://127.0.0.1:7861`
  - frontend dev server：`http://127.0.0.1:5173`
  - 已验证 `bootstrap / config / tools / runs / snapshot / events` 可用
  - 已验证配置写回后 `decision.provider=openai`、`perception.provider=openai_gpt4o`、`frontend.max_iterations=7`、`frontend.speed_scale=0.7`、`execution.home_pose={x:0.11,y:0.22,z:0.33}` 生效
  - 已验证 `run-e2e-phase3-5` 终态 `completed`，且事件流包含 `snapshot` 事件
- 浏览器 / 截图留痕：
  - `docs/records/phase3_workbench_2026-04-21.png`
  - `docs/records/phase3_workbench_2026-04-21_live.png`
- 本地最小闭环 smoke：
  - 执行命令：`uv run python scripts/phase4_local_e2e_smoke.py`
  - 结果：通过
  - 产物：`docs/records/phase4_local_e2e_smoke_result_2026-04-21.json`
  - 结论：确认 mock-first 前后端本地闭环可重复验收，配置保存、工具刷新、run 终态与事件流回放均可自动探测
- 结论：第三阶段“前端界面开发与 MCP 工具集成”已完成；并已建立第四阶段前置的“本地最小闭环”基线，但该完成边界仍限定在 mock-first backend + 本地联调，不外推为真实硬件、真实视频流或生产级流式服务完成

### 2026-04-24 本地联调入口与 execution flow 可视化修正验证

- 类型：前端构建验证 + 本地 `dev` 联调 + UI 行为诊断
- 执行命令：`npm --prefix frontend run build`
- 结果：通过
- 备注：Node 当前为 `20.18.0`，Vite 7 会提示建议升级到 `20.19+` 或 `22.12+`，但本轮构建仍成功
- 联调事实：
  - 根目录 `npm run dev` 可同时启动 backend 与 frontend
  - Vite 本地地址为 `http://localhost:5173/`
  - backend 已在当前链路下成功响应 `bootstrap / config / tools / runs / snapshot / events`
  - `frontend/src/store/workbench.ts` 已改为先建 SSE 再使用 `snapshot_url` 兜底，避免 run 过快时界面直接跳终态
  - `frontend/src/App.tsx` 中部执行流已按真实 `eventFeed + current_phase` 计算节点 `idle / active / done / failed`，不再依赖 demo 定时轮播
- 结论：当前“任务执行流不动”问题已定位并通过前端接线修正；但这仍属于 mock-first 本地联调事实，不代表真实长时流式服务已验证

## 当前风险与缺口
- 当前 run 状态推送依赖进程内 `RunRegistry + Thread`，未覆盖多进程部署、会话清理、并发竞争与持久化恢复
- 当前已覆盖重复 `run_id`、非法负数 `after_version / Last-Event-ID` 与终态过期清理，但仍未覆盖高频轮询、异常线程退出、一致性抖动与 `max_terminal_sessions` 溢出淘汰
- 当前已完成本地人工 live 联调与截图留痕，但浏览器自动化、长时间运行留痕与端到端 e2e 仍未建立，真实联调阶段仍有回归风险
- 当前前端错误提示依赖后端返回的 `error.message`，尚未形成按 `error.code` 做专门 UI 文案分流的策略
- 当前全量测试全部基于 mock-first 运行时，不代表真实模型、真实相机、真实机械臂与真实时延条件
- 当前环境下 `python -m pytest` 可用；若后续要求统一改回 `uv run ...`，需先恢复 `uv` 命令链可执行性

## 当前结论

- 第三阶段当前测试目标已扩展到前端最小工作台：run 生命周期收口、最小 HTTP / SSE 路由、后端 facade、统一入口装配与既有 mock 闭环全部通过回归，前端工程也已通过构建门禁
- 当前前端最小联调口径结论为：按代码/构建口径 `FE-A01 ~ FE-A09` 具备 9/9 项实现落点；按本地人工联调口径，`bootstrap / config / tools / runs / snapshot / events` 已完成 live 验证，execution flow 也已能随真实事件变化；但浏览器自动化与 Ubuntu / 真实链路验证仍未开始
- 下一阶段测试优先级应聚焦浏览器级 smoke / e2e、长生命周期流式推送方案、异常线程退出、`max_terminal_sessions` 淘汰、并发场景、前后端联调合同与 Ubuntu 实机验证

### 2026-04-20 第三阶段前端最小联调口径代码 / 构建评估

- 类型：前端构建门禁 + 代码接线评估
- 执行命令：`npm run build`
- 结果：通过
- 汇总：`tsc -b && vite build` 成功，Vite 产出 `dist/index.html`、CSS 与 JS 静态资源
- 覆盖范围：
  - 页面初始化：`initialize()` 并行消费 `bootstrap / config / tools`
  - run 提交：`submitRun()` 对接 `POST /api/v1/runtime/runs`
  - snapshot 同步：`syncRunSnapshot()` 消费 `snapshot_url`
  - 事件订阅：`EventSource(events_url)` 消费 `snapshot` 事件并按 `version` 去重
  - 终态收口：`terminal=true` 后关闭订阅并保留最终快照
  - 错误提示：初始化失败、run 创建失败、snapshot 同步失败与事件流错误均有可见提示
- 验收映射：
  - `FE-A01 ~ FE-A04`：通过，已覆盖加载态、初始化失败、run 提交与提交中保护
  - `FE-A05 ~ FE-A07`：通过，已覆盖 running 首帧、终态收口与失败态回显
  - `FE-A08 ~ FE-A09`：通过，已具备请求失败、事件异常与空事件列表的最小兜底展示
- 备注：本轮只证明前端工程构建通过且最小联调代码接线齐备，不代表真实浏览器环境、跨网络部署、自动重连策略或完整端到端闭环已验证

## 已记录测试事实

### 2026-04-20 第三阶段 run 生命周期收口 focused tests

- 类型：代码级集成 / 传输测试
- 执行命令：`python -m pytest .\tests\test_backend_run_stream_phase3.py .\tests\test_backend_http_phase3.py -q`
- 结果：通过
- 汇总：23 个测试全部通过，伴随 1 条第三方依赖 warning
- 覆盖范围：
  - `POST /api/v1/runtime/run`
  - `POST /api/v1/runtime/runs`
  - `GET /api/v1/runtime/runs/{run_id}`
  - `GET /api/v1/runtime/runs/{run_id}/events`
  - 重复 `run_id` 返回 `409 RunAlreadyExists`
  - `after_version` 与 `Last-Event-ID` 的非负游标校验
  - `FrontendRuntimeFacade.start_run / get_run / iter_run_events` 的 running ack、终态快照与事件发布
  - `RunRegistry.cleanup()` 的终态过期清理与运行中 session 保留
  - 空 `instruction`、非法 JSON、未知路由、未知 `run_id` 与内部异常统一错误载荷
- 备注：本轮证明第三阶段新增 run 生命周期收口、最小 HTTP 路由扩展、SSE 回放骨架与终态清理策略可单独回归，但不代表真实浏览器订阅、持续推送保活或生产级流式服务已验证

### 2026-04-20 第三阶段 run 生命周期收口后全量回归

- 类型：代码级全量回归测试
- 执行命令：`python -m pytest tests -q`
- 结果：通过
- 汇总：67 个测试全部通过，伴随 1 条第三方依赖 warning
- 覆盖范围：
  - 决策层：正常结束、循环继续、release / return_home 等 capability/action 选择
  - 感知层：成功 / 失败 envelope、provider 错误边界、配置映射、工厂注入
  - 执行层：`run_smolvla`、原子工具、安全边界、工厂注册与参数校验
  - 统一入口与桥接层：runtime 装配、配置加载、run snapshot、失败闭环、MCP gateway 统一 envelope
  - 后端层：contracts / presenters / service / http / run_registry 最小接口骨架、run 生命周期收口与状态推送骨架
- 备注：当前 67 个测试证明 mock-first 合同、最小 HTTP / SSE 骨架、生命周期边界与既有主线保持稳定，不代表真实模型、真实硬件、真实前端工程或生产级流式服务链路已验证

### 2026-04-20 第三阶段 run 状态推送骨架与 HTTP 路由 focused tests

- 类型：代码级集成 / 传输测试
- 执行命令：`python -m pytest .\tests\test_backend_run_stream_phase3.py .\tests\test_backend_http_phase3.py -q`
- 结果：通过
- 汇总：18 个测试全部通过，伴随 1 条第三方依赖 warning
- 覆盖范围：
  - `POST /api/v1/runtime/run`
  - `POST /api/v1/runtime/runs`
  - `GET /api/v1/runtime/runs/{run_id}`
  - `GET /api/v1/runtime/runs/{run_id}/events`
  - `after_version` 增量事件过滤与 SSE `snapshot` 事件编码
  - `FrontendRuntimeFacade.start_run / get_run / iter_run_events` 的 running ack、终态快照与事件发布
  - 空 `instruction`、非法 JSON、未知路由、未知 `run_id` 与内部异常统一错误载荷
- 备注：本轮证明第三阶段新增 run 状态推送骨架、最小 HTTP 路由扩展与 SSE 回放骨架可单独回归，但不代表真实浏览器订阅、持续推送保活或生产级流式服务已验证

### 2026-04-20 第三阶段 run 状态推送骨架后全量回归

- 类型：代码级全量回归测试
- 执行命令：`python -m pytest tests -q`
- 结果：通过
- 汇总：62 个测试全部通过，伴随 1 条第三方依赖 warning
- 覆盖范围：
  - 决策层：正常结束、循环继续、release / return_home 等 capability/action 选择
  - 感知层：成功 / 失败 envelope、provider 错误边界、配置映射、工厂注入
  - 执行层：`run_smolvla`、原子工具、安全边界、工厂注册与参数校验
  - 统一入口与桥接层：runtime 装配、配置加载、run snapshot、失败闭环、MCP gateway 统一 envelope
  - 后端层：contracts / presenters / service / http / run_registry 最小接口骨架与 run 状态推送骨架
- 备注：当前 62 个测试证明 mock-first 合同、最小 HTTP / SSE 骨架与既有主线保持稳定，不代表真实模型、真实硬件、真实前端工程或生产级流式服务链路已验证

### 2026-04-20 第三阶段最小 HTTP 接口骨架 focused tests

- 类型：代码级集成 / 传输测试
- 执行命令：`python -m pytest tests/test_backend_http_phase3.py -q`
- 结果：通过
- 汇总：10 个测试全部通过，伴随 1 条第三方依赖 warning
- 覆盖范围：
  - `GET /api/v1/runtime/bootstrap`
  - `GET /api/v1/runtime/config`
  - `GET /api/v1/runtime/tools`
  - `POST /api/v1/runtime/run`
  - 空 `instruction`、非法 JSON、未知路由、内部异常统一错误载荷
  - 业务失败态在 HTTP 层保持稳定 `run` 快照
- 备注：本轮证明第三阶段新增最小 HTTP 传输层与 facade 合同可单独回归，但不代表真实前端联调、长连接推送或生产级服务治理已验证

### 2026-04-20 第三阶段最小 HTTP 接口骨架后全量回归

- 类型：代码级全量回归测试
- 执行命令：`python -m pytest tests -q`
- 结果：通过
- 汇总：54 个测试全部通过，伴随 1 条第三方依赖 warning
- 覆盖范围：
  - 决策层：正常结束、循环继续、release / return_home 等 capability/action 选择
  - 感知层：成功 / 失败 envelope、provider 错误边界、配置映射、工厂注入
  - 执行层：`run_smolvla`、原子工具、安全边界、工厂注册与参数校验
  - 统一入口与桥接层：runtime 装配、配置加载、run snapshot、失败闭环、MCP gateway 统一 envelope
  - 后端层：contracts / presenters / service / http 最小接口骨架
- 备注：当前 54 个测试证明 mock-first 合同、最小 HTTP 骨架与既有主线保持稳定，不代表真实模型、真实硬件、真实前端工程或流式服务链路已验证

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
