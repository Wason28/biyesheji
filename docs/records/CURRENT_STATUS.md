# 当前状态

## 项目基准

- 唯一权威来源：`# 桌面级具身智能机器人感知-决策-执行一体化原型系统需求文档.md`
- docs 导航：`docs/README.md`
- 目标部署环境：`Ubuntu`

## 当前阶段判断

当前项目已完成第一阶段骨架实现，现进入“第一阶段完成，准备/开始推进第二阶段主线”的阶段；统一启动入口、P0 合同三批收敛与 44 个测试通过事实已构成当前 phase-2 主线推进基线，但 Ubuntu 实机、前端联动和真实链路外部验证尚未完成。

第二阶段主线完成的判断边界以“节点与状态流转能力稳定、合同与回归测试收敛”为准；Ubuntu 实机、前端联动、真实 `VLM/LLM/SmolVLA/机械臂` 链路和数据支线真实结果可以继续并行补齐，但不能被误写成端到端已完成。

## 当前里程碑

- 当前阶段：第一阶段完成，开始推进第二阶段主线
- 最近更新时间：2026-04-20

## 已完成

- 已建立 `src/embodied_agent/` 三层骨架目录：`perception/`、`decision/`、`execution/`
- 已建立共享配置与类型入口：`src/embodied_agent/shared/config.py`、`src/embodied_agent/shared/types.py`
- 已补齐决策层第一阶段主循环骨架，包括状态定义、节点编排、最小 MCP Client 与 LangGraph 主图
- 已补齐感知层 mock 能力，包括相机/机器人状态 mock、工具契约、错误类型与 MCP Server 包装
- 已补齐执行层 mock 能力，包括安全配置、参数校验、急停保护、LeRobot mock 适配器与 `run_smolvla`
- 已新增统一启动入口 `src/embodied_agent/app.py`，可串起配置加载、mock MCP 服务接线与决策图执行
- 已新增统一入口相关 9 个测试，覆盖单任务、多任务、配置加载、frontend 回退、未知工具、原子执行工具透传以及感知 / 执行失败闭环
- 已补 perception provider 工厂注册与 execution runtime 工厂注入测试
- 已沉淀前端接口占位，补齐最小 `bootstrap/config/run snapshot` 合同与状态字段约束，用于 phase-2 继续推进而不提前进入完整前端开发
- 已完成本地 Python 环境修复与依赖安装，当前仓库已具备本地验证条件
- 已执行 `python -m pytest tests -q`，结果通过
- 已执行 `uv run pytest -q`，结果通过，当前为 44 个测试全部通过
- 已执行 `uv run python -m embodied_agent.app --instruction "抓取桌面方块"`，统一入口可正常完成 mock 闭环
- 已执行 `uv run python -m embodied_agent.app --instruction "抓取桌面方块" --dump-final-state`，可输出最终状态 JSON
- 已执行 `uv run python -m embodied_agent.app --instruction "抓取桌面方块" --list-tools`，当前返回 8 个感知与执行工具

## 当前实现状态

- 决策层：可基于用户指令驱动 `task_planner -> scene_analyzer -> action_decider -> executor -> verifier` 固定流程，并输出 `selected_capability -> selected_action` 的决策结果
- 感知层：已进一步收敛 phase-2 感知合同，补齐结构化 `scene_observations` 字段校验、provider metadata 摘要、VLM 本地路径配置和更细的 provider 错误边界；mock 感知工具继续保持统一 envelope
- 执行层：可在 mock 运行时中执行 `move_to`、`move_home`、`grasp`、`release`、`run_smolvla`
- 启动层：已具备统一入口，可完成 `config loading -> mock MCP service wiring -> decision execution` 的最小装配，并暴露 8 个感知与执行工具
- 配置层：已支持从 YAML 加载 `decision`、`perception`、`execution`、`frontend` 四类配置，可从外部配置文件构建统一运行时，并在 `decision.max_iterations` 非正时回退到 `frontend.max_iterations`
- 前端联动占位：已具备最小前后端合同辅助函数，可导出配置面板快照、工具面板数据与运行态快照，且避免前端直接绑定完整决策内部状态
- 前端运行 facade：已在占位层基础上补 `FrontendRuntimeFacade`、`runtime_api`、`run_api` 与 `error` 组织形式，并额外暴露稳定的执行能力与安全展示字段，但仍未落成真实对外服务接口
- 测试层：已具备 43 个 pytest 测试通过事实，覆盖决策、感知、执行、统一入口装配、配置加载、frontend 回退、原子执行工具透传、失败闭环、provider 工厂注册与 execution runtime 工厂注入，以及第二阶段 capability/action 选择增强、感知接口边界补强、执行合同深化与前端接口占位 API / facade 占位

## 主要缺口

- 当前仍为 mock 骨架，尚未接入真实 VLM、真实 LLM、真实 `SmolVLA` 权重与真实机械臂
- 前端界面与决策层联动尚未开始
- 当前前端合同仍是占位层，尚未落为真实 HTTP/SSE/WebSocket 接口
- 已形成 Ubuntu mock CLI runbook，并完成当前 mock CLI 可运行链路验证；但 Ubuntu 实机安装、前端联动、真实模型与真实硬件链路仍未验证
- 端到端实体分拣测试、数据采集与微调流程尚未开始
- phase-2 数据支线当前仅完成前置梳理：已明确 LeRobot 数据采集目标为 50-100 组成功轨迹、格式为 `Parquet + 视频帧`，但真实采集链路、样本统计与训练产物仍未形成

## 第一阶段遗留项与第二阶段前置外部验证项

- Ubuntu 实机安装与最小 CLI 运行事实尚未落地
- 前端界面与决策层联动、前后端配置联动尚未开始
- 真实 `VLM` / `LLM` / `SmolVLA` 权重 / 真实机械臂链路尚未接入
- phase-2 数据支线当前仅完成前置梳理：已明确 LeRobot 数据采集目标为 50-100 组成功轨迹、格式为 `Parquet + 视频帧`，但真实采集链路、样本统计与训练产物仍未形成

## 当前阻塞项

- 缺少真实硬件与模型接入验证，因此当前闭环仅能证明骨架、统一入口装配方向与接口方向
- 尚未产出真实 MCP 联调与前后端联调记录
- 已形成 Ubuntu mock 运行与验证说明，并验证 `uv run pytest -q`、统一入口运行、最终状态导出与工具列表检查；这些可作为第二阶段主线推进基线，但 Ubuntu 实机安装、前端联动和真实链路前置项仍未完成

## 下一步建议

1. 以当前配置装配、合同收敛与 44 个测试通过事实为基线继续推进第二阶段主线实现。
2. 继续补 `--config` 失败路径、更多 perception/execution 合同回归测试，并跟踪 phase-2 新增 capability/action 路径的回归覆盖。
3. 开始设计前端到决策层的调用链路与状态回传方式。
4. 将当前前端运行 facade 继续收口为真实后端接口，优先打通 `bootstrap` 与 `run snapshot`。
5. 在第二阶段推进过程中并行跟踪 Ubuntu 实机安装、前端联动与真实适配策略三类前置项。
