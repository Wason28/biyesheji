# 开发记录

## 记录规则

每条记录至少包含：日期、负责 Agent、对应里程碑、修改模块、修改内容、对应需求点、风险和遗留问题、下一步建议、对应论文章节。

## 实际记录

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第二阶段当前事实持续同步
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / `docs/records/TEST_REPORT.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/specs/11-ubuntu-runbook.md`
- 修改内容：在第二阶段主线持续推进时继续同步 records；将当前全量测试口径更新到 `44 passed`，并在统一入口 CLI 恢复可运行后恢复 CURRENT_STATUS / HANDOFF / runbook 中关于命令行入口的正向事实描述，同时保留“外部链路未验证”的边界说明
- 对应需求点：第二阶段 records 需要持续反映最新测试基线、主线完成边界与未完成外部项，避免阶段判断和实际状态脱节
- 风险和遗留问题：当前全量测试虽已提升到 44 个通过，但仍主要证明 mock-first 合同、配置装配与占位接口稳定；Ubuntu 实机、前端联动与真实链路仍未验证，若后续不及时补齐，容易把“主线可推进”误读为“端到端已完成” 
- 下一步建议：继续补 phase-2 感知 / 执行 / 前端 facade 回归，并把 Ubuntu 实机验证结果与真实链路接入事实写回 records
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Frontend Agent
- 对应里程碑：第二阶段前端运行占位接口继续收敛
- 修改模块：`src/embodied_agent/app.py` / `src/embodied_agent/shared/types.py` / `src/embodied_agent/shared/__init__.py` / `src/embodied_agent/perception/errors.py` / `src/embodied_agent/perception/server.py` / `tests/test_app_phase1.py` / `docs/specs/07-frontend-spec.md` / `docs/records/*`
- 修改内容：在已有 `bootstrap/config/run/error` 占位基础上，继续收敛成更接近真实后端服务的 facade：新增 `FrontendRuntimeFacade`，补 `runtime_api` / `run_api` / `error` 组织方式，并把执行层展示能力与安全边界纳入 bootstrap；同时修复感知层阻塞当前 facade 回归的 `list_tools` 缺失与 `VLMResponseFormatError` 缺口，完成前端相关回归
- 对应需求点：第二阶段需要先把前端运行接口收口为稳定 facade，降低第三阶段接入真实服务时的返工成本
- 风险和遗留问题：当前 facade 仍是进程内辅助层，不是 HTTP/SSE/WebSocket 服务；不能把已存在的 facade 误写成真实前后端联调完成
- 下一步建议：在保持当前 facade 结构不变的前提下，后续优先把 `runtime_api` 与 `run_api` 映射到真实后端接口层
- 对应论文章节：系统架构设计、前端交互设计、系统实现与验证

### 2026-04-20

