# 实验记录

## 文档定位

本文档用于记录真实实验与验证过程。
当前项目已完成第一阶段骨架代码，但尚未进入真实实验和实物联调阶段，因此本文件当前以实验计划、记录框架和“暂无实验事实”状态为主。

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

## 当前实验状态

- 尚无真实实验数据
- 尚无 Ubuntu 环境下实际部署结果
- 尚无实物抓取和分拣记录
- 已具备统一启动入口下的 mock integration validation 事实，但该事实不计为真实实验结果

## 当前结论

当前实验工作处于规划完成、尚未执行的阶段。
后续一旦进入开发，应优先从决策层模拟闭环实验开始。
