import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";

export function ToolsPanel() {
  const tools = useWorkbenchStore((state) => state.tools);
  const toolsStatus = useWorkbenchStore((state) => state.toolsStatus);
  const refreshTools = useWorkbenchStore((state) => state.refreshTools);

  return (
    <PanelShell
      title="工具面板"
      subtitle="消费 GET /api/v1/runtime/tools，支持手动刷新并区分 perception / execution 图层。"
      actions={
        <button type="button" className="button-secondary" onClick={() => void refreshTools()}>
          刷新工具
        </button>
      }
    >
      <div className="stack">
        <div className="key-value-grid">
          <div className="kv-card">
            <span>状态</span>
            <strong>{toolsStatus}</strong>
          </div>
          <div className="kv-card">
            <span>工具数量</span>
            <strong>{tools.length}</strong>
          </div>
        </div>

        <div className="tool-list">
          {tools.map((tool) => (
            <article className="tool-card" key={`${tool.layer}-${tool.name}`}>
              <div className="tool-card__header">
                <strong>{tool.name}</strong>
                <span className={`layer-badge layer-badge--${tool.layer}`}>{tool.layer}</span>
              </div>
              <p>{tool.description || "未提供描述"}</p>
              <div className="tool-card__meta">
                <span>
                  capability_names:{" "}
                  {tool.capability_names?.length ? tool.capability_names.join(", ") : "无"}
                </span>
              </div>
              <pre className="code-block">
                {JSON.stringify(tool.input_schema || {}, null, 2)}
              </pre>
            </article>
          ))}
          {!tools.length ? <div className="empty-state">当前没有可展示的工具描述。</div> : null}
        </div>
      </div>
    </PanelShell>
  );
}
