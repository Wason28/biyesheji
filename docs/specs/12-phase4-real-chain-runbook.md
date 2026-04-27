# 12 第四阶段真实链路联调运行说明

## 1. 文档目标

本文档用于沉淀第四阶段 `real-chain P0` 的最小联调路径，覆盖：
- 真实链路配置模板选择
- 后端启动命令
- 前端联调入口
- `phase4_p0_real_smoke.py` 冒烟验证
- 常见失败点与排查顺序

本文档只描述当前仓库已经落地的“真实链路接入骨架”，不把真实机械臂抓取、真实视频流长期稳定性或实体任务闭环写成已完成事实。

## 2. 当前适用范围

当前适用于：
- `opencv + mcp_bridge`
- `opencv + lerobot_local`
- `backend/http + frontend workbench + runtime config`
- `scripts/phase4_p0_real_smoke.py` 的接口级冒烟验证

当前不覆盖：
- RealSense / 深度相机专用驱动
- 真实 `SmolVLA` 权重表现评估
- 手眼标定流程
- 实体抓取成功率统计
- 生产级部署、鉴权与持久化

## 3. 当前已落地入口

- 通用示例配置：[config/config.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/config.example.yaml)
- 桥接模式模板：[config/phase4_real_opencv_mcp_bridge.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/phase4_real_opencv_mcp_bridge.example.yaml)
- 本地 LeRobot 模板：[config/phase4_real_opencv_lerobot_local.example.yaml](/home/liuwenjie/lerobot/biyesheji/biyesheji/config/phase4_real_opencv_lerobot_local.example.yaml)
- 真实链路冒烟脚本：[scripts/phase4_p0_real_smoke.py](/home/liuwenjie/lerobot/biyesheji/biyesheji/scripts/phase4_p0_real_smoke.py)

## 4. 模式选择

### 4.1 `opencv + mcp_bridge`

适用场景：
- 摄像头由当前进程直接采集
- 机器人状态与动作下发走外部 bridge 服务
- 机械臂控制已经被封装成 HTTP bridge

关键字段：
- `perception.camera_backend=opencv`
- `perception.robot_state_backend=mcp_bridge`
- `execution.robot_adapter=mcp_bridge`

### 4.2 `opencv + lerobot_local`

适用场景：
- 摄像头由当前进程直接采集
- 机器人状态与动作由本地 `lerobot` Python 依赖直接接管
- 已具备本地 `robot_config` 与 `robot_pythonpath`

关键字段：
- `perception.camera_backend=opencv`
- `perception.robot_state_backend=lerobot_local`
- `execution.robot_adapter=lerobot_local`

## 5. 联调前置条件

### 5.1 通用前置

- Python 环境可正常导入当前仓库代码
- 摄像头设备已在宿主机可见
- 目标端口未被其他进程占用
- `config/` 中模板引用的环境变量已补齐

### 5.2 `mcp_bridge` 额外前置

- 外部 robot bridge 已启动
- `EMBODIED_AGENT_ROBOT_BRIDGE_BASE_URL` 可连通
- bridge 至少能返回机器人状态、遥测与动作下发结果

### 5.3 `lerobot_local` 额外前置

- `lerobot` / `draccus` 依赖可导入
- `EMBODIED_AGENT_LEROBOT_CONFIG_PATH` 指向真实配置
- `EMBODIED_AGENT_LEROBOT_PYTHONPATH` 已正确设置

## 6. 启动命令清单

### 6.1 桥接模式启动

```bash
export EMBODIED_AGENT_LLM_FALLBACK_MODEL=gpt-4o-mini
export EMBODIED_AGENT_LLM_FALLBACK_API_KEY=replace-me
export EMBODIED_AGENT_LLM_FALLBACK_BASE_URL=https://api.openai.com/v1
export EMBODIED_AGENT_VLM_MODEL=gpt-4o
export EMBODIED_AGENT_VLM_API_KEY=replace-me
export EMBODIED_AGENT_VLM_BASE_URL=https://api.openai.com/v1
export EMBODIED_AGENT_CAMERA_DEVICE_ID=/dev/video0
export EMBODIED_AGENT_CAMERA_FRAME_ID=wrist_camera
export EMBODIED_AGENT_ROBOT_BRIDGE_BASE_URL=http://127.0.0.1:8765

PYTHONPATH=src python -m embodied_agent.backend.http \
  --config config/phase4_real_opencv_mcp_bridge.example.yaml \
  --host 127.0.0.1 \
  --port 7864
```

### 6.2 本地 LeRobot 模式启动

