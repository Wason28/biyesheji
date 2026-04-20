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

export interface FrontendConfigPayload {
  decision: Record<string, unknown>;
  perception: Record<string, unknown>;
  execution: Record<string, unknown>;
  frontend: Record<string, unknown>;
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
