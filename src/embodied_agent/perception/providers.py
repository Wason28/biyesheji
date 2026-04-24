"""VLM provider abstraction with real HTTP-backed and mock fallback providers."""

from __future__ import annotations

import json
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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
TransportResponse = tuple[int, dict[str, str], bytes]
TransportCallable = Callable[[str, str, dict[str, str], bytes, float], TransportResponse]

DEFAULT_SCENE_PROMPT = (
    "请稳定输出桌面场景描述，覆盖物体类别、相对位置、遮挡关系、抓取状态与安全风险。"
)
VISION_RESPONSE_INSTRUCTIONS = (
    "你是桌面具身智能系统的视觉感知模块。"
    "请只返回一个 JSON 对象，字段必须包含 scene_description、confidence、structured_observations。"
    "structured_observations 必须包含 objects、relations、robot_grasp_state、risk_flags。"
)
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
MINIMAX_CHAT_COMPLETIONS_URL = "https://api.minimax.io/v1/chat/completions"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


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


def _default_transport(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes,
    timeout_s: float,
) -> TransportResponse:
    request = Request(url=url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout_s) as response:
            return int(response.status), dict(response.headers.items()), response.read()
    except HTTPError as exc:
        response_headers = dict(exc.headers.items()) if exc.headers is not None else {}
        return int(exc.code), response_headers, exc.read()
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise ConnectionError(str(exc)) from exc


