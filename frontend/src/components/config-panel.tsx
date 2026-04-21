import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";
import type {
  AssistantHint,
  ConfigSectionKey,
  DecisionConfigSection,
  ExecutionConfigSection,
  FrontendSettingsSection,
  PerceptionConfigSection,
} from "../types/runtime";

const CONFIG_TABS: Array<{ key: ConfigSectionKey; label: string }> = [
  { key: "decision", label: "决策 LLM" },
  { key: "perception", label: "感知 VLM" },
  { key: "execution", label: "执行层" },
  { key: "frontend", label: "前端参数" },
];

function renderAssistantCard(assistant: AssistantHint | undefined) {
  if (!assistant) {
    return null;
  }
  return (
    <div className={`assistant-card assistant-card--${assistant.status}`}>
      <div className="assistant-card__header">
        <strong>{assistant.title}</strong>
        <span>{assistant.status}</span>
      </div>
      <p>{assistant.message}</p>
      {assistant.detected_models?.length ? (
        <div className="assistant-model-list">
          {assistant.detected_models.map((model) => (
            <div className="assistant-model-item" key={`${model.provider}-${model.model}`}>
              <span>{model.provider}</span>
              <strong>{model.model}</strong>
              <em>{model.configured ? "已就绪" : "待配置"}</em>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function renderDecisionSection(
  section: DecisionConfigSection,
  onChange: (field: string, value: string | number) => void,
) {
  return (
    <div className="config-form-grid">
      <label className="field">
        <span>LLM Provider</span>
        <select value={section.provider} onChange={(event) => onChange("provider", event.target.value)}>
          {section.provider_options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>模型名称</span>
        <input
          className="text-input"
          value={section.model}
          onChange={(event) => onChange("model", event.target.value)}
        />
      </label>
      <label className="field field--span-2">
        <span>API Key</span>
        <input
          className="text-input"
          type="password"
          value={section.api_key}
          placeholder={section.api_key_configured ? "已配置，如需更新请重新输入" : "输入决策模型 API Key"}
          onChange={(event) => onChange("api_key", event.target.value)}
        />
      </label>
      <label className="field field--span-2">
        <span>本地模型路径</span>
        <input
          className="text-input"
          value={section.local_path}
          placeholder="可选：本地模型路径"
          onChange={(event) => onChange("local_path", event.target.value)}
        />
      </label>
      {renderAssistantCard(section.assistant)}
    </div>
  );
}

function renderPerceptionSection(
  section: PerceptionConfigSection,
  onChange: (field: string, value: string | number) => void,
) {
  return (
    <div className="config-form-grid">
      <label className="field">
        <span>VLM Provider</span>
        <select value={section.provider} onChange={(event) => onChange("provider", event.target.value)}>
          {section.provider_options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>模型名称</span>
        <input
          className="text-input"
          value={section.model}
          onChange={(event) => onChange("model", event.target.value)}
        />
      </label>
      <label className="field field--span-2">
        <span>API Key</span>
        <input
          className="text-input"
          type="password"
          value={section.api_key}
          placeholder={section.api_key_configured ? "已配置，如需更新请重新输入" : "输入感知模型 API Key"}
          onChange={(event) => onChange("api_key", event.target.value)}
        />
      </label>
      <label className="field field--span-2">
        <span>本地模型路径</span>
        <input
          className="text-input"
          value={section.local_path}
          placeholder="可选：本地 VLM 路径"
          onChange={(event) => onChange("local_path", event.target.value)}
        />
      </label>
      {renderAssistantCard(section.assistant)}
    </div>
  );
}

function renderExecutionSection(
  section: ExecutionConfigSection,
  onHomePoseChange: (axis: string, value: number) => void,
) {
  return (
    <div className="config-form-grid">
      <div className="field">
        <span>执行模型</span>
        <div className="readonly-card">
          <strong>{section.display_name}</strong>
          <p>执行层模型固定展示，不允许替换。</p>
        </div>
      </div>
      <label className="field">
        <span>模型路径</span>
        <input className="text-input" value={section.model_path} readOnly />
      </label>
      <div className="field field--span-2">
        <span>机械臂初始位置校准</span>
        <div className="home-pose-grid">
          {Object.entries(section.home_pose).map(([axis, value]) => (
            <label className="field" key={axis}>
              <span>{axis.toUpperCase()}</span>
              <input
                className="text-input"
                type="number"
                step="0.01"
                value={value}
                onChange={(event) => onHomePoseChange(axis, Number(event.target.value))}
              />
            </label>
          ))}
        </div>
      </div>
      <div className="key-value-grid field--span-2">
        <div className="kv-card">
          <span>adapter</span>
          <strong>{section.adapter}</strong>
        </div>
        <div className="kv-card">
          <span>backend</span>
          <strong>{section.backend}</strong>
        </div>
        <div className="kv-card">
          <span>safety_policy</span>
          <strong>{section.safety_policy}</strong>
        </div>
        <div className="kv-card">
          <span>stop_mode</span>
          <strong>{section.stop_mode}</strong>
        </div>
      </div>
    </div>
  );
}

function renderFrontendSection(
  section: FrontendSettingsSection,
  onChange: (field: string, value: string | number) => void,
) {
  return (
    <div className="config-form-grid">
      <label className="field">
        <span>端口</span>
        <input
          className="text-input"
          type="number"
          value={section.port}
          onChange={(event) => onChange("port", Number(event.target.value))}
        />
      </label>
      <label className="field">
        <span>最大闭环迭代次数</span>
        <input
          className="text-input"
          type="number"
          value={section.max_iterations}
          onChange={(event) => onChange("max_iterations", Number(event.target.value))}
        />
      </label>
      <label className="field field--span-2">
        <span>执行速度缩放系数</span>
        <input
          className="text-input"
          type="number"
          step="0.1"
          value={section.speed_scale}
          onChange={(event) => onChange("speed_scale", Number(event.target.value))}
        />
      </label>
    </div>
  );
}

export function ConfigPanel() {
  const bootstrap = useWorkbenchStore((state) => state.bootstrap);
  const config = useWorkbenchStore((state) => state.config);
  const configDraft = useWorkbenchStore((state) => state.configDraft);
  const configStatus = useWorkbenchStore((state) => state.configStatus);
  const configDraftStatus = useWorkbenchStore((state) => state.configDraftStatus);
  const configNotice = useWorkbenchStore((state) => state.configNotice);
  const latestError = useWorkbenchStore((state) => state.latestError);
  const latestErrorCode = useWorkbenchStore((state) => state.latestErrorCode);
  const activeConfigTab = useWorkbenchStore((state) => state.activeConfigTab);
  const setActiveConfigTab = useWorkbenchStore((state) => state.setActiveConfigTab);
  const refreshConfig = useWorkbenchStore((state) => state.refreshConfig);
  const saveConfigDraft = useWorkbenchStore((state) => state.saveConfigDraft);
  const resetConfigDraft = useWorkbenchStore((state) => state.resetConfigDraft);
  const updateConfigDraft = useWorkbenchStore((state) => state.updateConfigDraft);
  const updateHomePoseDraft = useWorkbenchStore((state) => state.updateHomePoseDraft);

  const resolvedConfig = configDraft || config || bootstrap?.config;

  if (!resolvedConfig) {
    return null;
  }

  const section = resolvedConfig[activeConfigTab];

  return (
    <PanelShell
      title="模型配置与个性化设置"
      subtitle="覆盖模型选择、API Key、本地路径、机械臂初始位置、执行速度与最大迭代次数。"
      actions={
        <div className="button-row">
          <button type="button" className="button-secondary" onClick={() => void refreshConfig()}>
            刷新配置
          </button>
          <button type="button" className="button-secondary" onClick={resetConfigDraft}>
            回滚草稿
          </button>
          <button type="button" onClick={() => void saveConfigDraft()} disabled={configDraftStatus === "loading"}>
            {configDraftStatus === "loading" ? "提交中" : "保存配置"}
          </button>
        </div>
      }
    >
      <div className="stack">
        <div className="key-value-grid">
          <div className="kv-card">
            <span>config_status</span>
            <strong>{configStatus}</strong>
          </div>
          <div className="kv-card">
            <span>draft_status</span>
            <strong>{configDraftStatus}</strong>
          </div>
          <div className="kv-card">
            <span>config_source</span>
            <strong>{config ? "GET /config" : "bootstrap fallback"}</strong>
          </div>
          <div className="kv-card">
            <span>execution_model</span>
            <strong>{String(bootstrap?.execution_model?.name || "SmolVLA")}</strong>
          </div>
        </div>

        <div className="alert alert-info">{configNotice}</div>
        {configDraftStatus === "error" && latestError ? (
          <div className="alert alert-error">
            <div>{latestError}</div>
            {latestErrorCode ? <code className="inline-code">{latestErrorCode}</code> : null}
          </div>
        ) : null}

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

        {activeConfigTab === "decision"
          ? renderDecisionSection(section as DecisionConfigSection, (field, value) =>
              updateConfigDraft("decision", field, value),
            )
          : null}
        {activeConfigTab === "perception"
          ? renderPerceptionSection(section as PerceptionConfigSection, (field, value) =>
              updateConfigDraft("perception", field, value),
            )
          : null}
        {activeConfigTab === "execution"
          ? renderExecutionSection(section as ExecutionConfigSection, updateHomePoseDraft)
          : null}
        {activeConfigTab === "frontend"
          ? renderFrontendSection(section as FrontendSettingsSection, (field, value) =>
              updateConfigDraft("frontend", field, value),
            )
          : null}
      </div>
    </PanelShell>
  );
}
