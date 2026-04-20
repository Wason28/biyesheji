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

  useEffect(() => {
    void initialize();
  }, [initialize]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">第三阶段最小前端工程骨架</p>
          <h1>Embodied Agent 主工作台</h1>
          <p className="app-header__summary">
            围绕任务输入、配置展示、工具面板、运行态快照和事件订阅占位组织主工作台，
            当前仅消费显式后端展示合同。
          </p>
        </div>
        <div className="app-header__meta">
          <div className="meta-card">
            <span>Backend Base URL</span>
            <strong>{runtimeBaseUrl || "同源 /api 代理"}</strong>
          </div>
          <div className="meta-card">
            <span>Bootstrap</span>
            <strong>{bootstrapStatus}</strong>
          </div>
          <div className="meta-card">
            <span>事件流</span>
            <strong>{streamStatus}</strong>
          </div>
          <div className="meta-card">
            <span>当前状态</span>
            <strong>{snapshot?.status || "idle"}</strong>
          </div>
        </div>
      </header>

      <main className="workbench-grid">
        <div className="workbench-column">
          <ControlPanel />
          <ConfigPanel />
        </div>
        <div className="workbench-column">
          <RuntimePanel />
          <EventPanel />
        </div>
        <div className="workbench-column">
          <ToolsPanel />
        </div>
      </main>
    </div>
  );
}
