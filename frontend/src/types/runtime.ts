export type RunStatus = "idle" | "running" | "completed" | "failed";

export interface FrontendToolDescriptor {
  name: string;
  layer: "perception" | "execution";
  description?: string;
  input_schema?: Record<string, unknown>;
  capability_names?: string[];
}

export interface FrontendToolsPayload {
  tools: FrontendToolDescriptor[];
}

export interface AssistantHint {
  title: string;
  status: string;
  message: string;
  detected_models?: Array<{
    provider: string;
    model: string;
    configured: boolean;
  }>;
}

export interface DecisionConfigSection {
  provider: string;
  model: string;
  provider_options: string[];
  api_key: string;
  api_key_configured: boolean;
  local_path: string;
  assistant?: AssistantHint;
}

export interface PerceptionConfigSection {
  provider: string;
  model: string;
  provider_options: string[];
  api_key: string;
  api_key_configured: boolean;
  local_path: string;
  assistant?: AssistantHint;
}

export interface ExecutionConfigSection {
  display_name: string;
  model_path: string;
  home_pose: Record<string, number>;
  adapter: string;
  backend: string;
  safety_policy: string;
  stop_mode: string;
  mutable: boolean;
}

export interface FrontendSettingsSection {
  port: number;
  max_iterations: number;
  speed_scale: number;
}

export interface FrontendConfigPayload {
  decision: DecisionConfigSection;
  perception: PerceptionConfigSection;
  execution: ExecutionConfigSection;
  frontend: FrontendSettingsSection;
}

export interface FrontendRunSnapshot {
  run_id: string;
  status: RunStatus;
  current_node?: string;
  current_task?: string;
  selected_capability?: string;
  selected_action?: string;
  scene_description?: string;
  scene_observations?: Record<string, unknown>;
  action_result?: string;
  iteration_count?: number;
  max_iterations?: number;
  current_image?: string;
  robot_state?: Record<string, unknown>;
  last_node_result?: Record<string, unknown>;
  last_execution?: Record<string, unknown>;
  logs?: Array<Record<string, unknown>>;
  error?: string;
}

export interface FrontendBootstrapPayload {
  config: FrontendConfigPayload;
  execution_model: Record<string, unknown>;
  tools: FrontendToolDescriptor[];
  status_fields: string[];
  execution_capabilities: Array<Record<string, unknown>>;
  execution_safety: Record<string, unknown>;
}

export interface FrontendRunStatePayload {
  run: FrontendRunSnapshot;
  version: number;
  terminal: boolean;
}

export interface FrontendRunAcceptedPayload {
  run_id: string;
  status: RunStatus;
  snapshot_url: string;
  events_url: string;
  run: FrontendRunSnapshot;
}

export interface FrontendErrorPayload {
  error: {
    code: string;
    message: string;
  };
}

export type ConfigSectionKey = keyof FrontendConfigPayload;
export type ConfigSectionValue = FrontendConfigPayload[ConfigSectionKey];
