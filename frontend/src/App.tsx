import { useEffect } from "react";

import { ConfigPanel } from "./components/config-panel";
import { ControlPanel } from "./components/control-panel";
import { EventPanel } from "./components/event-panel";
import { RuntimePanel } from "./components/runtime-panel";
import { ToolsPanel } from "./components/tools-panel";
import { useWorkbenchStore } from "./store/workbench";

export function App() {
  const initialize = useWorkbenchStore((state) => state.initialize);
  const runtimeBaseUrl = useWorkbenchStore((state) => state.runtimeBaseUrl);
  const bootstrapStatus = useWorkbenchStore((state) => state.bootstrapStatus);
  const streamStatus = useWorkbenchStore((state) => state.streamStatus);
  const snapshot = useWorkbenchStore((state) => state.snapshot);
  const lastRunSummary = useWorkbenchStore((state) => state.lastRunSummary);
  const themeMode = useWorkbenchStore((state) => state.themeMode);
  const setThemeMode = useWorkbenchStore((state) => state.setThemeMode);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  return (
    <div className={`app-shell theme-${themeMode}`}>
      <header className="app-hero">
        <div className="app-hero__content">
          <p className="eyebrow">Open Robotics Workspace</p>
          <h1>Embodied Agent Workbench</h1>
          <p className="app-hero__summary">
            面向机器人任务控制、运行监测与模型配置的开源工作台。保持灵活与透明，
            同时把关键状态、配置与事件流组织得更清晰。
          </p>
          <div className="app-hero__statusline">
            <span className="hero-pill">Backend · {runtimeBaseUrl || "同源 /api"}</span>
            <span className="hero-pill">Bootstrap · {bootstrapStatus}</span>
            <span className="hero-pill">Stream · {streamStatus}</span>
            <span className="hero-pill">Run · {snapshot?.status || "idle"}</span>
            <button
              type="button"
              className="hero-toggle"
              onClick={() => setThemeMode(themeMode === "dark" ? "light" : "dark")}
            >
              {themeMode === "dark" ? "切换浅色" : "切换深色"}
            </button>
          </div>
        </div>
        <div className="app-hero__aside">
          <div className="hero-stat-card">
            <span>当前 Run</span>
            <strong>{snapshot?.run_id || "未启动"}</strong>
          </div>
          <div className="hero-stat-card">
            <span>当前节点</span>
            <strong>{snapshot?.current_node || "bootstrap"}</strong>
          </div>
          <div className="hero-stat-card hero-stat-card--wide">
            <span>最近摘要</span>
            <p>{lastRunSummary}</p>
          </div>
        </div>
      </header>

      <main className="dashboard-grid">
        <section className="dashboard-main">
          <ControlPanel />
          <RuntimePanel />
        </section>
        <aside className="dashboard-side">
          <EventPanel />
          <ConfigPanel />
          <ToolsPanel />
        </aside>
      </main>
    </div>
  );
}
