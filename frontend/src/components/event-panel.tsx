import { useMemo } from "react";

import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";
import type { FrontendRunStatePayload, RunPhase, RuntimeEventName } from "../types/runtime";

const phaseMeta: Array<{ phase: RunPhase; label: string; short: string }> = [
  { phase: "trigger", label: "触发接入", short: "TRG" },
  { phase: "nlu", label: "任务理解", short: "NLU" },
  { phase: "sensory", label: "感知采样", short: "SNS" },
  { phase: "assessment", label: "场景评估", short: "ASM" },
  { phase: "active_perception", label: "主动感知", short: "APR" },
  { phase: "task_planning", label: "任务规划", short: "PLN" },
  { phase: "pre_feedback", label: "执行前反馈", short: "PFB" },
  { phase: "motion_control", label: "动作控制", short: "MOT" },
  { phase: "verification", label: "执行验证", short: "VER" },
  { phase: "error_diagnosis", label: "错误诊断", short: "ERR" },
  { phase: "hri", label: "人工交互", short: "HRI" },
  { phase: "compensation", label: "补偿处理", short: "CMP" },
  { phase: "success_notice", label: "成功通知", short: "SUC" },
  { phase: "goal_check", label: "目标检查", short: "GLC" },
  { phase: "state_compression", label: "状态压缩", short: "CMP2" },
  { phase: "final_status", label: "终态收口", short: "FIN" },
];

function classifyPhaseState(
  phase: RunPhase,
  currentPhase: RunPhase | undefined,
  completedPhases: Set<RunPhase>,
  failedPhase: RunPhase | undefined,
  interventionPhase: RunPhase | undefined,
) {
  if (failedPhase === phase) {
    return "failed";
  }
  if (interventionPhase === phase) {
    return "attention";
  }
  if (currentPhase === phase) {
    return "active";
  }
  if (completedPhases.has(phase)) {
    return "completed";
  }
  return "idle";
}

function eventTone(event: RuntimeEventName | undefined, terminal: boolean) {
  if (terminal) {
    return "completed";
  }
  if (event === "phase_failed") {
    return "failed";
  }
  if (event === "human_intervention_required") {
    return "attention";
  }
  return "active";
}

function formatTimestamp(timestamp: string | undefined) {
  if (!timestamp) {
    return "--";
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  return date.toLocaleTimeString("zh-CN", { hour12: false });
}

function formatEventLabel(event: RuntimeEventName | undefined) {
  return event ? event.toUpperCase() : "UNKNOWN_EVENT";
}

function findLatestPhaseByEvent(
  events: FrontendRunStatePayload[],
  eventName: RuntimeEventName,
): RunPhase | undefined {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    if (events[index]?.event === eventName) {
      return events[index]?.phase;
    }
  }
  return undefined;
}

export function EventPanel() {
  const runAccepted = useWorkbenchStore((state) => state.runAccepted);
  const latestRunState = useWorkbenchStore((state) => state.latestRunState);
  const eventFeed = useWorkbenchStore((state) => state.eventFeed);
  const streamStatus = useWorkbenchStore((state) => state.streamStatus);
  const streamNotice = useWorkbenchStore((state) => state.streamNotice);
  const disconnectStream = useWorkbenchStore((state) => state.disconnectStream);
  const syncRunSnapshot = useWorkbenchStore((state) => state.syncRunSnapshot);
  const snapshot = useWorkbenchStore((state) => state.snapshot);

  const completedPhases = useMemo(() => {
    return new Set(
      eventFeed
        .filter((event) => event.event === "phase_completed" || event.event === "run_completed")
        .map((event) => event.phase),
    );
  }, [eventFeed]);

  const failedPhase = useMemo(
    () => findLatestPhaseByEvent(eventFeed, "phase_failed"),
    [eventFeed],
  );

  const interventionPhase = useMemo(
    () => findLatestPhaseByEvent(eventFeed, "human_intervention_required"),
    [eventFeed],
  );

  const flowCards = phaseMeta.map((item) => ({
    ...item,
    status: classifyPhaseState(
      item.phase,
      latestRunState?.phase ?? snapshot?.current_phase,
      completedPhases,
      failedPhase,
      interventionPhase,
    ),
  }));

  return (
    <PanelShell
      title="任务执行流"
      subtitle="按真实阶段事件展示运行拓扑与终态收口，不使用演示定时器。"
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
      compact
    >
      <div className="mission-stack">
        <div className="mission-stage">
          <div className="mission-stage__header">
            <div>
              <h3>运行逻辑拓扑</h3>
              <p>LangGraph runtime · 事件驱动</p>
            </div>
            <div className="mission-chip">当前任务：{snapshot?.current_task || "等待任务"}</div>
          </div>

          <div className="phase-flow-grid">
            {flowCards.map((phase) => (
              <article key={phase.phase} className={`phase-node phase-node--${phase.status}`}>
                <span className="phase-node__short">{phase.short}</span>
                <strong>{phase.label}</strong>
                <small>{phase.phase}</small>
              </article>
            ))}
          </div>
        </div>

        <div className="mission-log-panel">
          <div className="mission-log-panel__header">
            <div>
              <h3>实时日志</h3>
              <p>{streamNotice}</p>
            </div>
            <div className="mission-log-stats">
              <span className={`status-badge status-badge--${streamStatus}`}>{streamStatus}</span>
              <span className="hero-pill">事件 {eventFeed.length}</span>
            </div>
          </div>

          <div className="log-console">
            {eventFeed.map((event) => (
              <article key={event.version} className={`log-entry log-entry--${eventTone(event.event, event.terminal)}`}>
                <div className="log-entry__meta">
                  <strong>v{event.version}</strong>
                  <span>{formatTimestamp(event.timestamp)}</span>
                  <span>{formatEventLabel(event.event)}</span>
                  <span>{event.phase}</span>
                </div>
                <p>
                  节点：{event.run.current_node || "-"} · terminal：{String(event.terminal)} · error：
                  {event.run.error || "无"}
                </p>
              </article>
            ))}
            {!eventFeed.length ? <div className="empty-state">尚未接收到运行事件。</div> : null}
          </div>

          <div className="endpoint-grid">
            <div className="endpoint-card">
              <span>snapshot_url</span>
              <strong>{runAccepted?.snapshot_url || "未创建"}</strong>
            </div>
            <div className="endpoint-card">
              <span>events_url</span>
              <strong>{runAccepted?.events_url || "未创建"}</strong>
            </div>
          </div>
        </div>
      </div>
    </PanelShell>
  );
}
