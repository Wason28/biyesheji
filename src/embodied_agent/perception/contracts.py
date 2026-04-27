"""Perception contracts, serialization helpers, and output validation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from ..shared.types import ToolEnvelope
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


def _ensure_non_empty_string(value: Any, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise OutputValidationError(f"{field_name} 不能为空", field=field_name)


def _ensure_timestamp(value: Any, *, field_name: str = "timestamp") -> None:
    _ensure_non_empty_string(value, field_name=field_name)


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
    metadata: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "joint_positions": self.joint_positions,
            "ee_pose": self.ee_pose,
            "timestamp": self.timestamp,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
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
    provider_metadata: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "scene_description": self.scene_description,
            "provider": self.provider,
            "model": self.model,
            "confidence": self.confidence,
            "prompt_used": self.prompt_used,
            "structured_observations": self.structured_observations,
            "provider_metadata": self.provider_metadata or {},
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
    _ensure_timestamp(payload.get("timestamp"))

    if not isinstance(resolution, dict):
        raise OutputValidationError("缺少 resolution", field="resolution")
    if not isinstance(resolution.get("width"), int) or not isinstance(resolution.get("height"), int):
        raise OutputValidationError("resolution 必须包含 width/height 整数", field="resolution")

    if not isinstance(camera_parameters, dict):
        raise OutputValidationError("缺少 camera_parameters", field="camera_parameters")
    _ensure_non_empty_string(camera_parameters.get("camera_id"), field_name="camera_parameters.camera_id")
    _ensure_non_empty_string(camera_parameters.get("frame_id"), field_name="camera_parameters.frame_id")


def validate_robot_state_payload(payload: dict[str, Any]) -> None:
    joint_positions = payload.get("joint_positions")
    ee_pose = payload.get("ee_pose")

    _ensure_number_list(joint_positions, field_name="joint_positions")
    _ensure_timestamp(payload.get("timestamp"))
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


def _validate_structured_observations(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise OutputValidationError("structured_observations 必须为对象", field="structured_observations")
    objects = payload.get("objects")
    relations = payload.get("relations")
    robot_grasp_state = payload.get("robot_grasp_state")
    risk_flags = payload.get("risk_flags")
    if not isinstance(objects, list):
        raise OutputValidationError("structured_observations.objects 必须为数组", field="structured_observations.objects")
    if not isinstance(relations, list):
        raise OutputValidationError("structured_observations.relations 必须为数组", field="structured_observations.relations")
    if not isinstance(robot_grasp_state, str) or not robot_grasp_state:
        raise OutputValidationError(
            "structured_observations.robot_grasp_state 不能为空",
            field="structured_observations.robot_grasp_state",
        )
    if not isinstance(risk_flags, list):
        raise OutputValidationError("structured_observations.risk_flags 必须为数组", field="structured_observations.risk_flags")
    for index, item in enumerate(objects):
        if not isinstance(item, dict):
            raise OutputValidationError(
                "structured_observations.objects 元素必须为对象",
                field=f"structured_observations.objects[{index}]",
            )
        _ensure_non_empty_string(item.get("name"), field_name=f"structured_observations.objects[{index}].name")
        _ensure_non_empty_string(item.get("category"), field_name=f"structured_observations.objects[{index}].category")
        if "graspable" in item and not isinstance(item.get("graspable"), bool):
            raise OutputValidationError(
                "structured_observations.objects.graspable 必须为布尔值",
                field=f"structured_observations.objects[{index}].graspable",
            )


def validate_scene_description_payload(payload: dict[str, Any]) -> None:
    _ensure_non_empty_string(payload.get("scene_description"), field_name="scene_description")
    _ensure_non_empty_string(payload.get("provider"), field_name="provider")
    _ensure_non_empty_string(payload.get("model"), field_name="model")
    _ensure_non_empty_string(payload.get("prompt_used"), field_name="prompt_used")
    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
        raise OutputValidationError("confidence 必须位于 [0, 1]", field="confidence")
    _validate_structured_observations(payload.get("structured_observations"))
    provider_metadata = payload.get("provider_metadata")
    if provider_metadata is not None and not isinstance(provider_metadata, dict):
        raise OutputValidationError("provider_metadata 必须为对象", field="provider_metadata")


def build_perception_success_envelope(
    tool_name: str,
    content: Any,
    *,
    metadata: dict[str, Any] | None = None,
) -> ToolEnvelope:
    return {
        "ok": True,
        "status_code": 200,
        "tool_name": tool_name,
        "content": content,
        "message": "ok",
        "metadata": metadata or {},
    }


def build_perception_error_envelope(
    *,
    tool_name: str,
    code: str,
    message: str,
    retriable: bool,
    details: dict[str, Any] | None = None,
    status_code: int = 500,
) -> ToolEnvelope:
    return {
        "ok": False,
        "status_code": status_code,
        "tool_name": tool_name,
        "content": None,
        "message": message,
        "metadata": {
            **(details or {}),
            "error_code": code,
            "retriable": retriable,
        },
    }
