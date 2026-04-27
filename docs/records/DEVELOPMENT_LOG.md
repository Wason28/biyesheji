# 开发记录

## 记录规则

每条记录至少包含：日期、负责 Agent、对应里程碑、修改模块、修改内容、对应需求点、风险和遗留问题、下一步建议、对应论文章节。

### 2026-04-26

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：phase4 真实链路模板、smoke 与联调 runbook 收口
- 修改模块：`config/config.example.yaml` / `config/phase4_real_opencv_mcp_bridge.example.yaml` / `config/phase4_real_opencv_lerobot_local.example.yaml` / `scripts/phase4_p0_real_smoke.py` / `tests/test_app_phase1.py` / `docs/specs/12-phase4-real-chain-runbook.md` / `docs/README.md` / `README.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/HANDOFF.md` / `docs/records/TEST_REPORT.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：在此前真实链路 P0 配置字段、前端配置面板和运行时 profile 已经落地的基础上，继续把“可执行入口”补齐：一方面新增 `phase4_real_opencv_mcp_bridge.example.yaml` 与 `phase4_real_opencv_lerobot_local.example.yaml` 两份真实链路模板，并把 `config.example.yaml` 扩到最新字段集合；另一方面新增 `scripts/phase4_p0_real_smoke.py`，统一检查 `bootstrap / config / tools / video-stream / runs / events` 是否可用，并把检查结果落盘到 `docs/records/phase4_p0_real_smoke_result_*.json`。随后在 `tests/test_app_phase1.py` 中新增参数化回归，锁住两份 phase4 模板的 YAML 加载与后端类型装配；最后补写 `docs/specs/12-phase4-real-chain-runbook.md`，给出 `opencv + mcp_bridge`、`opencv + lerobot_local` 两条联调路径的环境变量、启动命令、smoke 命令、通过标准与故障排查顺序，并同步更新 README、docs 导航、状态、交接与测试报告，确保这批 phase4 入口不会只存在于代码里而缺少执行说明
- 对应需求点：用户要求继续推进开发，在前后端支持真实链路配置之后，继续向下补齐真实设备联调说明、启动命令清单和可执行的 smoke 验收路径；因此本轮重点不是继续扩接口，而是把现有 phase4 接入骨架变成可启动、可验证、可交接的仓库内标准入口
- 风险和遗留问题：本轮只完成模板、脚本、测试和文档收口；真实摄像头、真实 bridge、真实 `lerobot_local` 依赖以及物理机械臂动作尚未实机验证；验证中使用的 `phase4_p0_real_smoke.py` mock backend 实跑，只能证明脚本与接口合同稳定，不代表真实硬件链路已通过
- 下一步建议：按 `docs/specs/12-phase4-real-chain-runbook.md` 至少完成一次真实设备 smoke，优先选择 `mcp_bridge` 或 `lerobot_local` 中更容易先打通的一条路线，并在完成后把 smoke 结果 JSON、截图和异常记录同步到 `TEST_REPORT.md` 与 `CURRENT_STATUS.md`
- 对应论文章节：系统实现与验证、执行层真实接入设计、工程化与交接规范、实验准备与验收流程

- 负责 Agent：Documentation Maintainer
- 对应里程碑：真实硬件与 MCP 扩展待办清单重构
- 修改模块：`docs/records/HARDWARE_INTEGRATION_TODOS.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/HANDOFF.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：按“优先更新现有待办文档并增加清晰分组”的要求，重写 `HARDWARE_INTEGRATION_TODOS.md`，先基于现有感知工具 `get_image / get_robot_state / describe_scene` 与执行工具 `move_to / move_home / grasp / release / servo_rotate / run_smolvla` 明确当前基线，再把建议后续扩展的 MCP 工具按 `P0 真实链路打通`、`P1 感知与定位增强`、`P1 VLA 执行增强`、`P2 数据闭环与运维能力` 四组重排，并逐项补齐工具职责、模块归属、优先级和推荐实现顺序；同时同步更新 `CURRENT_STATUS.md` 与 `HANDOFF.md`，避免交接时仍沿用旧的“按模块罗列但缺少优先级”的待办口径
- 对应需求点：用户要求把建议后续扩展的 MCP 工具直接写入项目里的 todo 相关 md，优先更新现有待办文档，并明确工具职责与优先级；因此本轮以现有硬件待办文档为主承载面，而不是新建分散文档
- 风险和遗留问题：本轮仅更新文档，不新增代码、测试或真实硬件接线；P0/P1/P2 优先级依据当前系统架构与现有 contract 推导，后续仍需结合真实设备选型、驱动可用性和答辩场景调整；MCP transport、相机型号和 LeRobot 目标设备仍未冻结
- 下一步建议：后续承接真实链路任务时，优先按文档中的第一批 P0 顺序推进 `stream_camera_frame`、`get_robot_telemetry`、`dispatch_lerobot_action` 与 `safety_precheck`，并在首次真实联调完成后补 `TEST_REPORT.md` 与验收记录
- 对应论文章节：系统架构设计、感知层设计、动作执行层设计、工程化与交接规范

### 2026-04-24

