# 论文材料章节分配表

本文档按当前论文结构，把现有材料直接分配到对应章节。

配套写作指引：
- [THESIS_CHAPTER_WRITING_GUIDE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_CHAPTER_WRITING_GUIDE.md)

## 第1章 绪论

- 使用材料：
  [THESIS_OUTLINE_AND_PROJECT_SUMMARY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_OUTLINE_AND_PROJECT_SUMMARY.md)
  [CURRENT_STATUS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/CURRENT_STATUS.md)
- 建议写入内容：
  - 研究背景
  - 研究意义
  - 当前系统完成边界

## 第2章 相关技术与理论基础

- 使用材料：
  [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
  [thesis_draft.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/thesis_draft.md)
- 建议写入内容：
  - LLM / VLM 在具身智能中的作用
  - Prompt 工程与结构化输出约束
  - LangGraph、SmolVLA、LeRobot 的技术定位

## 第3章 系统总体设计与架构

- 核心图：
  [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
- 重点使用：
  - 图 1 系统总体架构图
  - 图 2 三层解耦与统一装配关系图
  - 图 6 感知-决策-执行工具调用图
- 可配套文字材料：
  [THESIS_APPENDIX_READY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_APPENDIX_READY.md)

## 第4章 环境感知层设计与实现

- 核心图：
  [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
  图 9 感知层单层架构图
- Prompt 材料：
  [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
- 界面材料：
  [frontend_video_panel_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_panel_2026-04-27.png)
- 建议写入内容：
  - `get_image / get_robot_state / describe_scene`
  - 视觉结构化输出
  - 视频流与实时感知输入

## 第5章 决策规划层设计与实现

- 核心图：
  [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
  - 图 5 决策层 LangGraph 状态流图
  - 图 10 决策层单层架构图
- Prompt 材料：
  [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
- 技能扩展材料：
  [13-hanoi-task-skill.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/13-hanoi-task-skill.md)
  [hanoi.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/skills/hanoi.py)
- 建议写入内容：
  - JSON 规划提示词
  - 状态图闭环控制
  - 汉诺塔任务 skill 作为长程任务扩展示例

## 第6章 动作执行层设计与实现

- 核心图：
  [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
  - 图 7 执行层安全闭环图
  - 图 11 执行层单层架构图
- 配置材料：
  [phase4_real_opencv_lerobot_local.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/phase4_real_opencv_lerobot_local.example.yaml)
- 建议写入内容：
  - `move_to / move_home / grasp / release / servo_rotate / run_smolvla`
  - 安全前置检查
  - 急停与遥测边界

## 第7章 一体化工作台与后端服务实现

- 核心图：
  [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
  - 图 3 前后端运行时通信图
  - 图 4 `run_id` 生命周期时序图
  - 图 8 前端工作台状态管理与接口接线图
- 核心截图：
  [frontend_video_home_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_home_2026-04-27.png)
  [frontend_video_running_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_running_2026-04-27.png)
  [frontend_video_completed_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_completed_2026-04-27.png)
- 接口材料：
  [THESIS_APPENDIX_READY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_APPENDIX_READY.md)
- 建议写入内容：
  - REST + SSE + MJPEG
  - 页面状态管理
  - 任务开始 / 结束 / 终态收口

## 第8章 系统测试与实验分析

- 测试材料：
  [TEST_REPORT.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/TEST_REPORT.md)
  [EXPERIMENTS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/EXPERIMENTS.md)
  [phase4_local_e2e_smoke_result_2026-04-21.json](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/phase4_local_e2e_smoke_result_2026-04-21.json)
- 证据卡：
  [THESIS_APPENDIX_READY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_APPENDIX_READY.md)
- 建议写入内容：
  - 自动化测试覆盖
  - 本地最小闭环 smoke
  - 前端真实运行截图留痕
  - 真实链路未完成项与风险说明

## 第9章 总结与展望

- 使用材料：
  [CURRENT_STATUS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/CURRENT_STATUS.md)
  [13-hanoi-task-skill.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/13-hanoi-task-skill.md)
- 建议写入内容：
  - 从 mock-first 到真实硬件闭环的后续路线
  - 汉诺塔等长程任务 skill 的扩展方向
  - 真实执行、数据采集、训练与评测的下一步

## 附录

- 优先放：
  [THESIS_APPENDIX_READY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_APPENDIX_READY.md)
  [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)
  [THESIS_EVIDENCE_INDEX.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_EVIDENCE_INDEX.md)
- 汉诺塔 skill 附录材料：
  [13-hanoi-task-skill.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/13-hanoi-task-skill.md)
  [THESIS_MERMAID_ARCHITECTURE.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MERMAID_ARCHITECTURE.md)
