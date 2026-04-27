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
    case "cancelled":
      return "已结束";
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
  const lastRunSummary = useWorkbenchStore((state) => state.lastRunSummary);
  const latestRunState = useWorkbenchStore((state) => state.latestRunState);
  const setInstruction = useWorkbenchStore((state) => state.setInstruction);
  const setRequestedRunId = useWorkbenchStore((state) => state.setRequestedRunId);
  const clearInstruction = useWorkbenchStore((state) => state.clearInstruction);
  const submitRun = useWorkbenchStore((state) => state.submitRun);
  const stopRun = useWorkbenchStore((state) => state.stopRun);
  const initialize = useWorkbenchStore((state) => state.initialize);
  const canSubmit = bootstrapStatus === "ready" && runStatus !== "loading";
  const canStop = snapshot?.status === "running";

  return (
    <PanelShell
      title="交互控制中心"
      subtitle="保持原型右栏结构，但只接入真实可用的 run 能力。"
      actions={
        <span className={`status-badge status-badge--${runStatus}`}>
          {runStatus === "loading" ? "提交中" : bootstrapStatus === "ready" ? "就绪" : "初始化中"}
        </span>
      }
      compact
    >
      <div className="control-stack">
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

        <div className="command-card">
          <div className="command-card__header">
            <span>Command Input</span>
            <strong>自然语言任务</strong>
          </div>
          <textarea
            data-testid="instruction-input"
            value={instruction}
            onChange={(event) => setInstruction(event.target.value)}
            placeholder="输入指令，如：帮我把方块拿过来"
            rows={5}
          />
          <label className="field">
            <span>自定义 run_id（可选）</span>
            <input
              className="text-input"
              value={requestedRunId}
              onChange={(event) => setRequestedRunId(event.target.value)}
              placeholder="示例：run-demo-001"
            />
          </label>
          <div className="button-row command-card__actions">
            <button type="button" onClick={() => void submitRun()} disabled={!canSubmit}>
              启动任务
            </button>
            <button type="button" className="button-secondary" onClick={clearInstruction}>
              清空输入
            </button>
          </div>
        </div>

        <div className="action-grid">
          <button
            type="button"
            data-testid="start-run-button"
            className="action-button action-button--start"
            onClick={() => void submitRun()}
            disabled={!canSubmit}
          >
            <strong>开始</strong>
            <span>真实调用 submitRun()</span>
          </button>
          <button type="button" className="action-button action-button--disabled" onClick={() => void stopRun()} disabled={!canStop}>
            <strong>结束</strong>
            <span>{canStop ? "结束当前运行任务" : "当前没有运行中的任务"}</span>
          </button>
        </div>

        {latestError ? (
          <div className="alert alert-error">
            <div>{latestError}</div>
            {latestErrorCode ? <code className="inline-code">{latestErrorCode}</code> : null}
          </div>
        ) : null}

        <div className="control-metrics">
          <div className="metric-card">
            <span>当前 Run</span>
            <strong>{snapshot?.run_id || runAccepted?.run_id || "未创建"}</strong>
          </div>
          <div className="metric-card">
            <span>运行状态</span>
            <strong>{renderStatusLabel(snapshot?.status)}</strong>
          </div>
          <div className="metric-card">
            <span>当前阶段</span>
            <strong>{snapshot?.current_phase || "bootstrap"}</strong>
          </div>
          <div className="metric-card">
            <span>迭代进度</span>
            <strong>
              {snapshot?.iteration_count ?? 0} / {snapshot?.max_iterations ?? "-"}
            </strong>
          </div>
        </div>

        <div className="control-detail-card">
          <span>当前任务</span>
          <strong>{snapshot?.current_task || "等待后端返回 current_task 字段。"}</strong>
          <p>{lastRunSummary}</p>
        </div>

        <div className="control-detail-card">
          <span>场景描述</span>
          <strong>{snapshot?.scene_description || "等待后端返回 scene_description 字段。"}</strong>
          <p>能力：{snapshot?.selected_capability || "-"} · 动作：{snapshot?.selected_action || "-"}</p>
        </div>
      </div>
    </PanelShell>
  );
}
