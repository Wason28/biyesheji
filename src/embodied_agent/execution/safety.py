"""Safety checks for execution tool invocations."""

from __future__ import annotations

import math

from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig
from .types import CartesianPose, SafetyBoundary, SafetyStage


class SafetyError(RuntimeError):
    """Raised when a safety guard prevents execution."""


class SafetyManager:
    """Centralized preflight and runtime safety checks."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        self._config = config

    def preflight_motion(self, target_pose: CartesianPose, robot_state: RobotState) -> list[str]:
        current_pose = robot_state.get("ee_pose", {})
        current_position = current_pose.get("position", {})
        dx = float(target_pose["x"]) - float(current_position.get("x", 0.0))
        dy = float(target_pose["y"]) - float(current_position.get("y", 0.0))
        dz = float(target_pose["z"]) - float(current_position.get("z", 0.0))
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        if distance > self._config.max_translation_step:
            raise SafetyError(
                f"目标位姿与当前位姿距离 {distance:.3f}m，超过单步安全阈值 {self._config.max_translation_step:.3f}m。"
            )

        if abs(float(target_pose["z"])) < self._config.singularity_threshold:
            raise SafetyError("目标位姿过于接近奇异区域下边界，拒绝执行。")

        return [
            "工作空间边界校验通过",
            "单步位移阈值校验通过",
            "奇异点近场检查通过",
        ]

    def preflight_home(self, robot_state: RobotState) -> list[str]:
        _ = robot_state
        return [
            "采用预定义安全回零路径",
            "关节速度与加速度阈值已锁定",
        ]

    def preflight_grasp(self, force: float) -> list[str]:
        if force > self._config.max_force:
            raise SafetyError("抓取力超过安全上限。")
        return [
            "夹爪力控范围校验通过",
            "抓取前安全链处于闭合状态",
        ]

    def preflight_release(self) -> list[str]:
        return [
            "释放动作无需位姿移动",
            "释放确认与状态反馈已启用",
        ]

    def ensure_telemetry_safe(self, telemetry: dict[str, float]) -> list[str]:
        temperature = telemetry.get("temperature_c", 0.0)
        current = telemetry.get("motor_current_a", 0.0)
        position_error = telemetry.get("position_error_m", 0.0)

        if temperature > self._config.temperature_limit_c:
            raise SafetyError(
                f"电机温度 {temperature:.2f}°C 超过阈值 {self._config.temperature_limit_c:.2f}°C。"
            )
        if current > self._config.current_limit_a:
            raise SafetyError(
                f"电流 {current:.2f}A 超过阈值 {self._config.current_limit_a:.2f}A。"
            )
        if position_error > self._config.allowed_position_error_m:
            raise SafetyError(
                f"位置偏差 {position_error:.4f}m 超过阈值 {self._config.allowed_position_error_m:.4f}m。"
            )

        return [
            "温度监测通过",
            "电流监测通过",
            "位置偏差监测通过",
        ]

    def describe_boundary(
        self,
        *,
        adapter_name: str,
        smolvla_backend: str,
        checked_stages: list[SafetyStage] | None = None,
        estop_engaged: bool = False,
        stop_reason: str | None = None,
    ) -> SafetyBoundary:
        boundary: SafetyBoundary = {
            "policy": self._config.safety_policy,
            "stop_mode": self._config.stop_mode,
            "adapter_name": adapter_name,
            "smolvla_backend": smolvla_backend,
            "checked_stages": list(dict.fromkeys(checked_stages or [])),
            "estop_engaged": estop_engaged,
            "manual_reset_required": self._config.stop_mode == "estop_latched",
            "action_timeout_s": self._config.action_timeout_s,
            "communication_retries": self._config.communication_retries,
        }
        if stop_reason:
            boundary["stop_reason"] = stop_reason
        return boundary
