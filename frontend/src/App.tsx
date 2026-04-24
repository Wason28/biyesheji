import { useEffect, useMemo, useState } from "react";
import { Moon, Settings, Sun } from "lucide-react";

import { ControlPanel } from "./components/control-panel";
import { EventPanel } from "./components/event-panel";
import { PanelShell } from "./components/panel-shell";
import { RuntimePanel } from "./components/runtime-panel";
import { SettingsModal } from "./components/settings-modal";
import { useWorkbenchStore } from "./store/workbench";
import type { FrontendRunStatePayload, RunPhase } from "./types/runtime";

type DashboardNode = "perceive" | "plan" | "execute" | "verify";
type DashboardNodeState = "idle" | "active" | "done" | "failed";

const dashboardNodeOrder: DashboardNode[] = ["perceive", "plan", "execute", "verify"];

function mapPhaseToNode(phase: RunPhase | undefined): DashboardNode {
  switch (phase) {
    case "trigger":
    case "nlu":
    case "sensory":
    case "assessment":
    case "active_perception":
      return "perceive";
    case "task_planning":
    case "pre_feedback":
      return "plan";
    case "motion_control":
    case "hri":
    case "compensation":
      return "execute";
    case "verification":
    case "error_diagnosis":
    case "success_notice":
    case "goal_check":
    case "state_compression":
    case "final_status":
    default:
      return "verify";
  }
}

function buildNodeStates(
  events: FrontendRunStatePayload[],
  latestPhase: RunPhase | undefined,
): Record<DashboardNode, DashboardNodeState> {
  const states: Record<DashboardNode, DashboardNodeState> = {
    perceive: "idle",
    plan: "idle",
    execute: "idle",
    verify: "idle",
  };

  const activeNode = mapPhaseToNode(latestPhase);
  states[activeNode] = "active";

  for (const event of events) {
    const node = mapPhaseToNode(event.phase);
    if (event.event === "phase_completed" || event.event === "run_completed") {
      states[node] = states[node] === "failed" ? "failed" : "done";
    }
    if (event.event === "phase_failed" || event.event === "human_intervention_required") {
      states[node] = "failed";
    }
    if (event.event === "phase_started" && states[node] === "idle") {
      states[node] = "active";
    }
  }

  const activeIndex = dashboardNodeOrder.indexOf(activeNode);
  dashboardNodeOrder.forEach((node, index) => {
    if (states[node] === "idle" && index < activeIndex) {
      states[node] = "done";
    }
  });

  return states;
}

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

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2);
}

function RunStatusPanel() {
  const instruction = useWorkbenchStore((state) => state.instruction);
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const latestRunState = useWorkbenchStore((state) => state.latestRunState);
  const runAccepted = useWorkbenchStore((state) => state.runAccepted);
  const streamStatus = useWorkbenchStore((state) => state.streamStatus);
  const lastRunSummary = useWorkbenchStore((state) => state.lastRunSummary);
  const latestError = useWorkbenchStore((state) => state.latestError);
  const eventFeed = useWorkbenchStore((state) => state.eventFeed);

  const resolvedRunId = snapshot?.run_id || runAccepted?.run_id || "未创建";
  const resolvedTask =
    snapshot?.current_task || latestRunState?.run.current_task || instruction || "等待任务提交";
  const latestEvent = eventFeed.at(-1);

  return (
    <PanelShell
      title="运行状态"
      subtitle="聚合当前 run 的终态、规划与诊断字段，便于快速回归。"
      actions={<span className={`status-badge status-badge--${snapshot?.status || "idle"}`}>{renderStatusLabel(snapshot?.status)}</span>}
    >
      <div className="run-status-stack">
        <div className="key-value-grid">
          <div className="kv-card">
            <span>Run ID</span>
            <strong>{resolvedRunId}</strong>
          </div>
          <div className="kv-card">
            <span>Task</span>
            <strong>{resolvedTask}</strong>
          </div>
          <div className="kv-card">
            <span>当前阶段</span>
            <strong>{snapshot?.current_phase || latestRunState?.phase || "trigger"}</strong>
          </div>
          <div className="kv-card">
            <span>流状态</span>
            <strong>{streamStatus}</strong>
          </div>
        </div>

        <div className="run-status-readable">
          <p>
            <strong>Run ID:</strong> {resolvedRunId}
          </p>
          <p>
            <strong>Task:</strong> {resolvedTask}
          </p>
          <p>
            <strong>Status:</strong> {renderStatusLabel(snapshot?.status)}
          </p>
          <p>
            <strong>最新事件:</strong> {latestEvent ? `${latestEvent.event.toUpperCase()} / ${latestEvent.phase}` : "尚未接收事件"}
          </p>
        </div>

        <div className="alert alert-info">{lastRunSummary}</div>
        {latestError ? <div className="alert alert-error">{latestError}</div> : null}

        <div className="runtime-details-grid">
          <div className="info-block">
            <h3>plan</h3>
            <pre className="code-block compact-code-block">{prettyJson(snapshot?.plan)}</pre>
          </div>
          <div className="info-block">
            <h3>last_node_result</h3>
            <pre className="code-block compact-code-block">{prettyJson(snapshot?.last_node_result)}</pre>
          </div>
          <div className="info-block">
            <h3>execution_feedback</h3>
            <pre className="code-block compact-code-block">{prettyJson(snapshot?.execution_feedback)}</pre>
          </div>
          <div className="info-block">
            <h3>final_report</h3>
            <pre className="code-block compact-code-block">{prettyJson(snapshot?.final_report)}</pre>
          </div>
        </div>
      </div>
    </PanelShell>
  );
}

