export type RunStatus = "idle" | "running" | "completed" | "failed" | "cancelled";
export type RunPhase =
  | "trigger"
  | "nlu"
  | "sensory"
  | "assessment"
  | "active_perception"
  | "task_planning"
  | "pre_feedback"
  | "motion_control"
  | "verification"
  | "error_diagnosis"
  | "hri"
  | "compensation"
  | "success_notice"
  | "goal_check"
  | "state_compression"
  | "final_status";
export type RuntimeEventName =
  | "snapshot"
  | "phase_started"
  | "phase_completed"
  | "phase_failed"
  | "human_intervention_required"
  | "run_completed";

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
  base_url: string;
  assistant?: AssistantHint;
}

export interface PerceptionConfigSection {
  provider: string;
  model: string;
  provider_options: string[];
  api_key: string;
  api_key_configured: boolean;
  local_path: string;
  base_url: string;
  camera_backend?: string;
  camera_device_id?: string;
  camera_frame_id?: string;
  camera_width?: number;
  camera_height?: number;
  camera_fps?: number;
  camera_index?: number;
  robot_state_backend?: string;
  robot_state_base_url?: string;
  robot_state_config_path?: string;
  robot_state_base_frame?: string;
  assistant?: AssistantHint;
}

export interface ExecutionConfigSection {
  display_name: string;
  model_path: string;
  home_joint_positions?: number[];
  home_pose: Record<string, number>;
  adapter: string;
  backend: string;
  robot_base_url?: string;
  robot_timeout_s?: number;
  telemetry_poll_timeout_s?: number;
  safety_require_precheck?: boolean;
  robot_pythonpath?: string;
  safety_policy: string;
  stop_mode: string;
  mutable: boolean;
}

export interface CustomModelConfig {
  id: string;
  api: string;
  url: string;
}

export interface FrontendSettingsSection {
  port: number;
  max_iterations: number;
  speed_scale: number;
  custom_models: CustomModelConfig[];
}

export interface FrontendConfigPayload {
  decision: DecisionConfigSection;
  perception: PerceptionConfigSection;
  execution: ExecutionConfigSection;
  frontend: FrontendSettingsSection;
  vision_model?: string;
}

export interface FrontendRunSnapshot {
  run_id: string;
  status: RunStatus;
  user_instruction?: string;
  assistant_response?: string;
  current_phase?: RunPhase;
  current_node?: string;
  current_task?: string;
  selected_capability?: string;
  selected_action?: string;
  scene_description?: string;
  scene_observations?: Record<string, unknown>;
  perception_confidence?: number;
  action_result?: string;
  iteration_count?: number;
  max_iterations?: number;
  current_image?: string;
  robot_state?: Record<string, unknown>;
  plan?: Array<Record<string, unknown>>;
  pre_execution_feedback?: Record<string, unknown>;
  execution_feedback?: Record<string, unknown>;
  verification_result?: Record<string, unknown>;
  error_diagnosis?: Record<string, unknown>;
  retry_context?: Record<string, unknown>;
  memory_summary?: Record<string, unknown>;
  termination_reason?: string;
  final_report?: Record<string, unknown>;
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
  execution_runtime_profile?: Record<string, unknown>;
}

export interface FrontendRunStatePayload {
  run: FrontendRunSnapshot;
  version: number;
  terminal: boolean;
  event: RuntimeEventName;
  phase: RunPhase;
  timestamp: string;
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
