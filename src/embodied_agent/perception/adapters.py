"""Perception adapter protocols and mock-backed factories."""

from __future__ import annotations

from typing import Protocol

from .config import PerceptionRuntimeConfig
from .contracts import CapturedImage, RobotStateSnapshot
from .errors import AdapterConfigurationError
from .mocks import MockCamera, MockRobotStateClient


class CameraAdapter(Protocol):
    def capture(self) -> CapturedImage:
        ...


class RobotStateAdapter(Protocol):
    def read_state(self) -> RobotStateSnapshot:
        ...


def build_camera_adapter(config: PerceptionRuntimeConfig) -> CameraAdapter:
    if config.camera_backend == "mock":
        return MockCamera(
            camera_id=config.camera_device_id,
            width=config.camera_width,
            height=config.camera_height,
            frame_id=config.camera_frame_id,
        )
    raise AdapterConfigurationError(
        message=f"不支持的 camera backend: {config.camera_backend}",
        backend=config.camera_backend,
    )


def build_robot_state_adapter(config: PerceptionRuntimeConfig) -> RobotStateAdapter:
    if config.robot_state_backend == "mock":
        return MockRobotStateClient(reference_frame=config.robot_state_base_frame)
    raise AdapterConfigurationError(
        message=f"不支持的 robot_state backend: {config.robot_state_backend}",
        backend=config.robot_state_backend,
    )
