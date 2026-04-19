"""Execution runtime configuration derived from shared application config."""

from __future__ import annotations

from dataclasses import dataclass, field

from embodied_agent.shared.config import ExecutionConfig as SharedExecutionConfig

from .types import Quaternion


@dataclass(slots=True)
class ExecutionSafetyConfig:
    """Runtime safety profile for the phase-1 mock executor."""

    vla_model_path: str = "./models/smolvla_finetuned"
    robot_config: str = "./lerobot_configs/my_robot.yaml"
    workspace_limits: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {
            "x": (-0.5, 0.5),
            "y": (-0.5, 0.5),
            "z": (0.0, 0.8),
        }
    )
    home_joint_positions: list[float] = field(default_factory=lambda: [0.0] * 6)
    home_pose: dict[str, float] = field(
        default_factory=lambda: {
            "x": 0.0,
            "y": 0.0,
            "z": 0.4,
        }
    )
    default_orientation: Quaternion = field(
        default_factory=lambda: {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "w": 1.0,
        }
    )
    max_force: float = 40.0
    min_force: float = 1.0
    max_translation_step: float = 0.35
    max_joint_velocity: float = 1.0
    max_joint_acceleration: float = 1.5
    action_timeout_s: float = 5.0
    communication_retries: int = 2
    temperature_limit_c: float = 70.0
    current_limit_a: float = 4.0
    allowed_position_error_m: float = 0.02
    singularity_threshold: float = 0.05


def build_execution_safety_config(
    shared_config: SharedExecutionConfig | None = None,
) -> ExecutionSafetyConfig:
    """Map shared execution config into the richer runtime safety profile."""

    config = shared_config or SharedExecutionConfig()
    workspace_limits = {
        axis: tuple(bounds)  # type: ignore[arg-type]
        for axis, bounds in config.workspace_limits.items()
    }
    return ExecutionSafetyConfig(
        vla_model_path=config.vla_model_path,
        robot_config=config.robot_config,
        workspace_limits=workspace_limits,
    )