- 负责 Agent：Implementation / QA / Documentation Agent
- 对应里程碑：第三阶段本地软件级 embodied-agent demo 收口与最新文档同步
- 修改模块：`src/embodied_agent/perception/providers.py` / `src/embodied_agent/decision/providers.py` / `src/embodied_agent/decision/nodes.py` / `src/embodied_agent/backend/service.py` / `src/embodied_agent/backend/http.py` / `src/embodied_agent/backend/run_registry.py` / `frontend/src/App.tsx` / `frontend/src/components/control-panel.tsx` / `frontend/src/components/event-panel.tsx` / `frontend/src/styles.css` / `frontend/tests/e2e/workbench-smoke.spec.ts` / `tests/test_perception_phase1.py` / `tests/test_decision_phase1.py` / `tests/test_backend_phase3.py` / `tests/test_backend_http_phase3.py` / `tests/test_backend_run_stream_phase3.py` / `README.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/TEST_REPORT.md` / `docs/records/HANDOFF.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：基于“把项目补完整（除 MCP 执行）”的最新完成口径，完成第三阶段本地软件级 demo 收口：确认感知层已接通 `minimax_mcp_vision`、`openai_gpt4o`、`ollama_vision` 的真实 provider 装配，并在未配置时显式回退 mock；确认决策层已补 `minimax`、`openai`、`ollama` 真实 LLM adapter，同时保留 `_split_into_tasks()` 与 `_select_capability_and_action()` heuristic fallback；确认前端工作台已稳定消费 `bootstrap / config / tools / runs / snapshot / events`，并通过 `control-panel.tsx`、`event-panel.tsx`、`styles.css` 与 Playwright smoke 对运行提交流程、设置弹窗、事件日志和空指令校验形成浏览器级回归；确认 `backend/service.py` 已把配置更新改为原子热重载，`backend/http.py` 与 `run_registry.py` 已稳定覆盖 `run_id` 冲突、非法 `after_version / Last-Event-ID`、缺失 run 与终态会话治理；最后统一把 `README.md`、`CURRENT_STATUS.md`、`TEST_REPORT.md`、`HANDOFF.md` 与本文件同步到“本地软件级 embodied-agent demo 已完成”的真实表述，并写明 focused pytest `51 passed`、前端构建通过、Playwright e2e `3 passed`
- 对应需求点：用户明确要求补齐前端工作台、后端运行时、真实模型接入与工程化测试，但显式排除 MCP 执行；因此本轮实现必须在保留现有 contract、保留 mock/heuristic fallback 与不夸大完成边界的前提下，形成可本地运行、可观测、可回归的软件级 demo
- 风险和遗留问题：当前执行层仍保持 mock execution 边界，MCP 执行、真实机械臂动作、真实视频流与实体抓取闭环尚未实现；后端仍为同步 WSGI + 进程内 `RunRegistry` 骨架，不代表生产级流式服务已完成；Ubuntu 实机、真实 provider 凭据与长时运行稳定性仍待独立验收；Node `20.18.0` 仍低于 Vite 7 推荐下限
- 下一步建议：优先把 Ubuntu / 真实链路验证做成独立验收批次，补失败态与断流恢复的浏览器级回归记录，继续评估长连接服务栈与持久化演进方案，并把测试留痕、运行截图与论文材料持续同步到 records
- 对应论文章节：系统架构设计、前端交互设计、前后端接口设计、系统实现与验证、测试设计与结果分析、工程化与交接规范

## 实际记录

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第三阶段前端消费补强后的第三轮文档再次同步
- 修改模块：`frontend/src/store/workbench.ts` / `frontend/src/components/config-panel.tsx` / `frontend/src/components/control-panel.tsx` / `frontend/src/components/event-panel.tsx` / `frontend/src/lib/api.ts` / `docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/SESSION_START.md` / `README.md` / `docs/README.md`
- 修改内容：基于当前仓库前端现状重新核对第三阶段事实；确认 `config-panel.tsx` 已采用“优先读取 GET /config，失败时回退 `bootstrap.config`”的双来源消费方式，`control-panel.tsx` 已在初始化失败时提供“重试初始化”入口，`workbench.ts` 已在 run 受理后先调用 `snapshot_url` 主动同步一次快照，并在 SSE `onerror` 时再次触发 `snapshot_url` 兜底同步；同时保持 `EventPanel` 对 `snapshot_url / events_url` 的显式展示与 `version` 去重语义不变。基于这些新增事实，再次统一 `CURRENT_STATUS`、`DEVELOPMENT_LOG`、`HANDOFF`、`SESSION_START`、`README` 与 `docs/README` 的表述，明确当前状态是“前端消费边界补强并保持构建通过”，而不是“浏览器联调或端到端闭环已完成”
- 对应需求点：第三阶段文档要求在前端消费合同发生收敛时立即回写状态、交接和仓库导航；本轮重点是把 config 消费、`snapshot_url` 兜底同步、初始化重试和构建通过写成稳定事实，避免接手者继续沿用“仅有骨架、缺少兜底”的旧口径
- 风险和遗留问题：本轮只做文档同步，不新增业务代码或测试；当前前端虽已具备更完整的读取与兜底逻辑，但仍无浏览器级联调记录、自动化前端测试和截图证据；后端仍是同步 WSGI + 进程内 `RunRegistry` 骨架，不能据此表述为生产级流式服务
- 下一步建议：优先启动后端与前端开发服务器，按 `docs/specs/07-frontend-spec.md` 记录初始化成功/失败重试、run 提交、`snapshot_url` 同步、终态收口、事件断开与失败回显；一旦产生联调证据，再同步更新 `TEST_REPORT.md`、`FIGURE_ASSETS.md` 与 `THESIS_PROGRESS.md`
- 对应论文章节：前端交互设计、前后端接口设计、系统实现与验证、工程化与交接规范

- 负责 Agent：Documentation Agent
- 对应里程碑：第三阶段前端工程骨架落地后的第三轮文档同步
- 修改模块：`frontend/` 代码现状审查 / `docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/records/MILESTONES.md` / `docs/SESSION_START.md` / `README.md` / `docs/README.md`
- 修改内容：基于当前仓库已存在的 `frontend/` 工程重新核对第三阶段事实；确认前端已采用 `React 19 + TypeScript + Vite + Zustand` 落地工作台骨架，`App.tsx` 已组合任务输入、配置展示、运行态快照、事件订阅和工具面板五块区域，`workbench.ts` 已统一管理 bootstrap 加载、run 提交、SSE 订阅、事件去重与断开，`api.ts`/`sse.ts` 已对接 `bootstrap / tools / runs / events` 合同；执行 `npm run build` 后通过，产出 `dist/`，据此把 records、接手入口和仓库导航统一更新到“前端骨架已落地并构建通过，但仍是最小联调基线”的口径
- 对应需求点：第三阶段主线要求完成前端界面开发与 MCP 工具集成；按第三轮文档要求，在前端工程骨架落地后必须立即同步 `CURRENT_STATUS`、`DEVELOPMENT_LOG`、`HANDOFF`、`MILESTONES`、`SESSION_START`、`README` 与 `docs/README`，并显式区分“构建通过”与“真实浏览器联调完成”
- 风险和遗留问题：当前前端仅完成静态构建验证，尚无浏览器级联调记录、自动化前端测试或截图证据；后端仍为同步 WSGI + 进程内 `RunRegistry` 骨架，不能将当前状态表述为生产级流式服务或完整前后端闭环
- 下一步建议：先启动后端与前端开发服务器，按 `docs/specs/07-frontend-spec.md` 的 9 项最小验收清单补初始化、run 提交、终态收口、失败回显和事件断开场景的联调记录；如产生运行截图或浏览器验证证据，再同步更新 `TEST_REPORT.md`、`FIGURE_ASSETS.md` 与 `THESIS_PROGRESS.md`
- 对应论文章节：前端交互设计、前后端接口设计、系统实现与验证、工程化与交接规范

### 2026-04-20

- 负责 Agent：Thesis Curator
- 对应里程碑：第三阶段前端骨架推进前的论文/素材最小同步审查
- 修改模块：`docs/records/THESIS_PROGRESS.md` / `docs/records/FIGURE_ASSETS.md` / `docs/records/DEVELOPMENT_LOG.md` / 仓库代码与测试证据复核
- 修改内容：基于第三阶段已进入“前端骨架启动与第三轮文档交付准备”的当前状态，复核 `backend/contracts.py`、`backend/service.py`、`backend/http.py` 与 phase-3 backend tests，识别当前真正可同步到论文的最小内容仅包括“前端最小消费合同”“`run_id` 生命周期与 SSE 回放语义”“重复 `run_id` 与非负事件游标错误边界”三类事实；同步更新 `THESIS_PROGRESS.md` 与 `FIGURE_ASSETS.md`，明确哪些图表已具备文字/代码证据可先出图，哪些界面截图仍必须等待前端工程落地后采集
- 对应需求点：第三轮文档要求中，凡是已影响论文事实材料的阶段推进，都必须评估并同步 `THESIS_PROGRESS` 与 `FIGURE_ASSETS`；第三阶段当前主线已切换到前端骨架，因此需要先冻结论文可写边界与素材待采清单，避免把“接口准备完成”误写成“前端实现完成”
- 风险和遗留问题：当前仓库仍无前端工程目录，因而所有界面类素材仍不可采集；当前后端仅为最小 WSGI + 进程内 run registry 骨架，论文中只能将其表述为可联调基线，不能表述为生产级流式服务
- 下一步建议：前端目录创建后，第一时间补采任务输入区、模型配置面板、工具面板、运行态快照区与错误态截图；在此之前，论文仅先写接口合同图、路由图与时序图，不扩写未落地的 UI 细节
- 对应论文章节：系统架构设计、前后端接口设计、系统实现与验证、论文材料组织

- 负责 Agent：Orchestrator
- 对应里程碑：第三阶段下一批优先级重排（前端骨架与第三轮文档优先）
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/specs/07-frontend-spec.md` / `docs/specs/09-documentation-handoff.md` / 仓库现状审查
- 修改内容：基于“最小 HTTP 骨架、run 状态推送、`run_id` 生命周期已完成”的第三阶段现状，重新核对前端规范与文档交接规范，确认下一批不再以后端骨架扩写为先，而是切换为“前端工程骨架启动 + 第三轮文档同步”双 P0；同步把 records 中的优先级栈改写为前端骨架、文档交付、QA 联调清单、服务栈评估和 Ubuntu 命令链验证五个顺位，并明确当前只允许写文档、不改业务代码
- 对应需求点：第三阶段主线目标是完成前端界面开发与 MCP 工具集成；在后端最小合同已具备的前提下，下一批必须优先补前端承接体与交接文档，避免实现顺序继续失衡
- 风险和遗留问题：当前前端目录仍不存在，`docs/reference/INTERFACES.md` 仍缺失，前后端正式联调口径只能临时依赖 `07-frontend-spec.md`、backend tests 和 records；若后续前端落地后不持续补文档，会再次出现代码与交接事实脱节
- 下一步建议：先由 Frontend Agent 交付可消费 `bootstrap / config / tools / run / runs / events` 的工程骨架，再由 Documentation Agent 按 `09-documentation-handoff.md` 做第三轮同步；QA Agent 提前冻结联调验收清单，Backend Agent 仅保留服务栈评估，不抢占前端窗口
- 对应论文章节：前端交互设计、系统架构设计、系统实现与验证、工程化与交接规范

