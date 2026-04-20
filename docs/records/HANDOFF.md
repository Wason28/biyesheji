# 交接摘要

## 当前交接状态

- 日期：2026-04-20
- 当前阶段：第一阶段完成，开始推进第二阶段主线

## 本轮新增事实

- 本地 `python` / `python3` 命令已修复为可用的 `Python 3.12.12`
- 已创建项目虚拟环境 `.venv` 并完成依赖安装
- 已执行 `uv run pytest -q`，当前 44 个测试全部通过
- 已新增统一启动入口 `src/embodied_agent/app.py`
- 已新增统一入口相关 9 个测试，覆盖单任务、多任务、配置加载、frontend 回退、未知工具、原子执行工具透传以及感知 / 执行失败闭环
- 已补 perception provider 工厂注册与 execution runtime 工厂注入测试
- 已验证 `uv run python -m embodied_agent.app --instruction "抓取桌面方块"`、`--dump-final-state`、`--list-tools` 可完成当前 mock CLI 运行链路验证
- 已完成 P0 第一批合同收敛与统一入口测试补强，对应阶段回归达到 13 个通过
- 已完成 P0 第二批合同收敛：结构化 `ee_pose`、统一 perception / execution envelope、focused tests 回归，对应阶段回归达到 17 个通过
- 已补前端接口占位辅助函数，可导出最小 `bootstrap/config/run snapshot` 合同并收敛状态字段约束
- 已开始第二阶段决策主线改造的第一步，并新增 capability/action 选择测试
- 当前全量测试结果为 `44 passed`

## 交接提醒

- 下一位接手者先读 `# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- 再读 `docs/records/CURRENT_STATUS.md`
- 再进入与当前任务相关的 `docs/specs/`
- 如需追溯历史事实，优先看 `docs/records/DEVELOPMENT_LOG.md` 和 `docs/records/TEST_REPORT.md`

## 推荐下一步

1. 以当前配置装配、合同收敛与 44 个测试通过事实为基线继续推进第二阶段主线实现，并按 `docs/specs/08-milestones-data-test.md` 中的第二阶段完成边界收敛节点与状态流转能力。
2. 将当前前端运行 facade 落成真实后端接口，优先收口 `bootstrap` 与 `run snapshot`。
3. 在 phase-2 主线推进过程中继续补 `--config` 失败路径、更多 `release` / 放置场景以及 perception/execution 合同回归测试。
4. 按 `docs/specs/11-ubuntu-runbook.md` 在 Ubuntu 环境完成最小 CLI 验证，并把结果写回 `docs/records/TEST_REPORT.md`。
5. 并行跟踪前端联动、Ubuntu 实机验证与真实适配策略三类剩余前置项。
6. phase-2 数据支线当前只进入前置准备：先打通 `LeRobot` 真实采集链路、补实验记录模板与样本台账，再决定何时启动 `SmolVLA` 微调。

## Ubuntu 最小接手路径

- 安装项目依赖：`uv pip install -e . pytest`
- 运行测试入口：`uv run pytest -q`
- 运行统一入口：`uv run python -m embodied_agent.app --instruction "抓取桌面方块"`
- 导出最终状态：`uv run python -m embodied_agent.app --instruction "抓取桌面方块" --dump-final-state`
- 检查工具列表：`uv run python -m embodied_agent.app --instruction "抓取桌面方块" --list-tools`
- 当前 `--list-tools` 应返回 8 个工具：`describe_scene`、`get_image`、`get_robot_state`、`grasp`、`move_home`、`move_to`、`release`、`run_smolvla`
- 当前结论只适用于 mock CLI 可运行链路，不能视为前端联动、真实模型或真实硬件链路已验证
