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
    robot_adapter: str = "mock_lerobot"
    smolvla_backend: str = "mock_smolvla"
    robot_base_url: str = ""
    robot_headers: dict[str, str] = field(default_factory=dict)
    robot_timeout_s: float = 2.0
    telemetry_poll_timeout_s: float = 1.0
    safety_require_precheck: bool = True
    robot_pythonpath: str = ""
    safety_policy: str = "fail_closed"
    stop_mode: str = "estop_latched"
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
    max_servo_rotation_step_deg: float = 90.0
    servo_min_angle_deg: float = -180.0
    servo_max_angle_deg: float = 180.0
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
        robot_adapter=config.robot_adapter,
        smolvla_backend=config.smolvla_backend,
        robot_base_url=config.robot_base_url,
        robot_headers=dict(config.robot_headers),
        robot_timeout_s=config.robot_timeout_s,
        telemetry_poll_timeout_s=config.telemetry_poll_timeout_s,
        safety_require_precheck=config.safety_require_precheck,
        robot_pythonpath=config.robot_pythonpath,
        safety_policy=config.safety_policy,
        stop_mode=config.stop_mode,
        workspace_limits=workspace_limits,
        home_joint_positions=[float(value) for value in config.home_joint_positions],
        home_pose=dict(config.home_pose),
    )
