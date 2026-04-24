# embodied-agent-prototype

桌面级具身智能机器人感知-决策-执行一体化原型系统。

## 当前状态

- 第一阶段骨架实现已完成
- 第二阶段主线收敛已完成
- 第三阶段前端工作台、后端运行时、真实模型接入与工程化测试已补齐到“本地软件级 demo”口径
- 前端工作台已收口为真实 runtime 面板：`bootstrap / config / tools / runs / snapshot / events` 全链路接线，运行状态、阶段总览、事件日志、设置弹层与错误提示均可回归
- 感知层已支持 `minimax_mcp_vision`、`openai_gpt4o`、`ollama_vision` 的真实 provider 装配；决策层已支持 `minimax`、`openai`、`ollama` 的真实 LLM 规划接入，并保留 heuristic fallback
- 后端运行时已补齐 `HTTP + SSE + in-memory RunRegistry` 基线、原子配置热更新、`run_id` 冲突与事件游标错误收敛
- 根目录已支持 `npm run dev` 一键启动前后端，本地浏览器 live 联调、前端 Playwright smoke 与后端 focused pytest 已验证最小闭环
- 当前完成边界仍限定为“本地软件级 demo”，不代表 MCP 执行、真实硬件抓取、真实视频流或生产级流式服务已完成

## 仓库结构

- `src/embodied_agent/`：Python 后端、决策/感知/执行与统一入口
- `frontend/`：基于 `React 19 + TypeScript + Vite + Tailwind CSS v4 + Zustand + lucide-react` 的前端工作台
- `docs/`：实现规范、状态记录、交接与论文材料导航
- `config/`：示例配置
- `tests/`：当前 pytest 测试集

## 后端快速开始

```bash
python -m pytest tests -q
python -m embodied_agent.backend.http --host 127.0.0.1 --port 7860
```

可选 CLI 验证：

```bash
python -m embodied_agent.app --instruction "抓取桌面方块"
python -m embodied_agent.app --instruction "抓取桌面方块" --dump-final-state
python -m embodied_agent.app --instruction "抓取桌面方块" --list-tools
```

当前最小后端接口包括：
- `GET /api/v1/runtime/bootstrap`
- `GET /api/v1/runtime/config`
- `PUT /api/v1/runtime/config`
- `GET /api/v1/runtime/tools`
- `POST /api/v1/runtime/tools/refresh`
- `POST /api/v1/runtime/run`
- `POST /api/v1/runtime/runs`
- `GET /api/v1/runtime/runs/{run_id}`
- `GET /api/v1/runtime/runs/{run_id}/events`

## 前后端联调启动

根目录可直接执行：

```bash
npm run dev
```

它会同时启动：
- 后端运行时：`python -m embodied_agent.backend.http`
- 前端开发服务器：`npm --prefix frontend run dev`

共享环境变量：

```bash
EMBODIED_AGENT_HTTP_HOST=127.0.0.1
EMBODIED_AGENT_HTTP_PORT=7860
VITE_PROXY_TARGET=http://127.0.0.1:7860
VITE_RUNTIME_BASE_URL=http://127.0.0.1:7860
```

后端已支持开发期直接跨域访问与 SSE；如果未显式设置 `EMBODIED_AGENT_ALLOWED_ORIGIN`，将回显请求的浏览器 Origin。

## 前端快速开始

在 `frontend/` 目录执行：

```bash
npm install
npm run dev
npm run build
```

默认开发服务器端口为 `5173`，默认把同源 `/api` 请求代理到 `http://127.0.0.1:7860`。如需覆盖：

```bash
VITE_PROXY_TARGET=http://127.0.0.1:7860
VITE_RUNTIME_BASE_URL=http://127.0.0.1:7860
```

前端当前已落地：
- 面板化工作台主界面：运行状态、阶段总览、实时画面/遥测、事件日志、控制中心与设置弹层
- 任务输入面板：支持自然语言指令、可选 `run_id`、本地空指令校验与错误码回显
- 配置面板：优先消费 `GET /config`，支持保存、回滚、模型助手提示与原子配置热更新
- 工具面板：支持运行时刷新与结构展示
- 运行态快照面板：展示 `plan`、`last_node_result`、`execution_feedback`、`final_report` 等诊断字段
- SSE 事件订阅面板：支持 `snapshot / phase_started / phase_completed / phase_failed / human_intervention_required / run_completed`，事件流出错时仍会尝试通过 `snapshot_url` 兜底同步
- 图像/遥测区：承接 `current_image`、`robot_state`、`scene_observations` 与当前能力/动作
- 初始化失败重试入口与手动断开订阅入口

## 文档入口

- 根需求文档：`# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- 文档导航：`docs/README.md`
- 当前状态：`docs/records/CURRENT_STATUS.md`
- 交接摘要：`docs/records/HANDOFF.md`

## 验证命令

```bash
uv run python -m pytest tests/test_perception_phase1.py tests/test_decision_phase1.py tests/test_backend_phase3.py tests/test_backend_http_phase3.py tests/test_backend_run_stream_phase3.py
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

当前已知结果：
- focused pytest：`51 passed`
- Playwright e2e：`3 passed`
- 前端构建：通过（当前 Node `20.18.0` 低于 Vite 7 推荐下限，但不阻塞构建）

## 当前限制

- 当前仍以 mock 执行为主；MCP 执行、真实机械臂动作与实体抓取闭环不在本轮完成范围内
- SSE 当前为最小回放骨架，不代表生产级流式推送、断线恢复、跨进程会话治理或持久化能力已经完成
- 感知层与决策层虽已接通真实 provider / model adapter，但仍以本地软件级验证为主，未完成 Ubuntu 实机、真实视频流与真实硬件链路验收
- 当前完成口径不外推为真实 `SmolVLA` 权重验证、生产部署或端到端实体实验完成