- 负责 Agent：Documentation Agent
- 对应里程碑：第三阶段 run_id 生命周期、终态会话清理与事件游标约束同步
- 修改模块：`src/embodied_agent/backend/run_registry.py` / `src/embodied_agent/backend/service.py` / `src/embodied_agent/backend/http.py` / `tests/test_backend_run_stream_phase3.py` / `tests/test_backend_http_phase3.py` / `docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/records/MILESTONES.md` / `docs/records/TEST_REPORT.md`
- 修改内容：基于最新代码改动重新核对第三阶段后端语义；确认 `FrontendRuntimeFacade.start_run` 已形成“创建 session -> 发布 version=1 的 running ack -> 启动 worker -> 发布终态快照”的最小 `run_id` 生命周期；确认 `RunRegistry.create_session` 会拒绝重复 `run_id`，`cleanup()` 已基于 `retention_seconds` 与 `max_terminal_sessions` 清理过期或超额终态会话，同时保留运行中 session；确认 `backend/http.py` 已对 `after_version` 与 `Last-Event-ID` 施加非负整数约束，并把重复 `run_id` 映射为 `409 RunAlreadyExists`；据此同步更新 records 与测试口径，并补跑 focused tests 为 `23 passed, 1 warning`、全量回归为 `67 passed, 1 warning`
- 对应需求点：第三阶段最小后端合同不仅需要有 `runs / snapshot / events` 路由，还需要把 `run_id` 生命周期、终态会话回收与事件增量游标边界写成稳定可验证事实，避免前后端联调继续基于含糊语义推进
- 风险和遗留问题：当前生命周期治理仍停留在进程内最小骨架；已实现的清理仅覆盖终态会话保留与容量淘汰，不覆盖运行中会话取消、服务重启恢复、多进程共享状态或持久化历史；HTTP 传输仍是同步 WSGI，不代表生产级流式链路已确定
- 下一步建议：以当前 `run_id` 生命周期、终态清理和非负游标约束为基线冻结联调合同，再补异常线程退出观测、主动取消、长连接保活与持久化策略
- 对应论文章节：系统架构设计、前后端接口设计、系统实现与验证、测试设计与结果分析

