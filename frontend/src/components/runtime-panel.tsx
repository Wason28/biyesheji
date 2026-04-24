import { PanelShell } from "./panel-shell";
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

export function RuntimePanel() {
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const showRuntimeDetails = useWorkbenchStore((state) => state.showRuntimeDetails);
  const toggleRuntimeDetails = useWorkbenchStore((state) => state.toggleRuntimeDetails);
  const imageSource = resolveImageSource(snapshot?.current_image);
  const telemetryItems = renderRobotStateSummary(snapshot?.robot_state);

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
            {imageSource ? "LIVE · SNAPSHOT" : "WAITING · SNAPSHOT"}
          </div>
          <div className="video-frame__body">
            {imageSource ? (
              <img className="runtime-image runtime-image--frame" src={imageSource} alt="当前运行态图像" />
            ) : (
              <div className="video-empty-state">
                <strong>等待图像输入</strong>
                <p>当前还没有真实视频流服务，页面会优先展示最近一次 `current_image` 快照。</p>
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
        </div>

        {showRuntimeDetails ? (
          <div className="runtime-details-grid">
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
