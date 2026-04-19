"""Execution-layer typed structures aligned with shared state and config."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from embodied_agent.shared.types import ExecutionResult, RobotState


ToolName = Literal["move_to", "move_home", "grasp", "release", "run_smolvla"]


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


class ExecutionToolResult(ExecutionResult, total=False):
    tool_name: ToolName
    error_code: str
    mock: bool
    validated_params: dict[str, Any]
    safety_checks: list[str]
    telemetry: dict[str, float]
    robot_state: RobotState
    executed_plan: list[PlannedAction]


class ToolDefinition(TypedDict):
    name: ToolName
    description: str
    input_schema: dict[str, Any]


class MCPToolCall(TypedDict, total=False):
    tool: ToolName
    arguments: dict[str, Any]


class MCPServerDescription(TypedDict):
    name: str
    version: str
    tools: list[ToolDefinition]