- 负责 Agent：Data & Model Agent
- 对应里程碑：第二阶段数据支线前置模板细化
- 修改模块：`docs/records/EXPERIMENTS.md` / `docs/records/FIGURE_ASSETS.md` / `docs/records/THESIS_PROGRESS.md` / `docs/records/HANDOFF.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：在既有“数据采集与微调前置检查”基础上，进一步补齐首条真实轨迹记录字段、样本台账字段、微调准备字段，以及首条轨迹落盘截图和样本台账示例截图等素材占位；保持所有内容仍为模板与待补项，不将真实采集、真实样本统计或微调结果写成已完成
- 对应需求点：第二阶段数据支线需要尽早具备可实填的记录模板，保证真实轨迹一旦开始采集即可被稳定留痕，并支撑论文与答辩材料回溯
- 风险和遗留问题：当前模板虽已可用，但尚无首条真实轨迹实填样本；若后续采集时仍未同步填表，records 与论文材料会继续滞后于真实进展
- 下一步建议：以首条真实轨迹为触发点，立即实填 `EXPERIMENTS.md` 相关字段并登记素材索引，再按样本批次补齐样本规模统计与训练记录
- 对应论文章节：系统实现与验证、实验设计与结果分析、论文材料组织

### 2026-04-20

- 负责 Agent：Implementation Agent
- 对应里程碑：第二阶段主线完成判断与第三阶段准备期切换
- 修改模块：`docs/specs/08-milestones-data-test.md` / `docs/records/MILESTONES.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/HANDOFF.md` / `docs/SESSION_START.md` / `docs/records/THESIS_PROGRESS.md`
- 修改内容：在第二阶段主线持续推进并达到“节点与状态流转能力稳定、合同与回归测试收敛”的边界后，将阶段口径切换到“第二阶段主线完成，进入第三阶段准备期”；同时保留 Ubuntu 实机、前端联动、真实适配链路与数据支线真实结果为并行外部项，不将其误写成端到端已完成
- 对应需求点：阶段完成必须既符合已定义边界，又保持对外表述不越过真实性边界
- 风险和遗留问题：当前 records 里仍保留多组阶段性测试数字（13 / 17 / 21 / 22 / 24 / 37 / 44），后续对外汇总时仍需说明“阶段演进回归数”和“当前全量通过数”的差异
- 下一步建议：以 44 个测试通过、统一入口稳定可运行和前端运行占位 facade 为第三阶段准备基线，继续推进真实前端接口与界面开发
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20
- 对应里程碑：第二阶段前的前端接口占位收敛
- 修改模块：`src/embodied_agent/shared/config.py` / `src/embodied_agent/shared/types.py` / `src/embodied_agent/execution/config.py` / `src/embodied_agent/app.py` / `tests/test_app_phase1.py` / `config/config.example.yaml` / `docs/specs/07-frontend-spec.md` / `docs/records/*`
- 修改内容：在不进入第三阶段完整前端开发的前提下，先沉淀最小前后端合同：补 `llm_local_path`、`vlm_local_path`、`home_pose` 等配置占位；新增前端 `bootstrap/config/run snapshot` 辅助函数与状态字段清单；补测试覆盖配置快照、工具面板占位和失败态错误回传；同步更新 frontend spec 与 records，明确前端不得直接绑定完整决策内部状态
- 对应需求点：前端需承载任务输入、模型配置、状态监控和工具面板；在 phase-2 继续推进时应先稳定调用链路与展示合同，减少后续返工
- 风险和遗留问题：当前仍未提供真实 HTTP/SSE/WebSocket 服务接口；前端合同目前以进程内辅助函数形式存在，后续仍需在后端入口层落成真实对外接口
- 下一步建议：围绕当前 `bootstrap/config/run snapshot` 结构实现真实后端接口，并把前端刷新与运行态推送统一到单一适配层
- 对应论文章节：系统架构设计、决策层 Agent 设计、前端交互设计、系统实现与验证

### 2026-04-20

- 负责 Agent：Implementation Agent
- 对应里程碑：第二阶段感知接口接线恢复与主线继续推进
- 修改模块：`src/embodied_agent/perception/server.py` / `tests/test_perception_phase1.py` / `tests/test_app_phase1.py` / `docs/records/*`
- 修改内容：修复 perception server 在 phase2 接口补强中的初始化接线，恢复 `PerceptionRuntimeConfig + adapter factory + provider factory` 路径；重新跑 perception/app 相关回归并通过，随后全量 `uv run pytest -q` 提升到 24 个通过；同步更新阶段记录与测试口径
- 对应需求点：第二阶段主线推进期间，感知层必须在不破坏最小合同的前提下持续收敛到可替换的接口与配置边界
- 风险和遗留问题：当前 24 个测试仍然主要证明 mock CLI、统一入口与跨层合同稳定，不代表真实 Ubuntu、真实硬件或真实模型链路已验证；Documentation 线需要继续跟进更晚的测试口径
- 下一步建议：继续推进 phase2 感知 / 执行接口补强与回归测试，并同步把最新全量通过数写回 records
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20
- 对应里程碑：第二阶段数据支线前置收敛
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / `docs/records/EXPERIMENTS.md` / `docs/records/FIGURE_ASSETS.md` / `docs/records/THESIS_PROGRESS.md`
- 修改内容：补充 phase-2 数据支线记录口径；明确当前仅完成 `LeRobot` 数据采集与 `SmolVLA` 微调前置梳理，补充数据采集目标、样本台账、素材清单与训练记录待补项，同时明确真实采集链路、样本统计和训练产物尚未形成，不将未验证链路写成已完成事实
- 对应需求点：第二阶段支线需要提前收敛数据采集与模型训练前提，但论文与 records 必须严格区分“已验证事实”和“待启动前置”
- 风险和遗留问题：当前仍无真实 `LeRobot` 采集验证、真实样本规模统计和 `SmolVLA` 训练结果；若后续不及时建立样本台账和实验留痕，第二阶段后半程将难以支撑论文与实验回溯
- 下一步建议：先完成 1 条真实示教轨迹落盘验证与记录模板实填，再逐步扩展到 50-100 组成功轨迹，并在形成真实数据后再启动 `SmolVLA` 微调
- 对应论文章节：系统实现与验证、实验设计与结果分析、论文材料组织

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第二阶段当前事实持续同步
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / `docs/records/TEST_REPORT.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：在第二阶段主线持续推进时继续同步 records；将当前全量测试口径更新到 `38 passed`，并补记统一入口 CLI 当前因 `_build_parser` 缺失而不可运行的事实，避免继续沿用“统一入口已稳定可运行”的旧口径
- 对应需求点：第二阶段 records 需要持续反映最新测试基线、主线完成边界与未完成外部项，避免阶段判断和实际状态脱节
- 风险和遗留问题：当前全量测试虽已提升到 38 个通过，但统一入口 CLI 暂时不可运行；Ubuntu 实机、前端联动与真实链路仍未验证，若不及时修复 CLI 并继续收敛外部项，后续交接会出现“测试通过但入口不可用”的认知偏差
- 下一步建议：优先修复统一入口 CLI，再继续补 phase-2 接口与前端占位回归，并把最新通过数同步到 `TEST_REPORT.md`
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第二阶段启动记录同步
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/MILESTONES.md` / `docs/records/HANDOFF.md` / `docs/records/DEVELOPMENT_LOG.md`
- 修改内容：将阶段口径从“第二阶段已启动”收敛为“第一阶段完成，准备/开始推进第二阶段主线”；以统一入口可运行、P0 合同三批收敛完成、`uv run pytest -q` 为 37 个通过作为当前 phase-2 推进基线，并沉淀第一阶段遗留项与第二阶段前置外部验证项
- 对应需求点：阶段切换时 records 必须反映当前里程碑、基线事实和剩余前置项，保证后续实现、测试与交接口径一致
- 风险和遗留问题：当前第二阶段推进基线仍以 mock CLI、统一入口和合同回归为主；Ubuntu 实机、前端联动与真实链路尚未验证，后续若不及时补齐，可能影响 phase-2 后半程联调节奏
- 下一步建议：围绕 phase-2 主线实现持续更新当前状态、回归测试和里程碑记录，并把剩余前置项拆分为可追踪的独立事实
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段骨架实现后的阶段记录同步
- 修改模块：`docs/records/CURRENT_STATUS.md` / `docs/records/TEST_REPORT.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/records/MILESTONES.md`
- 修改内容：基于最近一轮 P0 合同收敛与测试扩展，同步当前 records 口径；明确 Ubuntu runbook 已落地，测试规模从 10 / 13 / 17 逐步扩展到当前 21 个通过，并补齐 phase-2 启动前仍未完成的前置项说明
- 对应需求点：阶段记录需随实现与测试推进保持一致，确保当前状态、测试事实、里程碑判断和交接内容可回溯
- 风险和遗留问题：records 现已统一到当前 21 个通过，但历史 6 / 7 / 10 / 13 / 17 / 19 / 21 的阶段性测试口径仍并存于记录链路中，后续若对外输出汇总，需要额外说明“阶段演进”与“当前全量”是两种不同统计口径
- 下一步建议：继续把 Ubuntu 实机验证、前端联动与真实适配前置项按 phase-2 启动门槛拆分记录
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段骨架实现后的 Ubuntu 运行说明落地
- 修改模块：`docs/specs/11-ubuntu-runbook.md` / `docs/records/TEST_REPORT.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/DEVELOPMENT_LOG.md` / `docs/records/HANDOFF.md` / `docs/README.md` / `docs/specs/09-documentation-handoff.md`
- 修改内容：新增 Ubuntu 运行与验证说明，收敛项目级安装基线、配置入口、统一启动入口命令与当前已验证的 mock CLI 链路；同步记录 `uv run pytest -q`、统一入口运行、最终状态导出与工具列表检查事实，并在后续代码与测试扩展后继续同步修正 records 口径至当前 19 个测试、8 个统一入口工具、frontend 回退与失败闭环验证事实
- 对应需求点：项目需面向 `Ubuntu` 部署目标保持可运行、可验证、可交接；文档需与当前实现和验证事实保持一致
- 风险和遗留问题：当前 runbook 与验证事实只覆盖 mock CLI 级链路，不代表 Ubuntu 实机安装、前端联动、真实 `LeRobot`、真实 `SmolVLA` 权重或真实硬件链路已验证
- 下一步建议：继续补 Ubuntu 实机安装、`--config` 配置路径、更多 release / 放置场景、失败路径以及前后端联调验证
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范


### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`src/embodied_agent/shared`
- 修改内容：建立共享配置与类型基础设施，新增 `shared/config.py` 与 `shared/types.py`，用于承载 decision、perception、execution、frontend 四类配置以及跨层共享数据结构
- 对应需求点：统一配置管理、模块解耦、后续真实模型与硬件接入的公共基础
- 风险和遗留问题：当前配置加载与默认值已经形成，但尚未补齐生产级配置校验、环境变量接入和多环境切换
- 下一步建议：在统一启动入口与接口层接入 `AppConfig`，避免各子模块自行读取配置
- 对应论文章节：系统总体架构设计、系统配置与运行时设计

### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`src/embodied_agent/decision`
- 修改内容：建立决策层第一阶段骨架，补齐状态定义、节点函数、最小 MCP Client 与 LangGraph 主图，形成 `task_planner -> scene_analyzer -> action_decider -> executor -> verifier` 固定流程
- 对应需求点：决策层 Agent 主流程、任务拆解、状态流转、执行结果验证
- 风险和遗留问题：当前节点逻辑以 mock 流转为主，尚未接入真实大模型推理与复杂任务规划策略
- 下一步建议：补统一入口、结构化日志和更细粒度状态观测字段，为第二阶段扩展做准备
- 对应论文章节：决策层 Agent 设计、工作流编排设计

### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`src/embodied_agent/perception`
- 修改内容：建立感知层 mock 能力，新增相机与机器人状态 mock、感知契约、错误类型、provider 封装与 MCP Server，对外提供可调用的 mock 感知工具
- 对应需求点：场景感知输入、图像获取、结构化观察结果输出、错误恢复基础
- 风险和遗留问题：当前感知结果为固定 mock 输出，未接入真实图像流与 VLM 推理链路
- 下一步建议：在接口不变前提下，引入真实图像输入和 provider 适配层抽象
- 对应论文章节：感知层设计、感知结果结构化表示

### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`src/embodied_agent/execution`
- 修改内容：建立执行层 mock 运行时，补齐安全配置、参数校验、急停保护、LeRobot mock 适配器、Mock MCP Server 与 `run_smolvla` 工具编排
- 对应需求点：执行层原子动作、VLA 推理入口、安全约束、错误回传
- 风险和遗留问题：当前执行成功只验证 mock 计划执行与安全链路，不代表真实机械臂动作可用
- 下一步建议：在保持工具签名稳定的前提下替换底层 mock 适配器，并补充更完整的异常场景测试
- 对应论文章节：执行层设计、安全机制设计、VLA 调用链路设计

### 2026-04-20

- 负责 Agent：Orchestrator / Decision / QA / Documentation / Thesis Agent Team
- 对应里程碑：第一阶段骨架实现后的统一入口与最小集成验证
- 修改模块：`src/embodied_agent/app.py` / `tests/test_app_phase1.py` / `docs/`
- 修改内容：新增统一启动入口 `src/embodied_agent/app.py`，以薄装配层形式完成 `config loading -> mock MCP service wiring -> decision execution`；通过 `PerceptionMCPServer`、`MockMCPServer` 与 `MinimalMCPClient(auto_mock=False)` 适配现有决策图；新增 `tests/test_app_phase1.py` 验证统一入口装配后的单任务 mock 闭环；执行 `uv run pytest -q` 与 `uv run python -m embodied_agent.app --instruction "抓取桌面方块"` 均通过；同步更新运行说明、状态记录和文档口径
- 对应需求点：系统应具备最小可运行的三层闭环装配入口、跨层调用验证事实和可交接的运行方式
- 风险和遗留问题：当前统一入口仍基于 in-process mock MCP facade，不代表真实 MCP 传输、前端联动、Ubuntu 部署或真实硬件链路已验证；`uv.lock` 是否纳入版本管理仍未决策
- 下一步建议：补失败路径与多任务路径的跨层集成测试，继续完善 Ubuntu 运行文档，并为真实模型/硬件替换保持接口稳定
- 对应论文章节：系统架构设计、决策层 Agent 设计、系统实现与验证

### 2026-04-20

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现后的环境验证与文档对齐
- 修改模块：本地运行环境 / `tests/` / `docs/`
- 修改内容：修复本地 `python` / `python3` 命令指向错误的问题，建立可用的 `Python 3.12.12` 本地入口；创建 `.venv` 并使用 `uv` 安装项目依赖；执行 `uv run pytest -q`，结果 6 个测试全部通过；同步修正 `README.md`、`docs/reference/`、`docs/specs/`、`docs/records/` 中与当前实现不一致的状态与接口描述，并补充“工作完成后的文档维护要求”
- 对应需求点：项目应具备可验证的第一阶段骨架基线、文档与实现一致性、可交接与可复现性
- 风险和遗留问题：当前测试仍以 mock 单元测试为主，尚未覆盖统一启动入口、跨层集成、前端联动与真实硬件场景；仓库当前新增 `uv.lock`，是否纳入版本管理尚未决策
- 下一步建议：优先建立统一启动入口，串起配置加载、决策图执行和 mock MCP 服务，并补跨层集成测试
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Documentation / Thesis Agent
- 对应里程碑：第一阶段完成后的文档体系重构
- 修改模块：`README.md` / `DEVELOPMENT_SPEC.md` / `docs/specs/` / `docs/records/`
- 修改内容：以根需求文档为唯一权威来源重构 `docs/`；保留 `docs/specs/` 作为实现规范层，删除重复的 `docs/reference/`，并重写导航、状态、交接、里程碑、论文与实验材料相关文档，确保论文材料与项目记录口径对齐
- 对应需求点：文档体系应可交接、可回溯，并与需求文档和当前实现保持一致
- 风险和遗留问题：`docs/records/TEST_REPORT.md`、`docs/records/MILESTONES.md`、`docs/records/HANDOFF.md` 仍保留 `6 个测试` 与 `7 个测试` 的历史口径差异，后续需要在核实后统一说明；`.claude/` 与 `uv.lock` 是否纳入版本管理仍未决策
- 下一步建议：核实测试总数口径后补充勘误说明，并继续保持 `specs`、`records` 与后续实现同步更新
- 对应论文章节：系统架构设计、系统实现与验证、论文材料组织与答辩准备

### 2026-04-20

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段骨架实现后的 Ubuntu 运行文档补齐
- 修改模块：`docs/specs/11-ubuntu-runbook.md` / `docs/records/TEST_REPORT.md` / `docs/records/CURRENT_STATUS.md` / `docs/records/HANDOFF.md` / `docs/README.md` / `DEVELOPMENT_SPEC.md` / `docs/specs/09-documentation-handoff.md`
- 修改内容：新增 Ubuntu 下 mock CLI 最小运行规范文档，并同步补齐测试报告、当前状态、交接入口和文档索引；明确当前只覆盖已验证的 mock CLI 命令面，不把前端联动、真实 LeRobot、真实机械臂、真实 SmolVLA 权重和真实实验写成已验证事实
- 对应需求点：目标部署环境为 Ubuntu；系统应具备可交接、可回溯、可验证的运行路径与文档基线
- 风险和遗留问题：当前仍无 Ubuntu 实机安装验证事实；前端联动、真实 MCP、真实硬件和真实实验链路仍未覆盖；records 中历史 6/7/18 测试口径差异仍待后续在需要时统一勘误说明
- 下一步建议：按 `docs/specs/11-ubuntu-runbook.md` 在 Ubuntu 环境执行最小 CLI 验证，并将结果、截图和失败项写回 `docs/records/TEST_REPORT.md`、`docs/records/FIGURE_ASSETS.md`
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-20

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现后的 P0 合同收敛与 focused tests 回归
- 修改模块：`src/embodied_agent/shared/types.py` / `src/embodied_agent/decision/*` / `src/embodied_agent/perception/*` / `src/embodied_agent/execution/*` / `tests/*` / `docs/records/*`
- 修改内容：继续完成第二阶段前的 P0 工作，补 capability contract 雏形、统一原子执行工具暴露、统一 `RobotState/ee_pose` 结构、统一 perception / execution envelope，并补统一入口的多任务、配置路径、未知工具失败、执行失败闭环、感知失败闭环，以及 perception focused tests；继续补 perception provider 工厂注册与 execution runtime 工厂注入测试；执行 focused tests 后为 17 个通过，随后全量 `uv run pytest -q` 为 21 个通过
- 对应需求点：第二阶段前需先固化接口定义、补足跨层集成入口与验证事实，确保 mock 到真实适配前的合同稳定
- 风险和遗留问题：当前仍未完成 Ubuntu 实机安装验证；真实 provider / adapter 虽开始支持可替换装配，但真实 LeRobot、真实 SmolVLA、真实 VLM/LLM 仍未接入；records 中历史 6/7 测试口径差异仍待后续勘误说明
- 下一步建议：继续补 `--config` 失败路径与更多 perception/execution 合同回归测试，并把 Ubuntu 实机验证结果写回 records
- 对应论文章节：系统实现与验证、测试设计与结果分析、工程化与交接规范

### 2026-04-19

- 负责 Agent：Implementation / Documentation Agent
- 对应里程碑：第一阶段骨架实现
- 修改模块：`tests/`
- 修改内容：新增 6 个 pytest 测试，分别验证决策层单任务/多任务循环、感知层成功/失败路径、执行层 `run_smolvla` 成功路径与 `move_to` 校验失败急停路径；执行 `python -m pytest tests -q` 结果通过
- 对应需求点：第一阶段最小可验证闭环、接口稳定性、失败链路保护
- 风险和遗留问题：当前测试仍以单元测试为主，尚未覆盖跨层集成、前端联动与真实硬件场景
- 下一步建议：以现有 6 个测试为基线继续补充集成测试和接口契约测试
- 对应论文章节：系统实现与验证、测试设计与结果分析

### 2026-04-19

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段启动前准备
- 修改模块：文档体系 / spec 结构 / 交接路径
- 修改内容：将原单文件 spec 拆分为 `docs/specs/` 多文件规范，并建立主索引 `DEVELOPMENT_SPEC.md`
- 对应需求点：系统架构、模块职责、里程碑、论文映射、交接规范
- 风险和遗留问题：文档已完善，但代码尚未开始实现
- 下一步建议：开始搭建 LangGraph + MCP 骨架代码
- 对应论文章节：系统架构设计、决策层 Agent 设计

### 2026-04-19

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段启动前准备
- 修改模块：docs 目录结构
- 修改内容：将 `docs/` 重构为 `specs/`、`reference/`、`records/` 三层，并修正全部路径引用
- 对应需求点：交接规范、文档维护、论文材料管理
- 风险和遗留问题：如果后续代码目录变化较大，需要同步调整参考文档中的路径和入口说明
- 下一步建议：补齐首版参考文档和记录文档，避免新 Agent 接手时依旧面对空模板
- 对应论文章节：系统架构设计、系统实现与验证

### 2026-04-19

- 负责 Agent：Documentation Agent
- 对应里程碑：第一阶段启动前准备
- 修改模块：reference / records 文档实填
- 修改内容：将架构、接口、Git、论文大纲写成稳定参考；将状态、里程碑、测试、实验、交接写成首版可接手内容
- 对应需求点：全生命周期开发记录、测试验证、论文写作并行推进
- 风险和遗留问题：当前记录基于文档建设成果，尚无代码与实验事实支撑
- 下一步建议：代码启动后第一时间把真实实现与运行结果写回 records 文档
- 对应论文章节：系统实现与验证、总结与展望