- 负责 Agent：Documentation Agent
- 对应里程碑：第三阶段 run 状态推送骨架落地同步
- 修改模块：`src/embodied_agent/backend/contracts.py` / `src/embodied_agent/backend/service.py` / `src/embodied_agent/backend/http.py` / `src/embodied_agent/backend/run_registry.py` / `tests/test_backend_http_phase3.py` / `tests/test_backend_run_stream_phase3.py` / `docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/records/MILESTONES.md` / `docs/records/TEST_REPORT.md`
- 修改内容：基于最新代码改动核对第三阶段后端进展；确认 `FrontendRuntimeFacade` 已从同步 `run_instruction` 扩展到 `start_run / get_run / iter_run_events` 三段式运行态接口，新增 `FrontendRunAcceptedPayload` 与 `FrontendRunStatePayload` 合同；确认 `backend/run_registry.py` 已通过进程内 `RunRegistry` 维护 run session、事件版本与终态快照，`backend/http.py` 已新增 `POST /api/v1/runtime/runs`、`GET /api/v1/runtime/runs/{run_id}`、`GET /api/v1/runtime/runs/{run_id}/events`，并支持 `after_version` 与 `Last-Event-ID` 最小过滤；同时确认 `tests/test_backend_http_phase3.py` 已扩展到 15 个测试，新增 `tests/test_backend_run_stream_phase3.py` 3 个测试；本轮补跑 focused tests 为 `18 passed, 1 warning`，全量回归为 `62 passed, 1 warning`
- 对应需求点：第三阶段需要把前端消费合同从“最小 HTTP 读/写骨架”继续推进到“具备 run_id、snapshot 查询与事件回放骨架的可验证后端接口”，为后续前端运行态展示与状态订阅接线提供稳定基线
- 风险和遗留问题：当前 run 状态推送仍依赖 `RunRegistry + Thread + wsgiref` 的进程内骨架，只证明最小事件回放与状态快照链路成立，不证明长连接保活、断线重连、并发治理、会话清理、持久化恢复和生产级服务栈已经确定；此外当前环境仍无法直接使用 `uv`
- 下一步建议：先冻结 `bootstrap / config / tools / run / runs / events / error` 的路径、方法、状态码、字段和错误码，再补重复 `run_id`、非法事件游标、异常线程退出和会话清理测试；前端工程启动后优先消费 `snapshot_url / events_url` 当前合同
- 对应论文章节：系统架构设计、前后端接口设计、系统实现与验证、测试设计与结果分析

- 负责 Agent：Documentation Agent
- 对应里程碑：第三阶段最小 HTTP 接口骨架落地同步
- 修改模块：`src/embodied_agent/backend/http.py` / `src/embodied_agent/backend/service.py` / `tests/test_backend_http_phase3.py` / `docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/records/MILESTONES.md`
- 修改内容：基于最新代码改动核对第三阶段后端进展；确认 `backend/http.py` 已新增基于标准库 `wsgiref` 的最小 WSGI HTTP 传输层，可从 runtime 或配置构建应用并提供 `GET /api/v1/runtime/bootstrap`、`GET /api/v1/runtime/config`、`GET /api/v1/runtime/tools`、`POST /api/v1/runtime/run` 四个最小接口；同时确认 `FrontendRuntimeFacade` 继续负责业务载荷拼装、错误载荷复用与缺省 `run_id` 生成；新增 `tests/test_backend_http_phase3.py` 后，全量测试从 44 个提升到 54 个通过
- 对应需求点：第三阶段需要先把前端消费合同从“进程内 facade”推进到“可验证的最小 HTTP 对外骨架”，并显式冻结读接口、运行接口、标准错误返回与参数校验边界
- 风险和遗留问题：当前 HTTP 层仍是同步 WSGI 骨架，不具备 SSE / WebSocket、运行态推送、持久化和生产级服务治理能力；长期是否继续沿用当前栈或迁移到更适合流式能力的框架仍待决策
- 下一步建议：围绕现有 HTTP 路由继续冻结请求方法、路径、状态码与错误码；随后补 `run` 的流式状态推送方案、前端工程接线与真实服务联调记录
- 对应论文章节：系统架构设计、前后端接口设计、系统实现与验证、测试设计与结果分析

- 负责 Agent：Documentation Agent
- 对应里程碑：第三阶段启动同步（后端接口层骨架已进入进行中）
- 修改模块：`src/embodied_agent/app.py` / `src/embodied_agent/adapters/mcp_gateway.py` / `src/embodied_agent/backend/*` / `src/embodied_agent/shared/types.py` / `src/embodied_agent/shared/__init__.py` / `tests/test_app_phase1.py` / `docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/records/MILESTONES.md`
- 修改内容：基于当前工作树代码改动重新核对第三阶段启动口径；确认已新增独立 `backend` 模块承载 `contracts / presenters / service`，新增 `UnifiedMCPClient` 作为感知层与执行层的统一桥接器，并将 `app.py` 收口为组合根与 CLI 入口；同时确认前端展示相关 TypedDict 已从 `shared/types.py` 移出，避免共享域继续承载第三阶段后端合同；据此将 records 从“第三阶段可启动”更新为“第三阶段已启动，当前处于后端接口层与启动装配收口阶段”；本轮补跑 `python -m pytest tests -q`，结果为 `44 passed`
- 对应需求点：第三阶段启动时必须先明确后端合同归属、统一入口职责边界与前端消费合同，避免继续沿用第二阶段“占位仍在 app/shared 内部”的旧口径
- 风险和遗留问题：当前 `backend/` 仍是进程内 facade，不是 HTTP/SSE/WebSocket 服务；真实后端服务栈尚未选定；本地当前 PowerShell 未识别 `uv` 命令，若后续要求统一使用 `uv run ...`，需要先补环境路径校验
- 下一步建议：以 `backend/service.py` 为起点补真实服务映射层，先冻结 `bootstrap / config / run / error` 最小接口，再推进前端工程骨架、流式状态推送与第三阶段联调测试
- 对应论文章节：系统架构设计、前后端接口设计、系统实现与验证、工程化与交接规范

