# 07 前端详细规范

## 1. 职责

前端负责：
- 任务输入
- 模型选择
- 状态监控
- MCP 工具扩展面板
- 个性化参数设置

## 2. 功能模块

### 2.1 任务交互区

必须包含：
- 用户自然语言输入框
- 当前任务显示
- 场景描述显示
- 动作日志显示
- 摄像头实时视频流展示

### 2.2 模型配置面板

必须包含：
- 决策 `LLM` 选择：`MiniMax / OpenAI / Ollama`
- 感知 `VLM` 选择：`MiniMax MCP Vision / OpenAI GPT-4o / Ollama Vision`
- API Key 输入
- 本地模型路径输入能力
- 执行层当前模型展示：`SmolVLA`

### 2.3 MCP 工具扩展面板

必须包含：
- 已注册工具列表展示
- 手动刷新工具列表能力

### 2.4 个性化设置

必须包含：
- 机械臂初始位置校准
- 执行速度缩放系数
- 最大闭环迭代次数

## 3. 辅助 Agent

### 3.1 模型部署助手 Agent

职责：
- 引导用户完成 API Key 配置或本地模型路径指定

### 3.2 系统载入助手 Agent

职责：
- 启动时检测可用模型
- 在前端自动填充可选模型列表

## 4. 前端边界

- 前端只负责交互、配置和状态展示。
- 前端不得承载核心决策逻辑。
- 执行层模型只展示，不允许替换。

## 5. 体验要求

- 当前状态必须可视化。
- 模型切换结果必须明确反馈。
- 工具刷新结果必须可见。
- 错误信息必须可提示给用户。

## 6. 第二阶段前置接口占位

在不进入第三阶段完整前端开发前，后端至少需要先沉淀以下最小接口占位和状态字段约束：

- `bootstrap` 占位载荷必须至少包含：
  - 当前配置快照：`decision / perception / execution / frontend`
  - 执行层展示模型：`SmolVLA`
  - 已注册工具列表
  - 运行态快照字段清单
- 配置快照最少覆盖：
  - `decision.provider / model / api_key_configured / local_path`
  - `perception.provider / model / api_key_configured / local_path`
  - `execution.display_name / model_path / home_pose / mutable`
  - `frontend.port / max_iterations / speed_scale`
- 运行态快照最少覆盖：
  - `run_id`
  - `status`
  - `current_node`
  - `current_task`
  - `scene_description`
  - `action_result`
  - `iteration_count`
  - `max_iterations`
  - `current_image`
  - `robot_state`
  - `last_execution`
  - `logs`
  - `error`

约束：
- 前端消费的运行态快照必须是显式适配后的展示合同，不直接暴露完整决策内部状态。
- 配置载荷默认不回传明文 API Key，只返回空字符串和 `api_key_configured` 标记。
- 工具面板依赖的工具列表合同必须兼容感知层与执行层当前已注册工具，并支持后续手动刷新。
- 第二阶段可继续把 `bootstrap / config / run / error` 组织成接近真实后端服务的 facade，但不得把该 facade 写成完整前端服务或真实 HTTP/SSE/WebSocket 接口已实现。
- 若需要补执行层展示信息，只能补稳定展示合同，如 `execution_capabilities` 与 `execution_safety`，不得让前端直接依赖执行层内部实现对象。

## 7. 第三阶段前端联调最小验收清单

### 7.1 联调范围

第三阶段前端骨架联调只验证“当前最小前端是否能稳定消费既有 backend 合同”，不验证真实硬件、真实视频流、生产级 SSE / WebSocket、历史记录管理、多 run 并发治理或断线自动重连策略。

本轮只测：
- 页面初始化对 `bootstrap / config / tools` 的最小消费
- 运行提交对 `POST /api/v1/runtime/runs` 的最小接线
- 运行中 UI 对 `snapshot_url / events_url` 的最小消费
- 事件追更对 `version / terminal / run.status / run.error / logs` 的最小展示
- 失败态、请求失败态与空态/加载态的基础可见反馈

本轮明确不测：
- 真实摄像头流、真实机械臂、真实 `SmolVLA` 或真实 `VLM / LLM`
- 生产级长连接保活、自动重连、心跳、丢包恢复、跨页会话恢复
- 多 run 并发标签页管理、历史 run 列表、主动取消、持久化回放
- UI 美术细节、复杂动效、性能压测与浏览器兼容矩阵

### 7.2 验收前提

- 前端骨架只依赖当前稳定合同：`GET /api/v1/runtime/bootstrap`、`GET /api/v1/runtime/config`、`GET /api/v1/runtime/tools`、`POST /api/v1/runtime/runs`、`GET /api/v1/runtime/runs/{run_id}`、`GET /api/v1/runtime/runs/{run_id}/events`
- 前端运行态只消费显式展示字段：`run_id / status / current_node / current_task / scene_description / action_result / iteration_count / max_iterations / logs / error`
- 联调环境允许使用当前 mock-first backend；不得把本轮通过误写为真实前后端闭环完成

### 7.3 最小验收项

