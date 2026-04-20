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

当前项目已完成第一阶段骨架实现与第二阶段主线收敛；第三阶段前端已补齐 config 消费、`snapshot_url` 兜底同步与初始化重试，并保持构建通过，当前重点转为浏览器联调、最小验收闭环和证据留痕。

## 3. 默认接手动作

如果没有额外指令，默认顺序是：
1. 先确认当前任务属于前端、后端、文档、测试还是论文支线
2. 先读对应 `docs/specs/`
3. 若是前端任务，优先看 `frontend/src/App.tsx`、`frontend/src/store/workbench.ts`、`frontend/src/components/config-panel.tsx`、`frontend/src/components/control-panel.tsx`、`frontend/src/components/event-panel.tsx`、`frontend/src/lib/api.ts`、`frontend/src/lib/sse.ts`
4. 若是后端联调任务，优先看 `src/embodied_agent/backend/http.py`、`service.py`、`run_registry.py`
5. 开工前确认本轮要更新哪些 `docs/records/`
6. 完成后补状态、记录和交接
