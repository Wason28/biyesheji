"""Execution-layer typed structures aligned with shared state and config."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

from embodied_agent.shared.types import ExecutionResult, RobotState


ToolName = Literal["move_to", "move_home", "grasp", "release", "run_smolvla"]
CapabilityName = Literal["pick_and_place", "return_home", "release_object"]
SafetyStage = Literal[
    "input_validation",
    "preflight",
    "adapter_dispatch",
    "telemetry_check",
    "emergency_stop",
]


class Quaternion(TypedDict):
    x: float
    y: float
    z: float
    w: float


class CartesianPose(TypedDict):
    x: float
    y: float
    z: float
    orientation: Quaternion


class MoveToInput(TypedDict):
    x: float
    y: float
    z: float
    orientation: Quaternion | list[float] | tuple[float, float, float, float]


class GraspInput(TypedDict):
    force: float


class SmolVLAInput(TypedDict):
    task_description: str
    current_image: str
    robot_state: RobotState


class PlannedAction(TypedDict):
    tool: ToolName
    arguments: dict[str, Any]
    reason: str


class ActionContract(TypedDict):
    action_name: ToolName
    tool_name: ToolName
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    capability_names: list[CapabilityName]
    safety_stages: list[SafetyStage]
    estop_on_failure: bool


class CapabilityContract(TypedDict):
    capability_name: CapabilityName
    description: str
    default_action: ToolName
    available_actions: list[ToolName]
    execution_mode: Literal["atomic", "vla"]
    required_tools: list[ToolName]
    fixed_model: bool


class SafetyBoundary(TypedDict, total=False):
    policy: str
    stop_mode: str
    adapter_name: str
    smolvla_backend: str
    checked_stages: list[SafetyStage]
    estop_engaged: bool
    stop_reason: str
    manual_reset_required: bool
    action_timeout_s: float
    communication_retries: int


class ExecutionToolResult(ExecutionResult, total=False):
    tool_name: ToolName
    error_code: str
    mock: bool
    validated_params: dict[str, Any]
    safety_checks: list[str]
    telemetry: dict[str, float]
    robot_state: RobotState
    executed_plan: list[PlannedAction]
    capability_name: CapabilityName
    capability_contract: CapabilityContract
    action_contract: ActionContract
    safety_boundary: SafetyBoundary


class ToolDefinition(TypedDict):
    name: ToolName
    description: str
    input_schema: dict[str, Any]
    output_schema: NotRequired[dict[str, Any]]
    capability_names: NotRequired[list[CapabilityName]]


class MCPToolCall(TypedDict, total=False):
    tool: ToolName
    arguments: dict[str, Any]


class ExecutionModelDescriptor(TypedDict):
    name: str
    model_path: str
    backend: str
    adapter: str
    mutable: bool
    capability_names: list[CapabilityName]


class ExecutionRuntimeProfile(TypedDict):
    adapter: dict[str, Any]
    smolvla_backend: dict[str, Any]
    safety_boundary: SafetyBoundary


class MCPServerDescription(TypedDict):
    name: str
    version: str
    tools: list[ToolDefinition]
    capabilities: NotRequired[list[CapabilityContract]]
    safety_boundary: NotRequired[SafetyBoundary]
    execution_model: NotRequired[ExecutionModelDescriptor]
    runtime_profile: NotRequired[ExecutionRuntimeProfile]
