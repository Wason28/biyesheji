"""Mock MCP-style server entrypoint for the execution layer."""

from __future__ import annotations

import json
import sys
from typing import Any, Callable

from embodied_agent.shared.config import AppConfig

from .tools import ExecutionRuntime
from .types import MCPServerDescription, MCPToolCall, ToolDefinition, ToolName


class MockMCPServer:
    """Minimal MCP-style server facade for local integration and tests."""

    def __init__(self, runtime: ExecutionRuntime | None = None) -> None:
        self._runtime = runtime or ExecutionRuntime.create()
        self._tools: dict[str, tuple[ToolDefinition, Callable[..., dict[str, Any]]]] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        self.register_tool(self._build_tool_definition("move_to"), self._runtime.move_to)
        self.register_tool(self._build_tool_definition("move_home"), self._runtime.move_home)
        self.register_tool(self._build_tool_definition("grasp"), self._runtime.grasp)
        self.register_tool(self._build_tool_definition("release"), self._runtime.release)
        self.register_tool(self._build_tool_definition("run_smolvla"), self._runtime.run_smolvla)

    def _build_tool_definition(self, tool_name: ToolName) -> ToolDefinition:
        contract = self._runtime.get_action_contract(tool_name)
        return {
            "name": tool_name,
            "description": contract["description"],
            "input_schema": contract["input_schema"],
            "output_schema": contract["output_schema"],
            "capability_names": contract["capability_names"],
        }

    def register_tool(
        self,
        definition: ToolDefinition,
        handler: Callable[..., dict[str, Any]],
    ) -> None:
        self._tools[definition["name"]] = (definition, handler)

    def describe(self) -> MCPServerDescription:
        return {
            "name": "embodied-agent-execution-mock",
            "version": "0.1.0",
            "tools": [definition for definition, _ in self._tools.values()],
            "capabilities": self._runtime.list_capabilities(),
            "safety_boundary": self._runtime.describe_safety_boundary(),
            "execution_model": self._runtime.describe_execution_model(),
            "runtime_profile": self._runtime.describe_runtime_profile(),
        }

    def list_tools(self) -> list[ToolDefinition]:
        return self.describe()["tools"]

    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if tool_name not in self._tools:
            return {
                "ok": False,
                "status_code": 404,
                "tool_name": tool_name,
                "content": None,
                "message": f"未注册的工具: {tool_name}",
                "metadata": {
                    "error_code": "UnknownTool",
                    "logs": ["server: 拒绝执行未注册工具。"],
                    "mock": self._runtime.is_mock,
                },
            }
        _, handler = self._tools[tool_name]
        try:
            payload = handler(**(arguments or {}))
        except TypeError as error:
            return {
                "ok": False,
                "status_code": 400,
                "tool_name": tool_name,
                "content": None,
                "message": f"工具参数不合法: {tool_name}",
                "metadata": {
                    "error_code": "ToolArgumentError",
                    "arguments": arguments or {},
                    "reason": str(error),
                    "mock": self._runtime.is_mock,
                },
            }
        ok = payload.get("status") != "failed"
        metadata = {
            key: value
            for key, value in payload.items()
            if key not in {"status", "action_name", "message", "logs"}
        }
        return {
            "ok": ok,
            "status_code": 200 if ok else 500,
            "tool_name": tool_name,
            "content": payload,
            "message": str(payload.get("message", "")),
            "metadata": metadata,
        }

    def handle_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = MCPToolCall(**payload)
        tool_name = request.get("tool")
        if not tool_name:
            return {
                "ok": False,
                "status_code": 400,
                "tool_name": "server",
                "content": None,
                "message": "请求中缺少 tool 字段。",
                "metadata": {
                    "error_code": "InvalidRequest",
                    "logs": ["server: 请求格式非法。"],
                    "mock": self._runtime.is_mock,
                },
            }
        return self.call_tool(tool_name, request.get("arguments"))

    def serve_stdio(self) -> int:
        print(json.dumps(self.describe(), ensure_ascii=False))
        raw = sys.stdin.read().strip()
        if not raw:
            return 0
        response = self.handle_request(json.loads(raw))
        print(json.dumps(response, ensure_ascii=False))
        return 0


def build_server(app_config: AppConfig | None = None) -> MockMCPServer:
    return MockMCPServer(ExecutionRuntime.create(app_config))


def main() -> int:
    return build_server().serve_stdio()


if __name__ == "__main__":
    raise SystemExit(main())
