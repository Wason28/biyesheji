# SmolVLA 实体执行证据卡

## 文档定位

本文档用于给论文正文、附录和答辩材料提供一份独立的“SmolVLA 实体执行”证据索引。它的作用是说明当前项目已经完成实体执行链路接入，并给出可追溯的工程资产入口；同时明确指出，本文档本身不替代后续大规模统计实验台账。

## 当前可写结论

截至 2026-04-27，项目已经完成 SmolVLA 实体执行链路打通。论文中可以据此表述为：

- 执行层已不再停留于 `run_smolvla` 接口预留或纯 mock 验证阶段。
- 系统已具备基于 SmolVLA 的真实高阶技能执行事实。
- 当前仍需把“实体执行已完成”与“统计性实验仍待补充”严格区分。

## 证据锚点

### 1. 执行层代码资产

- 工具注册入口：
  [server.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/execution/server.py)
- 运行时动作实现：
  [tools.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/execution/tools.py)
- SmolVLA 执行逻辑：
  [smolvla.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/execution/smolvla.py)
- 机器人适配器：
  [robot_adapter.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/execution/robot_adapter.py)
- 安全边界实现：
  [safety.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/execution/safety.py)

### 2. 真实链路配置与运行说明

- 真实链路模板：
  [phase4_real_opencv_lerobot_local.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/phase4_real_opencv_lerobot_local.example.yaml)
- MCP bridge 模板：
  [phase4_real_opencv_mcp_bridge.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/phase4_real_opencv_mcp_bridge.example.yaml)
- phase4 联调 runbook：
  [12-phase4-real-chain-runbook.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/12-phase4-real-chain-runbook.md)
- phase4 smoke 脚本：
  [phase4_p0_real_smoke.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/scripts/phase4_p0_real_smoke.py)

### 3. 论文与状态材料

- 当前状态：
  [CURRENT_STATUS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/CURRENT_STATUS.md)
- 论文长正文草稿：
  [THESIS_MAIN_TEXT_10000.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_MAIN_TEXT_10000.md)
- 论文大纲与项目总结：
  [THESIS_OUTLINE_AND_PROJECT_SUMMARY.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/THESIS_OUTLINE_AND_PROJECT_SUMMARY.md)
- 本文档对应的完整正文草稿：
  [thesis_draft.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/thesis_draft.md)

### 4. 前端与联调截图

- 前端运行中：
  [frontend_video_running_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_running_2026-04-27.png)
- 前端完成态：
  [frontend_video_completed_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_completed_2026-04-27.png)
- 视频流特写：
  [frontend_video_panel_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_panel_2026-04-27.png)

## 论文建议写法

### 正文可直接使用

- 当前执行层已经完成 SmolVLA 实体执行链路接入，系统具备真实高阶技能执行能力。
- 自动化测试主要证明软件级合同、运行时和前后端联调基线稳定；实体执行事实则需要结合真实链路材料与现场记录共同说明。
- 因此，论文应同时写清“已具备真实执行能力”与“统计性实验仍待继续”这两个层面。

### 更适合附录说明

- 真实链路模板和环境变量配置
- smoke 脚本入口与验收顺序
- 代码模块映射关系
- 前端联调截图索引

## 当前仍待补充

- 独立的实体执行实验台账
- 重复成功率与失败原因统计
- 长时间稳定性记录
- 不同场景条件下的鲁棒性量化结果
