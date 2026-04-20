# 当前状态

## 项目基准

- 唯一权威来源：`# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- docs 导航：`docs/README.md`
- 目标部署环境：`Ubuntu`

## 当前阶段判断

当前项目已完成第一阶段骨架实现，并具备统一启动入口下的最小 mock 闭环验证基础；当前重点是稳定模块边界、补充验证、为真实适配和前端联动做准备。

## 当前里程碑

- 当前阶段：第一阶段骨架实现已完成
- 最近更新时间：2026-04-20

## 已完成

- 已建立 `src/embodied_agent/` 三层骨架目录：`perception/`、`decision/`、`execution/`
- 已建立共享配置与类型入口：`src/embodied_agent/shared/config.py`、`src/embodied_agent/shared/types.py`
- 已补齐决策层第一阶段主循环骨架，包括状态定义、节点编排、最小 MCP Client 与 LangGraph 主图
- 已补齐感知层 mock 能力，包括相机/机器人状态 mock、工具契约、错误类型与 MCP Server 包装
- 已补齐执行层 mock 能力，包括安全配置、参数校验、急停保护、LeRobot mock 适配器与 `run_smolvla`
- 已新增统一启动入口 `src/embodied_agent/app.py`，可串起配置加载、mock MCP 服务接线与决策图执行
- 已新增 1 个跨层最小集成测试，验证统一入口装配后的 mock 闭环调用
- 已完成本地 Python 环境修复与依赖安装，当前仓库已具备本地验证条件
- 已执行 `python -m pytest tests -q`，结果通过
- 已执行 `uv run pytest -q`，结果通过
- 已执行 `uv run python -m embodied_agent.app --instruction "抓取桌面方块"`，统一入口可正常完成 mock 闭环

## 当前实现状态

- 决策层：可基于用户指令驱动 `task_planner -> scene_analyzer -> action_decider -> executor -> verifier` 固定流程
- 感知层：可通过 mock 相机与 mock 机器人状态生成场景描述，并返回统一错误载荷
- 执行层：可在 mock 运行时中执行 `move_to`、`move_home`、`grasp`、`release`、`run_smolvla`
- 启动层：已具备统一入口，可完成 `config loading -> mock MCP service wiring -> decision execution` 的最小装配
- 配置层：已支持从 YAML 加载 `decision`、`perception`、`execution`、`frontend` 四类配置
- 测试层：已具备第一批代码级测试事实与最小跨层集成验证事实

## 主要缺口

- 当前仍为 mock 骨架，尚未接入真实 VLM、真实 LLM、真实 `SmolVLA` 权重与真实机械臂
- 前端界面与决策层联动尚未开始
- Ubuntu 环境下的安装、部署、运行说明尚未形成已验证文档
- 端到端实体分拣测试、数据采集与微调流程尚未开始

## 当前阻塞项

- 缺少真实硬件与模型接入验证，因此当前闭环仅能证明骨架、统一入口装配方向与接口方向
- 尚未产出真实 MCP 联调与前后端联调记录
- Ubuntu 环境下的统一入口运行与部署说明尚未形成已验证文档

## 下一步建议

1. 在现有统一入口基础上继续补跨层集成测试与失败路径验证。
2. 将 mock MCP 和工具输出进一步对齐后续真实接口契约。
3. 开始设计前端到决策层的调用链路与状态回传方式。
4. 准备 Ubuntu 环境安装、运行与验证文档，支撑下一阶段联调。
