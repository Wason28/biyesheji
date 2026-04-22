import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";

export function EventPanel() {
  const runAccepted = useWorkbenchStore((state) => state.runAccepted);
  const latestRunState = useWorkbenchStore((state) => state.latestRunState);
  const eventFeed = useWorkbenchStore((state) => state.eventFeed);
  const streamStatus = useWorkbenchStore((state) => state.streamStatus);
  const streamNotice = useWorkbenchStore((state) => state.streamNotice);
  const disconnectStream = useWorkbenchStore((state) => state.disconnectStream);
  const syncRunSnapshot = useWorkbenchStore((state) => state.syncRunSnapshot);

  return (
    <PanelShell
      title="事件记录"
      subtitle="按时间顺序查看状态推进、终态收口与事件流异常提示。"
      actions={
        <div className="button-row">
          <button type="button" className="button-secondary" onClick={() => void syncRunSnapshot()}>
            同步快照
          </button>
          <button type="button" className="button-secondary" onClick={disconnectStream}>
            断开订阅
          </button>
        </div>
      }
    >
      <div className="stack">
        <div className="key-value-grid">
          <div className="kv-card">
            <span>事件流</span>
            <strong>{streamStatus}</strong>
          </div>
          <div className="kv-card">
            <span>最新版本</span>
            <strong>{latestRunState?.version ?? "-"}</strong>
          </div>
          <div className="kv-card">
            <span>终态标记</span>
            <strong>{String(latestRunState?.terminal ?? false)}</strong>
          </div>
          <div className="kv-card">
            <span>事件总数</span>
            <strong>{eventFeed.length}</strong>
          </div>
        </div>

        <div className="alert alert-info">{streamNotice}</div>
        {streamStatus === "error" ? (
          <div className="alert alert-error">
            事件流暂时不可用，当前保留最近一次有效快照，可手动触发“同步快照”继续对齐状态。
          </div>
        ) : null}

        <div className="config-table">
          <div className="config-row">
            <div className="config-row__label">snapshot_url</div>
            <div className="config-row__value">{runAccepted?.snapshot_url || "未创建"}</div>
          </div>
          <div className="config-row">
            <div className="config-row__label">events_url</div>
            <div className="config-row__value">{runAccepted?.events_url || "未创建"}</div>
          </div>
        </div>

        <div className="timeline">
          {eventFeed.map((event) => (
            <article className="timeline-item" key={event.version}>
              <header>
                <strong>版本 {event.version}</strong>
                <span>{event.run.status}</span>
              </header>
              <p>
                节点：{event.run.current_node || "-"}，任务：{event.run.current_task || "-"}
              </p>
              <p>
                terminal: {String(event.terminal)}，error: {event.run.error || "无"}
              </p>
            </article>
          ))}
          {!eventFeed.length ? <div className="empty-state">尚未接收到 snapshot 事件。</div> : null}
        </div>
      </div>
    </PanelShell>
  );
}
