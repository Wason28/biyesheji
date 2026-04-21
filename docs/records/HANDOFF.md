# 交接摘要

## 当前交接状态

- 日期：2026-04-21
- 当前阶段：第三阶段已启动，当前处于“前端消费边界继续补强，未提交改动已推进到 `run_id` / 错误展示，但后端新增配置写回草稿尚未收口”的状态

## 本轮新增事实

- 仓库已存在 `frontend/` 前端工程，当前基于 `React 19 + TypeScript + Vite + Zustand` 组织第三阶段最小工作台骨架
- `frontend/src/App.tsx` 已组合任务输入、配置展示、运行态快照、事件订阅与工具面板五个区域，当前只消费显式后端展示合同
- `frontend/src/components/config-panel.tsx` 已采用双来源 config 消费：优先展示 `GET /api/v1/runtime/config`，缺省时回退 `bootstrap.config`
- `frontend/src/components/control-panel.tsx` 已在初始化失败时提供“重试初始化”入口，并新增可选 `run_id` 输入与错误码回显
- `frontend/src/store/workbench.ts` 已在 run 受理后先通过 `snapshot_url` 主动同步一次快照，并在 SSE `onerror` 时再次触发 `snapshot_url` 兜底同步；事件继续按 `version` 去重，并支持手动断开；当前开始区分错误码
- `frontend/src/components/event-panel.tsx` 已显式补出事件流错误提示，便于联调时区分“续连中”与“当前不可用”
- `frontend/src/lib/api.ts` 已统一解析 `bootstrap / config / tools / runs / snapshot` 合同，`frontend/src/lib/sse.ts` 继续对接 `events_url`
- `frontend/src/components/runtime-panel.tsx` 已保留视频区占位，当前仅展示 `current_image` 合同，不代表真实视频流已完成
- `frontend/vite.config.ts` 已提供同源 `/api` 代理，默认转发到 `http://127.0.0.1:7860`，也支持通过 `VITE_RUNTIME_BASE_URL` 或 `VITE_PROXY_TARGET` 覆盖
- 当前未提交改动里已出现后端 `PUT /api/v1/runtime/config` 与 `POST /api/v1/runtime/tools/refresh` 的接口草稿，并新增 `tests/test_backend_phase3.py` 作为 phase3 草稿测试补充
- 当前后端新增草稿尚未收口：前端仍未消费这两项接口，配置写回字段名与展示字段名未完全对齐
- 历史基线仍以“67 个 pytest 通过、前端构建通过”为准；但本轮未提交改动尚未在当前环境重新复验，本地 `python -m pytest` 当前因缺少 `pytest` 模块无法直接执行

## 交接提醒

- 下一位接手者先读 `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- 再读 `docs/SESSION_START.md`
- 再读 `docs/records/CURRENT_STATUS.md`
- 若承接前端任务，优先读 `docs/specs/07-frontend-spec.md`、`frontend/src/App.tsx`、`frontend/src/store/workbench.ts`、`frontend/src/components/config-panel.tsx`、`frontend/src/components/control-panel.tsx`、`frontend/src/components/event-panel.tsx`、`frontend/src/lib/api.ts`、`frontend/src/lib/sse.ts`
- 若承接后端联调任务，优先读 `src/embodied_agent/backend/http.py`、`src/embodied_agent/backend/service.py`、`src/embodied_agent/backend/run_registry.py`
- 若追溯历史事实，优先看 `docs/records/DEVELOPMENT_LOG.md` 和 `docs/records/TEST_REPORT.md`

## 推荐下一步

1. QA Agent：按 `docs/specs/07-frontend-spec.md` 的 9 项前端最小验收清单执行首轮浏览器联调，优先覆盖初始化成功/失败重试、run 提交、`snapshot_url` 兜底同步、终态收口和事件断开场景。
2. Backend Agent：先修平 `PUT /config` 草稿字段对齐问题，再决定是否继续保留配置写回能力。
3. Frontend Agent：在不突破展示合同边界的前提下补空态、错误态和加载态细节，并判断是否要真正消费 `POST /tools/refresh` / `PUT /config`；若暂不消费，应避免文档误写成已闭环。
4. Documentation Agent：待浏览器联调或后端收口产生新事实后，同步回写 `TEST_REPORT.md`、`FIGURE_ASSETS.md`、`THESIS_PROGRESS.md` 与 `CURRENT_STATUS.md`。
5. Infra Agent：补通 `uv` 命令链与 Ubuntu 前端启动路径，确保 runbook 能覆盖前端开发服务器与后端 HTTP 服务的联合启动。

## 当前风险与待定项

- 当前前端虽已补齐 config 消费、初始化重试、`snapshot_url` 兜底同步、可选 `run_id` 与错误态展示，但仍仅有构建验证，尚无浏览器级联调记录、自动化前端测试或真实交互截图
- 当前后端仍是同步 WSGI + 进程内线程骨架；SSE 回放语义已可联调，但不代表生产级长连接能力已经稳定
- 当前未提交后端草稿仍未收口：`PUT /config` 与 `POST /tools/refresh` 尚未形成前端消费闭环，且配置写回字段合同仍需进一步整理
- `tests/test_backend_phase3.py` 当前为新增草稿测试，与既有 phase3 HTTP / run stream 测试的职责边界仍需后续整理
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
