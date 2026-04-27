"""Configuration loading helpers for the phase-1 skeleton."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class DecisionConfig:
    llm_provider: str = "minimax"
    llm_model: str = "MiniMax-M2.1"
    llm_api_key: str = ""
    llm_local_path: str = ""
    llm_base_url: str = ""
    max_iterations: int = 10


@dataclass(slots=True)
class PerceptionConfig:
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
    camera_backend_options: dict[str, Any] = field(default_factory=dict)
    robot_state_backend: str = "mock"
    robot_state_topic: str = "/mock/robot_state"
    robot_state_config_path: str = ""
    robot_state_base_frame: str = "base_link"
    robot_state_timeout_s: float = 1.0
    robot_state_base_url: str = ""
    robot_state_headers: dict[str, str] = field(default_factory=dict)
    robot_pythonpath: str = ""


@dataclass(slots=True)
class ExecutionConfig:
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
    workspace_limits: dict[str, list[float]] = field(
        default_factory=lambda: {
            "x": [-0.5, 0.5],
            "y": [-0.5, 0.5],
            "z": [0.0, 0.8],
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


@dataclass(slots=True)
class FrontendConfig:
    port: int = 7860
    max_iterations: int = 10
    speed_scale: float = 1.0
    custom_models: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    decision: DecisionConfig = field(default_factory=DecisionConfig)
    perception: PerceptionConfig = field(default_factory=PerceptionConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    frontend: FrontendConfig = field(default_factory=FrontendConfig)
    vision_model: str = "SmolVLA-0.1B"


def _merge_dataclass(dataclass_type: type[Any], values: dict[str, Any] | None) -> Any:
    values = values or {}
    return dataclass_type(**values)


def _expand_env_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env_values(item) for item in value]
    if isinstance(value, str):
        expanded = os.path.expandvars(value)
        return re.sub(r"\$\{[^}]+\}", "", expanded)
    return value


def load_config(config_path: str | Path) -> AppConfig:
    """Load runtime configuration from YAML."""
    path = Path(config_path)
    raw = _expand_env_values(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    return AppConfig(
        decision=_merge_dataclass(DecisionConfig, raw.get("decision")),
        perception=_merge_dataclass(PerceptionConfig, raw.get("perception")),
        execution=_merge_dataclass(ExecutionConfig, raw.get("execution")),
        frontend=_merge_dataclass(FrontendConfig, raw.get("frontend")),
    )
