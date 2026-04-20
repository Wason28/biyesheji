# 交接摘要

## 当前交接状态

- 日期：2026-04-20
- 当前阶段：第三阶段已启动，当前处于“前端消费边界已补强并保持构建通过，第三轮文档再次同步已完成”的状态

## 本轮新增事实

- 仓库已存在 `frontend/` 前端工程，当前基于 `React 19 + TypeScript + Vite + Zustand` 组织第三阶段最小工作台骨架
- `frontend/src/App.tsx` 已组合任务输入、配置展示、运行态快照、事件订阅与工具面板五个区域，当前只消费显式后端展示合同
- `frontend/src/components/config-panel.tsx` 已采用双来源 config 消费：优先展示 `GET /api/v1/runtime/config`，缺省时回退 `bootstrap.config`
- `frontend/src/components/control-panel.tsx` 已在初始化失败时提供“重试初始化”入口，避免首屏失败后只能刷新整页
- `frontend/src/store/workbench.ts` 已在 run 受理后先通过 `snapshot_url` 主动同步一次快照，并在 SSE `onerror` 时再次触发 `snapshot_url` 兜底同步；事件继续按 `version` 去重，并支持手动断开
- `frontend/src/lib/api.ts` 已统一解析 `bootstrap / config / tools / runs / snapshot` 合同，`frontend/src/lib/sse.ts` 继续对接 `events_url`
- `frontend/src/components/runtime-panel.tsx` 已保留视频区占位，当前仅展示 `current_image` 合同，不代表真实视频流已完成
- `frontend/vite.config.ts` 已提供同源 `/api` 代理，默认转发到 `http://127.0.0.1:7860`，也支持通过 `VITE_RUNTIME_BASE_URL` 或 `VITE_PROXY_TARGET` 覆盖
- 本轮前端实现事实以“config 消费补强、`snapshot_url` 兜底同步、初始化重试、构建通过”为准；后端最小合同与测试基线仍保持 `67 passed`
- 本轮只更新文档，不改业务代码；所有同步均以“前端消费边界补强但尚未完成真实浏览器联调”为口径

## 交接提醒

- 下一位接手者先读 `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- 再读 `docs/SESSION_START.md`
- 再读 `docs/records/CURRENT_STATUS.md`
- 若承接前端任务，优先读 `docs/specs/07-frontend-spec.md`、`frontend/src/App.tsx`、`frontend/src/store/workbench.ts`、`frontend/src/components/config-panel.tsx`、`frontend/src/components/control-panel.tsx`、`frontend/src/components/event-panel.tsx`、`frontend/src/lib/api.ts`、`frontend/src/lib/sse.ts`
- 若承接后端联调任务，优先读 `src/embodied_agent/backend/http.py`、`src/embodied_agent/backend/service.py`、`src/embodied_agent/backend/run_registry.py`
- 若追溯历史事实，优先看 `docs/records/DEVELOPMENT_LOG.md` 和 `docs/records/TEST_REPORT.md`

## 推荐下一步

1. QA Agent：按 `docs/specs/07-frontend-spec.md` 的 9 项前端最小验收清单执行首轮浏览器联调，优先覆盖初始化成功/失败重试、run 提交、`snapshot_url` 兜底同步、终态收口和事件断开场景。
2. Frontend Agent：在不突破展示合同边界的前提下补空态、错误态和加载态细节，并为 config fallback、SSE 续连提示与手动同步快照采集截图或录屏证据。
3. Documentation Agent：待浏览器联调产生新事实后，同步回写 `TEST_REPORT.md`、`FIGURE_ASSETS.md`、`THESIS_PROGRESS.md` 与 `CURRENT_STATUS.md`。
4. Backend Agent：保持 `bootstrap / config / tools / runs / events` 合同稳定，只做必要缺陷修正与服务栈评估，不在联调窗口随意改字段语义。
5. Infra Agent：补通 `uv` 命令链与 Ubuntu 前端启动路径，确保 runbook 能覆盖前端开发服务器与后端 HTTP 服务的联合启动。

## 当前风险与待定项

- 当前前端虽已补齐 config 消费、初始化重试与 `snapshot_url` 兜底同步，但仍仅有构建验证，尚无浏览器级联调记录、自动化前端测试或真实交互截图
- 当前视频展示仍为 `current_image` 占位，真实摄像头流、媒体资源管理和实时画面刷新尚未实现
- 当前后端仍是同步 WSGI + 进程内线程骨架；SSE 回放语义已可联调，但不代表生产级长连接能力已经稳定
- `docs/reference/INTERFACES.md` 仍不存在；当前接口口径仍需依赖 `docs/specs/07-frontend-spec.md`、backend tests、frontend 代码与 records 共同维护
- 当前 PowerShell 仍未识别 `uv` 命令，可能影响后续按 runbook 复现实验环境

## Ubuntu / 本地最小接手路径

- 后端测试：`python -m pytest tests -q`
- 后端服务：`python -m embodied_agent.backend.http --host 127.0.0.1 --port 7860`
- 前端依赖安装：`npm install`（目录：`frontend/`）
- 前端开发服务器：`npm run dev`
- 前端构建：`npm run build`
- 如需修改代理目标：设置 `VITE_PROXY_TARGET=http://127.0.0.1:7860`
- 如需直接指定运行时地址：设置 `VITE_RUNTIME_BASE_URL=http://127.0.0.1:7860`
- 当前结论只适用于 mock-first backend + 最小前端骨架链路，不能视为真实前后端闭环、真实模型或真实硬件链路已验证
