# embodied-agent-prototype

桌面级具身智能机器人感知-决策-执行一体化原型系统。

## 当前状态

- 第一阶段骨架实现已完成
- 第二阶段主线收敛已完成
- 第三阶段前端工程骨架已落地，已补齐 config 消费、`snapshot_url` 兜底同步与初始化重试，并保持 `npm run build` 构建通过
- 当前仍是 mock-first、最小联调基线，不代表真实前后端闭环、生产级流式服务或真实硬件链路已完成

## 仓库结构

- `src/embodied_agent/`：Python 后端、决策/感知/执行与统一入口
- `frontend/`：基于 `React 19 + TypeScript + Vite + Zustand` 的前端工作台骨架
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
- `GET /api/v1/runtime/tools`
- `POST /api/v1/runtime/run`
- `POST /api/v1/runtime/runs`
- `GET /api/v1/runtime/runs/{run_id}`
- `GET /api/v1/runtime/runs/{run_id}/events`

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
- 任务输入面板
- 配置展示面板（优先消费 `GET /config`，缺省时回退 `bootstrap.config`）
- 工具刷新面板
- 运行态快照面板（run 受理后可先经 `snapshot_url` 同步一次快照）
- SSE 事件订阅面板（事件流出错时仍会尝试通过 `snapshot_url` 兜底同步）
- 视频流占位区
- 初始化失败重试入口

## 文档入口

- 根需求文档：`# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- 文档导航：`docs/README.md`
- 当前状态：`docs/records/CURRENT_STATUS.md`
- 交接摘要：`docs/records/HANDOFF.md`

## 当前限制

- 当前仍以 mock 感知、mock 执行和最小 WSGI HTTP 骨架为主
- 前端已补齐基础消费与兜底逻辑并可构建，但尚无浏览器级自动化测试与完整联调留痕
- SSE 当前为最小回放骨架，不代表生产级流式推送、断线恢复或持久化能力已经完成
- 真实 `VLM / LLM / SmolVLA / 机械臂`、Ubuntu 实机和端到端实验仍未验证
