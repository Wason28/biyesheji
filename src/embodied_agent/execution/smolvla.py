"""SmolVLA backend boundary and mock implementation for execution."""

from __future__ import annotations

from typing import Callable

from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig
from .types import PlannedAction


class SmolVLAError(RuntimeError):
    """Raised when SmolVLA planning fails."""


class BaseSmolVLAAdapter:
    """Minimal SmolVLA backend boundary for phase-2 execution wiring."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        self._config = config

    @property
    def backend_name(self) -> str:
        return "smolvla_backend"

    def plan(
        self,
        task_description: str,
        current_image: str,
        robot_state: RobotState,
    ) -> list[PlannedAction]:
        raise NotImplementedError


class MockSmolVLAAdapter(BaseSmolVLAAdapter):
    """Produces deterministic mock plans for local integration tests."""

    @property
    def backend_name(self) -> str:
        return "mock_smolvla"

    def plan(
        self,
        task_description: str,
        current_image: str,
        robot_state: RobotState,
    ) -> list[PlannedAction]:
        if not task_description.strip():
            raise SmolVLAError("任务描述为空，无法生成动作序列。")
        if not current_image.strip():
            raise SmolVLAError("图像引用为空，无法生成动作序列。")

        ee_pose = robot_state.get("ee_pose", {})
        position = ee_pose.get("position", {})
        current_x = float(position.get("x", 0.0))
        current_y = float(position.get("y", 0.0))
        current_z = float(position.get("z", self._config.home_pose["z"]))
        target_z = min(
            max(current_z - 0.05, self._config.workspace_limits["z"][0] + 0.05),
            self._config.workspace_limits["z"][1],
        )
        grasp_force = min(max(8.0, self._config.min_force), self._config.max_force)

        plan: list[PlannedAction] = [
            {
                "tool": "move_to",
                "arguments": {
                    "x": current_x,
                    "y": current_y,
                    "z": target_z,
                    "orientation": dict(self._config.default_orientation),
                },
                "reason": f"SmolVLA mock 对图像 {current_image} 生成接近目标的预抓取位姿。",
            }
        ]

        if "release" in task_description.lower():
            plan.append(
                {
                    "tool": "release",
                    "arguments": {},
                    "reason": "任务描述包含 release，执行释放动作。",
                }
            )
        else:
            plan.append(
                {
                    "tool": "grasp",
                    "arguments": {"force": grasp_force},
                    "reason": "默认抓取策略：闭合夹爪完成 mock 抓取。",
                }
            )

        plan.append(
            {
                "tool": "move_home",
                "arguments": {},
                "reason": "动作结束后回到安全 home 位姿。",
            }
        )
        return plan


SmolVLAFactory = Callable[[ExecutionSafetyConfig], BaseSmolVLAAdapter]


_SMOLVLA_FACTORIES: dict[str, SmolVLAFactory] = {
    "mock_smolvla": MockSmolVLAAdapter,
}


def register_smolvla_backend(backend_name: str, factory: SmolVLAFactory) -> None:
    _SMOLVLA_FACTORIES[backend_name] = factory


def build_smolvla_backend(config: ExecutionSafetyConfig) -> BaseSmolVLAAdapter:
    factory = _SMOLVLA_FACTORIES.get(config.smolvla_backend)
    if factory is None:
        raise SmolVLAError(f"不支持的 SmolVLA backend: {config.smolvla_backend}")
    return factory(config)
