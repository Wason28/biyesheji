# 桌面级具身智能机器人感知-决策-执行一体化原型系统 Spec 索引

## 1. 文档定位

本文件为多文件 spec 的总入口，用于说明阅读顺序、文档边界和维护方式。

总原则：
- 唯一权威来源是 `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- `docs/specs/` 负责从需求文档派生出可执行的实现规范
- `docs/records/` 负责维护当前状态、测试事实、里程碑、实验和论文材料记录
- `docs/SESSION_START.md` 负责新会话快速接手
- `docs/README.md` 负责解释 `docs/` 目录结构和维护原则

## 2. 阅读顺序

所有接手 Agent 建议按以下顺序阅读：
1. `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
2. `DEVELOPMENT_SPEC.md`
3. `docs/SESSION_START.md`
4. `docs/records/CURRENT_STATUS.md`
5. `docs/specs/01-project-baseline.md`
6. `docs/specs/02-agent-team.md`
7. `docs/specs/03-system-architecture.md`
8. `docs/specs/09-documentation-handoff.md`
9. 按任务进入对应模块 spec：
   - `docs/specs/04-perception-spec.md`
   - `docs/specs/05-decision-spec.md`
   - `docs/specs/06-execution-spec.md`
   - `docs/specs/07-frontend-spec.md`
10. 需要追溯历史事实时再读：
   - `docs/records/DEVELOPMENT_LOG.md`
   - `docs/records/TEST_REPORT.md`
   - `docs/records/HANDOFF.md`
   - `docs/records/MILESTONES.md`
   - `docs/records/THESIS_PROGRESS.md`

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

## 4. docs 目录边界

- `docs/specs/`：实现规范
- `docs/records/`：动态记录
- `docs/SESSION_START.md`：新会话入口
- `docs/README.md`：目录说明

`docs/reference/` 不再作为主干知识层维护。系统边界、接口、论文映射等内容统一回收进 `docs/specs/` 或 `docs/records/`。

## 5. 维护原则

- 新增或修改模块规范时，优先在对应子规范中维护。
- 新增或修改动态状态与记录时，优先在 `docs/records/` 中维护。
- 若系统范围或目标变化，先核对需求文档，再更新 `docs/specs/`。
- 若 `specs` 与 `records` 冲突，先核对需求文档和当前事实，再统一修正。

## 6. 记录文档

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
- 上述 `records` 文档用于保留当前状态和历史事实
- 任何重构都不能删除已形成的真实记录事实
