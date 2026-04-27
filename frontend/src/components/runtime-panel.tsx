import { useState } from "react";

import { PanelShell } from "./panel-shell";
import { resolveRuntimeUrl } from "../lib/api";
import { useWorkbenchStore } from "../store/workbench";

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2);
}

function resolveImageSource(currentImage: string | undefined) {
  if (!currentImage) {
    return null;
  }
  if (
    currentImage.startsWith("data:image/") ||
    currentImage.startsWith("http://") ||
    currentImage.startsWith("https://")
  ) {
    return currentImage;
  }
  return `data:image/png;base64,${currentImage}`;
}

function renderRobotStateSummary(robotState: Record<string, unknown> | undefined) {
  if (!robotState) {
    return [
      { label: "Joint State", value: "--", tone: "neutral" },
      { label: "EE Pose", value: "--", tone: "neutral" },
      { label: "Gripper", value: "Unknown", tone: "neutral" },
    ];
  }

  const joints = Array.isArray(robotState.joint_positions)
    ? `${robotState.joint_positions.length} joints`
    : "--";
  const pose =
    robotState.ee_pose && typeof robotState.ee_pose === "object"
      ? Object.entries(robotState.ee_pose as Record<string, unknown>)
          .slice(0, 3)
          .map(([axis, value]) => `${axis}:${String(value)}`)
          .join(" ")
      : "--";
  const graspState =
    typeof robotState.grasp_state === "string"
      ? robotState.grasp_state
      : typeof robotState.gripper === "string"
        ? robotState.gripper
        : "Unknown";

  return [
    { label: "Joint State", value: joints, tone: "normal" },
    { label: "EE Pose", value: pose, tone: "normal" },
    {
      label: "Gripper",
      value: graspState,
      tone: graspState.toLowerCase().includes("open") ? "warning" : "active",
    },
  ];
}

function resolveRuntimeProfileCardData(
  bootstrap: Record<string, unknown> | null,
  config: Record<string, unknown> | null,
) {
  const runtimeProfile =
    bootstrap && typeof bootstrap.execution_runtime_profile === "object"
      ? (bootstrap.execution_runtime_profile as Record<string, unknown>)
      : {};
  const adapterProfile =
    runtimeProfile.adapter && typeof runtimeProfile.adapter === "object"
      ? (runtimeProfile.adapter as Record<string, unknown>)
      : {};
  const connection =
    adapterProfile.connection && typeof adapterProfile.connection === "object"
      ? (adapterProfile.connection as Record<string, unknown>)
      : {};
  const perception =
    config && typeof config.perception === "object" ? (config.perception as Record<string, unknown>) : {};
  const execution =
    config && typeof config.execution === "object" ? (config.execution as Record<string, unknown>) : {};

  return [
    {
      label: "相机后端",
      value: String(perception.camera_backend || "unknown"),
    },
    {
      label: "状态后端",
      value: String(perception.robot_state_backend || "unknown"),
    },
    {
      label: "执行适配器",
      value: String(execution.adapter || adapterProfile.name || "unknown"),
    },
    {
      label: "连接模式",
      value: String(connection.mode || "unknown"),
    },
    {
      label: "桥接地址",
      value: String(execution.robot_base_url || perception.robot_state_base_url || "--"),
    },
    {
      label: "Precheck",
      value: execution.safety_require_precheck === false ? "disabled" : "enabled",
    },
  ];
}

