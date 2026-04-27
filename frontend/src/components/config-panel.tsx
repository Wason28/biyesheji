import { useState } from "react";
import { PanelShell } from "./panel-shell";
import { useWorkbenchStore } from "../store/workbench";
import { Plus, Trash2 } from "lucide-react";
import type {
  AssistantHint,
  ConfigSectionKey,
  ConfigSectionValue,
  CustomModelConfig,
  DecisionConfigSection,
  ExecutionConfigSection,
  FrontendSettingsSection,
  PerceptionConfigSection,
} from "../types/runtime";

type EditableConfigSectionKey = Exclude<ConfigSectionKey, "vision_model">;

const CONFIG_TABS: Array<{ key: EditableConfigSectionKey | "custom_models"; label: string }> = [
  { key: "decision", label: "决策 LLM" },
  { key: "perception", label: "感知 VLM" },
  { key: "execution", label: "执行层" },
  { key: "frontend", label: "前端参数" },
  { key: "custom_models", label: "自定义模型" },
];

const CAMERA_BACKEND_OPTIONS = ["mock", "opencv"];
const ROBOT_STATE_BACKEND_OPTIONS = ["mock", "mcp_bridge", "lerobot_local"];
const EXECUTION_ADAPTER_OPTIONS = ["mock_lerobot", "mcp_bridge", "lerobot_local"];

