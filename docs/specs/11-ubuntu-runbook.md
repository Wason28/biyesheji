# 11 Ubuntu 运行与验证说明

## 1. 文档目标

本文档用于沉淀面向 `Ubuntu` 目标环境的最小安装、运行与验证基线。
当前只覆盖第一阶段已实现的 mock CLI 可运行链路，不扩展未验证的真实硬件、真实 `LeRobot`、真实 `SmolVLA` 权重部署细节。

## 2. 适用范围

本文档当前适用于：
- 项目级依赖安装后的最小运行验证
- 统一启动入口 `embodied_agent.app` 的 mock 闭环验证
- 统一入口最终状态导出与工具列表检查

本文档当前不覆盖：
- 前端界面启动、状态监控与交互验证
- 前后端配置联动验证
- 真实 `MCP` 传输链路
- 真实 `LeRobot` 接入
- 真实机械臂、真实 `SmolVLA` 权重与实物分拣验证

## 3. 环境基线

- 目标部署环境：`Ubuntu`
- Python 基线：`>=3.11`
- 包管理与运行入口：`uv`
- 项目根目录：`E:\lwj\biyesheji`

说明：
- 当前仓库已验证的命令面以 `uv run` 为准。
- 本文档只记录项目级依赖与运行命令，不展开 `apt`、驱动、CUDA 或机器人系统安装步骤。

## 4. 项目级安装基线

在项目根目录下准备可用的 Python 与 `uv` 后，使用以下命令安装项目依赖：

- `uv pip install -e . pytest`

说明：
- 当前仓库已存在 `.venv` 并具备本地运行条件。
- 本节只定义项目级安装方式，不将其表述为 Ubuntu 实机已验证事实。

## 5. 配置入口

- 示例配置文件：`config/config.example.yaml`
- 当前配置包含：`decision`、`perception`、`execution`、`frontend`
- 统一入口支持可选参数：`--config`

说明：
- 当前 runbook 默认以仓库现有配置与默认装配路径为准。
- 本轮未追加外部配置文件路径的独立验证事实。

## 6. 最小运行与验证路径

### 6.1 测试入口

执行：
- `uv run pytest -q`

当前事实：
- 命令通过
- 输出结果为 `44 passed`

### 6.2 统一启动入口

执行：
- `uv run python -m embodied_agent.app --instruction "抓取桌面方块"`

当前事实：
- 命令通过
- 默认输出为 `全部任务完成`

### 6.3 导出最终状态

执行：
- `uv run python -m embodied_agent.app --instruction "抓取桌面方块" --dump-final-state`

当前事实：
- 命令通过
- 可输出最终状态 JSON
- 当前结果包含 `action_result: success` 与 `last_node_result.message: 全部任务完成`

### 6.4 检查统一入口工具列表

执行：
- `uv run python -m embodied_agent.app --instruction "抓取桌面方块" --list-tools`

当前事实：
- 命令通过
- 当前返回 8 个工具：`describe_scene`、`get_image`、`get_robot_state`、`grasp`、`move_home`、`move_to`、`release`、`run_smolvla`

说明：
- 当前参数解析要求传入 `--instruction`，即使同时使用 `--list-tools`。

## 6.5 本地最小前后端闭环（mock-first）

目标：
- 固化当前 `frontend + backend/http + mock runtime` 的本地可重复闭环，作为第四阶段前的演示与回归基线。

启动：
- 后端：`uv run python -m embodied_agent.backend.http --host 127.0.0.1 --port 7861`
- 前端：`npm --prefix "/e/lwj/biyesheji/frontend" run dev -- --host 127.0.0.1 --port 5173`

验证：
- `uv run python scripts/phase4_local_e2e_smoke.py`

最小通过标准：
- 能拉取 `bootstrap / config / tools`
- 能提交 `PUT /config` 并看到配置回写生效
- 能提交 `POST /runs` 并通过 `snapshot_url` 看到终态
- 能从 `events_url` 读取到 `snapshot` 事件
- 能输出 smoke 结果 JSON 到 `docs/records/phase4_local_e2e_smoke_result_2026-04-21.json`

说明：
- 本闭环只证明 mock-first 本地链路可重复验收，不代表 Ubuntu 实机、真实模型、真实相机、真实机械臂或生产级长连接已验证。

## 7. 当前验证结论

当前已验证事实可支持：
- 项目级测试入口可运行
- 统一入口单任务 mock 闭环可运行
- 统一入口可导出最终状态 JSON
- 统一入口已装配工具列表可被直接检查

当前仍不能证明：
- Ubuntu 实机上的依赖安装已验证
- 前端 UI 与前后端联调已验证
- 真实 `LeRobot`、真实硬件、真实 `SmolVLA` 权重与实物链路已验证

## 8. 待补项

后续应继续补充：
- Ubuntu 实机上的依赖安装验证
- `--config` 路径下的配置加载验证
- 失败路径、多任务路径与配置路径验证
- 前端联动验证
- 真实适配器、真实模型与真实硬件验证