export function RuntimePanel() {
  const [videoStreamFailed, setVideoStreamFailed] = useState(false);
  const bootstrap = useWorkbenchStore((state) => state.bootstrap);
  const config = useWorkbenchStore((state) => state.configDraft || state.config || state.bootstrap?.config || null);
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const showRuntimeDetails = useWorkbenchStore((state) => state.showRuntimeDetails);
  const toggleRuntimeDetails = useWorkbenchStore((state) => state.toggleRuntimeDetails);
  const imageSource = resolveImageSource(snapshot?.current_image);
  const videoStreamUrl = `${resolveRuntimeUrl("/api/v1/runtime/video-stream")}?fps=12&width=320&height=240&quality=50`;
  const telemetryItems = renderRobotStateSummary(snapshot?.robot_state);
  const runtimeProfileItems = resolveRuntimeProfileCardData(bootstrap as Record<string, unknown> | null, config as Record<string, unknown> | null);

  return (
    <PanelShell
      title="实时画面"
      subtitle="使用最近一次运行快照承接原型中的 LIVE 视图，并展示核心遥测。"
      actions={
        <button type="button" className="button-secondary" onClick={toggleRuntimeDetails}>
          {showRuntimeDetails ? "收起详情" : "展开详情"}
        </button>
      }
      compact
    >
      <div className="runtime-stack">
        <div className="video-frame">
          <div className="video-frame__badge">
            <span className="video-frame__dot" />
            {!videoStreamFailed ? "LIVE · STREAM" : imageSource ? "LIVE · SNAPSHOT" : "WAITING · STREAM"}
          </div>
          <div className="video-frame__body">
            {!videoStreamFailed ? (
              <img
                className="runtime-image runtime-image--frame"
                src={videoStreamUrl}
                alt="当前运行态视频流"
                onError={() => setVideoStreamFailed(true)}
              />
            ) : imageSource ? (
              <img className="runtime-image runtime-image--frame" src={imageSource} alt="当前运行态图像" />
            ) : (
              <div className="video-empty-state">
                <strong>等待视频流输入</strong>
                <p>当前未拿到视频流，页面才会回退到最近一次 `current_image` 快照。</p>
              </div>
            )}
          </div>
          <div className="video-frame__footer">Vision Feedback Stream</div>
        </div>

        <div className="telemetry-panel">
          <div className="telemetry-panel__header">
            <div>
              <h3>硬件遥测</h3>
              <p>当前执行状态与感知摘要</p>
            </div>
            <span className={`status-badge status-badge--${snapshot?.status || "idle"}`}>{snapshot?.status || "idle"}</span>
          </div>

          <div className="telemetry-list">
            {telemetryItems.map((item) => (
              <div className="telemetry-item" key={item.label}>
                <span>{item.label}</span>
                <div>
                  <strong>{item.value}</strong>
                  <small className={`telemetry-tone telemetry-tone--${item.tone}`}>{item.tone}</small>
                </div>
              </div>
            ))}
          </div>

          <div className="telemetry-metrics">
            <div className="metric-card">
              <span>当前阶段</span>
              <strong>{snapshot?.current_phase || "-"}</strong>
            </div>
            <div className="metric-card">
              <span>当前结果</span>
              <strong>{snapshot?.action_result || "-"}</strong>
            </div>
            <div className="metric-card">
              <span>感知置信度</span>
              <strong>
                {snapshot?.perception_confidence != null ? snapshot.perception_confidence.toFixed(2) : "-"}
              </strong>
            </div>
            <div className="metric-card">
              <span>当前能力</span>
              <strong>{snapshot?.selected_capability || "-"}</strong>
            </div>
            <div className="metric-card">
              <span>当前动作</span>
              <strong>{snapshot?.selected_action || "-"}</strong>
            </div>
            <div className="metric-card metric-card--danger">
              <span>错误信息</span>
              <strong>{snapshot?.error || "无"}</strong>
            </div>
          </div>

          <div className="telemetry-list">
            {runtimeProfileItems.map((item) => (
              <div className="telemetry-item" key={item.label}>
                <span>{item.label}</span>
                <div>
                  <strong>{item.value}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>

        {showRuntimeDetails ? (
          <div className="runtime-details-grid">
            <div className="info-block">
              <h3>execution_runtime_profile</h3>
              <pre className="code-block compact-code-block">{prettyJson(bootstrap?.execution_runtime_profile)}</pre>
            </div>
            <div className="info-block">
              <h3>execution_safety</h3>
              <pre className="code-block compact-code-block">{prettyJson(bootstrap?.execution_safety)}</pre>
            </div>
            <div className="info-block">
              <h3>robot_state</h3>
              <pre className="code-block compact-code-block">{prettyJson(snapshot?.robot_state)}</pre>
            </div>
            <div className="info-block">
              <h3>scene_observations</h3>
              <pre className="code-block compact-code-block">{prettyJson(snapshot?.scene_observations)}</pre>
            </div>
            <div className="info-block">
              <h3>last_execution</h3>
              <pre className="code-block compact-code-block">{prettyJson(snapshot?.last_execution)}</pre>
            </div>
            <div className="info-block">
              <h3>last_node_result</h3>
              <pre className="code-block compact-code-block">{prettyJson(snapshot?.last_node_result)}</pre>
            </div>
          </div>
        ) : null}
      </div>
    </PanelShell>
  );
}
