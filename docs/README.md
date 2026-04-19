# docs 目录说明

## 1. 目录定位

`docs/` 目录当前分为三类文档：
- `docs/specs/`：详细设计规范文档，属于长期维护的 `spec`
- `docs/reference/`：稳定参考文档，属于项目基线、接口、工作规范、论文框架等非动态文档
- `docs/records/`：动态记录文档，属于状态、里程碑、测试、实验、交接、论文进度等持续更新文档
- `docs/SESSION_START.md`：新会话接手入口文档，优先解决“现在是什么状态、接下来做什么”

不要混用这三类文档。

## 2. 三类文档的区别

### 2.1 Spec 文档

位置：
- `docs/specs/`

作用：
- 定义项目基线
- 定义 Agent Team 分工
- 定义系统架构与模块约束
- 定义里程碑、测试、交接、论文规范

特征：
- 面向“应该怎么做”
- 属于规则、约束、设计和标准
- 修改时要谨慎，优先依据需求文档更新

当前文件：
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

### 2.2 参考文档

位置：
- `docs/reference/`

作用：
- 提供系统当前参考架构
- 提供接口与工作流参考
- 提供论文结构基线

特征：
- 面向“参考什么来做”
- 属于相对稳定的项目参考文档
- 不是纯模板，也不是底层设计 `spec`

当前文件：
- `docs/reference/ARCHITECTURE.md`
- `docs/reference/INTERFACES.md`
- `docs/reference/GIT_WORKFLOW.md`
- `docs/reference/THESIS_OUTLINE.md`

### 2.3 记录文档

位置：
- `docs/records/`

作用：
- 记录当前状态
- 跟踪里程碑推进
- 记录开发日志、测试结果、论文进度和交接内容

特征：
- 面向“现在做到哪里了”
- 属于动态维护文档
- 当前已完成首版实填，后续会持续沉淀真实内容

当前文件：
- `docs/records/CURRENT_STATUS.md`
- `docs/records/MILESTONES.md`
- `docs/records/DEVELOPMENT_LOG.md`
- `docs/records/TEST_REPORT.md`
- `docs/records/THESIS_PROGRESS.md`
- `docs/records/EXPERIMENTS.md`
- `docs/records/FIGURE_ASSETS.md`
- `docs/records/HANDOFF.md`

## 3. 阅读建议

新 Agent 接手时建议按以下顺序阅读：
1. `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
2. `DEVELOPMENT_SPEC.md`
3. `docs/SESSION_START.md`
4. `docs/README.md`
5. `docs/specs/01-project-baseline.md`
6. `docs/specs/02-agent-team.md`
7. `docs/specs/03-system-architecture.md`
8. `docs/specs/09-documentation-handoff.md`
9. `docs/reference/ARCHITECTURE.md`
10. `docs/reference/INTERFACES.md`
11. `docs/records/CURRENT_STATUS.md`
12. `docs/records/HANDOFF.md`

## 4. 维护原则

- 改规则、改边界、改设计：优先改 `docs/specs/`
- 改稳定参考信息：优先改 `docs/reference/`
- 改状态、改记录、改交接：优先改 `docs/records/`
- 若 spec、reference 与 records 冲突，先核对需求文档，再统一修正
- 所有非 spec 文档都应与目标部署环境 `Ubuntu` 保持一致
