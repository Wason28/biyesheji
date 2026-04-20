# 09 文档、记录与交接规范

## 1. 文档目标

本项目所有开发都必须支持快速接手、快速定位和全过程回溯，因此文档不是附属产物，而是主交付物之一。

## 2. 接手顺序

新 Agent 接手时按以下顺序阅读：
1. `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
2. `docs/SESSION_START.md`
3. `docs/records/CURRENT_STATUS.md`
4. 与当前任务对应的 `docs/specs/`
5. 需要追溯历史事实时再读 `docs/records/DEVELOPMENT_LOG.md`、`docs/records/TEST_REPORT.md`

## 3. 必备文档

- `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- `README.md`
- `docs/README.md`
- `docs/SESSION_START.md`
- `docs/specs/01-project-baseline.md`
- `docs/specs/02-agent-team.md`
- `docs/specs/03-system-architecture.md`
- `docs/specs/04-perception-spec.md`
- `docs/specs/05-decision-spec.md`
- `docs/specs/06-execution-spec.md`
- `docs/specs/07-frontend-spec.md`
- `docs/specs/08-milestones-data-test.md`
- `docs/specs/09-documentation-handoff.md`
- `docs/specs/10-thesis-spec.md`
- `docs/specs/11-ubuntu-runbook.md`
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
- `docs/records/CURRENT_STATUS.md`
- `docs/records/DEVELOPMENT_LOG.md`
- `docs/records/HANDOFF.md`

如有影响，还必须更新：
- `docs/records/MILESTONES.md`
- 对应 `docs/specs/`
- `docs/records/TEST_REPORT.md`
- `docs/records/THESIS_PROGRESS.md`
- `docs/records/EXPERIMENTS.md`
- `docs/records/FIGURE_ASSETS.md`

工作完成后的文档维护要求：
- 完成代码实现后，必须检查 `README.md`、`docs/SESSION_START.md`、`docs/records/CURRENT_STATUS.md` 和对应 `docs/specs/` 是否仍与当前实现一致。
- 完成 Ubuntu 相关运行或验证工作后，必须同步检查 `docs/specs/11-ubuntu-runbook.md`、`docs/records/TEST_REPORT.md`、`docs/records/CURRENT_STATUS.md` 和 `docs/records/HANDOFF.md` 是否仍与当前事实一致。
- 完成测试或验证后，必须同步更新 `docs/records/TEST_REPORT.md`；若阶段判断变化，还必须同步更新 `docs/records/CURRENT_STATUS.md`、`docs/records/MILESTONES.md` 和 `docs/records/HANDOFF.md`。
- 完成影响论文事实材料的工作后，必须评估是否需要同步更新 `docs/records/THESIS_PROGRESS.md`、`docs/records/EXPERIMENTS.md` 和 `docs/records/FIGURE_ASSETS.md`。
- 如果本轮工作未更新上述文档，交接时必须明确说明原因和待补项。

## 6. 冲突处理原则

若发现文档、代码和需求文档不一致：
1. 先核对需求文档
2. 再核对当前实现或当前真实记录
3. 最后统一修正文档和记录
