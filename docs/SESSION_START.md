# 新会话接手入口

## 1. 这个文档是干什么的

如果你是一个新开的会话、新接手的 Agent，先读这一个文件。

这个文档的目标只有三个：
- 让你快速知道项目现在处于什么状态
- 让你快速知道接下来优先做什么
- 让你快速知道需要继续读哪些文档

## 2. 项目一句话说明

这是一个桌面级具身智能机器人原型项目，目标是在 `Ubuntu` 部署环境下，完成“感知-决策-执行”三层解耦的机械臂闭环分拣系统。

## 3. 当前状态摘要

当前阶段：
- 文档体系和开发基线已经建立完成
- 项目正准备进入第一阶段代码骨架开发

已经完成：
- 需求文档、主 spec、多文件详细 spec 已整理完成
- `docs/` 已重构为 `specs/`、`reference/`、`records/` 三层
- 架构参考、接口参考、Git 管理参考、论文大纲参考已建立
- 当前状态、里程碑、测试、实验、论文进度、交接文档已完成首版实填

还没完成：
- 代码仓库尚未进入核心模块实现
- 还没有真实的 LangGraph 主流程代码
- 还没有感知层、执行层、前端的真实联调结果
- 还没有 Ubuntu 环境安装与运行验证文档

## 4. 新会话现在该做什么

如果没有额外指令，默认优先级如下：
0. 创建agent team
1. 搭建第一阶段代码骨架。
2. 建立决策层 `LangGraph` 主图和状态结构。
3. 建立感知层、执行层最小 MCP 工具桩。
4. 建立 Ubuntu 环境安装与运行说明。
5. 每做完一轮工作，同步更新 `docs/records/DEVELOPMENT_LOG.md` 和 `docs/records/HANDOFF.md`。

## 5. 新会话阅读顺序

必须先读：
1. `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
2. `DEVELOPMENT_SPEC.md`
3. `docs/SESSION_START.md`
4. `docs/specs/02-agent-team.md`

建议继续读：
5. `docs/specs/01-project-baseline.md`
6. `docs/specs/09-documentation-handoff.md`
7. `docs/reference/ARCHITECTURE.md`
8. `docs/reference/INTERFACES.md`
9. `docs/records/CURRENT_STATUS.md`
10. `docs/records/HANDOFF.md`

按任务再继续读：
- 做决策层：读 `docs/specs/05-decision-spec.md`
- 做感知层：读 `docs/specs/04-perception-spec.md`
- 做执行层：读 `docs/specs/06-execution-spec.md`
- 做前端：读 `docs/specs/07-frontend-spec.md`
- 做测试：读 `docs/specs/08-milestones-data-test.md` 和 `docs/records/TEST_REPORT.md`
- 做论文：读 `docs/specs/10-thesis-spec.md`、`docs/reference/THESIS_OUTLINE.md`、`docs/records/THESIS_PROGRESS.md`

## 6. 文档怎么理解

- `docs/specs/`：规定应该怎么做
- `docs/reference/`：提供当前稳定参考
- `docs/records/`：记录当前真实进展

如果三类文档冲突：
1. 先看需求文档
2. 再看 `DEVELOPMENT_SPEC.md`
3. 再看 `docs/specs/`
4. 最后修正 `reference` 和 `records`

## 7. 接手时的默认行为

新会话接手后，默认应该：
- 先判断当前任务属于哪个模块
- 先确认是否已有对应 spec 和 reference
- 开始动代码或文档前，先明确要更新哪些 records 文档
- 完成后补 `DEVELOPMENT_LOG`、`HANDOFF`、必要时补 `CURRENT_STATUS` 和 `TEST_REPORT`

## 8. 一句话结论

如果你是新会话，现在不用继续整理文档结构，项目文档基线已经够用了；优先进入第一阶段代码骨架开发。
