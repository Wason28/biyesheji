import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2);
}

export function RuntimePanel() {
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const bootstrap = useWorkbenchStore((state) => state.bootstrap);

  return (
    <PanelShell
      title="运行态快照"
      subtitle="优先展示 run snapshot 字段、运行日志和视频流占位，保持与后端展示合同解耦。"
    >
      <div className="stack">
        <div className="video-placeholder">
          <div className="video-placeholder__overlay">
            <span>{snapshot?.current_image ? "收到 current_image 字段" : "等待视频流合同"}</span>
          </div>
          <div className="video-placeholder__body">
            {snapshot?.current_image ? (
              <code>{snapshot.current_image}</code>
            ) : (
              <p>当前后端未提供真实视频流 URL，先展示 current_image 占位与连接状态。</p>
            )}
          </div>
        </div>

        <div className="key-value-grid">
          <div className="kv-card">
            <span>action_result</span>
            <strong>{snapshot?.action_result || "-"}</strong>
          </div>
          <div className="kv-card">
            <span>error</span>
            <strong>{snapshot?.error || "无"}</strong>
          </div>
          <div className="kv-card">
            <span>status_fields</span>
            <strong>{bootstrap?.status_fields.length || 0}</strong>
          </div>
          <div className="kv-card">
            <span>capabilities</span>
            <strong>{bootstrap?.execution_capabilities.length || 0}</strong>
          </div>
        </div>

        <div className="json-grid">
          <div className="info-block">
            <h3>robot_state</h3>
            <pre className="code-block">{prettyJson(snapshot?.robot_state)}</pre>
          </div>
          <div className="info-block">
            <h3>last_execution</h3>
            <pre className="code-block">{prettyJson(snapshot?.last_execution)}</pre>
          </div>
          <div className="info-block">
            <h3>scene_observations</h3>
            <pre className="code-block">{prettyJson(snapshot?.scene_observations)}</pre>
          </div>
          <div className="info-block">
            <h3>last_node_result</h3>
            <pre className="code-block">{prettyJson(snapshot?.last_node_result)}</pre>
          </div>
        </div>

        <div className="info-block">
          <h3>运行日志</h3>
          <pre className="code-block">
            {JSON.stringify(snapshot?.logs || [], null, 2)}
          </pre>
        </div>
      </div>
    </PanelShell>
  );
}
