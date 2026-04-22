import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2);
}

function resolveImageSource(currentImage: string | undefined) {
  if (!currentImage) {
    return null;
  }
  if (currentImage.startsWith("data:image/") || currentImage.startsWith("http://") || currentImage.startsWith("https://")) {
    return currentImage;
  }
  return `data:image/png;base64,${currentImage}`;
}

export function RuntimePanel() {
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const bootstrap = useWorkbenchStore((state) => state.bootstrap);
  const showRuntimeDetails = useWorkbenchStore((state) => state.showRuntimeDetails);
  const toggleRuntimeDetails = useWorkbenchStore((state) => state.toggleRuntimeDetails);
  const imageSource = resolveImageSource(snapshot?.current_image);

  return (
    <PanelShell
      title="实时画面与状态"
      subtitle="聚焦当前任务画面、核心状态、动作结果与关键运行上下文。"
      actions={
        <button type="button" className="button-secondary" onClick={toggleRuntimeDetails}>
          {showRuntimeDetails ? "收起详情" : "展开详情"}
        </button>
      }
    >
      <div className="stack">
        <div className="video-placeholder">
          <div className="video-placeholder__overlay">
            <span>{imageSource ? "实时画面已接入" : "等待图像输入"}</span>
          </div>
          <div className="video-placeholder__body">
            {imageSource ? (
              <img className="runtime-image" src={imageSource} alt="当前运行态图像" />
            ) : (
              <p>当前还没有真实视频流服务，页面会优先承接最近一次图像输入并保留运行态说明。</p>
            )}
          </div>
        </div>

        <div className="key-value-grid">
          <div className="kv-card">
            <span>当前结果</span>
            <strong>{snapshot?.action_result || "-"}</strong>
          </div>
          <div className="kv-card">
            <span>错误信息</span>
            <strong>{snapshot?.error || "无"}</strong>
          </div>
          <div className="kv-card">
            <span>状态字段</span>
            <strong>{bootstrap?.status_fields.length || 0}</strong>
          </div>
          <div className="kv-card">
            <span>能力数量</span>
            <strong>{bootstrap?.execution_capabilities.length || 0}</strong>
          </div>
        </div>

        {showRuntimeDetails ? (
          <>
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
          </>
        ) : null}
      </div>
    </PanelShell>
  );
}