function renderTextField(
  label: string,
  value: string | number | undefined,
  onChange: (value: string) => void,
  options?: { placeholder?: string; type?: "text" | "number"; step?: string; span?: boolean; readOnly?: boolean },
) {
  return (
    <label className={options?.span ? "field field--span-2" : "field"}>
      <span>{label}</span>
      <input
        className="text-input"
        type={options?.type || "text"}
        step={options?.step}
        value={value ?? ""}
        placeholder={options?.placeholder}
        readOnly={options?.readOnly}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function renderSelectField(
  label: string,
  value: string | undefined,
  items: string[],
  onChange: (value: string) => void,
  span = false,
) {
  return (
    <label className={span ? "field field--span-2" : "field"}>
      <span>{label}</span>
      <select value={value || ""} onChange={(event) => onChange(event.target.value)}>
        {items.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </label>
  );
}

function renderCheckboxField(
  label: string,
  checked: boolean,
  onChange: (value: boolean) => void,
  hint: string,
) {
  return (
    <label className="field field--span-2">
      <span>{label}</span>
      <div className="readonly-card flex items-center justify-between gap-4">
        <div>
          <strong>{checked ? "已启用" : "已关闭"}</strong>
          <p>{hint}</p>
        </div>
        <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      </div>
    </label>
  );
}

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
  showModelAssistants: boolean,
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
      <label className="field field--span-2">
        <span>兼容网关 Base URL</span>
        <input
          className="text-input"
          value={section.base_url}
          placeholder="可选：OpenAI 兼容网关地址"
          onChange={(event) => onChange("base_url", event.target.value)}
        />
      </label>
      {showModelAssistants ? renderAssistantCard(section.assistant) : null}
    </div>
  );
}

function renderPerceptionSection(
  section: PerceptionConfigSection,
  showModelAssistants: boolean,
  onChange: (field: string, value: string | number | boolean) => void,
) {
  return (
    <div className="config-form-grid">
      {renderSelectField("VLM Provider", section.provider, section.provider_options, (value) => onChange("provider", value))}
      {renderTextField("模型名称", section.model, (value) => onChange("model", value))}
      {renderTextField("API Key", section.api_key, (value) => onChange("api_key", value), {
        placeholder: section.api_key_configured ? "已配置，如需更新请重新输入" : "输入感知模型 API Key",
        span: true,
      })}
      {renderTextField("本地模型路径", section.local_path, (value) => onChange("local_path", value), {
        placeholder: "可选：本地 VLM 路径",
        span: true,
      })}
      {renderTextField("兼容网关 Base URL", section.base_url, (value) => onChange("base_url", value), {
        placeholder: "可选：OpenAI 兼容网关地址",
        span: true,
      })}

      <div className="field field--span-2">
        <span>相机接入</span>
        <div className="config-form-grid">
          {renderSelectField("camera_backend", section.camera_backend, CAMERA_BACKEND_OPTIONS, (value) => onChange("camera_backend", value))}
          {renderTextField("camera_device_id", section.camera_device_id, (value) => onChange("camera_device_id", value), {
            placeholder: "/dev/video0 或 mock_camera_rgb_01",
          })}
          {renderTextField("camera_index", section.camera_index, (value) => onChange("camera_index", Number(value)), {
            type: "number",
          })}
          {renderTextField("camera_frame_id", section.camera_frame_id, (value) => onChange("camera_frame_id", value))}
          {renderTextField("camera_width", section.camera_width, (value) => onChange("camera_width", Number(value)), {
            type: "number",
          })}
          {renderTextField("camera_height", section.camera_height, (value) => onChange("camera_height", Number(value)), {
            type: "number",
          })}
          {renderTextField("camera_fps", section.camera_fps, (value) => onChange("camera_fps", Number(value)), {
            type: "number",
            step: "0.1",
          })}
        </div>
      </div>

      <div className="field field--span-2">
        <span>机器人状态接入</span>
        <div className="config-form-grid">
          {renderSelectField("robot_state_backend", section.robot_state_backend, ROBOT_STATE_BACKEND_OPTIONS, (value) =>
            onChange("robot_state_backend", value),
          )}
          {renderTextField("robot_state_base_frame", section.robot_state_base_frame, (value) =>
            onChange("robot_state_base_frame", value),
          )}
          {renderTextField("robot_state_base_url", section.robot_state_base_url, (value) =>
            onChange("robot_state_base_url", value), {
            placeholder: "桥接模式下填写，例如 http://127.0.0.1:8765",
            span: true,
          })}
          {renderTextField("robot_state_config_path", section.robot_state_config_path, (value) =>
            onChange("robot_state_config_path", value), {
            placeholder: "本地 LeRobot 配置文件路径",
            span: true,
          })}
        </div>
      </div>
      {showModelAssistants ? renderAssistantCard(section.assistant) : null}
    </div>
  );
}

function renderExecutionSection(
  section: ExecutionConfigSection,
  onFieldChange: (field: string, value: string | number | boolean) => void,
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
      {renderSelectField("adapter", section.adapter, EXECUTION_ADAPTER_OPTIONS, (value) => onFieldChange("adapter", value))}
      {renderTextField("robot_base_url", section.robot_base_url, (value) => onFieldChange("robot_base_url", value), {
        placeholder: "桥接模式下填写，例如 http://127.0.0.1:9901",
      })}
      {renderTextField("robot_timeout_s", section.robot_timeout_s, (value) => onFieldChange("robot_timeout_s", Number(value)), {
        type: "number",
        step: "0.1",
      })}
      {renderTextField(
        "telemetry_poll_timeout_s",
        section.telemetry_poll_timeout_s,
        (value) => onFieldChange("telemetry_poll_timeout_s", Number(value)),
        {
          type: "number",
          step: "0.1",
        },
      )}
      {renderTextField("robot_pythonpath", section.robot_pythonpath, (value) => onFieldChange("robot_pythonpath", value), {
        placeholder: "本地 lerobot 源码路径，可为空",
        span: true,
      })}
      {renderCheckboxField(
        "safety_require_precheck",
        Boolean(section.safety_require_precheck),
        (value) => onFieldChange("safety_require_precheck", value),
        "真实动作前先检查连接、心跳、错误码和急停状态。",
      )}
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
        <div className="kv-card">
          <span>precheck</span>
          <strong>{section.safety_require_precheck ? "enabled" : "disabled"}</strong>
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

function CustomModelsSection({ models, onAdd, onRemove, onConfirm, status }: { 
  models: CustomModelConfig[], 
  onAdd: (m: CustomModelConfig) => void, 
  onRemove: (id: string) => void,
  onConfirm: () => void,
  status: "idle" | "loading" | "ready" | "success" | "error"
}) {
  const [newModel, setNewModel] = useState<CustomModelConfig>({ id: "", api: "", url: "" });

  return (
    <div className="stack">
      <div className="config-form-grid border-b border-slate-800/50 pb-6 mb-2">
        <label className="field">
          <span>模型 ID</span>
          <input 
            className="text-input" 
            value={newModel.id} 
            placeholder="例如：my-custom-vlm"
            onChange={e => setNewModel({...newModel, id: e.target.value})} 
          />
        </label>
        <label className="field">
          <span>模型 API</span>
          <input 
            className="text-input" 
            value={newModel.api} 
            placeholder="例如：openai"
            onChange={e => setNewModel({...newModel, api: e.target.value})} 
          />
        </label>
        <label className="field field--span-2">
          <span>Base URL</span>
          <input 
            className="text-input" 
            value={newModel.url} 
            placeholder="例如：https://api.openai.com/v1"
            onChange={e => setNewModel({...newModel, url: e.target.value})} 
          />
        </label>
        <div className="field--span-2 flex justify-end gap-3">
          <button 
            type="button" 
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl transition-all text-sm font-medium border border-slate-700"
            onClick={() => {
              if (newModel.id && newModel.api && newModel.url) {
                onAdd(newModel);
                setNewModel({ id: "", api: "", url: "" });
              }
            }}
          >
            <Plus size={16} /> 添加到列表
          </button>
          <button 
            type="button" 
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-all text-sm font-bold shadow-lg shadow-indigo-500/20"
            onClick={onConfirm}
            disabled={status === "loading"}
          >
            {status === "loading" ? "提交中..." : "确认并保存配置"}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <span className="text-[10px] opacity-40 uppercase tracking-widest">已添加的模型</span>
        {models.length === 0 ? (
          <div className="text-center py-8 border border-dashed border-slate-800 rounded-2xl opacity-40 text-sm italic">
            暂无自定义模型配置
          </div>
        ) : (
          models.map(model => (
            <div key={model.id} className="flex items-center justify-between p-4 rounded-2xl border border-slate-800/50 bg-slate-900/30 group hover:border-indigo-500/30 transition-all">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <strong className="text-indigo-400">{model.id}</strong>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase">{model.api}</span>
                </div>
                <code className="text-[10px] opacity-50 truncate max-w-xs">{model.url}</code>
              </div>
              <button 
                type="button"
                className="p-2 text-slate-500 hover:text-rose-500 hover:bg-rose-500/10 rounded-lg transition-all"
                onClick={() => onRemove(model.id)}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

interface ConfigPanelProps {
  embedded?: boolean;
}

export function ConfigPanel({ embedded = false }: ConfigPanelProps) {
  const bootstrap = useWorkbenchStore((state) => state.bootstrap);
  const config = useWorkbenchStore((state) => state.config);
  const configDraft = useWorkbenchStore((state) => state.configDraft);
  const configStatus = useWorkbenchStore((state) => state.configStatus);
  const configDraftStatus = useWorkbenchStore((state) => state.configDraftStatus);
  const configNotice = useWorkbenchStore((state) => state.configNotice);
  const showModelAssistants = useWorkbenchStore((state) => state.showModelAssistants);
  const toggleModelAssistants = useWorkbenchStore((state) => state.toggleModelAssistants);
  const latestError = useWorkbenchStore((state) => state.latestError);
  const latestErrorCode = useWorkbenchStore((state) => state.latestErrorCode);
  const activeConfigTab = useWorkbenchStore((state) => state.activeConfigTab);
  const setActiveConfigTab = useWorkbenchStore((state) => state.setActiveConfigTab);
  const refreshConfig = useWorkbenchStore((state) => state.refreshConfig);
  const saveConfigDraft = useWorkbenchStore((state) => state.saveConfigDraft);
  const resetConfigDraft = useWorkbenchStore((state) => state.resetConfigDraft);
  const updateConfigDraft = useWorkbenchStore((state) => state.updateConfigDraft);
  const updateHomePoseDraft = useWorkbenchStore((state) => state.updateHomePoseDraft);
  const addCustomModel = useWorkbenchStore((state) => state.addCustomModel);
  const removeCustomModel = useWorkbenchStore((state) => state.removeCustomModel);

  const resolvedConfig = configDraft || config || bootstrap?.config;

  if (!resolvedConfig) {
    return (
      <PanelShell title="模型设置" subtitle="正在加载配置或连接后端..." compact={embedded}>
        <div className="flex flex-col items-center justify-center py-12 opacity-50 italic text-sm">
          正在尝试从后端获取配置...
        </div>
      </PanelShell>
    );
  }

  const section = activeConfigTab !== "custom_models" ? (resolvedConfig[activeConfigTab as ConfigSectionKey] as ConfigSectionValue) : null;

  return (
    <PanelShell
      title="模型设置"
      subtitle="管理决策、感知与执行相关配置，并保留清晰的保存与回滚反馈。"
      actions={
        <div className="button-row">
          <button type="button" className="button-secondary" onClick={() => void refreshConfig()}>
            刷新配置
          </button>
          <button type="button" className="button-secondary" onClick={resetConfigDraft}>
            回滚草稿
          </button>
          <button type="button" className="button-secondary" onClick={toggleModelAssistants}>
            {showModelAssistants ? "隐藏助手" : "显示助手"}
          </button>
          <button type="button" onClick={() => void saveConfigDraft()} disabled={configDraftStatus === "loading"}>
            {configDraftStatus === "loading" ? "提交中" : "保存配置"}
          </button>
        </div>
      }
      compact={embedded}
      className={embedded ? "settings-section" : undefined}
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

        <div className="config-content-area">
          {activeConfigTab === "decision"
            ? renderDecisionSection(section as DecisionConfigSection, showModelAssistants, (field, value) =>
                updateConfigDraft("decision", field, value),
              )
            : null}
          {activeConfigTab === "perception"
            ? renderPerceptionSection(section as PerceptionConfigSection, showModelAssistants, (field, value) =>
                updateConfigDraft("perception", field, value),
              )
            : null}
          {activeConfigTab === "execution"
            ? renderExecutionSection(
                section as ExecutionConfigSection,
                (field, value) => updateConfigDraft("execution", field, value),
                updateHomePoseDraft,
              )
            : null}
          {activeConfigTab === "frontend"
            ? renderFrontendSection(section as FrontendSettingsSection, (field, value) =>
                updateConfigDraft("frontend", field, value),
              )
            : null}
          {activeConfigTab === "custom_models"
            ? <CustomModelsSection 
                models={(resolvedConfig.frontend as FrontendSettingsSection).custom_models || []} 
                onAdd={addCustomModel} 
                onRemove={removeCustomModel} 
                onConfirm={() => void saveConfigDraft()}
                status={configDraftStatus}
              />
            : null}

          {/* 全局保存按钮：确保在所有选项卡下都可见 */}
          {activeConfigTab !== "custom_models" && (
            <div className="mt-8 flex justify-end border-t border-slate-800/50 pt-6">
              <button 
                type="button" 
                className="flex items-center gap-2 px-8 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-all text-sm font-bold shadow-lg shadow-indigo-500/20"
                onClick={() => void saveConfigDraft()}
                disabled={configDraftStatus === "loading"}
              >
                {configDraftStatus === "loading" ? "提交保存中..." : "确认并保存当前配置"}
              </button>
            </div>
          )}
        </div>
      </div>
    </PanelShell>
  );
}
