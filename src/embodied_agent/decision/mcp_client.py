"""Minimal MCP client adapter with mock-friendly tool dispatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Callable, Protocol, TypedDict

from ..shared.types import ExecutionResult, ToolEnvelope

ToolHandler = Callable[[dict[str, Any]], Any]


class MCPResponse(ToolEnvelope, total=False):
    pass


class MCPClientProtocol(Protocol):
    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> MCPResponse:
        ...

    def get_image(self) -> MCPResponse:
        ...

    def get_robot_state(self) -> MCPResponse:
        ...

    def describe_scene(self, image: str, prompt: str | None = None) -> MCPResponse:
        ...

    def run_smolvla(
        self,
        task_description: str,
        current_image: str,
        robot_state: dict[str, Any],
    ) -> MCPResponse:
        ...


@dataclass(slots=True)
class MinimalMCPClient:
    """Registry-based MCP adapter used by the phase-1 decision skeleton."""

    tool_registry: dict[str, ToolHandler] = field(default_factory=dict)
    auto_mock: bool = True

    def __post_init__(self) -> None:
        if self.auto_mock and not self.tool_registry:
            self._register_default_mock_tools()

    def register_tool(self, tool_name: str, handler: ToolHandler) -> None:
        self.tool_registry[tool_name] = handler

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> MCPResponse:
        arguments = arguments or {}
        handler = self.tool_registry.get(tool_name)
        if handler is None:
            return {
                "ok": False,
                "status_code": 404,
                "tool_name": tool_name,
                "content": None,
                "message": f"tool '{tool_name}' is not registered",
                "metadata": {"arguments": arguments},
            }

        started_at = perf_counter()
        try:
            result = handler(arguments)
            elapsed_ms = round((perf_counter() - started_at) * 1000, 3)
            if isinstance(result, dict) and any(key in result for key in {"ok", "status_code", "tool_name", "content", "metadata"}):
                metadata = dict(result.get("metadata", {}))
                metadata.setdefault("arguments", arguments)
                metadata.setdefault("elapsed_ms", elapsed_ms)
                return {
                    "ok": bool(result.get("ok", True)),
                    "status_code": int(result.get("status_code", 200)),
                    "tool_name": str(result.get("tool_name", tool_name)),
                    "content": result.get("content"),
                    "message": str(result.get("message", "ok")),
                    "metadata": metadata,
                }
            return {
                "ok": True,
                "status_code": 200,
                "tool_name": tool_name,
                "content": result,
                "message": "ok",
                "metadata": {
                    "arguments": arguments,
                    "elapsed_ms": elapsed_ms,
                },
            }
        except Exception as exc:  # pragma: no cover - defensive path
            elapsed_ms = round((perf_counter() - started_at) * 1000, 3)
            return {
                "ok": False,
                "status_code": 500,
                "tool_name": tool_name,
                "content": None,
                "message": str(exc),
                "metadata": {
                    "arguments": arguments,
                    "elapsed_ms": elapsed_ms,
                },
            }

    def get_image(self) -> MCPResponse:
        return self.call_tool("get_image")

    def get_robot_state(self) -> MCPResponse:
        return self.call_tool("get_robot_state")

    def describe_scene(self, image: str, prompt: str | None = None) -> MCPResponse:
        return self.call_tool(
            "describe_scene",
            {
                "image": image,
                "prompt": prompt or "",
            },
        )

    def run_smolvla(
        self,
        task_description: str,
        current_image: str,
        robot_state: dict[str, Any],
    ) -> MCPResponse:
        return self.call_tool(
            "run_smolvla",
            {
                "task_description": task_description,
                "current_image": current_image,
                "robot_state": robot_state,
            },
        )

    def _register_default_mock_tools(self) -> None:
        self.register_tool("get_image", self._mock_get_image)
        self.register_tool("get_robot_state", self._mock_get_robot_state)
        self.register_tool("describe_scene", self._mock_describe_scene)
        self.register_tool("run_smolvla", self._mock_run_smolvla)
        self.register_tool("move_home", self._mock_execution_result("move_home"))
        self.register_tool("move_to", self._mock_execution_result("move_to"))
        self.register_tool("grasp", self._mock_execution_result("grasp"))
        self.register_tool("release", self._mock_execution_result("release"))

    @staticmethod
    def _mock_get_image(_: dict[str, Any]) -> str:
        return "mock_base64_image"

    @staticmethod
    def _mock_get_robot_state(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "joint_positions": [0.0, -0.2, 0.4, 0.0, 1.2, 0.0],
            "ee_pose": {
                "x": 0.15,
                "y": 0.05,
                "z": 0.22,
                "roll": 0.0,
                "pitch": 1.57,
                "yaw": 0.0,
            },
        }

    @staticmethod
    def _mock_describe_scene(arguments: dict[str, Any]) -> MCPResponse:
        prompt = str(arguments.get("prompt", "")).strip()
        suffix = f" 提示词: {prompt}" if prompt else ""
        return {
            "ok": True,
            "status_code": 200,
            "tool_name": "describe_scene",
            "content": (
                "桌面场景已检测到一个机械臂、一个待操作目标物和可达工作区域。"
                f"{suffix}"
            ),
            "message": "ok",
            "metadata": {
                "provider": "mock_minimal_perception",
                "model": "mock_describe_scene",
                "confidence": 0.91,
                "structured_observations": {
                    "robot_grasp_state": "open",
                    "risk_flags": [],
                    "objects": [
                        {
                            "name": "cube",
                            "category": "target_object",
                            "graspable": True,
                        }
                    ],
                },
            },
        }

    @staticmethod
    def _mock_run_smolvla(arguments: dict[str, Any]) -> ExecutionResult:
        task_description = str(arguments.get("task_description", "")).strip() or "执行当前任务"
        return {
            "status": "success",
            "action_name": "run_smolvla",
            "message": f"mock run_smolvla 已处理任务: {task_description}",
            "logs": [
                "skill=run_smolvla",
                "mode=mock",
            ],
        }

    @staticmethod
    def _mock_execution_result(action_name: str) -> ToolHandler:
        def _handler(_: dict[str, Any]) -> ExecutionResult:
            return {
                "status": "success",
                "action_name": action_name,
                "message": f"mock {action_name} executed",
                "logs": ["mode=mock"],
            }

        return _handler
