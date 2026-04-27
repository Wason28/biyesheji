# 交接摘要

## 当前交接状态

- 日期：2026-04-26
- 当前阶段：第三阶段已完成，当前处于“本地软件级 embodied-agent demo 已完成，进入文档同步 + Ubuntu / 真实链路待验收”的状态

## 本轮新增事实

- `frontend/src/App.tsx` 已收口为面板化工作台，真实消费 `bootstrap / config / tools / runs / snapshot / events`
- `frontend/src/store/workbench.ts` 已稳定编排初始化、配置保存、工具刷新、run 提交、`snapshot_url` 兜底同步、SSE 订阅与断开
- `src/embodied_agent/perception/providers.py` 已支持 `minimax_mcp_vision`、`openai_gpt4o`、`ollama_vision` 真实 provider 装配；未配置时显式回退 mock 并如实暴露 readiness
- `src/embodied_agent/decision/providers.py` 与 `src/embodied_agent/decision/nodes.py` 已支持 `minimax`、`openai`、`ollama` 的真实 LLM 规划接入，并保留 heuristic fallback
- `src/embodied_agent/backend/service.py`、`src/embodied_agent/backend/http.py`、`src/embodied_agent/backend/run_registry.py` 已补齐原子配置热更新、`run_id` 冲突、非法 `after_version / Last-Event-ID`、缺失 run 与终态会话回收的稳定语义
- `frontend/tests/e2e/workbench-smoke.spec.ts` 已覆盖工作台 run smoke、设置弹窗工具刷新/配置保存与空指令本地校验
- 当前工程化验证结果为：focused pytest `51 passed`、`npm --prefix frontend run build` 通过、Playwright e2e `3 passed`
- `docs/records/HARDWARE_INTEGRATION_TODOS.md` 已按 P0/P1/P2 重构硬件与 MCP 扩展待办，补齐 Camera / LeRobot / SmolVLA / Ops 四类工具职责、优先级与推荐实现顺序
- `config/phase4_real_opencv_mcp_bridge.example.yaml` 与 `config/phase4_real_opencv_lerobot_local.example.yaml` 已作为真实链路模板落地
- `scripts/phase4_p0_real_smoke.py` 已作为 phase4 接口级 smoke 脚本落地，并已完成 mock backend 实跑验证
- `docs/specs/12-phase4-real-chain-runbook.md` 已收口真实链路联调说明、启动命令清单与排障顺序

## 交接提醒

- 下一位接手者先读 `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- 再读 `docs/README.md`、`docs/SESSION_START.md`、`docs/records/CURRENT_STATUS.md`
- 若承接后端 / 模型接入任务，优先读 `src/embodied_agent/perception/providers.py`、`src/embodied_agent/decision/providers.py`、`src/embodied_agent/decision/nodes.py`、`src/embodied_agent/backend/service.py`、`src/embodied_agent/backend/http.py`、`src/embodied_agent/backend/run_registry.py`
- 若承接前端工作台任务，优先读 `frontend/src/App.tsx`、`frontend/src/store/workbench.ts`、`frontend/src/components/runtime-panel.tsx`、`frontend/src/components/event-panel.tsx`、`frontend/src/components/control-panel.tsx`、`frontend/src/components/settings-modal.tsx`
- 若承接验证任务，优先读 `tests/test_perception_phase1.py`、`tests/test_decision_phase1.py`、`tests/test_backend_phase3.py`、`tests/test_backend_http_phase3.py`、`tests/test_backend_run_stream_phase3.py`、`frontend/tests/e2e/workbench-smoke.spec.ts`
- 若追溯状态与完成边界，优先看 `README.md`、`docs/records/CURRENT_STATUS.md`、`docs/records/TEST_REPORT.md`、`docs/records/DEVELOPMENT_LOG.md`
- 若承接真实链路联调，优先读 `docs/specs/12-phase4-real-chain-runbook.md`、`config/phase4_real_opencv_mcp_bridge.example.yaml`、`config/phase4_real_opencv_lerobot_local.example.yaml`、`scripts/phase4_p0_real_smoke.py`

## 推荐下一步

1. QA / Validation Agent：把 Ubuntu / 真实链路验证做成独立验收批次，重点验证真实 provider 凭据、配置切换和长时运行稳定性。
2. QA / Validation Agent：按 `docs/specs/12-phase4-real-chain-runbook.md` 至少完成一次 `mcp_bridge` 或 `lerobot_local` 的真实设备 smoke 留痕。
3. Frontend / QA Agent：继续补失败态、断流与恢复读取的 e2e / 手工验收记录，但不要为此重构现有 store 或 contract。
4. Execution / Perception Agent：按 `HARDWARE_INTEGRATION_TODOS.md` 的第一批 P0 先推进 `stream_camera_frame`、`get_robot_telemetry`、`dispatch_lerobot_action` 与 `safety_precheck`。
5. Backend Agent：只评估长连接服务栈、主动取消与持久化演进方案，不提前展开生产级流式重构。
6. Documentation / Thesis Agent：继续同步测试截图、运行记录、论文材料与完成边界表述，避免把“本地软件级 demo”误写成“真实硬件闭环完成”。

## 当前风险与待定项

- 当前仍以 mock execution 为边界，MCP 执行、真实机械臂动作、真实视频流与实体抓取闭环尚未实现
- `src/embodied_agent/backend/http.py` 仍是同步 WSGI + SSE 回放骨架，`RunRegistry` 仍为进程内实现，不代表生产级流式服务已完成
- 前端 e2e 已具备 smoke 基线，但更长链路的失败态、断流恢复与 Ubuntu 实机尚未形成完整留痕
- 本地 Node 仍为 `20.18.0`，低于 Vite 7 推荐下限 `20.19+`，当前不阻塞构建但后续应统一环境
- 本地 PowerShell 仍可能未识别 `uv`；若继续依赖 `uv run ...`，需先确认安装路径与环境变量
- 硬件待办现已明确优先级，但真实设备选型、标定方案和 MCP transport 仍待后续实现阶段确认

## Ubuntu / 本地最小接手路径

- 根目录一键联调：`npm run dev`
- focused pytest：`uv run python -m pytest tests/test_perception_phase1.py tests/test_decision_phase1.py tests/test_backend_phase3.py tests/test_backend_http_phase3.py tests/test_backend_run_stream_phase3.py`
- 后端单独启动：`python -m embodied_agent.backend.http --host 127.0.0.1 --port 7860`
- 前端构建：`npm --prefix frontend run build`
- 前端浏览器回归：`npm --prefix frontend run test:e2e`
- 如需覆盖运行时地址：设置 `EMBODIED_AGENT_HTTP_HOST`、`EMBODIED_AGENT_HTTP_PORT`、`VITE_PROXY_TARGET`、`VITE_RUNTIME_BASE_URL`
- 当前结论仅适用于“本地软件级 demo”口径，不能外推为 MCP 执行、真实视频流、真实机械臂或生产级服务链路已完成
