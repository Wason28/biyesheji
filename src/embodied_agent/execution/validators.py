"""Validation helpers for execution tools."""

from __future__ import annotations

import math
from typing import Any

from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig
from .types import CartesianPose, Quaternion


class ValidationError(ValueError):
    """Raised when a tool input fails validation."""


def require_mapping(name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{name} 必须是对象类型。")
    return value


def require_non_empty_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} 不能为空。")
    return value.strip()


def require_float(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{name} 必须是数值。")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValidationError(f"{name} 必须是有限数值。")
    return numeric


def normalize_quaternion(orientation: Any) -> Quaternion:
    if isinstance(orientation, dict):
        source = {key: require_float(f"orientation.{key}", orientation.get(key)) for key in ("x", "y", "z", "w")}
    elif isinstance(orientation, (list, tuple)) and len(orientation) == 4:
        source = {
            "x": require_float("orientation[0]", orientation[0]),
            "y": require_float("orientation[1]", orientation[1]),
            "z": require_float("orientation[2]", orientation[2]),
            "w": require_float("orientation[3]", orientation[3]),
        }
    else:
        raise ValidationError("orientation 必须是包含 x/y/z/w 的对象或长度为 4 的序列。")

    norm = math.sqrt(sum(component * component for component in source.values()))
    if norm <= 1e-8:
        raise ValidationError("orientation 不能是零四元数。")

    return {
        axis: component / norm
        for axis, component in source.items()
    }


def validate_workspace_value(axis: str, value: float, config: ExecutionSafetyConfig) -> float:
    limits = config.workspace_limits.get(axis)
    if limits is None:
        raise ValidationError(f"未配置 {axis} 轴工作空间。")
    lower, upper = limits
    if not lower <= value <= upper:
        raise ValidationError(
            f"{axis}={value:.3f} 超出安全范围 [{lower:.3f}, {upper:.3f}]。"
        )
    return value


def validate_cartesian_pose(
    x: Any,
    y: Any,
    z: Any,
    orientation: Any,
    config: ExecutionSafetyConfig,
) -> CartesianPose:
    pose_x = validate_workspace_value("x", require_float("x", x), config)
    pose_y = validate_workspace_value("y", require_float("y", y), config)
    pose_z = validate_workspace_value("z", require_float("z", z), config)
    return {
        "x": pose_x,
        "y": pose_y,
        "z": pose_z,
        "orientation": normalize_quaternion(orientation),
    }


def validate_force(force: Any, config: ExecutionSafetyConfig) -> float:
    grasp_force = require_float("force", force)
    if not config.min_force <= grasp_force <= config.max_force:
        raise ValidationError(
            f"force={grasp_force:.2f} 超出安全夹取范围 [{config.min_force:.2f}, {config.max_force:.2f}]。"
        )
    return grasp_force


def validate_robot_state(robot_state: Any) -> RobotState:
    state = require_mapping("robot_state", robot_state)
    joints = state.get("joint_positions")
    ee_pose = state.get("ee_pose")

    if not isinstance(joints, list) or not joints:
        raise ValidationError("robot_state.joint_positions 必须是非空数组。")
    for index, joint in enumerate(joints):
        require_float(f"robot_state.joint_positions[{index}]", joint)

    ee_pose_mapping = require_mapping("robot_state.ee_pose", ee_pose)
    for field_name in ("x", "y", "z"):
        if field_name in ee_pose_mapping:
            require_float(f"robot_state.ee_pose.{field_name}", ee_pose_mapping[field_name])

    return {
        "joint_positions": [float(joint) for joint in joints],
        "ee_pose": ee_pose_mapping,
    }


def validate_image_reference(current_image: Any) -> str:
    image_ref = require_non_empty_text("current_image", current_image)
    return image_ref


def validate_task_description(task_description: Any) -> str:
    return require_non_empty_text("task_description", task_description)
