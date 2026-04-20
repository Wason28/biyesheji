# docs 目录说明

## 1. 文档定位

`docs/` 只承担两类职责：
- `docs/specs/`：从根需求文档派生出的实现规范，服务开发执行
- `docs/records/`：项目当前状态、测试结果、里程碑、论文与实验材料的真实记录

唯一权威来源：
- `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`

如果 `docs/` 中任意内容与根需求文档冲突，以根需求文档为准，再回头修正文档。

## 2. 当前目录结构

- `docs/SESSION_START.md`：新会话快速接手入口
- `docs/specs/`：实现规范
- `docs/records/`：动态记录

`docs/reference/` 不再作为主干知识层维护。若后续确有辅助资料需要保留，必须避免与 `specs/` 和 `records/` 重复。

## 3. 阅读顺序

新会话默认按以下顺序阅读：
1. `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
2. `docs/SESSION_START.md`
3. `docs/records/CURRENT_STATUS.md`
4. 按任务进入对应 `docs/specs/`
5. 需要追溯历史事实时再读 `docs/records/DEVELOPMENT_LOG.md`、`docs/records/TEST_REPORT.md`

## 4. 维护原则

- 修改系统边界、接口、流程、阶段要求：更新对应 `docs/specs/`
- 修改当前状态、测试事实、阶段推进、论文与实验材料：更新对应 `docs/records/`
- 完成一轮工作后，至少检查：
  - `docs/SESSION_START.md`
  - `docs/records/CURRENT_STATUS.md`
  - `docs/records/HANDOFF.md`
  - `docs/records/DEVELOPMENT_LOG.md`
  - `docs/records/TEST_REPORT.md`（如本轮有测试或验证）
- 论文相关工作完成后，还应检查：
  - `docs/records/THESIS_PROGRESS.md`
  - `docs/records/EXPERIMENTS.md`
  - `docs/records/FIGURE_ASSETS.md`

## 5. 冲突处理

若发现需求文档、spec、records、代码之间不一致：
1. 先核对根需求文档
2. 再核对当前实现或当前真实记录
3. 最后统一修正 `docs/`