| 编号 | 场景 | 触发方式 | 最小通过标准 |
| --- | --- | --- | --- |
| FE-A01 | 加载态：页面首屏初始化 | 首次进入前端骨架，`bootstrap / config / tools` 仍在请求中 | 页面出现明确加载提示；任务提交入口暂不可重复触发；未出现空白页、未渲染 `undefined/null` 文案 |
| FE-A02 | 错误态：初始化请求失败 | 任一初始化请求返回非 2xx、超时或网络失败 | 页面出现统一错误提示和可见重试入口；错误信息不阻塞页面刷新；用户能判断当前是“未加载成功”而非“无数据” |
| FE-A03 | run 提交：正常受理 | 输入非空指令后触发 `POST /api/v1/runtime/runs` | 前端正确发送 `instruction`，如有自定义 `run_id` 则一并发送；收到 `202` 后保存 `run_id / snapshot_url / events_url`；UI 立即切到运行中态 |
| FE-A04 | run 提交：提交中保护 | 用户连续点击提交或请求尚未返回 | 提交按钮进入提交中态或禁用；同一轮提交不会在前端生成重复请求风暴；页面保留本次指令上下文 |
| FE-A05 | events 追更：running 首次呈现 | `runs` 接口返回 accepted payload 后开始消费事件流 | 页面先用 accepted payload 或首个事件展示 `status=running`；至少能看到 `run_id`、运行状态和基础日志/节点占位 |
| FE-A06 | events 追更：终态收口 | 事件流返回 `terminal=true` 且 `run.status=completed` | 页面停止加载态；终态信息稳定停留；最终状态、日志和关键字段不被后续空刷新覆盖 |
| FE-A07 | 失败态：业务失败回显 | 终态事件或快照中 `run.status=failed`，且 `run.error` 非空 | 页面显示失败状态标识、错误文案和已产生的日志；提交控件恢复可用；不会一直卡在“运行中” |
| FE-A08 | 错误态：运行请求失败 | `POST /api/v1/runtime/runs` 返回 `4xx/5xx`，如重复 `run_id` 或服务不可用 | 页面显示接口错误文案；不创建伪 run 卡片；用户可重新提交；重复 `run_id` 与通用服务错误至少能区分 |
| FE-A09 | events 追更：非法或无事件结果兜底 | `events` 请求失败、返回空列表，或快照查询失败 | 页面出现“事件获取失败/暂无更新”的可见提示，并保留最近一次有效状态；不得把已有状态清空成初始态 |

### 7.4 核心字段核对

前端骨架最少需要在联调时核对以下字段是否被正确消费并可见：
- 初始化阶段：`config.execution.display_name`、`tools[].name`、`status_fields`
- run 受理阶段：`run_id`、`status`、`snapshot_url`、`events_url`
- 事件阶段：`version`、`terminal`、`run.status`、`run.current_node`、`run.logs`
- 失败阶段：`run.status=failed`、`run.error`

### 7.5 退出标准

- 上述 9 个最小验收项全部通过，且不存在阻塞主线的 P0 问题
- 页面已证明能区分加载态、初始化错误态、提交中、运行中、完成态和失败态
- 前端骨架已证明能消费当前最小合同，但结论仍限定为“第三阶段最小联调骨架通过”，不能外推为完整前端工程或生产级流式能力通过
- 若当前仅完成代码审查与 `npm run build`，尚未形成真实浏览器联调记录，则只能写成“代码接线通过 / 浏览器留痕待补”，不能直接宣告本节退出标准全部达成

### 7.6 当前实现评估口径（2026-04-20）

当前仓库已经具备前端工程代码与构建证据，因此第三阶段最小联调口径需要拆成两层判定：

- 代码 / 构建口径：检查 `App.tsx`、`store/workbench.ts`、`components/*`、`lib/api.ts`、`lib/sse.ts` 是否已经把 9 个验收项接到既有 backend 合同，并确认 `npm run build` 通过
- 浏览器 / 联调留痕口径：检查是否已有真实页面加载、run 提交、事件追更、终态收口的人工记录或自动化证据

当前阶段允许写入文档的事实：

| 验收项 | 当前代码依据 | 当前判定 |
| --- | --- | --- |
| FE-A01 | `initialize()` 进入 `loading`，`ControlPanel` 展示“初始化中”且禁用提交 | 通过（代码级） |
| FE-A02 | 初始化失败时统一写入 `latestError`，页面展示错误提示与“重试初始化”按钮 | 通过（代码级） |
| FE-A03 | `startRun()` 调用 `POST /api/v1/runtime/runs`，保存 `run_id / snapshot_url / events_url` 并立即切换运行态 | 通过（代码级） |
| FE-A04 | `runStatus=loading` 时提交按钮禁用，避免重复点击风暴 | 通过（代码级） |
| FE-A05 | accepted payload 先写入 `snapshot`，随后连接 `events_url` 并展示运行中信息 | 通过（代码级） |
| FE-A06 | 收到 `terminal=true` 后关闭订阅、保留终态快照并更新事件提示 | 通过（代码级） |
| FE-A07 | `run.status=failed` 与 `run.error` 会展示在运行态/事件面板，提交按钮恢复可用 | 通过（代码级） |
| FE-A08 | `RuntimeRequestError` 统一承接 `4xx/5xx`，页面显示请求失败文案且不创建本轮 accepted run | 通过（代码级） |
| FE-A09 | `syncRunSnapshot()` 与 `source.onerror` 提供事件异常兜底，空事件列表显示空态提示并保留最近快照 | 通过（代码级） |

当前阶段结论：

- 按代码 / 构建口径，`FE-A01 ~ FE-A09` 已具备 9/9 项实现落点，可以写成“第三阶段最小联调骨架代码接线通过”
- 按浏览器 / 联调留痕口径，当前仍缺少真实页面实测记录，因此不能写成“第三阶段前后端联调完成”
