# docs 目录说明

## 1. 文档定位

`docs/` 只承担两类职责：
- `docs/specs/`：从根需求文档派生出的实现规范，服务开发执行
- `docs/records/`：项目当前状态、测试结果、里程碑、论文与实验材料的真实记录

唯一权威来源：
- `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`

如果 `docs/` 中任意内容与根需求文档冲突，以根需求文档为准，再回头修正文档。

## 2. 当前阶段摘要

当前项目已完成第一阶段骨架实现与第二阶段主线收敛；第三阶段前端已完成 prototype 风格工作台重构、真实 runtime 接线、本地 `npm run dev` 一键联调与 execution flow 可视化修正。当前文档口径必须始终保持为：
- 已有前端三栏工作台、设置 modal 与真实 runtime 数据接线
- 已有根目录一键启动脚本、env-driven Vite 代理与 backend CORS
- 已有 `eventFeed` 驱动的执行流展示与 `snapshot_url` 兜底同步
- 已具备 focused tests、前端构建和本地浏览器 live 联调事实
- 尚未完成真实硬件、真实视频流、浏览器自动化与生产级流式服务

## 3. 当前目录结构

- `docs/SESSION_START.md`：新会话快速接手入口
- `docs/specs/`：实现规范
  - `docs/specs/07-frontend-spec.md`：第三阶段前端职责、展示边界与联调验收清单
  - `docs/specs/09-documentation-handoff.md`：文档、记录与交接规范
  - `docs/specs/11-ubuntu-runbook.md`：Ubuntu 目标环境下的最小安装、运行与验证说明
  - `docs/specs/12-phase4-real-chain-runbook.md`：第四阶段真实链路模板、启动命令与 smoke 验收说明
- `docs/records/`：动态记录
  - `CURRENT_STATUS.md`：当前项目状态
  - `DEVELOPMENT_LOG.md`：详细开发记录
  - `HANDOFF.md`：跨会话交接摘要
  - `MILESTONES.md`：阶段推进判断

`docs/reference/` 不再作为主干知识层维护。若后续确有辅助资料需要保留，必须避免与 `specs/` 和 `records/` 重复。

## 4. 阅读顺序

新会话默认按以下顺序阅读：
1. `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
2. `docs/SESSION_START.md`
3. `docs/records/CURRENT_STATUS.md`
4. 按任务进入对应 `docs/specs/`
5. 需要追溯历史事实时再读 `docs/records/DEVELOPMENT_LOG.md`、`docs/records/TEST_REPORT.md`、`docs/records/HANDOFF.md`

## 5. 维护原则

- 修改系统边界、接口、流程、阶段要求：更新对应 `docs/specs/`
- 修改当前状态、测试事实、阶段推进、论文与实验材料：更新对应 `docs/records/`
- 前端工程、后端接口或构建验证有阶段性推进后，至少检查以下文档；若本轮新增 fallback、重试、同步兜底等用户可见行为，也必须同步更新这些导航和交接文件：
  - `docs/SESSION_START.md`
  - `docs/records/CURRENT_STATUS.md`
  - `docs/records/HANDOFF.md`
  - `docs/records/DEVELOPMENT_LOG.md`
  - `README.md`
- 若本轮新增测试、联调或截图事实，再补查：
  - `docs/records/TEST_REPORT.md`
  - `docs/records/FIGURE_ASSETS.md`
  - `docs/records/THESIS_PROGRESS.md`

## 6. 冲突处理

若发现需求文档、spec、records、代码之间不一致：
1. 先核对根需求文档
2. 再核对当前实现或当前真实记录
3. 最后统一修正 `docs/`
