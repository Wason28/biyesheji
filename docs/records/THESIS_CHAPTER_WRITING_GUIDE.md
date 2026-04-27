# 论文正文写作指引

本文档在“章节分配表”的基础上，进一步给出每章建议小标题、推荐插图/表格和可直接引用的材料入口，便于快速展开正文。

## 第1章 绪论

### 建议小标题

1. 研究背景
2. 研究意义
3. 研究目标与研究内容
4. 论文结构安排

### 推荐插图 / 表格

- 本章通常不强制放图
- 如需放表，可放“系统完成边界简表”

### 可引用材料

- [THESIS_OUTLINE_AND_PROJECT_SUMMARY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_OUTLINE_AND_PROJECT_SUMMARY.md)
- [CURRENT_STATUS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/CURRENT_STATUS.md)

### 写作重点

- 强调课题针对“感知-决策-执行”一体化系统，而不是单一算法
- 明确当前成果边界是“本地软件级 demo”，避免过度表述

## 第2章 相关技术与理论基础

### 建议小标题

1. 具身智能系统的基本组成
2. 大语言模型与视觉语言模型
3. LangGraph 状态图式编排
4. SmolVLA 与轻量视觉-语言-动作模型
5. Prompt 工程与结构化输出约束

### 推荐插图 / 表格

- Prompt 资产表
- 技术栈对照表

### 可引用材料

- [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
- [thesis_draft.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/thesis_draft.md)

### 写作重点

- 说明为什么系统需要 LLM 负责规划、VLM 负责感知增强
- 说明结构化 Prompt 对降低自由生成风险的价值

## 第3章 系统总体设计与架构

### 建议小标题

1. 系统设计目标
2. 系统总体架构
3. 三层解耦设计
4. 统一运行时装配机制
5. 系统主流程

### 推荐插图 / 表格

- 图 1 系统总体架构图
- 图 2 三层解耦与统一装配关系图
- 图 6 感知-决策-执行工具调用图

### 可引用材料

- [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
- [03-system-architecture.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/03-system-architecture.md)

### 写作重点

- 先画大图，再落到三层边界
- 明确前端、后端门面、统一运行时、三层核心之间的责任划分

## 第4章 环境感知层设计与实现

### 建议小标题

1. 感知层职责与输入来源
2. 感知工具合同设计
3. VLM 结构化输出机制
4. 主动感知与降级策略
5. 感知层当前实现状态

### 推荐插图 / 表格

- 图 9 感知层单层架构图
- 左上角视频流特写图
- 感知工具输入输出表

### 可引用材料

- [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
- [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
- [frontend_video_panel_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_panel_2026-04-27.png)
- [04-perception-spec.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/04-perception-spec.md)

### 写作重点

- 把 `get_image / get_robot_state / describe_scene` 作为核心工具说明
- 明确视觉失败时的降级逻辑，不要写成“始终成功识别”

## 第5章 决策规划层设计与实现

### 建议小标题

1. 决策层总体设计思路
2. LangGraph 状态流转机制
3. 任务规划与动作选择
4. Prompt 驱动的 JSON 规划约束
5. 汉诺塔任务 skill 扩展示例
6. 决策层当前实现状态

### 推荐插图 / 表格

- 图 5 决策层 LangGraph 状态流图
- 图 10 决策层单层架构图
- Prompt 资产表
- 汉诺塔 task skill 流程图

### 可引用材料

- [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
- [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
- [13-hanoi-task-skill.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/13-hanoi-task-skill.md)
- [hanoi.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/skills/hanoi.py)
- [05-decision-spec.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/05-decision-spec.md)

### 写作重点

- 先写状态机，再写 provider 与 heuristic fallback
- 汉诺塔 skill 建议单独作为“复杂序列任务扩展”的案例小节

## 第6章 动作执行层设计与实现

### 建议小标题

1. 执行层职责与工具集合
2. 原子动作与高阶技能
3. 安全检查与急停策略
4. 遥测反馈与执行结果回传
5. 执行层当前实现状态与后续验证项

### 推荐插图 / 表格

- 图 7 执行层安全闭环图
- 图 11 执行层单层架构图
- 执行工具表
- 安全边界参数表

### 可引用材料

- [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
- [phase4_real_opencv_lerobot_local.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/phase4_real_opencv_lerobot_local.example.yaml)
- [06-execution-spec.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/06-execution-spec.md)

### 写作重点

- 说明执行层如何保持“决策层不直连硬件”
- 明确 SmolVLA 实体执行链路已完成，同时区分“已能实体执行”和“统计性实验仍待继续”这两个层面

## 第7章 一体化工作台与后端服务实现

### 建议小标题

1. 前端工作台设计目标
2. 后端 HTTP / SSE / 视频流服务设计
3. 前端状态管理与接口接线
4. `run_id` 生命周期管理
5. 页面运行证据与交互留痕

### 推荐插图 / 表格

- 图 3 前后端运行时通信图
- 图 4 `run_id` 生命周期时序图
- 图 8 前端工作台状态管理与接口接线图
- 前端首页、运行中、完成态三张截图
- 后端接口总表

### 可引用材料

- [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
- [frontend_video_home_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_home_2026-04-27.png)
- [frontend_video_running_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_running_2026-04-27.png)
- [frontend_video_completed_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_completed_2026-04-27.png)
- [THESIS_APPENDIX_READY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_APPENDIX_READY.md)
- [07-frontend-spec.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/07-frontend-spec.md)

### 写作重点

- 这一章最适合放截图和接口表
- 页面截图要配运行地址、任务指令和状态说明

## 第8章 系统测试与实验分析

### 建议小标题

1. 测试目标与测试边界
2. 自动化测试覆盖
3. 本地最小闭环 smoke 验证
4. 前端真实运行留痕
5. 当前风险、限制与结果分析

### 推荐插图 / 表格

- 自动化测试覆盖摘要表
- 本地最小闭环 smoke 证据卡
- 前端运行证据卡

### 可引用材料

- [TEST_REPORT.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/TEST_REPORT.md)
- [EXPERIMENTS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/EXPERIMENTS.md)
- [phase4_local_e2e_smoke_result_2026-04-21.json](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/phase4_local_e2e_smoke_result_2026-04-21.json)
- [THESIS_APPENDIX_READY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_APPENDIX_READY.md)

### 写作重点

- 本章必须明确“验证的是本地软件级闭环”
- 把“支持的结论”和“不支持的结论”分开写

## 第9章 总结与展望

### 建议小标题

1. 全文工作总结
2. 当前系统不足
3. 未来工作展望

### 推荐插图 / 表格

- 不强制放图
- 可放“未来工作路线表”

### 可引用材料

- [CURRENT_STATUS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/CURRENT_STATUS.md)
- [13-hanoi-task-skill.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/13-hanoi-task-skill.md)

### 写作重点

- 展望优先写真实硬件闭环、长程任务 skill 扩展、数据采集与训练闭环

## 附录

### 建议附录条目

1. 关键 Prompt 完整文本
2. 后端接口总表
3. 真实链路配置模板参数表
4. 自动化测试覆盖摘要表
5. 前端运行证据卡
6. 本地最小闭环 smoke 证据卡
7. 汉诺塔任务 Skill 证据卡

### 直接来源

- [THESIS_APPENDIX_READY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_APPENDIX_READY.md)
- [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
- [THESIS_EVIDENCE_INDEX.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_EVIDENCE_INDEX.md)
