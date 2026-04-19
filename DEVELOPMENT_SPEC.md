# 桌面级具身智能机器人感知-决策-执行一体化原型系统 Spec 索引

## 1. 文档定位

本文件为多文件 spec 的总入口。详细规范已拆分到 `docs/specs/` 目录，后续开发应优先维护子规范，避免在单文件中堆积全部内容。

总原则：
- 需求基线以 `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md` 为准。
- 目标部署环境为 `Ubuntu`，相关实现与部署说明优先按 `Ubuntu` 维护。
- `DEVELOPMENT_SPEC.md` 负责导航、阅读顺序和文档边界说明。
- `docs/specs/` 负责详细设计编排。

## 2. 阅读顺序

所有接手 Agent 建议按以下顺序阅读：
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
13. `docs/specs/04-perception-spec.md`
14. `docs/specs/05-decision-spec.md`
15. `docs/specs/06-execution-spec.md`
16. `docs/specs/07-frontend-spec.md`
17. `docs/specs/08-milestones-data-test.md`
18. `docs/specs/10-thesis-spec.md`

## 3. Spec 结构

### 3.1 项目总览

- `docs/specs/01-project-baseline.md`
- 定义项目目标、核心原则、技术栈和系统边界。

### 3.2 Agent Team

- `docs/specs/02-agent-team.md`
- 定义对照 spec 开发项目的协作 Agent Team。

### 3.3 架构设计

- `docs/specs/03-system-architecture.md`
- 定义三层架构、闭环数据流和扩展方式。

### 3.4 模块详细规范

- `docs/specs/04-perception-spec.md`
- `docs/specs/05-decision-spec.md`
- `docs/specs/06-execution-spec.md`
- `docs/specs/07-frontend-spec.md`

### 3.5 计划与验证

- `docs/specs/08-milestones-data-test.md`
- 定义里程碑、数据采集和测试验证要求。

### 3.6 文档与交接

- `docs/specs/09-documentation-handoff.md`
- 定义接手顺序、开发记录和交接规范。

### 3.7 论文规范

- `docs/specs/10-thesis-spec.md`
- 定义论文映射、论文 Agent 职责和阶段性产出。

## 4. docs 目录说明

- `docs/specs/`：详细设计规范文档，属于 `spec`
- `docs/reference/`：稳定参考文档，属于项目架构、接口、Git 规范、论文框架等参考材料
- `docs/records/`：动态记录文档，属于状态、里程碑、测试、实验、交接、论文进度等持续更新材料
- `docs/SESSION_START.md`：新会话快速接手入口文档
- `docs/README.md`：用于解释这三类文档的区别和阅读建议

## 5. 维护原则

- 新增或修改模块规范时，优先在对应子规范中维护。
- 新增或修改稳定参考信息时，优先在 `docs/reference/` 中维护。
- 新增或修改动态状态与记录时，优先在 `docs/records/` 中维护。
- 若系统范围或目标变化，先核对需求文档，再更新 spec。
- 若主索引与子规范冲突，以子规范为准，并及时修正主索引。
- 若 `spec`、`reference`、`records` 三类文档冲突，先核对需求文档，再统一修正。

## 6. 参考与记录文档

稳定参考文档：
- `docs/reference/ARCHITECTURE.md`
- `docs/reference/INTERFACES.md`
- `docs/reference/GIT_WORKFLOW.md`
- `docs/reference/THESIS_OUTLINE.md`

动态记录文档：
- `docs/records/CURRENT_STATUS.md`
- `docs/records/MILESTONES.md`
- `docs/records/DEVELOPMENT_LOG.md`
- `docs/records/TEST_REPORT.md`
- `docs/records/THESIS_PROGRESS.md`
- `docs/records/EXPERIMENTS.md`
- `docs/records/FIGURE_ASSETS.md`
- `docs/records/HANDOFF.md`

说明：
- 上述 `reference` 文档已形成稳定首版参考内容
- 上述 `records` 文档已完成首版实填，后续随开发持续更新
