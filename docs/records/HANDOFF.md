# 交接摘要

## 当前交接状态

- 日期：2026-04-21
- 当前阶段：第三阶段已完成，当前处于“完整规范功能、后端配置写回与工具刷新、浏览器联调截图与 live 验证事实已补齐”的状态

## 本轮新增事实

- `frontend/src/components/config-panel.tsx` 已升级为完整配置工作区，支持 `decision / perception / execution / frontend` 四分区编辑、提交、回滚、模型部署助手与系统载入助手提示
- `frontend/src/components/runtime-panel.tsx` 已由文本占位升级为 `current_image` 图像承接展示，并保留运行日志、场景观测与动作结果视图
- `frontend/src/store/workbench.ts` 已新增配置草稿、配置提交、工具刷新结果提示与对应错误反馈状态
- `frontend/src/lib/api.ts` 已补 `PUT /api/v1/runtime/config` 与 `POST /api/v1/runtime/tools/refresh` 请求封装
- `src/embodied_agent/backend/presenters.py` 与 `src/embodied_agent/backend/service.py` 已完成 phase3 配置合同对称化与助手元数据补充；`PUT /config` 和 `POST /tools/refresh` 已可用
- `tests/test_backend_phase3.py` 已扩展覆盖配置写回对称性与助手元数据返回
- 已执行 `uv run pytest tests/test_backend_phase3.py tests/test_backend_http_phase3.py tests/test_backend_run_stream_phase3.py -q`，结果 `16 passed`
- 已执行 `npm --prefix "/e/lwj/biyesheji/frontend" run build`，结果通过；Node 版本仍提示低于 Vite 推荐下限，但不影响当前构建通过
- 已完成浏览器联调截图与 headless 留档：`docs/records/phase3_workbench_2026-04-21.png`、`docs/records/phase3_workbench_2026-04-21_live.png`
- 本地最小闭环基线已补齐：`scripts/phase4_local_e2e_smoke.py` 可重复验证 `bootstrap / config / tools / runs / snapshot / events` 全链路，并输出结果到 `docs/records/phase4_local_e2e_smoke_result_2026-04-21.json`

## 交接提醒

- 下一位接手者先读 `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- 再读 `docs/SESSION_START.md`
- 再读 `docs/records/CURRENT_STATUS.md`
- 若承接前端任务，优先读 `docs/specs/07-frontend-spec.md`、`frontend/src/App.tsx`、`frontend/src/store/workbench.ts`、`frontend/src/components/config-panel.tsx`、`frontend/src/components/control-panel.tsx`、`frontend/src/components/event-panel.tsx`、`frontend/src/lib/api.ts`、`frontend/src/lib/sse.ts`
- 若承接后端联调任务，优先读 `src/embodied_agent/backend/http.py`、`src/embodied_agent/backend/service.py`、`src/embodied_agent/backend/run_registry.py`
- 若追溯历史事实，优先看 `docs/records/DEVELOPMENT_LOG.md` 和 `docs/records/TEST_REPORT.md`

## 推荐下一步

1. Phase4 Agent：转入第四阶段端到端闭环调试，优先规划 Ubuntu 实机、真实后端长生命周期流式方案与真实链路验证。
2. Documentation Agent：把本轮第三阶段完成事实、截图索引和 focused tests 结果同步进论文正文与答辩素材。
3. QA Agent：后续补前端自动化测试、异常线程退出、长连接保活与并发场景验证。
4. Infra Agent：补通 PowerShell 下 `uv` 命令链与 Ubuntu 启动 runbook，减少后续联调环境差异。

## 当前风险与待定项

- 第三阶段前端规范功能已完成，但当前仍仅适用于 mock-first backend + 最小/增强型前端链路，不代表真实 VLM / LLM / SmolVLA / 机械臂链路已验证
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
