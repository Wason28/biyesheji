import type { ReactNode } from "react";

import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";
import type { ConfigSectionKey, ConfigSectionValue } from "../types/runtime";

const CONFIG_TABS: Array<{ key: ConfigSectionKey; label: string }> = [
  { key: "decision", label: "决策 LLM" },
  { key: "perception", label: "感知 VLM" },
  { key: "execution", label: "执行层" },
  { key: "frontend", label: "前端参数" },
];

function renderValue(value: unknown): ReactNode {
  if (typeof value === "boolean") {
    return <span>{value ? "是" : "否"}</span>;
  }
  if (Array.isArray(value) || (typeof value === "object" && value !== null)) {
    return (
      <pre className="code-block">{JSON.stringify(value, null, 2)}</pre>
    );
  }
  return <span>{String(value ?? "-")}</span>;
}

function renderConfigRows(section: ConfigSectionValue) {
  return Object.entries(section).map(([key, value]) => (
    <div className="config-row" key={key}>
      <div className="config-row__label">{key}</div>
      <div className="config-row__value">{renderValue(value)}</div>
    </div>
  ));
}

export function ConfigPanel() {
  const bootstrap = useWorkbenchStore((state) => state.bootstrap);
  const config = useWorkbenchStore((state) => state.config);
  const configStatus = useWorkbenchStore((state) => state.configStatus);
  const activeConfigTab = useWorkbenchStore((state) => state.activeConfigTab);
  const setActiveConfigTab = useWorkbenchStore((state) => state.setActiveConfigTab);
  const refreshConfig = useWorkbenchStore((state) => state.refreshConfig);

  const resolvedConfig = config || bootstrap?.config;
  const section = resolvedConfig?.[activeConfigTab] || {};

  return (
    <PanelShell
      title="配置展示"
      subtitle="当前消费 bootstrap + GET /api/v1/runtime/config 两条读取合同，不直接改写后端结构。"
      actions={
        <button type="button" className="button-secondary" onClick={() => void refreshConfig()}>
          刷新配置
        </button>
      }
    >
      <div className="stack">
        <div className="key-value-grid">
          <div className="kv-card">
            <span>config_status</span>
            <strong>{configStatus}</strong>
          </div>
          <div className="kv-card">
            <span>config_source</span>
            <strong>{config ? "GET /config" : "bootstrap fallback"}</strong>
          </div>
        </div>

        <div className="tab-row">
          {CONFIG_TABS.map((tab) => (
            <button
              type="button"
              key={tab.key}
              className={tab.key === activeConfigTab ? "tab-button tab-button--active" : "tab-button"}
              onClick={() => setActiveConfigTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="alert alert-info">
          当前第三阶段后端仅冻结读取合同，配置面板先以展示为主，待 PUT /config 稳定后再接入提交与回滚。
        </div>

        <div className="config-table">
          {renderConfigRows(section)}
        </div>

        <div className="key-value-grid">
          <div className="kv-card">
            <span>execution_model</span>
            <strong>{String(bootstrap?.execution_model?.name || "SmolVLA")}</strong>
          </div>
          <div className="kv-card">
            <span>execution_safety</span>
            <strong>{String(bootstrap?.execution_safety?.stop_mode || "已接线")}</strong>
          </div>
        </div>
      </div>
    </PanelShell>
  );
}
