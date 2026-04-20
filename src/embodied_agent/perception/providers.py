"""VLM provider abstraction and phase-1 mock provider implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

from embodied_agent.shared.config import PerceptionConfig

from .config import PerceptionRuntimeConfig

from .contracts import SceneDescriptionRequest, SceneDescriptionResult
from .errors import (
    UnsupportedProviderError,
    VLMAuthenticationError,
    VLMRateLimitError,
    VLMResponseFormatError,
    VLMServiceUnavailableError,
)

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

ProviderFactory = Callable[["ProviderSettings"], "BaseVLMProvider"]

DEFAULT_SCENE_PROMPT = (
    "请稳定输出桌面场景描述，覆盖物体类别、相对位置、遮挡关系、抓取状态与安全风险。"
)


@dataclass(slots=True)
class ProviderSettings:
    provider: str
    model: str
    api_key: str
    local_path: str
    base_url: str
    timeout_s: float
    max_retries: int
    max_tokens: int

    @classmethod
    def from_perception_config(cls, config: PerceptionConfig | PerceptionRuntimeConfig) -> "ProviderSettings":
        return cls(
            provider=config.vlm_provider,
            model=config.vlm_model,
            api_key=config.vlm_api_key,
            local_path=config.vlm_local_path,
            base_url=config.vlm_base_url,
            timeout_s=config.vlm_timeout_s,
            max_retries=config.vlm_max_retries,
            max_tokens=config.vlm_max_tokens,
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

    def config_summary(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "base_url": self.settings.base_url,
            "local_path": self.settings.local_path,
            "timeout_s": self.settings.timeout_s,
            "max_retries": self.settings.max_retries,
            "max_tokens": self.settings.max_tokens,
            "auth_configured": bool(self.settings.api_key),
        }

    @abstractmethod
    def describe_scene(self, request: SceneDescriptionRequest) -> SceneDescriptionResult:
        """Generate a scene description for the given image."""


class MockVLMProvider(BaseVLMProvider):
    """Single mock provider that simulates all supported provider routes."""

    def __init__(
        self,
        settings: ProviderSettings,
        *,
        fail_on_inference: bool = False,
        fail_mode: str | None = None,
    ) -> None:
        super().__init__(settings)
        self.fail_on_inference = fail_on_inference
        self.fail_mode = fail_mode

    def describe_scene(self, request: SceneDescriptionRequest) -> SceneDescriptionResult:
        if self.fail_mode == "auth":
            raise VLMAuthenticationError(provider=self.provider_name, model=self.model_name)
        if self.fail_mode == "rate_limit":
            raise VLMRateLimitError(provider=self.provider_name, model=self.model_name)
        if self.fail_mode == "invalid_response":
            raise VLMResponseFormatError(provider=self.provider_name, model=self.model_name)
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
            provider_metadata=self.config_summary(),
        )


_PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "minimax_mcp_vision": lambda settings: MockVLMProvider(settings),
    "openai_gpt4o": lambda settings: MockVLMProvider(settings),
    "ollama_vision": lambda settings: MockVLMProvider(settings),
}


def register_vlm_provider(provider_name: str, factory: ProviderFactory) -> None:
    _PROVIDER_FACTORIES[provider_name] = factory



def build_vlm_provider(config: PerceptionConfig | PerceptionRuntimeConfig | ProviderSettings) -> BaseVLMProvider:
    settings = (
        config if isinstance(config, ProviderSettings) else ProviderSettings.from_perception_config(config)
    )
    if settings.provider not in SUPPORTED_VLM_PROVIDERS:
        raise UnsupportedProviderError(settings.provider)
    factory = _PROVIDER_FACTORIES.get(settings.provider)
    if factory is None:
        raise UnsupportedProviderError(settings.provider)
    return factory(settings)
