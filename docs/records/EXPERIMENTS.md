# 实验记录

## 文档定位

本文档用于记录真实实验与验证过程。
截至 2026-04-27，项目已不再处于“完全没有真实执行事实”的阶段：SmolVLA 实体执行链路已经完成接入。与此同时，本文件仍需如实区分“实体执行链路已完成”与“系统性实验台账尚待补齐”这两个层面，因此当前内容同时包含已确认事实与待补充实验框架。

## 计划实验方向

### 1. 决策层模拟闭环实验

目标：
- 验证 LangGraph 主流程是否能在模拟 MCP 工具下正常闭环

关键指标：
- 流程是否按预期到达 `verifier`
- 是否能根据结果继续或结束

### 2. 感知层工具实验

目标：
- 验证 `get_image`、`get_robot_state`、`describe_scene` 的输入输出稳定性

关键指标：
- 调用成功率
- 输出结构稳定性
- 错误回退可用性

### 3. 执行层技能实验

目标：
- 验证原子动作和 `run_smolvla` 的调用链路

关键指标：
- 动作执行成功率
- 失败保护行为
- 与 LeRobot 接口兼容性

### 4. 实物分拣实验

目标：
- 验证桌面级分拣任务闭环效果

关键指标：
- 连续成功次数
- 平均成功率
- 常见失败原因

### 5. 数据采集与微调前置检查

目标：
- 在不虚构真实链路的前提下，收敛 `LeRobot` 数据采集与 `SmolVLA` 微调启动门槛

前置项：
- 真实 `LeRobot` 机器人配置、相机输入与示教脚本可跑通
- 至少完成 1 条真实示教轨迹落盘，用于验证数据目录、`Parquet + 视频帧` 格式和命名规则
- 建立样本台账，记录轨迹编号、任务类型、成功/失败、失败原因、环境条件与素材索引
- 明确目标样本规模为 50-100 组成功轨迹，覆盖不同物体位置与抓取角度
- 明确 `SmolVLA` 训练输入、权重输出路径与实验记录回写位置，但在真实数据形成前不记录训练完成事实

建议首条真实轨迹记录字段：
- 记录日期
- 执行人 / 负责 Agent
- 设备与环境（机械臂、相机、桌面场景、光照）
- 轨迹编号与数据目录
- 任务类型（抓取 / 放置 / 分拣）
- 目标物体与初始摆放情况
- 是否成功落盘
- 失败原因（若失败）
- 视频 / 截图 / 日志索引
- 对应样本版本号

建议样本台账字段：
- `sample_id`
- `collection_date`
- `task_type`
- `object_type`
- `success`
- `failure_reason`
- `operator`
- `environment_tag`
- `data_path`
- `asset_refs`
- `notes`

建议微调准备字段：
- `dataset_version`
- `train_split`
- `eval_split`
- `base_model`
- `output_dir`
- `config_path`
- `key_hparams`
- `expected_metrics`
- `run_status`
- `result_refs`

## 2026-04-21 本地最小前后端闭环验证

- 类型：mock-first 本地闭环 / 非真实实体实验
- 环境：本机代码环境，frontend dev server + backend HTTP facade
- 后端地址：`http://127.0.0.1:7861`
- 前端地址：`http://127.0.0.1:5173`
- 验证脚本：`uv run python scripts/phase4_local_e2e_smoke.py`
- 结果文件：`docs/records/phase4_local_e2e_smoke_result_2026-04-21.json`
- 截图文件：
  - `docs/records/phase3_workbench_2026-04-21.png`
  - `docs/records/phase3_workbench_2026-04-21_live.png`
- 核心结果：
  - `bootstrap / config / tools / runs / snapshot / events` 全链路可用
  - 配置写回后 `decision.provider=openai`、`perception.provider=openai_gpt4o`、`frontend.max_iterations=7`、`frontend.speed_scale=0.7`、`execution.home_pose={x:0.11,y:0.22,z:0.33}` 生效
  - `run-local-e2e` 路径可从指令提交推进到终态，事件流包含 `snapshot`
- 备注：本记录只证明“本地最小闭环”成立，不计为 Ubuntu 实机、真实视频流或真实硬件实验事实

## 2026-04-27 SmolVLA 实体执行里程碑

- 类型：真实执行链路完成 / 非统计性实验结论
- 当前结论：执行层中的 `run_smolvla` 已完成实体执行链路接入，系统已具备真实高阶技能执行事实
- 可引用材料：
  - `docs/records/CURRENT_STATUS.md`
  - `docs/records/SMOLVLA_REAL_EXECUTION_EVIDENCE.md`
  - `docs/records/THESIS_MAIN_TEXT_10000.md`
  - `docs/thesis_draft.md`
- 说明：
  - 该里程碑说明“真实执行能力已具备”
  - 该里程碑不自动等价于“大规模成功率统计已完成”
  - 后续仍需补充重复执行记录、失败案例分析与长时间稳定性数据

## 当前实验状态

- 已具备 SmolVLA 实体执行链路完成这一真实执行事实
- 尚未形成系统性的重复实验台账
- 尚无完整的 Ubuntu 长时间部署验收记录
- 实物抓取和分拣的成功率统计、失败原因分类与鲁棒性数据仍待补充

## 当前结论

当前实验工作已从“纯规划阶段”进入“已具备实体执行事实、待补统计验证阶段”。
后续应优先围绕真实执行链路补齐标准化实验台账，而不是继续把项目表述为仅有 mock 验证。
