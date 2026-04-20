"""Frontend-facing contracts for the phase-3 backend layer."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from ..shared.types import ActionStatus, ExecutionResult, RobotState


RunStatus = Literal["idle", "running", "completed", "failed"]


class FrontendToolDescriptor(TypedDict, total=False):
    name: str
    layer: Literal["perception", "execution"]
    description: str
    input_schema: dict[str, Any]
    capability_names: list[str]


class FrontendToolsPayload(TypedDict):
    tools: list[FrontendToolDescriptor]


class FrontendConfigPayload(TypedDict):
    decision: dict[str, Any]
    perception: dict[str, Any]
    execution: dict[str, Any]
    frontend: dict[str, Any]


class FrontendRunSnapshot(TypedDict, total=False):
    run_id: str
    status: RunStatus
    current_node: str
    current_task: str
    selected_capability: str
    selected_action: str
    scene_description: str
    scene_observations: dict[str, Any]
    action_result: ActionStatus
    iteration_count: int
    max_iterations: int
    current_image: str
    robot_state: RobotState
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


class FrontendRunAcceptedPayload(TypedDict):
    run_id: str
    status: RunStatus
    snapshot_url: str
    events_url: str
    run: FrontendRunSnapshot


class FrontendErrorPayload(TypedDict):
    error: dict[str, Any]
