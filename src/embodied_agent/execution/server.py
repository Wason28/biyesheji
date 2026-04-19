"""Mock MCP-style server entrypoint for the execution layer."""

from __future__ import annotations

import json
import sys
from typing import Any, Callable

from embodied_agent.shared.config import AppConfig

from .tools import ExecutionRuntime
from .types import MCPServerDescription, MCPToolCall, ToolDefinition


class MockMCPServer:
    """Minimal MCP-style server facade for local integration and tests."""

    def __init__(self, runtime: ExecutionRuntime | None = None) -> None:
        self._runtime = runtime or ExecutionRuntime.create()
        self._tools: dict[str, tuple[ToolDefinition, Callable[..., dict[str, Any]]]] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        self.register_tool(
            {
                "name": "move_to",
                "description": "移动末端执行器到指定笛卡尔位姿。",
                "input_schema": {
                    "type": "object",
                    "required": ["x", "y", "z", "orientation"],
                },
            },
            self._runtime.move_to,
        )
        self.register_tool(
            {
                "name": "move_home",
                "description": "按照安全路径回零。",
                "input_schema": {"type": "object"},
            },
            self._runtime.move_home,
        )
        self.register_tool(
            {
                "name": "grasp",
                "description": "执行夹爪抓取。",
                "input_schema": {"type": "object", "required": ["force"]},
            },
            self._runtime.grasp,
        )
        self.register_tool(
            {
                "name": "release",
                "description": "执行夹爪释放。",
                "input_schema": {"type": "object"},
            },
            self._runtime.release,
        )
        self.register_tool(
            {
                "name": "run_smolvla",
                "description": "调用固定 SmolVLA mock 规划并安全执行。",
                "input_schema": {
                    "type": "object",
                    "required": ["task_description", "current_image", "robot_state"],
                },
            },
            self._runtime.run_smolvla,
        )

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
        }

    def list_tools(self) -> list[ToolDefinition]:
        return self.describe()["tools"]

    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if tool_name not in self._tools:
            return {
                "status": "failed",
                "action_name": tool_name,
                "message": f"未注册的工具: {tool_name}",
                "error_code": "UnknownTool",
                "logs": ["server: 拒绝执行未注册工具。"],
                "mock": True,
            }
        _, handler = self._tools[tool_name]
        return handler(**(arguments or {}))

    def handle_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = MCPToolCall(**payload)
        tool_name = request.get("tool")
        if not tool_name:
            return {
                "status": "failed",
                "action_name": "server",
                "message": "请求中缺少 tool 字段。",
                "error_code": "InvalidRequest",
                "logs": ["server: 请求格式非法。"],
                "mock": True,
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