def _resolve_endpoint(base_url: str, *, default_url: str, suffix: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        return default_url
    if normalized.endswith(suffix):
        return normalized
    return f"{normalized}/{suffix}"


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(str(item["text"]))
        return "\n".join(part for part in parts if part.strip()).strip()
    return ""


def _extract_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3:
            candidate = "\n".join(lines[1:-1]).strip()
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise VLMResponseFormatError(message="VLM 返回内容不是合法 JSON") from exc
    if not isinstance(payload, dict):
        raise VLMResponseFormatError(message="VLM 返回内容必须为 JSON 对象")
    return payload


def _normalize_confidence(value: Any) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    return 0.5


def _normalize_structured_observations(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "objects": [],
            "relations": [],
            "robot_grasp_state": "unknown",
            "risk_flags": [],
        }

    objects: list[dict[str, Any]] = []
    raw_objects = value.get("objects")
    if isinstance(raw_objects, list):
        for item in raw_objects:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            category = str(item.get("category", "")).strip()
            if not name or not category:
                continue
            normalized_item: dict[str, Any] = {
                "name": name,
                "category": category,
            }
            if "position_hint" in item and str(item.get("position_hint", "")).strip():
                normalized_item["position_hint"] = str(item["position_hint"]).strip()
            if "graspable" in item:
                normalized_item["graspable"] = bool(item["graspable"])
            objects.append(normalized_item)

    relations = []
    raw_relations = value.get("relations")
    if isinstance(raw_relations, list):
        relations = [str(item).strip() for item in raw_relations if str(item).strip()]

    risk_flags = []
    raw_risk_flags = value.get("risk_flags")
    if isinstance(raw_risk_flags, list):
        risk_flags = [str(item).strip() for item in raw_risk_flags if str(item).strip()]

    robot_grasp_state = str(value.get("robot_grasp_state", "unknown") or "unknown").strip()
    if not robot_grasp_state:
        robot_grasp_state = "unknown"

    return {
        "objects": objects,
        "relations": relations,
        "robot_grasp_state": robot_grasp_state,
        "risk_flags": risk_flags,
    }


def _normalize_scene_payload(payload: dict[str, Any]) -> dict[str, Any]:
    scene_description = ""
    for field_name in ("scene_description", "description", "summary"):
        value = payload.get(field_name)
        if isinstance(value, str) and value.strip():
            scene_description = value.strip()
            break
    if not scene_description:
        raise VLMResponseFormatError(message="VLM 返回缺少 scene_description")

    return {
        "scene_description": scene_description,
        "confidence": _normalize_confidence(payload.get("confidence")),
        "structured_observations": _normalize_structured_observations(payload.get("structured_observations")),
    }


def _decode_json_body(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VLMResponseFormatError(message="VLM 返回不是合法 JSON 响应") from exc
    if not isinstance(payload, dict):
        raise VLMResponseFormatError(message="VLM 返回根对象必须为 JSON 对象")
    return payload


def _error_details_from_body(body: bytes) -> dict[str, Any]:
    text = body.decode("utf-8", errors="ignore").strip()
    if not text:
        return {}
    return {"response_excerpt": text[:300]}


def _build_mock_fallback_reason(settings: ProviderSettings) -> str:
    if settings.provider == "ollama_vision":
        return "未提供本地模型路径或自定义服务地址，保持 mock fallback。"
    return "未提供 API Key 或自定义服务地址，保持 mock fallback。"


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
        fallback_reason: str | None = None,
    ) -> None:
        super().__init__(settings)
        self.fail_on_inference = fail_on_inference
        self.fail_mode = fail_mode
        self.fallback_reason = fallback_reason

    def config_summary(self) -> dict[str, Any]:
        summary = super().config_summary()
        summary.update(
            {
                "mode": "mock_fallback" if self.fallback_reason else "mock",
                "active_provider": "mock_vlm",
                "configured": not bool(self.fallback_reason),
                "status": "attention" if self.fallback_reason else "ready",
            }
        )
        if self.fallback_reason:
            summary["fallback_reason"] = self.fallback_reason
        return summary

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


class HTTPVLMProvider(BaseVLMProvider):
    def __init__(
        self,
        settings: ProviderSettings,
        *,
        endpoint: str,
        mode: str,
        transport: TransportCallable = _default_transport,
    ) -> None:
        super().__init__(settings)
        self.endpoint = endpoint
        self.mode = mode
        self.transport = transport

    def config_summary(self) -> dict[str, Any]:
        summary = super().config_summary()
        summary.update(
            {
                "mode": self.mode,
                "active_provider": self.provider_name,
                "configured": True,
                "status": "configured",
                "endpoint": self.endpoint,
                "transport": "http",
            }
        )
        return summary

    def _request_json(self, payload: dict[str, Any], *, headers: dict[str, str]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **headers,
        }
        try:
            status_code, _, response_body = self.transport(
                "POST",
                self.endpoint,
                request_headers,
                body,
                self.settings.timeout_s,
            )
        except ConnectionError as exc:
            raise VLMServiceUnavailableError(
                provider=self.provider_name,
                model=self.model_name,
                endpoint=self.endpoint,
                reason=str(exc),
            ) from exc

        if status_code in {401, 403}:
            raise VLMAuthenticationError(
                provider=self.provider_name,
                model=self.model_name,
                endpoint=self.endpoint,
                **_error_details_from_body(response_body),
            )
        if status_code == 429:
            raise VLMRateLimitError(
                provider=self.provider_name,
                model=self.model_name,
                endpoint=self.endpoint,
                **_error_details_from_body(response_body),
            )
        if status_code >= 500:
            raise VLMServiceUnavailableError(
                provider=self.provider_name,
                model=self.model_name,
                endpoint=self.endpoint,
                status_code=status_code,
                **_error_details_from_body(response_body),
            )
        if status_code >= 400:
            raise VLMResponseFormatError(
                provider=self.provider_name,
                model=self.model_name,
                endpoint=self.endpoint,
                status_code=status_code,
                **_error_details_from_body(response_body),
            )
        return _decode_json_body(response_body)


class OpenAICompatibleVisionProvider(HTTPVLMProvider):
    def __init__(
        self,
        settings: ProviderSettings,
        *,
        endpoint: str,
        provider_mode: str = "remote",
        transport: TransportCallable = _default_transport,
    ) -> None:
        super().__init__(settings, endpoint=endpoint, mode=provider_mode, transport=transport)

    def _authorization_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        return headers

    def describe_scene(self, request: SceneDescriptionRequest) -> SceneDescriptionResult:
        prompt_used = request.prompt or DEFAULT_SCENE_PROMPT
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": VISION_RESPONSE_INSTRUCTIONS},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_used},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{request.image}"},
                        },
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": self.settings.max_tokens,
        }
        response_payload = self._request_json(payload, headers=self._authorization_headers())
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise VLMResponseFormatError(message="VLM 返回缺少 choices")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise VLMResponseFormatError(message="VLM 返回的 choice 结构不合法")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise VLMResponseFormatError(message="VLM 返回缺少 message")
        content_text = _extract_text_content(message.get("content"))
        if not content_text:
            raise VLMResponseFormatError(message="VLM 返回缺少可解析内容")
        normalized = _normalize_scene_payload(_extract_json_object(content_text))
        metadata = self.config_summary()
        usage = response_payload.get("usage")
        if isinstance(usage, dict):
            metadata["usage"] = dict(usage)
        if isinstance(first_choice.get("finish_reason"), str):
            metadata["finish_reason"] = str(first_choice["finish_reason"])
        response_model = response_payload.get("model")
        if isinstance(response_model, str) and response_model.strip():
            metadata["response_model"] = response_model.strip()

        return SceneDescriptionResult(
            scene_description=normalized["scene_description"],
            provider=self.provider_name,
            model=self.model_name,
            confidence=normalized["confidence"],
            prompt_used=prompt_used,
            structured_observations=normalized["structured_observations"],
            provider_metadata=metadata,
        )


