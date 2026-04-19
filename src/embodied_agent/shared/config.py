"""Configuration loading helpers for the phase-1 skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class DecisionConfig:
    llm_provider: str = "minimax"
    llm_model: str = "MiniMax-M2.1"
    llm_api_key: str = ""
    max_iterations: int = 10


@dataclass(slots=True)
class PerceptionConfig:
    vlm_provider: str = "minimax_mcp_vision"
    vlm_model: str = "minimax-mcp-vision-latest"
    vlm_api_key: str = ""


@dataclass(slots=True)
class ExecutionConfig:
    vla_model_path: str = "./models/smolvla_finetuned"
    robot_config: str = "./lerobot_configs/my_robot.yaml"
    workspace_limits: dict[str, list[float]] = field(
        default_factory=lambda: {
            "x": [-0.5, 0.5],
            "y": [-0.5, 0.5],
            "z": [0.0, 0.8],
        }
    )


@dataclass(slots=True)
class FrontendConfig:
    port: int = 7860
    max_iterations: int = 10
    speed_scale: float = 1.0


@dataclass(slots=True)
class AppConfig:
    decision: DecisionConfig = field(default_factory=DecisionConfig)
    perception: PerceptionConfig = field(default_factory=PerceptionConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    frontend: FrontendConfig = field(default_factory=FrontendConfig)


def _merge_dataclass(dataclass_type: type[Any], values: dict[str, Any] | None) -> Any:
    values = values or {}
    return dataclass_type(**values)


def load_config(config_path: str | Path) -> AppConfig:
    """Load runtime configuration from YAML."""
    path = Path(config_path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return AppConfig(
        decision=_merge_dataclass(DecisionConfig, raw.get("decision")),
        perception=_merge_dataclass(PerceptionConfig, raw.get("perception")),
        execution=_merge_dataclass(ExecutionConfig, raw.get("execution")),
        frontend=_merge_dataclass(FrontendConfig, raw.get("frontend")),
    )
