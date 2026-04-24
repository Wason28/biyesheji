"""Decision LLM provider abstraction with real HTTP-backed and heuristic fallback planning."""

from __future__ import annotations

import json
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from embodied_agent.shared.config import DecisionConfig

SUPPORTED_DECISION_PROVIDERS = {"minimax", "openai", "ollama"}

TransportResponse = tuple[int, dict[str, str], bytes]
TransportCallable = Callable[[str, str, dict[str, str], bytes, float], TransportResponse]

PLANNING_SYSTEM_PROMPT = (
    "你是桌面具身智能体的任务规划器。"
    "请只返回一个 JSON 对象，字段可以包含 task_queue、selected_capability、selected_action、selected_action_args、reason。"
    "不要输出 markdown，不要输出解释性前缀。"
)
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
MINIMAX_CHAT_COMPLETIONS_URL = "https://api.minimax.io/v1/chat/completions"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


@dataclass(slots=True)
class DecisionProviderSettings:
    provider: str
    model: str
    api_key: str
    local_path: str
    timeout_s: float = 15.0
    max_tokens: int = 512

    @classmethod
    def from_decision_config(cls, config: DecisionConfig) -> "DecisionProviderSettings":
        return cls(
            provider=config.llm_provider,
            model=config.llm_model,
            api_key=config.llm_api_key,
            local_path=config.llm_local_path,
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
    payload = json.loads(candidate)
    if not isinstance(payload, dict):
        raise ValueError("decision payload must be a JSON object")
    return payload


class DecisionProviderError(Exception):
    pass


class DecisionProviderAuthError(DecisionProviderError):
    pass


class DecisionProviderRateLimitError(DecisionProviderError):
    pass


class DecisionProviderResponseError(DecisionProviderError):
    pass


class DecisionProviderUnavailableError(DecisionProviderError):
    pass


class BaseDecisionProvider(ABC):
    def __init__(self, settings: DecisionProviderSettings) -> None:
        self.settings = settings

    def summary(self) -> dict[str, Any]:
        return {
            "provider": self.settings.provider,
            "model": self.settings.model,
            "local_path": self.settings.local_path,
            "auth_configured": bool(self.settings.api_key),
        }

    @abstractmethod
    def plan(self, *, instruction: str, current_task: str, scene_description: str, scene_observations: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class MockDecisionProvider(BaseDecisionProvider):
    def __init__(self, settings: DecisionProviderSettings, *, fallback_reason: str) -> None:
        super().__init__(settings)
        self.fallback_reason = fallback_reason

    def summary(self) -> dict[str, Any]:
        summary = super().summary()
        summary.update(
            {
                "mode": "mock_fallback",
                "configured": False,
                "status": "attention",
                "fallback_reason": self.fallback_reason,
            }
        )
        return summary

    def plan(self, *, instruction: str, current_task: str, scene_description: str, scene_observations: dict[str, Any]) -> dict[str, Any]:
        return {}


class OpenAICompatibleDecisionProvider(BaseDecisionProvider):
    def __init__(
        self,
        settings: DecisionProviderSettings,
        *,
        endpoint: str,
        mode: str,
        transport: TransportCallable = _default_transport,
    ) -> None:
        super().__init__(settings)
        self.endpoint = endpoint
        self.mode = mode
        self.transport = transport

    def summary(self) -> dict[str, Any]:
        summary = super().summary()
        summary.update(
            {
                "mode": self.mode,
                "configured": True,
                "status": "configured",
                "endpoint": self.endpoint,
            }
        )
        return summary

    def _authorization_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        return headers

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
            raise DecisionProviderUnavailableError(str(exc)) from exc

        if status_code in {401, 403}:
            raise DecisionProviderAuthError("decision provider auth failed")
        if status_code == 429:
            raise DecisionProviderRateLimitError("decision provider rate limited")
        if status_code >= 500:
            raise DecisionProviderUnavailableError(f"decision provider status {status_code}")
        if status_code >= 400:
            raise DecisionProviderResponseError(f"decision provider status {status_code}")
        try:
            decoded = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DecisionProviderResponseError("decision provider returned invalid json") from exc
        if not isinstance(decoded, dict):
            raise DecisionProviderResponseError("decision provider root must be json object")
        return decoded

    def plan(self, *, instruction: str, current_task: str, scene_description: str, scene_observations: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "instruction": instruction,
                            "current_task": current_task,
                            "scene_description": scene_description,
                            "scene_observations": scene_observations,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": self.settings.max_tokens,
        }
        response_payload = self._request_json(payload, headers=self._authorization_headers())
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise DecisionProviderResponseError("decision provider response missing choices")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise DecisionProviderResponseError("decision provider response missing message")
        content_text = _extract_text_content(message.get("content"))
        if not content_text:
            raise DecisionProviderResponseError("decision provider response missing content")
        plan_payload = _extract_json_object(content_text)
        plan_payload["provider_metadata"] = {
            **self.summary(),
            "finish_reason": choices[0].get("finish_reason", ""),
            "usage": dict(response_payload.get("usage", {})) if isinstance(response_payload.get("usage"), dict) else {},
        }
        return plan_payload


class OllamaDecisionProvider(OpenAICompatibleDecisionProvider):
    def plan(self, *, instruction: str, current_task: str, scene_description: str, scene_observations: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.settings.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "instruction": instruction,
                            "current_task": current_task,
                            "scene_description": scene_description,
                            "scene_observations": scene_observations,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "options": {"num_predict": self.settings.max_tokens},
        }
        response_payload = self._request_json(payload, headers={})
        message = response_payload.get("message")
        if not isinstance(message, dict):
            raise DecisionProviderResponseError("ollama decision response missing message")
        content_text = _extract_text_content(message.get("content"))
        if not content_text:
            raise DecisionProviderResponseError("ollama decision response missing content")
        plan_payload = _extract_json_object(content_text)
        plan_payload["provider_metadata"] = {
            **self.summary(),
            "finish_reason": response_payload.get("done_reason", ""),
        }
        return plan_payload


ProviderFactory = Callable[[DecisionProviderSettings], BaseDecisionProvider]


def _build_openai_provider(settings: DecisionProviderSettings) -> BaseDecisionProvider:
    if settings.api_key:
        return OpenAICompatibleDecisionProvider(
            settings,
            endpoint=OPENAI_CHAT_COMPLETIONS_URL,
            mode="remote",
        )
    return MockDecisionProvider(settings, fallback_reason="未配置 API Key，保留 heuristic fallback。")



def _build_minimax_provider(settings: DecisionProviderSettings) -> BaseDecisionProvider:
    if settings.api_key:
        return OpenAICompatibleDecisionProvider(
            settings,
            endpoint=MINIMAX_CHAT_COMPLETIONS_URL,
            mode="remote",
        )
    return MockDecisionProvider(settings, fallback_reason="未配置 API Key，保留 heuristic fallback。")



def _build_ollama_provider(settings: DecisionProviderSettings) -> BaseDecisionProvider:
    if settings.local_path:
        return OllamaDecisionProvider(
            settings,
            endpoint=OLLAMA_CHAT_URL,
            mode="local",
        )
    return MockDecisionProvider(settings, fallback_reason="未配置本地模型路径，保留 heuristic fallback。")


_PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "openai": _build_openai_provider,
    "minimax": _build_minimax_provider,
    "ollama": _build_ollama_provider,
}



def build_decision_provider(config: DecisionConfig | DecisionProviderSettings) -> BaseDecisionProvider:
    settings = config if isinstance(config, DecisionProviderSettings) else DecisionProviderSettings.from_decision_config(config)
    if settings.provider not in SUPPORTED_DECISION_PROVIDERS:
        raise ValueError(f"unsupported decision provider: {settings.provider}")
    return _PROVIDER_FACTORIES[settings.provider](settings)
