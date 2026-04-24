"""Shared data structures aligned with the runtime and frontend contracts."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


ActionStatus = Literal["success", "in_progress", "failed"]
RunStatus = Literal["idle", "running", "completed", "failed"]
RunPhase = Literal[
    "trigger",
    "nlu",
    "sensory",
    "assessment",
    "active_perception",
    "task_planning",
    "pre_feedback",
    "motion_control",
    "verification",
    "error_diagnosis",
    "hri",
    "compensation",
    "success_notice",
    "goal_check",
    "state_compression",
    "final_status",
]
RuntimeEventName = Literal[
    "snapshot",
    "phase_started",
    "phase_completed",
    "phase_failed",
    "human_intervention_required",
    "run_completed",
]


class CartesianPosition(TypedDict):
    x: float
    y: float
    z: float


class Quaternion(TypedDict):
    x: float
    y: float
    z: float
    w: float


class EndEffectorPose(TypedDict, total=False):
    position: CartesianPosition
    orientation: Quaternion
    reference_frame: str
    gripper_force: float
    gripper_closed: bool
    holding_object: bool
    estop_reason: str


class RobotState(TypedDict):
    joint_positions: list[float]
    ee_pose: EndEffectorPose


class ExecutionResult(TypedDict, total=False):
    status: ActionStatus
    action_name: str
    message: str
    logs: list[str]


class CapabilitySelection(TypedDict, total=False):
    capability_name: str
    arguments: dict[str, Any]
    action_name: str


class ToolEnvelope(TypedDict, total=False):
    ok: bool
    status_code: int
    tool_name: str
    content: Any
    message: str
    metadata: dict[str, Any]


class FrontendToolDescriptor(TypedDict, total=False):
    name: str
    layer: Literal["perception", "execution"]
    description: str
    input_schema: dict[str, Any]
    capability_names: list[str]


class FrontendConfigPayload(TypedDict):
    decision: dict[str, Any]
    perception: dict[str, Any]
    execution: dict[str, Any]
    frontend: dict[str, Any]


class FrontendRunSnapshot(TypedDict, total=False):
    run_id: str
    status: RunStatus
    current_phase: RunPhase
    current_node: str
    current_task: str
    selected_capability: str
    selected_action: str
    scene_description: str
    scene_observations: dict[str, Any]
    perception_confidence: float
    action_result: ActionStatus
    iteration_count: int
    max_iterations: int
    current_image: str
    robot_state: RobotState
    plan: list[dict[str, Any]]
    pre_execution_feedback: dict[str, Any]
    execution_feedback: dict[str, Any]
    verification_result: dict[str, Any]
    error_diagnosis: dict[str, Any]
    retry_context: dict[str, Any]
    memory_summary: dict[str, Any]
    termination_reason: str
    final_report: dict[str, Any]
    last_node_result: dict[str, Any]
    last_execution: ExecutionResult
    logs: list[dict[str, Any]]
    error: str


class FrontendBootstrapPayload(TypedDict):
    config: FrontendConfigPayload
    execution_model: dict[str, Any]
    tools: list[FrontendToolDescriptor]
    status_fields: list[str]
    execution_capabilities: list[dict[str, Any]]
    execution_safety: dict[str, Any]


class FrontendRuntimeAPI(TypedDict):
    bootstrap: FrontendBootstrapPayload
    config: FrontendConfigPayload


class FrontendRunAPI(TypedDict):
    run: FrontendRunSnapshot


class FrontendRunStatePayload(TypedDict):
    run: FrontendRunSnapshot
    version: int
    terminal: bool
    event: RuntimeEventName
    phase: RunPhase
    timestamp: str


class FrontendRunAcceptedPayload(TypedDict):
    run_id: str
    status: RunStatus
    snapshot_url: str
    events_url: str
    run: FrontendRunSnapshot


class FrontendErrorPayload(TypedDict):
    error: dict[str, Any]


class AgentState(TypedDict):
    user_instruction: str
    task_queue: list[str]
    current_task: str
    current_image: str
    robot_state: RobotState
    scene_description: str
    action_result: ActionStatus
    iteration_count: int
    conversation_history: list[dict[str, Any]]
