# 论文附录现成材料

本文档把当前已经有证据支撑、但此前尚未整理成“可直接放入论文附录”的内容收口成稿。

## A1. 后端接口总表

来源：
- [http.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/backend/http.py)
- [api.ts](/home/liuwenjie/lerobot/biyesheji/biyesheji/frontend/src/lib/api.ts)

| 接口 | 方法 | 作用 | 前端用途 |
| --- | --- | --- | --- |
| `/api/v1/runtime/bootstrap` | `GET` | 返回启动所需的聚合信息，包括配置、工具、执行模型和安全信息 | 页面初始化 |
| `/api/v1/runtime/config` | `GET` | 获取当前运行时配置 | 设置面板加载 |
| `/api/v1/runtime/config` | `PUT` | 原子更新当前运行时配置 | 保存配置 |
| `/api/v1/runtime/tools` | `GET` | 获取当前注册工具列表 | 工具面板展示 |
| `/api/v1/runtime/tools/refresh` | `POST` | 刷新工具视图 | 设置面板刷新工具 |
| `/api/v1/runtime/video-stream` | `GET` | 输出 MJPEG 视频流 | 左上角实时画面 |
| `/api/v1/runtime/run` | `POST` | 同步 run 接口，保留兼容 | 调试 / 兼容路径 |
| `/api/v1/runtime/runs` | `POST` | 异步创建运行任务，返回 `run_id / snapshot_url / events_url` | 正常任务启动 |
| `/api/v1/runtime/runs/{run_id}` | `GET` | 获取某次任务的最新快照 | 终态补偿同步 |
| `/api/v1/runtime/runs/{run_id}/events` | `GET` | 读取某次任务的阶段事件流 | 事件时间线订阅 |
| `/api/v1/runtime/runs/{run_id}/stop` | `POST` | 请求停止当前任务 | “结束”按钮 |

## A2. phase4 本地真实链路模板参数表

来源：
- [phase4_real_opencv_lerobot_local.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/phase4_real_opencv_lerobot_local.example.yaml)

| 配置分区 | 关键字段 | 当前值 / 模板值 | 说明 |
| --- | --- | --- | --- |
| `decision` | `llm_provider` | `openai` | 决策模型走 OpenAI 兼容网关 |
| `decision` | `max_iterations` | `6` | 单次闭环最大迭代次数 |
| `perception` | `vlm_provider` | `minimax_mcp_vision` | 视觉感知模型供应商 |
| `perception` | `camera_backend` | `opencv` | 摄像头采集后端 |
| `perception` | `camera_device_id` | `${EMBODIED_AGENT_CAMERA_DEVICE_ID}` | 实际摄像头设备路径 |
| `perception` | `camera_width` / `camera_height` | `640 / 480` | 相机分辨率 |
| `perception` | `camera_fps` | `15.0` | 视频流帧率 |
| `perception` | `robot_state_backend` | `lerobot_local` | 机器人状态读取模式 |
| `execution` | `vla_model_path` | `./models/smolvla_finetuned` | VLA 模型目录 |
| `execution` | `robot_adapter` | `lerobot_local` | 本地执行适配器 |
| `execution` | `smolvla_backend` | `mock_smolvla` | 该模板当前示例值为 mock backend；项目已另行完成 SmolVLA 实体执行链路接入 |
| `execution` | `safety_require_precheck` | `true` | 启用执行前安全检查 |
| `execution` | `safety_policy` | `fail_closed` | 默认失败关闭策略 |
| `execution` | `stop_mode` | `estop_latched` | 急停锁存模式 |
| `frontend` | `port` | `7864` | 后端运行端口 |
| `frontend` | `speed_scale` | `1.0` | 前端速度倍率 |

## A3. 自动化测试覆盖摘要表

来源：
- [TEST_REPORT.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/TEST_REPORT.md)