```bash
export EMBODIED_AGENT_LLM_FALLBACK_MODEL=gpt-4o-mini
export EMBODIED_AGENT_LLM_FALLBACK_API_KEY=replace-me
export EMBODIED_AGENT_LLM_FALLBACK_BASE_URL=https://api.openai.com/v1
export EMBODIED_AGENT_VLM_MODEL=gpt-4o
export EMBODIED_AGENT_VLM_API_KEY=replace-me
export EMBODIED_AGENT_VLM_BASE_URL=https://api.openai.com/v1
export EMBODIED_AGENT_CAMERA_DEVICE_ID=/dev/video0
export EMBODIED_AGENT_CAMERA_FRAME_ID=wrist_camera
export EMBODIED_AGENT_LEROBOT_CONFIG_PATH=./lerobot_configs/my_robot.yaml
export EMBODIED_AGENT_LEROBOT_PYTHONPATH=/opt/lerobot/src

PYTHONPATH=src python -m embodied_agent.backend.http \
  --config config/phase4_real_opencv_lerobot_local.example.yaml \
  --host 127.0.0.1 \
  --port 7864
```

### 6.3 前端联调

```bash
VITE_PROXY_TARGET=http://127.0.0.1:7864 \
VITE_RUNTIME_BASE_URL=http://127.0.0.1:7864 \
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

## 7. 冒烟验证

### 7.1 桥接模式

```bash
PYTHONPATH=src python scripts/phase4_p0_real_smoke.py \
  --base-url http://127.0.0.1:7864/api/v1/runtime \
  --run-id run-p0-real-bridge \
  --expect-camera-backend opencv \
  --expect-robot-state-backend mcp_bridge \
  --expect-robot-adapter mcp_bridge
```

### 7.2 本地 LeRobot 模式

```bash
PYTHONPATH=src python scripts/phase4_p0_real_smoke.py \
  --base-url http://127.0.0.1:7864/api/v1/runtime \
  --run-id run-p0-real-lerobot \
  --expect-camera-backend opencv \
  --expect-robot-state-backend lerobot_local \
  --expect-robot-adapter lerobot_local
```

### 7.3 通过标准

- `bootstrap_ok=true`
- `config_ok=true`
- `tools_ok=true`
- `video_stream_ok=true`
- `events_ok=true`
- `run_accepted=true`
- `run_terminal=true`
- 所有 `expect-*` 检查为 `true`

输出产物默认写入：
- `docs/records/phase4_p0_real_smoke_result_YYYY-MM-DD.json`

## 8. 建议验收顺序

1. 先只启动 backend，确认 `/bootstrap` 与 `/config` 返回正常。
2. 再确认 `/video-stream` 可以产出一帧 MJPEG。
3. 再确认 `/runs` 能受理一次低风险指令，例如“回到安全位置”。
4. 最后再打开前端工作台检查 runtime profile、连接模式与安全预检状态。

## 9. 常见失败点

### 9.1 `video_stream_ok=false`

优先检查：
- `camera_device_id`
- `camera_index`
- 摄像头权限
- `opencv` 设备是否已被其他进程占用

### 9.2 `robot_state_backend_match=false`

优先检查：
- 是否加载了错误模板
- 环境变量展开后是否覆盖了预期配置
- 前端或其他请求是否做过 `PUT /config`

### 9.3 `run_terminal=false`

优先检查：
- 机器人状态接口是否卡住
- 安全预检是否阻断动作
- bridge / lerobot_local 是否能返回遥测

### 9.4 `lerobot_local adapter` 初始化失败

优先检查：
- `EMBODIED_AGENT_LEROBOT_PYTHONPATH`
- `EMBODIED_AGENT_LEROBOT_CONFIG_PATH`
- 本地 Python 环境里是否能直接导入 `lerobot`

### 9.5 `mcp_bridge` 请求失败

优先检查：
- `EMBODIED_AGENT_ROBOT_BRIDGE_BASE_URL`
- bridge 服务进程是否存活
- 目标端口是否可访问

## 10. 当前真实验证边界

当前已经确认：
- 两份 phase4 真实链路模板可以被 `build_runtime_from_config` 正常加载
- `phase4_p0_real_smoke.py` 已完成语法检查、命令行参数检查与 mock backend 实跑验证

当前仍未确认：
- 真实摄像头在目标 Ubuntu 设备上的长期稳定性
- 真实 bridge / 真实 LeRobot 控制链路的物理动作结果
- 实体抓取、放置、回零等任务的成功率

## 11. 推荐配套记录

完成首次真实联调后，应同步更新：
- `docs/records/TEST_REPORT.md`
- `docs/records/CURRENT_STATUS.md`
- `docs/records/HANDOFF.md`
- `docs/records/DEVELOPMENT_LOG.md`
