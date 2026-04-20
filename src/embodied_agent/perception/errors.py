"""Perception-layer error types with stable upstream-facing payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PerceptionError(Exception):
    """Base exception for perception failures."""

    code: str
    message: str
    retriable: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": "error",
            "error": {
                "code": self.code,
                "message": self.message,
                "retriable": self.retriable,
                "details": self.details,
            },
        }


class CameraDisconnectedError(PerceptionError):
    def __init__(self, message: str = "摄像头未连接或初始化失败", **details: Any) -> None:
        super().__init__(
            code="PERCEPTION_CAMERA_DISCONNECTED",
            message=message,
            retriable=True,
            details=details,
        )


class RobotCommunicationError(PerceptionError):
    def __init__(self, message: str = "机器人状态读取失败", **details: Any) -> None:
        super().__init__(
            code="PERCEPTION_ROBOT_COMMUNICATION_FAILURE",
            message=message,
            retriable=True,
            details=details,
        )


class VLMServiceUnavailableError(PerceptionError):
    def __init__(self, message: str = "VLM 服务不可用", **details: Any) -> None:
        super().__init__(
            code="PERCEPTION_VLM_SERVICE_UNAVAILABLE",
            message=message,
            retriable=True,
            details=details,
        )


class OutputValidationError(PerceptionError):
    def __init__(self, message: str = "感知输出校验失败", **details: Any) -> None:
        super().__init__(
            code="PERCEPTION_OUTPUT_VALIDATION_FAILURE",
            message=message,
            retriable=False,
            details=details,
        )


class UnsupportedProviderError(PerceptionError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            code="PERCEPTION_UNSUPPORTED_PROVIDER",
            message=f"不支持的 VLM provider: {provider}",
            retriable=False,
            details={"provider": provider},
        )




class VLMAuthenticationError(PerceptionError):
    def __init__(self, message: str = "VLM 鉴权失败", **details: Any) -> None:
        super().__init__(
            code="PERCEPTION_VLM_AUTHENTICATION_FAILURE",
            message=message,
            retriable=False,
            details=details,
        )


class VLMRateLimitError(PerceptionError):
    def __init__(self, message: str = "VLM 调用触发限流", **details: Any) -> None:
        super().__init__(
            code="PERCEPTION_VLM_RATE_LIMITED",
            message=message,
            retriable=True,
            details=details,
        )


class VLMResponseFormatError(PerceptionError):
    def __init__(self, message: str = "VLM 返回格式不合法", **details: Any) -> None:
        super().__init__(
            code="PERCEPTION_VLM_INVALID_RESPONSE",
            message=message,
            retriable=False,
            details=details,
        )


class AdapterConfigurationError(PerceptionError):
    def __init__(self, message: str = "感知适配器配置不合法", **details: Any) -> None:
        super().__init__(
            code="PERCEPTION_ADAPTER_CONFIGURATION_ERROR",
            message=message,
            retriable=False,
            details=details,
        )
