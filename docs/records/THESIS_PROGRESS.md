# 论文进度

## 基本信息

- 当前阶段：论文结构建立完成；第三阶段前端完整规范能力已落地，配置提交、工具刷新、助手提示、运行态图像承接与浏览器截图留痕均已补齐，第三轮文档同步进入“可按完成事实实填”阶段
- 当前负责人 Agent：Thesis Curator
- 最近更新时间：2026-04-21

## 各章节进度

- 绪论：已明确写作方向，未展开正文
- 相关工作：已明确研究范围，未补文献综述
- 系统架构设计：已有完整结构基线，且可纳入第三阶段 backend 独立层、统一工具桥接、前端独立工程与运行态消费链路的最新事实
- 决策层 Agent 设计：已有 phase-2 主线事实，可按已验证证据写正文骨架
- 系统实现与验证：已具备第一阶段骨架、第二阶段主线合同、第三阶段最小 HTTP + run 状态推送骨架，以及前端完整配置工作区、配置写回、工具刷新、运行态图像承接、REST/SSE 消费层与浏览器截图留痕事实；当前已可写前端界面开发与 MCP 工具集成章节的完成版正文，但仍缺真实视频流、Ubuntu 实机、实验数据与真实硬件链路
- 总结与展望：已明确方向，待最终成稿时撰写

## 第三轮前端骨架同步内容

- 前端工程骨架成熟度已可写入论文：`frontend/` 基于 React 19 + Vite 7 + Zustand 5 落地，`App.tsx` 已组织任务输入、配置展示、运行态快照、事件订阅、工具面板五块主工作台，并形成可截图的首屏布局
- 前端配置合同消费已升级为完整可写工作区：`lib/api.ts` 已接入 `GET /bootstrap`、`GET /config`、`PUT /config`、`GET /tools`、`POST /tools/refresh`；`store/workbench.ts` 已支持配置草稿、提交、回滚与刷新；`config-panel.tsx` 已支持模型选择、API Key、本地路径、机械臂初始位置、速度缩放和最大迭代次数编辑
- 前端助手提示已可写入论文：配置面板已引入“模型部署助手”和“系统载入助手”提示卡，后端通过 `config` 合同返回当前模型候选、配置状态与下一步引导信息
- 前端运行态快照消费已可写入论文：`POST /runs` 返回的 `accepted.run`、`snapshot_url` 与 `events_url` 已被 `store/workbench.ts` 承接，`syncRunSnapshot()` 可主动拉取最新 `snapshot`，`runtime-panel.tsx` 已显式展示 `robot_state / last_execution / scene_observations / logs`，并承接 `current_image` 图像展示
- 前端运行态订阅语义已可写入论文：`lib/sse.ts` + `store/workbench.ts` 使用 `EventSource` 消费 `events_url` 的 `snapshot` 事件，并按 `version` 去重、在终态主动关闭订阅；`event-panel.tsx` 已提供 `snapshot_url / events_url`、版本时间线与终态收口提示
- 本轮已补浏览器截图与 live 联调留痕：`docs/records/phase3_workbench_2026-04-21.png`、`docs/records/phase3_workbench_2026-04-21_live.png` 已形成第三阶段完成边界的图像证据
## 已完成

- 已完成论文章节主框架
- 已完成论文与需求文档、spec 的映射
- 已完成论文图表准备方向梳理
- 已具备统一启动入口与最小跨层集成验证事实，可支撑系统实现与验证章节增加 mock integration validation 小节
- 已具备第三阶段前端承接所需的最小后端证据链：frontend contracts、run registry、HTTP / SSE 骨架与 67 个测试通过基线
- 已完成第三阶段前端工程目录与 Vite / React 基础脚手架落地
- 已完成主工作台五块面板骨架与显式展示合同接线
- 已完成 `bootstrap + GET /config` 双来源只读配置消费与四分区展示
- 已完成 `accepted.run + snapshot_url + events_url` 运行态快照承接与同步逻辑
- 已完成 REST + SSE 消费适配层与 Zustand 状态管理骨架
- 已完成 `npm run build` 前端构建验证，可作为工程骨架已落地的直接证据

## 证据基线

- 前端工作台布局：`frontend/src/App.tsx`
- 前端状态管理与 run 消费链路：`frontend/src/store/workbench.ts`
- 前端 REST 适配与错误封装：`frontend/src/lib/api.ts`
- 前端 SSE 订阅适配：`frontend/src/lib/sse.ts`
- 前端配置合同展示：`frontend/src/components/config-panel.tsx`
- 前端运行态快照展示：`frontend/src/components/runtime-panel.tsx`
- 前端事件时间线与订阅信息展示：`frontend/src/components/event-panel.tsx`
- 前端显式类型合同：`frontend/src/types/runtime.ts`
- 前端展示合同：`src/embodied_agent/backend/contracts.py`
- 运行态与 `run_id` 生命周期：`src/embodied_agent/backend/service.py`
- HTTP / SSE 路由与错误返回：`src/embodied_agent/backend/http.py`
- 接口与生命周期验证：`tests/test_backend_http_phase3.py`、`tests/test_backend_run_stream_phase3.py`
- 前端构建验证：`frontend/package.json` 中 `build` 脚本已通过执行

## 待补材料

- 相关工作文献整理
- 浏览器实际运行截图留档、页面模块截图索引与前后端联调记录
- 系统实现截图和关键代码说明
- Ubuntu 实机启动、前后端联调与错误态回显材料
- 实验数据与成功率分析
- 数据采集台账、样本规模统计、首条真实轨迹验证记录与 `SmolVLA` 训练记录
- 架构图、时序图、界面图、结果图表

## 当前风险项

- 当前前端虽已具备 `config/snapshot` 合同消费与首批可截图界面，但尚未沉淀浏览器运行截图、联调回执与自动化前端测试，因此前端实现与工具集成章节仍不能写成已完成端到端验证
- 当前 HTTP / SSE 仅为同步 WSGI + 进程内 run registry 骨架，论文必须明确其为可联调基线，而非生产级长连接服务
- `current_image` 当前仍是占位字段，前端运行态面板尚未接入真实视频流或图像链路
- 如果前端骨架落地后不立即收集截图与联调记录，系统实现与验证章节仍会在后期集中补写，风险较高

## 下一步建议

1. 先按当前代码与构建证据撰写第三阶段前端工程骨架、配置读取合同与运行态快照消费小节，避免实现事实继续滞留在代码中。
2. 立即在浏览器联调后补采配置分页、`config_source`、运行态 JSON 块、`snapshot_url / events_url`、事件时间线的首批截图索引。
3. 补充重复 `run_id`、非法事件游标、空态、加载态与手动同步快照的前端回显记录，形成异常处理小节的图文证据。
4. 每次联调、实验或截图产出后，立即同步更新 `docs/records/EXPERIMENTS.md` 和 `docs/records/FIGURE_ASSETS.md`。

