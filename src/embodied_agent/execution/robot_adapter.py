"""Robot adapter boundary and mock LeRobot implementation for execution."""

from __future__ import annotations

from copy import deepcopy
from typing import Callable, TypeVar

from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig
from .types import CartesianPose


class AdapterError(RuntimeError):
    """Raised when the robot adapter cannot complete a request."""


T = TypeVar("T")


class BaseRobotAdapter:
    """Minimal robot adapter boundary for phase-2 execution wiring."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        self._config = config
        self._estopped = False
        self._last_stop_reason = ""

    @property
    def adapter_name(self) -> str:
        return "robot_adapter"

    @property
    def estopped(self) -> bool:
        return self._estopped

    @property
    def last_stop_reason(self) -> str:
        return self._last_stop_reason

    def sync_state(self) -> RobotState:
        raise NotImplementedError

    def load_state(self, robot_state: RobotState) -> RobotState:
        raise NotImplementedError

    def snapshot_state(self) -> RobotState:
        raise NotImplementedError

    def move_to_pose(self, pose: CartesianPose) -> RobotState:
        raise NotImplementedError

    def move_home(self) -> RobotState:
        raise NotImplementedError

    def close_gripper(self, force: float) -> RobotState:
        raise NotImplementedError

    def open_gripper(self) -> RobotState:
        raise NotImplementedError

    def read_telemetry(self) -> dict[str, float]:
        raise NotImplementedError

    def emergency_stop(self, reason: str) -> None:
        raise NotImplementedError

    def clear_emergency_stop(self) -> None:
        raise NotImplementedError


class MockLeRobotAdapter(BaseRobotAdapter):
    """In-memory mock of a LeRobot-compatible robot adapter."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        super().__init__(config)
        self._holding_object = False
        self._state: RobotState = {
            "joint_positions": list(config.home_joint_positions),
            "ee_pose": {
                "position": {
                    **config.home_pose,
                },
                "orientation": dict(config.default_orientation),
                "reference_frame": "base_link",
            },
        }

    @property
    def adapter_name(self) -> str:
        return "mock_lerobot"

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

    def load_state(self, robot_state: RobotState) -> RobotState:
        self._state = deepcopy(robot_state)
        return deepcopy(self._state)

    def snapshot_state(self) -> RobotState:
        return deepcopy(self._state)

    def move_to_pose(self, pose: CartesianPose) -> RobotState:
        def operation() -> RobotState:
            self._state["ee_pose"] = {
                "position": {
                    "x": pose["x"],
                    "y": pose["y"],
                    "z": pose["z"],
                },
                "orientation": dict(pose["orientation"]),
                "reference_frame": str(self._state["ee_pose"].get("reference_frame", "base_link")),
            }
            return deepcopy(self._state)

        return self._with_retry("move_to", operation)

    def move_home(self) -> RobotState:
        def operation() -> RobotState:
            self._state["joint_positions"] = list(self._config.home_joint_positions)
            self._state["ee_pose"] = {
                "position": {
                    **self._config.home_pose,
                },
                "orientation": dict(self._config.default_orientation),
                "reference_frame": "base_link",
            }
            return deepcopy(self._state)

        return self._with_retry("move_home", operation)

    def close_gripper(self, force: float) -> RobotState:
        def operation() -> RobotState:
            self._holding_object = force >= max(self._config.min_force, 5.0)
            ee_pose = dict(self._state["ee_pose"])
            ee_pose["gripper_force"] = force
            ee_pose["gripper_closed"] = True
            ee_pose["holding_object"] = self._holding_object
            self._state["ee_pose"] = ee_pose
            return deepcopy(self._state)

        return self._with_retry("grasp", operation)

    def open_gripper(self) -> RobotState:
        def operation() -> RobotState:
            self._holding_object = False
            ee_pose = dict(self._state["ee_pose"])
            ee_pose["gripper_force"] = 0.0
            ee_pose["gripper_closed"] = False
            ee_pose["holding_object"] = self._holding_object
            self._state["ee_pose"] = ee_pose
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
        self._last_stop_reason = reason
        ee_pose = dict(self._state["ee_pose"])
        ee_pose["estop_reason"] = reason
        self._state["ee_pose"] = ee_pose

    def clear_emergency_stop(self) -> None:
        self._estopped = False
        self._last_stop_reason = ""


RobotAdapterFactory = Callable[[ExecutionSafetyConfig], BaseRobotAdapter]


_ADAPTER_FACTORIES: dict[str, RobotAdapterFactory] = {
    "mock_lerobot": MockLeRobotAdapter,
}


def register_robot_adapter(adapter_name: str, factory: RobotAdapterFactory) -> None:
    _ADAPTER_FACTORIES[adapter_name] = factory


def build_robot_adapter(config: ExecutionSafetyConfig) -> BaseRobotAdapter:
    factory = _ADAPTER_FACTORIES.get(config.robot_adapter)
    if factory is None:
        raise AdapterError(f"不支持的 robot adapter: {config.robot_adapter}")
    return factory(config)