- 负责 Agent：Orchestrator
- 对应里程碑：第三阶段启动前仓库审查与优先级重排
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / 仓库代码与 specs 审查
- 修改内容：基于 `docs/specs/07-frontend-spec.md`、`08-milestones-data-test.md` 与当前代码现状，对第三阶段目标、缺口与可并行任务进行重新核对；确认当前仓库已具备第三阶段启动前的骨架基线，但仍缺少真实后端接口、前端工程骨架、`SmolVLA` 非 mock backend 与第三阶段联调测试；同步修正 records 中“第三阶段前准备期 / 未开始 / 第二阶段继续推进”三套口径不一致的问题，并把当前优先级栈显式写入 `CURRENT_STATUS.md`
- 对应需求点：阶段切换时必须让 records、spec 与代码事实一致，并明确下一步 owner、优先级与并行策略，避免第三阶段启动时继续沿用第二阶段口径
- 风险和遗留问题：当前仓库仍无真实 HTTP/SSE/WebSocket 服务实现，也无任何前端工程文件；`docs/reference/INTERFACES.md` 当前不存在，第三阶段若新增真实接口，需要以现有 `specs + shared/types + app facade` 作为临时合同基线并继续保持文档同步
- 下一步建议：先由 Backend Agent 落真实接口骨架并冻结最小合同，再由 Frontend Agent 创建 UI 工程接线；Execution / QA / Infra 可围绕 `SmolVLA` MCP 化、联调测试与 Ubuntu 实机验证并行推进
- 对应论文章节：系统架构设计、前端交互设计、系统实现与验证、工程化与交接规范

- 负责 Agent：Documentation Agent
- 对应里程碑：第二阶段当前事实持续同步
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / `docs/records/TEST_REPORT.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/specs/11-ubuntu-runbook.md`
- 修改内容：在第二阶段主线持续推进时继续同步 records；将当前全量测试口径更新到 `44 passed`，并在统一入口 CLI 恢复可运行后恢复 CURRENT_STATUS / HANDOFF / runbook 中关于命令行入口的正向事实描述，同时保留“外部链路未验证”的边界说明
- 对应需求点：第二阶段 records 需要持续反映最新测试基线、主线完成边界与未完成外部项，避免阶段判断和实际状态脱节
- 风险和遗留问题：当前全量测试虽已提升到 44 个通过，但仍主要证明 mock-first 合同、配置装配与占位接口稳定；Ubuntu 实机、前端联动与真实链路仍未验证，若后续不及时补齐，容易把“主线可推进”误读为“端到端已完成” 
- 下一步建议：继续补 phase-2 感知 / 执行 / 前端 facade 回归，并把 Ubuntu 实机验证结果与真实链路接入事实写回 records
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Frontend Agent
- 对应里程碑：第二阶段前端运行占位接口继续收敛
- 修改模块：`src/embodied_agent/app.py` / `src/embodied_agent/shared/types.py` / `src/embodied_agent/shared/__init__.py` / `src/embodied_agent/perception/errors.py` / `src/embodied_agent/perception/server.py` / `tests/test_app_phase1.py` / `docs/specs/07-frontend-spec.md` / `docs/records/*`
- 修改内容：在已有 `bootstrap/config/run/error` 占位基础上，继续收敛成更接近真实后端服务的 facade：新增 `FrontendRuntimeFacade`，补 `runtime_api` / `run_api` / `error` 组织方式，并把执行层展示能力与安全边界纳入 bootstrap；同时修复感知层阻塞当前 facade 回归的 `list_tools` 缺失与 `VLMResponseFormatError` 缺口，完成前端相关回归
- 对应需求点：第二阶段需要先把前端运行接口收口为稳定 facade，降低第三阶段接入真实服务时的返工成本
- 风险和遗留问题：当前 facade 仍是进程内辅助层，不是 HTTP/SSE/WebSocket 服务；不能把已存在的 facade 误写成真实前后端联调完成
- 下一步建议：在保持当前 facade 结构不变的前提下，后续优先把 `runtime_api` 与 `run_api` 映射到真实后端接口层
- 对应论文章节：系统架构设计、前端交互设计、系统实现与验证

### 2026-04-20