class OllamaVisionProvider(HTTPVLMProvider):
    def __init__(
        self,
        settings: ProviderSettings,
        *,
        endpoint: str,
        transport: TransportCallable = _default_transport,
    ) -> None:
        super().__init__(settings, endpoint=endpoint, mode="local", transport=transport)

    def describe_scene(self, request: SceneDescriptionRequest) -> SceneDescriptionResult:
        prompt_used = request.prompt or DEFAULT_SCENE_PROMPT
        payload = {
            "model": self.model_name,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": VISION_RESPONSE_INSTRUCTIONS,
                },
                {
                    "role": "user",
                    "content": prompt_used,
                    "images": [request.image],
                },
            ],
            "options": {
                "num_predict": self.settings.max_tokens,
            },
        }
        response_payload = self._request_json(payload, headers={})
        message = response_payload.get("message")
        if not isinstance(message, dict):
            raise VLMResponseFormatError(message="Ollama 返回缺少 message")
        content_text = _extract_text_content(message.get("content"))
        if not content_text:
            raise VLMResponseFormatError(message="Ollama 返回缺少可解析内容")
        normalized = _normalize_scene_payload(_extract_json_object(content_text))
        metadata = self.config_summary()
        if isinstance(response_payload.get("total_duration"), int):
            metadata["total_duration"] = int(response_payload["total_duration"])
        if isinstance(response_payload.get("prompt_eval_count"), int):
            metadata["prompt_eval_count"] = int(response_payload["prompt_eval_count"])
        if isinstance(response_payload.get("eval_count"), int):
            metadata["eval_count"] = int(response_payload["eval_count"])
        if isinstance(response_payload.get("done_reason"), str):
            metadata["finish_reason"] = str(response_payload["done_reason"])

        return SceneDescriptionResult(
            scene_description=normalized["scene_description"],
            provider=self.provider_name,
            model=self.model_name,
            confidence=normalized["confidence"],
            prompt_used=prompt_used,
            structured_observations=normalized["structured_observations"],
            provider_metadata=metadata,
        )


def _build_minimax_provider(settings: ProviderSettings) -> BaseVLMProvider:
    if settings.api_key or settings.base_url:
        endpoint = _resolve_endpoint(
            settings.base_url,
            default_url=MINIMAX_CHAT_COMPLETIONS_URL,
            suffix="chat/completions",
        )
        return OpenAICompatibleVisionProvider(settings, endpoint=endpoint, provider_mode="remote")
    return MockVLMProvider(settings, fallback_reason=_build_mock_fallback_reason(settings))



def _build_openai_provider(settings: ProviderSettings) -> BaseVLMProvider:
    if settings.api_key or settings.base_url:
        endpoint = _resolve_endpoint(
            settings.base_url,
            default_url=OPENAI_CHAT_COMPLETIONS_URL,
            suffix="chat/completions",
        )
        return OpenAICompatibleVisionProvider(settings, endpoint=endpoint, provider_mode="remote")
    return MockVLMProvider(settings, fallback_reason=_build_mock_fallback_reason(settings))



def _build_ollama_provider(settings: ProviderSettings) -> BaseVLMProvider:
    if settings.base_url or settings.local_path:
        endpoint = _resolve_endpoint(
            settings.base_url,
            default_url=OLLAMA_CHAT_URL,
            suffix="api/chat",
        )
        return OllamaVisionProvider(settings, endpoint=endpoint)
    return MockVLMProvider(settings, fallback_reason=_build_mock_fallback_reason(settings))


_PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "minimax_mcp_vision": _build_minimax_provider,
    "openai_gpt4o": _build_openai_provider,
    "ollama_vision": _build_ollama_provider,
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
