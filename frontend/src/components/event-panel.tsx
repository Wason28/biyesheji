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
      title="事件订阅"
      subtitle="当前按后端 SSE snapshot 事件消费；由于服务端是最小回放骨架，前端采用版本去重并显式展示续连状态。"
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
            <span>stream_status</span>
            <strong>{streamStatus}</strong>
          </div>
          <div className="kv-card">
            <span>latest_version</span>
            <strong>{latestRunState?.version ?? "-"}</strong>
          </div>
          <div className="kv-card">
            <span>terminal</span>
            <strong>{String(latestRunState?.terminal ?? false)}</strong>
          </div>
          <div className="kv-card">
            <span>event_count</span>
            <strong>{eventFeed.length}</strong>
          </div>
        </div>

        <div className="alert alert-info">{streamNotice}</div>

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