- 负责 Agent：Data & Model Agent
- 对应里程碑：第二阶段数据支线前置模板细化
- 修改模块：`docs/records/EXPERIMENTS.md` / `docs/records/FIGURE_ASSETS.md` / `docs/records/THESIS_PROGRESS.md` / `docs/records/HANDOFF.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：在既有“数据采集与微调前置检查”基础上，进一步补齐首条真实轨迹记录字段、样本台账字段、微调准备字段，以及首条轨迹落盘截图和样本台账示例截图等素材占位；保持所有内容仍为模板与待补项，不将真实采集、真实样本统计或微调结果写成已完成
- 对应需求点：第二阶段数据支线需要尽早具备可实填的记录模板，保证真实轨迹一旦开始采集即可被稳定留痕，并支撑论文与答辩材料回溯
- 风险和遗留问题：当前模板虽已可用，但尚无首条真实轨迹实填样本；若后续采集时仍未同步填表，records 与论文材料会继续滞后于真实进展
- 下一步建议：以首条真实轨迹为触发点，立即实填 `EXPERIMENTS.md` 相关字段并登记素材索引，再按样本批次补齐样本规模统计与训练记录
- 对应论文章节：系统实现与验证、实验设计与结果分析、论文材料组织

### 2026-04-20

- 负责 Agent：Implementation Agent
- 对应里程碑：第二阶段主线完成判断与第三阶段准备期切换
- 修改模块：`docs/specs/08-milestones-data-test.md` / `docs/records/MILESTONES.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/HANDOFF.md` / `docs/SESSION_START.md` / `docs/records/THESIS_PROGRESS.md`
- 修改内容：在第二阶段主线持续推进并达到“节点与状态流转能力稳定、合同与回归测试收敛”的边界后，将阶段口径切换到“第二阶段主线完成，进入第三阶段准备期”；同时保留 Ubuntu 实机、前端联动、真实适配链路与数据支线真实结果为并行外部项，不将其误写成端到端已完成
- 对应需求点：阶段完成必须既符合已定义边界，又保持对外表述不越过真实性边界
- 风险和遗留问题：当前 records 里仍保留多组阶段性测试数字（13 / 17 / 21 / 22 / 24 / 37 / 44），后续对外汇总时仍需说明“阶段演进回归数”和“当前全量通过数”的差异
- 下一步建议：以 44 个测试通过、统一入口稳定可运行和前端运行占位 facade 为第三阶段准备基线，继续推进真实前端接口与界面开发
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20
- 对应里程碑：第二阶段前的前端接口占位收敛
- 修改模块：`src/embodied_agent/shared/config.py` / `src/embodied_agent/shared/types.py` / `src/embodied_agent/execution/config.py` / `src/embodied_agent/app.py` / `tests/test_app_phase1.py` / `config/config.example.yaml` / `docs/specs/07-frontend-spec.md` / `docs/records/*`
- 修改内容：在不进入第三阶段完整前端开发的前提下，先沉淀最小前后端合同：补 `llm_local_path`、`vlm_local_path`、`home_pose` 等配置占位；新增前端 `bootstrap/config/run snapshot` 辅助函数与状态字段清单；补测试覆盖配置快照、工具面板占位和失败态错误回传；同步更新 frontend spec 与 records，明确前端不得直接绑定完整决策内部状态
- 对应需求点：前端需承载任务输入、模型配置、状态监控和工具面板；在 phase-2 继续推进时应先稳定调用链路与展示合同，减少后续返工
- 风险和遗留问题：当前仍未提供真实 HTTP/SSE/WebSocket 服务接口；前端合同目前以进程内辅助函数形式存在，后续仍需在后端入口层落成真实对外接口
- 下一步建议：围绕当前 `bootstrap/config/run snapshot` 结构实现真实后端接口，并把前端刷新与运行态推送统一到单一适配层
- 对应论文章节：系统架构设计、决策层 Agent 设计、前端交互设计、系统实现与验证

### 2026-04-20

- 负责 Agent：Implementation Agent
- 对应里程碑：第二阶段感知接口接线恢复与主线继续推进
- 修改模块：`src/embodied_agent/perception/server.py` / `tests/test_perception_phase1.py` / `tests/test_app_phase1.py` / `docs/records/*`
- 修改内容：修复 perception server 在 phase2 接口补强中的初始化接线，恢复 `PerceptionRuntimeConfig + adapter factory + provider factory` 路径；重新跑 perception/app 相关回归并通过，随后全量 `uv run pytest -q` 提升到 24 个通过；同步更新阶段记录与测试口径
- 对应需求点：第二阶段主线推进期间，感知层必须在不破坏最小合同的前提下持续收敛到可替换的接口与配置边界
- 风险和遗留问题：当前 24 个测试仍然主要证明 mock CLI、统一入口与跨层合同稳定，不代表真实 Ubuntu、真实硬件或真实模型链路已验证；Documentation 线需要继续跟进更晚的测试口径
- 下一步建议：继续推进 phase2 感知 / 执行接口补强与回归测试，并同步把最新全量通过数写回 records
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20
- 对应里程碑：第二阶段数据支线前置收敛
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / `docs/records/EXPERIMENTS.md` / `docs/records/FIGURE_ASSETS.md` / `docs/records/THESIS_PROGRESS.md`
- 修改内容：补充 phase-2 数据支线记录口径；明确当前仅完成 `LeRobot` 数据采集与 `SmolVLA` 微调前置梳理，补充数据采集目标、样本台账、素材清单与训练记录待补项，同时明确真实采集链路、样本统计和训练产物尚未形成，不将未验证链路写成已完成事实
- 对应需求点：第二阶段支线需要提前收敛数据采集与模型训练前提，但论文与 records 必须严格区分“已验证事实”和“待启动前置”
- 风险和遗留问题：当前仍无真实 `LeRobot` 采集验证、真实样本规模统计和 `SmolVLA` 训练结果；若后续不及时建立样本台账和实验留痕，第二阶段后半程将难以支撑论文与实验回溯
- 下一步建议：先完成 1 条真实示教轨迹落盘验证与记录模板实填，再逐步扩展到 50-100 组成功轨迹，并在形成真实数据后再启动 `SmolVLA` 微调
- 对应论文章节：系统实现与验证、实验设计与结果分析、论文材料组织

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第二阶段当前事实持续同步
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / `docs/records/TEST_REPORT.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：在第二阶段主线持续推进时继续同步 records；将当前全量测试口径更新到 `38 passed`，并补记统一入口 CLI 当前因 `_build_parser` 缺失而不可运行的事实，避免继续沿用“统一入口已稳定可运行”的旧口径
- 对应需求点：第二阶段 records 需要持续反映最新测试基线、主线完成边界与未完成外部项，避免阶段判断和实际状态脱节
- 风险和遗留问题：当前全量测试虽已提升到 38 个通过，但统一入口 CLI 暂时不可运行；Ubuntu 实机、前端联动与真实链路仍未验证，若不及时修复 CLI 并继续收敛外部项，后续交接会出现“测试通过但入口不可用”的认知偏差
- 下一步建议：优先修复统一入口 CLI，再继续补 phase-2 接口与前端占位回归，并把最新通过数同步到 `TEST_REPORT.md`
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第二阶段启动记录同步
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：将阶段口径从“第二阶段已启动”收敛为“第一阶段完成，准备/开始推进第二阶段主线”；以统一入口可运行、P0 合同三批收敛完成、`uv run pytest -q` 为 37 个通过作为当前 phase-2 推进基线，并沉淀第一阶段遗留项与第二阶段前置外部验证项
- 对应需求点：阶段切换时 records 必须反映当前里程碑、基线事实和剩余前置项，保证后续实现、测试与交接口径一致
- 风险和遗留问题：当前第二阶段推进基线仍以 mock CLI、统一入口和合同回归为主；Ubuntu 实机、前端联动与真实链路尚未验证，后续若不及时补齐，可能影响 phase-2 后半程联调节奏
- 下一步建议：围绕 phase-2 主线实现持续更新当前状态、回归测试和里程碑记录，并把剩余前置项拆分为可追踪的独立事实
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段骨架实现后的阶段记录同步
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/TEST_REPORT.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/records/MILESTONES.md`
- 修改内容：基于最近一轮 P0 合同收敛与测试扩展，同步当前 records 口径；明确 Ubuntu runbook 已落地，测试规模从 10 / 13 / 17 逐步扩展到当前 21 个通过，并补齐 phase-2 启动前仍未完成的前置项说明
- 对应需求点：阶段记录需随实现与测试推进保持一致，确保当前状态、测试事实、里程碑判断和交接内容可回溯
- 风险和遗留问题：records 现已统一到当前 21 个通过，但历史 6 / 7 / 10 / 13 / 17 / 19 / 21 的阶段性测试口径仍并存于记录链路中，后续若对外输出汇总，需要额外说明“阶段演进”与“当前全量”是两种不同统计口径
- 下一步建议：继续把 Ubuntu 实机验证、前端联动与真实适配前置项按 phase-2 启动门槛拆分记录
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段骨架实现后的 Ubuntu 运行说明落地
- 修改模块：`docs/specs/11-ubuntu-runbook.md` / `docs/records/TEST_REPORT.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/README.md` / `docs/specs/09-documentation-handoff.md`
- 修改内容：新增 Ubuntu 运行与验证说明，收敛项目级安装基线、配置入口、统一启动入口命令与当前已验证的 mock CLI 链路；同步记录 `uv run pytest -q`、统一入口运行、最终状态导出与工具列表检查事实，并在后续代码与测试扩展后继续同步修正 records 口径至当前 19 个测试、8 个统一入口工具、frontend 回退与失败闭环验证事实
- 对应需求点：项目需面向 `Ubuntu` 部署目标保持可运行、可验证、可交接；文档需与当前实现和验证事实保持一致
- 风险和遗留问题：当前 runbook 与验证事实只覆盖 mock CLI 级链路，不代表 Ubuntu 实机安装、前端联动、真实 `LeRobot`、真实 `SmolVLA` 权重或真实硬件链路已验证
- 下一步建议：继续补 Ubuntu 实机安装、`--config` 配置路径、更多 release / 放置场景、失败路径以及前后端联调验证
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范


### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`src/embodied_agent/shared`
- 修改内容：建立共享配置与类型基础设施，新增 `shared/config.py` 与 `shared/types.py`，用于承载 decision、perception、execution、frontend 四类配置以及跨层共享数据结构
- 对应需求点：统一配置管理、模块解耦、后续真实模型与硬件接入的公共基础
- 风险和遗留问题：当前配置加载与默认值已经形成，但尚未补齐生产级配置校验、环境变量接入和多环境切换
- 下一步建议：在统一启动入口与接口层接入 `AppConfig`，避免各子模块自行读取配置
- 对应论文章节：系统总体架构设计、系统配置与运行时设计

### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`src/embodied_agent/decision`
- 修改内容：建立决策层第一阶段骨架，补齐状态定义、节点函数、最小 MCP Client 与 LangGraph 主图，形成 `task_planner -> scene_analyzer -> action_decider -> executor -> verifier` 固定流程
- 对应需求点：决策层 Agent 主流程、任务拆解、状态流转、执行结果验证
- 风险和遗留问题：当前节点逻辑以 mock 流转为主，尚未接入真实大模型推理与复杂任务规划策略
- 下一步建议：补统一入口、结构化日志和更细粒度状态观测字段，为第二阶段扩展做准备
- 对应论文章节：决策层 Agent 设计、工作流编排设计

### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`src/embodied_agent/perception`
- 修改内容：建立感知层 mock 能力，新增相机与机器人状态 mock、感知契约、错误类型、provider 封装与 MCP Server，对外提供可调用的 mock 感知工具
- 对应需求点：场景感知输入、图像获取、结构化观察结果输出、错误恢复基础
- 风险和遗留问题：当前感知结果为固定 mock 输出，未接入真实图像流与 VLM 推理链路
- 下一步建议：在接口不变前提下，引入真实图像输入和 provider 适配层抽象
- 对应论文章节：感知层设计、感知结果结构化表示

### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`src/embodied_agent/execution`
- 修改内容：建立执行层 mock 运行时，补齐安全配置、参数校验、急停保护、LeRobot mock 适配器、Mock MCP Server 与 `run_smolvla` 工具编排
- 对应需求点：执行层原子动作、VLA 推理入口、安全约束、错误回传
- 风险和遗留问题：当前执行成功只验证 mock 计划执行与安全链路，不代表真实机械臂动作可用
- 下一步建议：在保持工具签名稳定的前提下替换底层 mock 适配器，并补充更完整的异常场景测试
- 对应论文章节：执行层设计、安全机制设计、VLA 调用链路设计

### 2026-04-20

- 负责 Agent：Orchestrator / Decision / QA / Documentation / Thesis Agent Team
- 对应里程碑：第一阶段骨架实现后的统一入口与最小集成验证
- 修改模块：`src/embodied_agent/app.py` / `tests/test_app_phase1.py` / `docs/`
- 修改内容：新增统一启动入口 `src/embodied_agent/app.py`，以薄装配层形式完成 `config loading -> mock MCP service wiring -> decision execution`；通过 `PerceptionMCPServer`、`MockMCPServer` 与 `MinimalMCPClient(auto_mock=False)` 适配现有决策图；新增 `tests/test_app_phase1.py` 验证统一入口装配后的单任务 mock 闭环；执行 `uv run pytest -q` 与 `uv run python -m embodied_agent.app --instruction "抓取桌面方块"` 均通过；同步更新运行说明、状态记录和文档口径
- 对应需求点：系统应具备最小可运行的三层闭环装配入口、跨层调用验证事实和可交接的运行方式
- 风险和遗留问题：当前统一入口仍基于 in-process mock MCP facade，不代表真实 MCP 传输、前端联动、Ubuntu 部署或真实硬件链路已验证；`uv.lock` 是否纳入版本管理仍未决策
- 下一步建议：补失败路径与多任务路径的跨层集成测试，继续完善 Ubuntu 运行文档，并为真实模型/硬件替换保持接口稳定
- 对应论文章节：系统架构设计、决策层 Agent 设计、系统实现与验证

### 2026-04-20

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现后的环境验证与文档对齐
- 修改模块：本地运行环境 / `tests/` / `docs/`
- 修改内容：修复本地 `python` / `python3` 命令指向错误的问题，建立可用的 `Python 3.12.12` 本地入口；创建 `.venv` 并使用 `uv` 安装项目依赖；执行 `uv run pytest -q`，结果 6 个测试全部通过；同步修正 `README.md`、`docs/reference/`、`docs/specs/`、`docs/records/` 中与当前实现不一致的状态与接口描述，并补充“工作完成后的文档维护要求”
- 对应需求点：项目应具备可验证的第一阶段骨架基线、文档与实现一致性、可交接与可复现性
- 风险和遗留问题：当前测试仍以 mock 单元测试为主，尚未覆盖统一启动入口、跨层集成、前端联动与真实硬件场景；仓库当前新增 `uv.lock`，是否纳入版本管理尚未决策
- 下一步建议：优先建立统一启动入口，串起配置加载、决策图执行和 mock MCP 服务，并补跨层集成测试
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Documentation / Thesis Agent
- 对应里程碑：第一阶段完成后的文档体系重构
- 修改模块：`README.md` / `DEVELOPMENT_SPEC.md` / `docs/specs/` / `docs/records/`
- 修改内容：以根需求文档为唯一权威来源重构 `docs/`；保留 `docs/specs/` 作为实现规范层，删除重复的 `docs/reference/`，并重写导航、状态、交接、里程碑、论文与实验材料相关文档，确保论文材料与项目记录口径对齐
- 对应需求点：文档体系应可交接、可回溯，并与需求文档和当前实现保持一致
- 风险和遗留问题：`docs/records/TEST_REPORT.md`、`docs/records/MILESTONES.md`、`docs/records/HANDOFF.md` 仍保留 `6 个测试` 与 `7 个测试` 的历史口径差异，后续需要在核实后统一说明；`.claude/` 与 `uv.lock` 是否纳入版本管理仍未决策
- 下一步建议：核实测试总数口径后补充勘误说明，并继续保持 `specs`、`records` 与后续实现同步更新
- 对应论文章节：系统架构设计、系统实现与验证、论文材料组织与答辩准备

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段骨架实现后的 Ubuntu 运行文档补齐
- 修改模块：`docs/specs/11-ubuntu-runbook.md` / `docs/records/TEST_REPORT.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/HANDOFF.md` / `docs/README.md` / `DEVELOPMENT_SPEC.md` / `docs/specs/09-documentation-handoff.md`
- 修改内容：新增 Ubuntu 下 mock CLI 最小运行规范文档，并同步补齐测试报告、当前状态、交接入口和文档索引；明确当前只覆盖已验证的 mock CLI 命令面，不把前端联动、真实 LeRobot、真实机械臂、真实 SmolVLA 权重和真实实验写成已验证事实
- 对应需求点：目标部署环境为 Ubuntu；系统应具备可交接、可回溯、可验证的运行路径与文档基线
- 风险和遗留问题：当前仍无 Ubuntu 实机安装验证事实；前端联动、真实 MCP、真实硬件和真实实验链路仍未覆盖；records 中历史 6/7/18 测试口径差异仍待后续在需要时统一勘误说明
- 下一步建议：按 `docs/specs/11-ubuntu-runbook.md` 在 Ubuntu 环境执行最小 CLI 验证，并将结果、截图和失败项写回 `docs/records/TEST_REPORT.md`、`docs/records/FIGURE_ASSETS.md`
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现后的 P0 合同收敛与 focused tests 回归
- 修改模块：`src/embodied_agent/shared/types.py` / `src/embodied_agent/decision/*` / `src/embodied_agent/perception/*` / `src/embodied_agent/execution/*` / `tests/*` / `docs/records/*`
- 修改内容：继续完成第二阶段前的 P0 工作，补 capability contract 雏形、统一原子执行工具暴露、统一 `RobotState/ee_pose` 结构、统一 perception / execution envelope，并补统一入口的多任务、配置路径、未知工具失败、执行失败闭环、感知失败闭环，以及 perception focused tests；继续补 perception provider 工厂注册与 execution runtime 工厂注入测试；执行 focused tests 后为 17 个通过，随后全量 `uv run pytest -q` 为 21 个通过
- 对应需求点：第二阶段前需先固化接口定义、补足跨层集成入口与验证事实，确保 mock 到真实适配前的合同稳定
- 风险和遗留问题：当前仍未完成 Ubuntu 实机安装验证；真实 provider / adapter 虽开始支持可替换装配，但真实 LeRobot、真实 SmolVLA、真实 VLM/LLM 仍未接入；records 中历史 6/7 测试口径差异仍待后续勘误说明
- 下一步建议：继续补 `--config` 失败路径与更多 perception/execution 合同回归测试，并把 Ubuntu 实机验证结果写回 records
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`tests/`
- 修改内容：新增 6 个 pytest 测试，分别验证决策层单任务/多任务循环、感知层成功/失败路径、执行层 `run_smolvla` 成功路径与 `move_to` 校验失败急停路径；执行 `python -m pytest tests -q` 结果通过
- 对应需求点：第一阶段最小可验证闭环、接口稳定性、失败链路保护
- 风险和遗留问题：当前测试仍以单元测试为主，尚未覆盖跨层集成、前端联动与真实硬件场景
- 下一步建议：以现有 6 个测试为基线继续补充集成测试和接口契约测试
- 对应论文章节：系统实现与验证、测试设计与结果分析

### 2026-04-19

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段启动前准备
- 修改模块：文档体系 / spec 结构 / 交接路径
- 修改内容：将原单文件 spec 拆分为 `docs/specs/` 多文件规范，并建立主索引 `DEVELOPMENT_SPEC.md`
- 对应需求点：系统架构、模块职责、里程碑、论文映射、交接规范
- 风险和遗留问题：文档已完善，但代码尚未开始实现
- 下一步建议：开始搭建 LangGraph + MCP 骨架代码
- 对应论文章节：系统架构设计、决策层 Agent 设计

### 2026-04-19

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段启动前准备
- 修改模块：docs 目录结构
- 修改内容：将 `docs/` 重构为 `specs/`、`reference/`、`records/` 三层，并修正全部路径引用
- 对应需求点：交接规范、文档维护、论文材料管理
- 风险和遗留问题：如果后续代码目录变化较大，需要同步调整参考文档中的路径和入口说明
- 下一步建议：补齐首版参考文档和记录文档，避免新 Agent 接手时依旧面对空模板
- 对应论文章节：系统架构设计、系统实现与验证

### 2026-04-19

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段启动前准备
- 修改模块：reference / records 文档实填
- 修改内容：将架构、接口、Git、论文大纲写成稳定参考；将状态、里程碑、测试、实验、交接写成首版可接手内容
- 对应需求点：全生命周期开发记录、测试验证、论文写作并行推进
- 风险和遗留问题：当前记录基于文档建设成果，尚无代码与实验事实支撑
- 下一步建议：代码启动后第一时间把真实实现与运行结果写回 records 文档
- 对应论文章节：系统实现与验证、总结与展望
