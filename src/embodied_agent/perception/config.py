"""Perception runtime configuration derived from shared application config."""

from __future__ import annotations

from dataclasses import dataclass, field

from embodied_agent.shared.config import PerceptionConfig as SharedPerceptionConfig


@dataclass(slots=True)
class PerceptionRuntimeConfig:
    vlm_provider: str = "minimax_mcp_vision"
    vlm_model: str = "minimax-mcp-vision-latest"
    vlm_api_key: str = ""
    vlm_local_path: str = ""
    vlm_base_url: str = ""
    vlm_timeout_s: float = 15.0
    vlm_max_retries: int = 2
    vlm_max_tokens: int = 512
    camera_backend: str = "mock"
    camera_device_id: str = "mock_camera_rgb_01"
    camera_frame_id: str = "camera_color_optical_frame"
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: float = 30.0
    camera_index: int = 0
    camera_backend_options: dict[str, object] = field(default_factory=dict)
    robot_state_backend: str = "mock"
    robot_state_topic: str = "/mock/robot_state"
    robot_state_config_path: str = ""
    robot_state_base_frame: str = "base_link"
    robot_state_timeout_s: float = 1.0
    robot_state_base_url: str = ""
    robot_state_headers: dict[str, str] = field(default_factory=dict)
    robot_pythonpath: str = ""


def build_perception_runtime_config(
    shared_config: SharedPerceptionConfig | None = None,
) -> PerceptionRuntimeConfig:
    config = shared_config or SharedPerceptionConfig()
    return PerceptionRuntimeConfig(
        vlm_provider=config.vlm_provider,
        vlm_model=config.vlm_model,
        vlm_api_key=config.vlm_api_key,
        vlm_local_path=config.vlm_local_path,
        vlm_base_url=config.vlm_base_url,
        vlm_timeout_s=config.vlm_timeout_s,
        vlm_max_retries=config.vlm_max_retries,
        vlm_max_tokens=config.vlm_max_tokens,
        camera_backend=config.camera_backend,
        camera_device_id=config.camera_device_id,
        camera_frame_id=config.camera_frame_id,
        camera_width=config.camera_width,
        camera_height=config.camera_height,
        camera_fps=config.camera_fps,
        camera_index=config.camera_index,
        camera_backend_options=dict(config.camera_backend_options),
        robot_state_backend=config.robot_state_backend,
        robot_state_topic=config.robot_state_topic,
        robot_state_config_path=config.robot_state_config_path,
        robot_state_base_frame=config.robot_state_base_frame,
        robot_state_timeout_s=config.robot_state_timeout_s,
        robot_state_base_url=config.robot_state_base_url,
        robot_state_headers=dict(config.robot_state_headers),
        robot_pythonpath=config.robot_pythonpath,
    )
