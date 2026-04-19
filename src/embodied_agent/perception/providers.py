"""VLM provider abstraction and phase-1 mock provider implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from embodied_agent.shared.config import PerceptionConfig

from .contracts import SceneDescriptionRequest, SceneDescriptionResult
from .errors import UnsupportedProviderError, VLMServiceUnavailableError

SUPPORTED_VLM_PROVIDERS = {
    "minimax_mcp_vision",
    "openai_gpt4o",
    "ollama_vision",
}

PROVIDER_CAPABILITIES: dict[str, dict[str, Any]] = {
    "minimax_mcp_vision": {"vision": True, "structured_output": True, "local": False},
    "openai_gpt4o": {"vision": True, "structured_output": True, "local": False},
    "ollama_vision": {"vision": True, "structured_output": True, "local": True},
}

DEFAULT_SCENE_PROMPT = (
    "请稳定输出桌面场景描述，覆盖物体类别、相对位置、遮挡关系、抓取状态与安全风险。"
)


@dataclass(slots=True)
class ProviderSettings:
    provider: str
    model: str
    api_key: str

    @classmethod
    def from_perception_config(cls, config: PerceptionConfig) -> "ProviderSettings":
        return cls(
            provider=config.vlm_provider,
            model=config.vlm_model,
            api_key=config.vlm_api_key,
        )


class BaseVLMProvider(ABC):
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    @property
    def provider_name(self) -> str:
        return self.settings.provider

    @property
    def model_name(self) -> str:
        return self.settings.model

    @abstractmethod
    def describe_scene(self, request: SceneDescriptionRequest) -> SceneDescriptionResult:
        """Generate a scene description for the given image."""


class MockVLMProvider(BaseVLMProvider):
    """Single mock provider that simulates all supported provider routes."""

    def __init__(self, settings: ProviderSettings, *, fail_on_inference: bool = False) -> None:
        super().__init__(settings)
        self.fail_on_inference = fail_on_inference

    def describe_scene(self, request: SceneDescriptionRequest) -> SceneDescriptionResult:
        if self.fail_on_inference:
            raise VLMServiceUnavailableError(provider=self.provider_name, model=self.model_name)

        prompt_used = request.prompt or DEFAULT_SCENE_PROMPT
        description = (
            "桌面中央存在一个可抓取的小方块，位于机械臂末端前方偏左；"
            "右后方有空置区域；当前未检测到夹爪闭合抓取，环境无遮挡。"
        )

        return SceneDescriptionResult(
            scene_description=description,
            provider=self.provider_name,
            model=self.model_name,
            confidence=0.91,
            prompt_used=prompt_used,
            structured_observations={
                "objects": [
                    {
                        "name": "cube",
                        "category": "target_object",
                        "position_hint": "front_left_of_ee",
                        "graspable": True,
                    }
                ],
                "relations": ["cube is in front-left of end effector"],
                "robot_grasp_state": "open",
                "risk_flags": [],
            },
        )


def build_vlm_provider(config: PerceptionConfig | ProviderSettings) -> BaseVLMProvider:
    settings = (
        config if isinstance(config, ProviderSettings) else ProviderSettings.from_perception_config(config)
    )
    if settings.provider not in SUPPORTED_VLM_PROVIDERS:
        raise UnsupportedProviderError(settings.provider)
    return MockVLMProvider(settings)
