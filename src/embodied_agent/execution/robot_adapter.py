"""Mock LeRobot adapter used by the phase-1 execution layer."""

from __future__ import annotations

from copy import deepcopy
from typing import Callable, TypeVar

from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig
from .types import CartesianPose


class AdapterError(RuntimeError):
    """Raised when the robot adapter cannot complete a request."""


T = TypeVar("T")


class MockLeRobotAdapter:
    """In-memory mock of a LeRobot-compatible robot adapter."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        self._config = config
        self._estopped = False
        self._holding_object = False
        self._state: RobotState = {
            "joint_positions": list(config.home_joint_positions),
            "ee_pose": {
                **config.home_pose,
                "orientation": dict(config.default_orientation),
            },
        }

    def _ensure_ready(self) -> None:
        if self._estopped:
            raise AdapterError("机器人处于急停状态，请人工复位后再执行。")

    def _with_retry(self, action_name: str, operation: Callable[[], T]) -> T:
        attempts = self._config.communication_retries + 1
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                self._ensure_ready()
                return operation()
            except AdapterError as error:
                last_error = error
        raise AdapterError(f"{action_name} 通讯重试失败: {last_error}") from last_error

    def sync_state(self) -> RobotState:
        return deepcopy(self._state)

    def snapshot_state(self) -> RobotState:
        return deepcopy(self._state)

    def move_to_pose(self, pose: CartesianPose) -> RobotState:
        def operation() -> RobotState:
            self._state["ee_pose"] = {
                "x": pose["x"],
                "y": pose["y"],
                "z": pose["z"],
                "orientation": dict(pose["orientation"]),
            }
            return deepcopy(self._state)

        return self._with_retry("move_to", operation)

    def move_home(self) -> RobotState:
        def operation() -> RobotState:
            self._state["joint_positions"] = list(self._config.home_joint_positions)
            self._state["ee_pose"] = {
                **self._config.home_pose,
                "orientation": dict(self._config.default_orientation),
            }
            return deepcopy(self._state)

        return self._with_retry("move_home", operation)

    def close_gripper(self, force: float) -> RobotState:
        def operation() -> RobotState:
            self._holding_object = force >= max(self._config.min_force, 5.0)
            self._state["ee_pose"]["gripper_force"] = force
            self._state["ee_pose"]["gripper_closed"] = True
            self._state["ee_pose"]["holding_object"] = self._holding_object
            return deepcopy(self._state)

        return self._with_retry("grasp", operation)

    def open_gripper(self) -> RobotState:
        def operation() -> RobotState:
            self._holding_object = False
            self._state["ee_pose"]["gripper_force"] = 0.0
            self._state["ee_pose"]["gripper_closed"] = False
            self._state["ee_pose"]["holding_object"] = self._holding_object
            return deepcopy(self._state)

        return self._with_retry("release", operation)

    def read_telemetry(self) -> dict[str, float]:
        return {
            "temperature_c": 32.0,
            "motor_current_a": 1.2,
            "position_error_m": 0.001,
        }

    def emergency_stop(self, reason: str) -> None:
        self._estopped = True
        self._state["ee_pose"]["estop_reason"] = reason

    def clear_emergency_stop(self) -> None:
        self._estopped = False
