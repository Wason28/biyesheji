"""Shared data structures aligned with the project interface baseline."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


ActionStatus = Literal["success", "in_progress", "failed"]


class RobotState(TypedDict):
    joint_positions: list[float]
    ee_pose: dict[str, Any]


class ExecutionResult(TypedDict, total=False):
    status: ActionStatus
    action_name: str
    message: str
    logs: list[str]


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
