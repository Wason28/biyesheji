# 09 文档、记录与交接规范

## 1. 文档目标

本项目所有开发都必须支持快速接手、快速定位和全过程回溯，因此文档不是附属产物，而是主交付物之一。

## 2. 接手顺序

新 Agent 接手时必须按以下顺序阅读：
1. `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
2. `DEVELOPMENT_SPEC.md`
3. `docs/SESSION_START.md`
4. `docs/README.md`
5. `docs/reference/ARCHITECTURE.md`
6. `docs/reference/INTERFACES.md`
7. `docs/records/CURRENT_STATUS.md`
8. `docs/records/DEVELOPMENT_LOG.md`
9. `docs/records/THESIS_PROGRESS.md`

## 3. 必备文档

- `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- `README.md`
- `DEVELOPMENT_SPEC.md`
- `docs/SESSION_START.md`
- `docs/README.md`
- `docs/reference/ARCHITECTURE.md`
- `docs/reference/INTERFACES.md`
- `docs/reference/GIT_WORKFLOW.md`
- `docs/reference/THESIS_OUTLINE.md`
- `docs/records/CURRENT_STATUS.md`
- `docs/records/MILESTONES.md`
- `docs/records/DEVELOPMENT_LOG.md`
- `docs/records/TEST_REPORT.md`
- `docs/records/THESIS_PROGRESS.md`
- `docs/records/EXPERIMENTS.md`
- `docs/records/FIGURE_ASSETS.md`
- `docs/records/HANDOFF.md`

## 4. 开发记录要求

`docs/records/DEVELOPMENT_LOG.md` 每条记录至少包含：
- 日期
- 负责 Agent
- 对应里程碑
- 修改模块
- 修改内容
- 对应需求点
- 风险和遗留问题
- 下一步建议
- 对应论文章节

## 5. 交接要求

每轮工作结束前至少更新：
- `CURRENT_STATUS`
- `DEVELOPMENT_LOG`
- `HANDOFF`

如有影响，还必须更新：
- `MILESTONES`
- `ARCHITECTURE`
- `INTERFACES`
- `TEST_REPORT`
- `THESIS_PROGRESS`
- `EXPERIMENTS`

推荐使用的实际路径：
- `docs/records/CURRENT_STATUS.md`
- `docs/records/DEVELOPMENT_LOG.md`
- `docs/records/HANDOFF.md`
- `docs/records/MILESTONES.md`
- `docs/reference/ARCHITECTURE.md`
- `docs/reference/INTERFACES.md`
- `docs/records/TEST_REPORT.md`
- `docs/records/THESIS_PROGRESS.md`
- `docs/records/EXPERIMENTS.md`

## 6. 冲突处理原则

若发现文档、代码和需求文档不一致：
1. 先核对需求文档
2. 再核对当前实现
3. 最后统一修正文档和记录
