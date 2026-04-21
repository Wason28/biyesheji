import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";

function renderStatusLabel(status: string | undefined) {
  switch (status) {
    case "running":
      return "运行中";
    case "completed":
      return "已完成";
    case "failed":
      return "失败";
    case "idle":
      return "空闲";
    default:
      return "未启动";
  }
}

export function ControlPanel() {
  const instruction = useWorkbenchStore((state) => state.instruction);
  const requestedRunId = useWorkbenchStore((state) => state.requestedRunId);
  const bootstrapStatus = useWorkbenchStore((state) => state.bootstrapStatus);
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const runAccepted = useWorkbenchStore((state) => state.runAccepted);
  const runStatus = useWorkbenchStore((state) => state.runStatus);
  const latestError = useWorkbenchStore((state) => state.latestError);
  const latestErrorCode = useWorkbenchStore((state) => state.latestErrorCode);
  const setInstruction = useWorkbenchStore((state) => state.setInstruction);
  const setRequestedRunId = useWorkbenchStore((state) => state.setRequestedRunId);
  const clearInstruction = useWorkbenchStore((state) => state.clearInstruction);
  const submitRun = useWorkbenchStore((state) => state.submitRun);
  const initialize = useWorkbenchStore((state) => state.initialize);
  const canSubmit = bootstrapStatus === "ready" && runStatus !== "loading";

  return (
    <PanelShell
      title="任务输入"
      subtitle="对接 POST /api/v1/runtime/runs，优先消费第三阶段 run_id 生命周期合同。"
      actions={
        <span className={`status-badge status-badge--${runStatus}`}>
          {runStatus === "loading" ? "提交中" : bootstrapStatus === "ready" ? "就绪" : "初始化中"}
        </span>
      }
    >
      <div className="stack">
        {bootstrapStatus === "error" ? (
          <div className="alert alert-error">
            初始化未完成，当前无法提交任务。
            <div className="button-row">
              <button type="button" className="button-secondary" onClick={() => void initialize()}>
                重试初始化
              </button>
            </div>
          </div>
        ) : null}

        <label className="field">
          <span>自然语言任务</span>
          <textarea
            value={instruction}
            onChange={(event) => setInstruction(event.target.value)}
            placeholder="示例：抓取桌面方块并回到安全位置"
            rows={5}
          />
        </label>

        <label className="field">
          <span>自定义 run_id（可选）</span>
          <input
            className="text-input"
            value={requestedRunId}
            onChange={(event) => setRequestedRunId(event.target.value)}
            placeholder="示例：run-demo-001"
          />
        </label>

        <div className="button-row">
          <button type="button" onClick={() => void submitRun()} disabled={!canSubmit}>
            发送任务
          </button>
          <button type="button" className="button-secondary" onClick={clearInstruction}>
            清空输入
          </button>
        </div>

        {latestError ? (
          <div className="alert alert-error">
            <div>{latestError}</div>
            {latestErrorCode ? <code className="inline-code">{latestErrorCode}</code> : null}
          </div>
        ) : null}

        <div className="key-value-grid">
          <div className="kv-card">
            <span>当前 Run</span>
            <strong>{snapshot?.run_id || runAccepted?.run_id || "未创建"}</strong>
          </div>
          <div className="kv-card">
            <span>运行状态</span>
            <strong>{renderStatusLabel(snapshot?.status)}</strong>
          </div>
          <div className="kv-card">
            <span>当前节点</span>
            <strong>{snapshot?.current_node || "bootstrap"}</strong>
          </div>
          <div className="kv-card">
            <span>迭代进度</span>
            <strong>
              {snapshot?.iteration_count ?? 0} / {snapshot?.max_iterations ?? "-"}
            </strong>
          </div>
        </div>

        <div className="info-block">
          <h3>当前任务</h3>
          <p>{snapshot?.current_task || "等待后端返回 current_task 字段。"}</p>
        </div>

        <div className="info-block">
          <h3>场景描述</h3>
          <p>{snapshot?.scene_description || "等待后端返回 scene_description 字段。"}</p>
        </div>

        <div className="key-value-grid">
          <div className="kv-card">
            <span>selected_capability</span>
            <strong>{snapshot?.selected_capability || "-"}</strong>
          </div>
          <div className="kv-card">
            <span>selected_action</span>
            <strong>{snapshot?.selected_action || "-"}</strong>
          </div>
        </div>
      </div>
    </PanelShell>
  );
}
