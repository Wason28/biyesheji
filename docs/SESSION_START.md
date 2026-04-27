# 新会话接手入口

## 1. 先看什么

新会话接手时，先读：
1. `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
2. `docs/SESSION_START.md`
3. `docs/records/CURRENT_STATUS.md`
4. 与当前任务对应的 `docs/specs/`

如果需要追溯历史事实，再读：
- `docs/records/DEVELOPMENT_LOG.md`
- `docs/records/TEST_REPORT.md`
- `docs/records/HANDOFF.md`

## 2. 当前项目一句话状态

当前项目已完成第一阶段骨架实现与第二阶段主线收敛；第三阶段前端已完成 prototype 风格工作台重构、根目录 `npm run dev` 一键联调、真实 execution flow 可视化修正与本地 live 验证，当前重点转为 Ubuntu / 真实链路扩展与自动化留痕。

## 3. 默认接手动作

如果没有额外指令，默认顺序是：
1. 先确认当前任务属于前端、后端、文档、测试还是论文支线
2. 先读对应 `docs/specs/`
3. 若是前端任务，优先看 `frontend/src/App.tsx`、`frontend/src/store/workbench.ts`、`frontend/src/components/config-panel.tsx`、`frontend/src/components/control-panel.tsx`、`frontend/src/components/event-panel.tsx`、`frontend/src/lib/api.ts`、`frontend/src/lib/sse.ts`、`frontend/vite.config.ts`
4. 若是后端联调任务，优先看 `src/embodied_agent/backend/http.py`、`service.py`、`run_registry.py`、`package.json`、`scripts/dev.js`
5. 若是 phase4 真实链路任务，优先看 `docs/specs/12-phase4-real-chain-runbook.md`、`config/phase4_real_opencv_mcp_bridge.example.yaml`、`config/phase4_real_opencv_lerobot_local.example.yaml`、`scripts/phase4_p0_real_smoke.py`
6. 开工前确认本轮要更新哪些 `docs/records/`
7. 完成后补状态、记录和交接