| 测试对象 | 数量 | 覆盖重点 | 结论 |
| --- | ---: | --- | --- |
| `tests/test_perception_phase1.py` | 19 | 感知 provider 装配、fallback、错误映射 | 通过 |
| `tests/test_decision_phase1.py` | 10 | 决策 provider 与 heuristic fallback | 通过 |
| `tests/test_backend_phase3.py` | 9 | 后端运行时与 facade | 通过 |
| `tests/test_backend_http_phase3.py` | 7 | HTTP 路由、错误码、SSE 边界 | 通过 |
| `tests/test_backend_run_stream_phase3.py` | 6 | `run_id` 生命周期与终态清理 | 通过 |
| `frontend/tests/e2e/workbench-smoke.spec.ts` | 3 | 页面启动、run、设置面板 smoke | 通过 |
| `frontend build` | 1 | 前端构建门禁 | 通过 |
| `phase4 smoke` | 1 | mock backend 下的真实链路模板冒烟 | 通过 |

补充事实：
- focused pytest 汇总：`51 passed`
- Playwright e2e 汇总：`3 passed`
- 当前结论支持“本地软件级 demo 已形成回归基线”；同时根据最新项目进展，SmolVLA 实体执行链路已完成，但该表中的自动化 smoke 结果本身并不单独承担实体执行验收结论。

## A4. 前端运行证据卡

来源：
- [frontend_video_home_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_home_2026-04-27.png)
- [frontend_video_running_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_running_2026-04-27.png)
- [frontend_video_completed_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_completed_2026-04-27.png)
- [frontend_video_panel_2026-04-27.png](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/frontend_video_panel_2026-04-27.png)

| 证据项 | 内容 |
| --- | --- |
| 采集日期 | 2026-04-27 |
| 前端地址 | `http://127.0.0.1:5173` |
| 后端地址 | `http://127.0.0.1:7864` |
| 任务指令 | `你看到什么` |
| 首页证据 | 左上角视频流在线，工作台待机 |
| 运行中证据 | 任务执行流推进，事件日志持续刷新 |
| 完成态证据 | 页面显示 `completed`，视频流继续在线，返回中文视觉理解结果 |
| 可引用表述 | 该组截图证明前端工作台、视频流消费、run 生命周期展示和任务终态收口已在本地环境完成留痕 |

## A5. 本地最小闭环 smoke 证据卡

来源：
- [phase4_local_e2e_smoke_result_2026-04-21.json](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/phase4_local_e2e_smoke_result_2026-04-21.json)

| 证据项 | 内容 |
| --- | --- |
| 采集日期 | 2026-04-21 |
| smoke 名称 | `phase4_local_e2e_smoke` |
| `bootstrap_status_fields` | `17` |
| `tools_count` | `8` |
| `refreshed_tools_count` | `8` |
| `accepted_run_id` | `run-local-e2e-smoke` |
| `snapshot_status` | `completed` |
| `snapshot_terminal` | `true` |
| `events_contains_snapshot` | `true` |

可引用表述：
该结果证明 `bootstrap / config / tools / runs / snapshot / events` 在 mock backend 下可形成最小闭环，不等同于真实机械臂闭环验收。

## A6. 汉诺塔任务 Skill 证据卡

来源：
- [13-hanoi-task-skill.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/specs/13-hanoi-task-skill.md)
- [hanoi.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/src/embodied_agent/skills/hanoi.py)
- [PROMPT_ASSETS.md](/home/liuwenjie/lerobot/biyesheji/biyesheji/docs/records/PROMPT_ASSETS.md)

| 证据项 | 内容 |
| --- | --- |
| skill 名称 | `汉诺塔任务技能` |
| `skill_id` | `hanoi_task_skill` |
| 默认任务 | 三柱三环，从 `A柱` 到 `C柱` |
| 默认步数 | `7` |
| 约束 | 一次一环；大环不能压小环；每步显式给出源柱与目标柱 |
| Prompt 资产 | `DECISION_HANOI_SKILL_SYSTEM_PROMPT` |
| 当前状态 | 已加入项目，已形成代码、Prompt 与规范文档，但尚未接入真实硬件执行 |

## A7. 可直接放附录的说明文字

建议原文：

```text
为提高论文材料的可追溯性，本文将系统架构图、关键 Prompt、接口定义、配置模板、测试覆盖摘要和运行留痕统一整理为附录材料。其中，附录中的 Prompt 与接口表均能够回溯到项目源码；运行截图与 smoke 结果均来自本地实际联调过程；汉诺塔任务 skill 则作为复杂序列任务扩展的示例资产，用于说明本系统在长程任务规划方面的可扩展性。
```