function PhaseSummaryPanel() {
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const latestRunState = useWorkbenchStore((state) => state.latestRunState);
  const eventFeed = useWorkbenchStore((state) => state.eventFeed);

  const nodeStates = useMemo(
    () => buildNodeStates(eventFeed, latestRunState?.phase ?? snapshot?.current_phase),
    [eventFeed, latestRunState?.phase, snapshot?.current_phase],
  );

  return (
    <PanelShell
      title="阶段总览"
      subtitle="用稳定的四段视图映射实际 LangGraph 事件，保持 smoke 锚点不变。"
    >
      <div className="phase-summary-grid">
        <article data-testid="node-perceive" data-state={nodeStates.perceive} className={`phase-summary-card phase-summary-card--${nodeStates.perceive}`}>
          <span>01</span>
          <strong>多模态感知</strong>
          <small>trigger / nlu / sensory / assessment / active_perception</small>
        </article>
        <article data-testid="node-plan" data-state={nodeStates.plan} className={`phase-summary-card phase-summary-card--${nodeStates.plan}`}>
          <span>02</span>
          <strong>决策路径规划</strong>
          <small>task_planning / pre_feedback</small>
        </article>
        <article data-testid="node-execute" data-state={nodeStates.execute} className={`phase-summary-card phase-summary-card--${nodeStates.execute}`}>
          <span>03</span>
          <strong>动作执行控制</strong>
          <small>motion_control / hri / compensation</small>
        </article>
        <article data-testid="node-verify" data-state={nodeStates.verify} className={`phase-summary-card phase-summary-card--${nodeStates.verify}`}>
          <span>04</span>
          <strong>执行结果验证</strong>
          <small>verification / final_status</small>
        </article>
      </div>
    </PanelShell>
  );
}

export function App() {
  const initialize = useWorkbenchStore((state) => state.initialize);
  const themeMode = useWorkbenchStore((state) => state.themeMode);
  const setThemeMode = useWorkbenchStore((state) => state.setThemeMode);
  const bootstrapStatus = useWorkbenchStore((state) => state.bootstrapStatus);
  const configStatus = useWorkbenchStore((state) => state.configStatus);
  const toolsStatus = useWorkbenchStore((state) => state.toolsStatus);
  const runStatus = useWorkbenchStore((state) => state.runStatus);
  const latestError = useWorkbenchStore((state) => state.latestError);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  return (
    <div className={`app-shell app-shell--${themeMode}`} data-testid="app-shell">
      <header className="workbench-header">
        <div>
          <p className="brand-kicker">Embodied Agent Workbench</p>
          <h1>本地闭环运行工作台</h1>
          <p className="workbench-header__subtitle">
            前端工作台已切到真实 runtime store，配置、工具、run、snapshot 与事件流共用同一条链路。
          </p>
        </div>
        <div className="workbench-header__actions">
          <div className="status-pill-row">
            <span className={`status-badge status-badge--${bootstrapStatus}`}>bootstrap {bootstrapStatus}</span>
            <span className={`status-badge status-badge--${configStatus}`}>config {configStatus}</span>
            <span className={`status-badge status-badge--${toolsStatus}`}>tools {toolsStatus}</span>
            <span className={`status-badge status-badge--${runStatus}`}>run {runStatus}</span>
          </div>
          <div className="header-button-row">
            <button
              type="button"
              className="icon-button button-secondary"
              onClick={() => setThemeMode(themeMode === "dark" ? "light" : "dark")}
              aria-label="切换主题"
            >
              {themeMode === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              type="button"
              className="icon-button button-secondary"
              onClick={() => setShowSettings(true)}
              aria-label="打开设置"
            >
              <Settings size={18} />
            </button>
          </div>
        </div>
      </header>

      {latestError && bootstrapStatus === "error" ? <div className="alert alert-error">{latestError}</div> : null}

      <main className="workbench-layout">
        <div className="workbench-main">
          <div data-testid="run-status-panel">
            <RunStatusPanel />
          </div>
          <div className="workbench-grid workbench-grid--top">
            <div data-testid="phase-flow-panel">
              <PhaseSummaryPanel />
            </div>
            <RuntimePanel />
          </div>
          <div data-testid="event-log-panel">
            <EventPanel />
          </div>
        </div>

        <aside className="workbench-sidebar">
          <div data-testid="control-panel">
            <ControlPanel />
          </div>
        </aside>
      </main>

      <SettingsModal open={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
}
