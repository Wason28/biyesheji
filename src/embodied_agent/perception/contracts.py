"""Perception contracts, serialization helpers, and output validation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from .errors import OutputValidationError


def _ensure_base64(value: str) -> None:
    try:
        base64.b64decode(value, validate=True)
    except Exception as exc:  # pragma: no cover - defensive branch
        raise OutputValidationError("图像不是合法的 base64 编码", field="image_base64") from exc


def _ensure_number_list(values: list[float], *, field_name: str) -> None:
    if not isinstance(values, list) or not values:
        raise OutputValidationError(f"{field_name} 必须是非空数值数组", field=field_name)
    if not all(isinstance(item, (int, float)) for item in values):
        raise OutputValidationError(f"{field_name} 必须只包含数值", field=field_name)


@dataclass(slots=True)
class CapturedImage:
    image_base64: str
    timestamp: str
    resolution: dict[str, int]
    camera_parameters: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "image_base64": self.image_base64,
            "timestamp": self.timestamp,
            "resolution": self.resolution,
            "camera_parameters": self.camera_parameters,
        }
        validate_image_payload(payload)
        return payload


@dataclass(slots=True)
class RobotStateSnapshot:
    joint_positions: list[float]
    ee_pose: dict[str, Any]
    timestamp: str

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "joint_positions": self.joint_positions,
            "ee_pose": self.ee_pose,
            "timestamp": self.timestamp,
        }
        validate_robot_state_payload(payload)
        return payload


@dataclass(slots=True)
class SceneDescriptionRequest:
    image: str
    prompt: str | None = None


@dataclass(slots=True)
class SceneDescriptionResult:
    scene_description: str
    provider: str
    model: str
    confidence: float
    prompt_used: str
    structured_observations: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "scene_description": self.scene_description,
            "provider": self.provider,
            "model": self.model,
            "confidence": self.confidence,
            "prompt_used": self.prompt_used,
            "structured_observations": self.structured_observations,
        }
        validate_scene_description_payload(payload)
        return payload


def validate_image_payload(payload: dict[str, Any]) -> None:
    image_base64 = payload.get("image_base64")
    resolution = payload.get("resolution")
    camera_parameters = payload.get("camera_parameters")

    if not isinstance(image_base64, str) or not image_base64:
        raise OutputValidationError("缺少 image_base64", field="image_base64")
    _ensure_base64(image_base64)

    if not isinstance(resolution, dict):
        raise OutputValidationError("缺少 resolution", field="resolution")
    if not isinstance(resolution.get("width"), int) or not isinstance(resolution.get("height"), int):
        raise OutputValidationError("resolution 必须包含 width/height 整数", field="resolution")

    if not isinstance(camera_parameters, dict) or "camera_id" not in camera_parameters:
        raise OutputValidationError("camera_parameters 缺少 camera_id", field="camera_parameters")


def validate_robot_state_payload(payload: dict[str, Any]) -> None:
    joint_positions = payload.get("joint_positions")
    ee_pose = payload.get("ee_pose")

    _ensure_number_list(joint_positions, field_name="joint_positions")
    if not isinstance(ee_pose, dict):
        raise OutputValidationError("缺少 ee_pose", field="ee_pose")

    position = ee_pose.get("position")
    orientation = ee_pose.get("orientation")
    reference_frame = ee_pose.get("reference_frame")

    if not isinstance(position, dict) or not {"x", "y", "z"}.issubset(position):
        raise OutputValidationError("ee_pose.position 必须包含 x/y/z", field="ee_pose.position")
    if not isinstance(orientation, dict) or not {"x", "y", "z", "w"}.issubset(orientation):
        raise OutputValidationError(
            "ee_pose.orientation 必须包含 x/y/z/w",
            field="ee_pose.orientation",
        )
    if not isinstance(reference_frame, str) or not reference_frame:
        raise OutputValidationError("ee_pose.reference_frame 不能为空", field="ee_pose.reference_frame")


def validate_scene_description_payload(payload: dict[str, Any]) -> None:
    scene_description = payload.get("scene_description")
    confidence = payload.get("confidence")

    if not isinstance(scene_description, str) or not scene_description.strip():
        raise OutputValidationError("scene_description 不能为空", field="scene_description")
    if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
        raise OutputValidationError("confidence 必须位于 [0, 1]", field="confidence")
