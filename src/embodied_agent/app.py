from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .decision.graph import DecisionEngine
from .decision.mcp_client import MCPResponse, MinimalMCPClient
from .execution.server import MockMCPServer, build_server
from .perception.server import PerceptionMCPServer, build_server as build_perception_server
from .shared.config import AppConfig, load_config


@dataclass(slots=True)
class Phase1Runtime:
    config: AppConfig
    perception: PerceptionMCPServer
    execution: MockMCPServer
    decision: DecisionEngine
    mcp_client: MinimalMCPClient


class UnifiedMCPClient(MinimalMCPClient):
    def __init__(self, perception_server: PerceptionMCPServer, execution_server: MockMCPServer) -> None:
        super().__init__(auto_mock=False)
        self._perception_server = perception_server
        self._execution_server = execution_server
        self.register_tool("get_image", self._get_image)
        self.register_tool("get_robot_state", self._get_robot_state)
        self.register_tool("describe_scene", self._describe_scene)
        self.register_tool("run_smolvla", self._run_smolvla)
        self.register_tool("move_to", self._move_to)
        self.register_tool("move_home", self._move_home)
        self.register_tool("grasp", self._grasp)
        self.register_tool("servo_rotate", self._servo_rotate)
        self.register_tool("release", self._release)
        self.register_tool("clear_emergency_stop", self._clear_emergency_stop)

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> MCPResponse:
        arguments = arguments or {}
        if tool_name == "get_image":
            return self._perception_response(tool_name, self._perception_server.call_tool("get_image", arguments))
        if tool_name == "get_robot_state":
            return self._perception_response(tool_name, self._perception_server.call_tool("get_robot_state", arguments))
        if tool_name == "describe_scene":
            return self._perception_response(tool_name, self._perception_server.call_tool("describe_scene", arguments))
        if tool_name == "run_smolvla":
            return self._execution_response(tool_name, self._execution_server.call_tool("run_smolvla", arguments))
        if tool_name == "move_to":
            return self._execution_response(tool_name, self._execution_server.call_tool("move_to", arguments))
        if tool_name == "move_home":
            return self._execution_response(tool_name, self._execution_server.call_tool("move_home", arguments))
        if tool_name == "grasp":
            return self._execution_response(tool_name, self._execution_server.call_tool("grasp", arguments))
        if tool_name == "servo_rotate":
            return self._execution_response(tool_name, self._execution_server.call_tool("servo_rotate", arguments))
        if tool_name == "release":
            return self._execution_response(tool_name, self._execution_server.call_tool("release", arguments))
        if tool_name == "clear_emergency_stop":
            return self._execution_response(tool_name, self._execution_server.call_tool("clear_emergency_stop", arguments))
        return {
            "ok": False,
            "status_code": 404,
            "tool_name": tool_name,
            "content": None,
            "message": f"tool '{tool_name}' is not registered",
            "metadata": {"arguments": arguments},
        }

    def _get_image(self, arguments: dict[str, Any]) -> Any:
        return self._perception_server.call_tool("get_image", arguments)

    def _get_robot_state(self, arguments: dict[str, Any]) -> Any:
        return self._perception_server.call_tool("get_robot_state", arguments)

    def _describe_scene(self, arguments: dict[str, Any]) -> Any:
        return self._perception_server.call_tool("describe_scene", arguments)

    def _run_smolvla(self, arguments: dict[str, Any]) -> Any:
        return self._execution_server.call_tool("run_smolvla", arguments)

    def _move_to(self, arguments: dict[str, Any]) -> Any:
        return self._execution_server.call_tool("move_to", arguments)

    def _move_home(self, arguments: dict[str, Any]) -> Any:
        return self._execution_server.call_tool("move_home", arguments)

    def _grasp(self, arguments: dict[str, Any]) -> Any:
        return self._execution_server.call_tool("grasp", arguments)

    def _servo_rotate(self, arguments: dict[str, Any]) -> Any:
        return self._execution_server.call_tool("servo_rotate", arguments)

    def _release(self, arguments: dict[str, Any]) -> Any:
        return self._execution_server.call_tool("release", arguments)

    def _clear_emergency_stop(self, arguments: dict[str, Any]) -> Any:
        return self._execution_server.call_tool("clear_emergency_stop", arguments)

    @staticmethod
    def _perception_response(tool_name: str, payload: dict[str, Any]) -> MCPResponse:
        content = payload.get("content")
        metadata = dict(payload.get("metadata", {}))
        if payload.get("ok"):
            if tool_name == "get_image" and isinstance(content, dict):
                return {
                    "ok": True,
                    "status_code": int(payload.get("status_code", 200)),
                    "tool_name": tool_name,
                    "content": content.get("image_base64", ""),
                    "message": str(payload.get("message", "ok")),
                    "metadata": {
                        **metadata,
                        **{key: value for key, value in content.items() if key != "image_base64"},
                    },
                }
            if tool_name == "get_robot_state" and isinstance(content, dict):
                return {
                    "ok": True,
                    "status_code": int(payload.get("status_code", 200)),
                    "tool_name": tool_name,
                    "content": {
                        "joint_positions": content.get("joint_positions", []),
                        "ee_pose": content.get("ee_pose", {}),
                    },
                    "message": str(payload.get("message", "ok")),
                    "metadata": {
                        **metadata,
                        **{key: value for key, value in content.items() if key not in {"joint_positions", "ee_pose"}},
                    },
                }
            if tool_name == "describe_scene" and isinstance(content, dict):
                return {
                    "ok": True,
                    "status_code": int(payload.get("status_code", 200)),
                    "tool_name": tool_name,
                    "content": content.get("scene_description", ""),
                    "message": str(payload.get("message", "ok")),
                    "metadata": {
                        **metadata,
                        **{key: value for key, value in content.items() if key != "scene_description"},
                    },
                }
        return {
            "ok": bool(payload.get("ok", False)),
            "status_code": int(payload.get("status_code", 500)),
            "tool_name": tool_name,
            "content": content,
            "message": str(payload.get("message", "")),
            "metadata": metadata,
        }

    @staticmethod
    def _execution_response(tool_name: str, payload: dict[str, Any]) -> MCPResponse:
        if "ok" in payload:
            return {
                "ok": bool(payload.get("ok", False)),
                "status_code": int(payload.get("status_code", 500)),
                "tool_name": tool_name,
                "content": payload.get("content"),
                "message": str(payload.get("message", "")),
                "metadata": dict(payload.get("metadata", {})),
            }
        ok = payload.get("status") != "failed"
        return {
            "ok": ok,
            "status_code": 200 if ok else 500,
            "tool_name": tool_name,
            "content": payload,
            "message": str(payload.get("message", "")),
            "metadata": {},
        }



def build_runtime(config: AppConfig | None = None) -> Phase1Runtime:
    runtime_config = config or AppConfig()
    perception = build_perception_server(runtime_config)
    execution = build_server(runtime_config)
    mcp_client = UnifiedMCPClient(perception, execution)
    decision = DecisionEngine.from_config(runtime_config, mcp_client=mcp_client)
    return Phase1Runtime(
        config=runtime_config,
        perception=perception,
        execution=execution,
        decision=decision,
        mcp_client=mcp_client,
    )



def build_runtime_from_config(config_path: str | Path) -> Phase1Runtime:
    return build_runtime(load_config(config_path))


from .backend.presenters import (  # noqa: E402
    build_frontend_bootstrap,
    build_frontend_config_payload,
    build_frontend_run_api,
    build_frontend_run_error,
    build_frontend_run_snapshot,
    build_frontend_runtime_api,
)
from .backend.service import FrontendRuntimeFacade, build_frontend_facade  # noqa: E402



def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified startup entry for the mock embodied agent")
    parser.add_argument("--instruction", type=str, required=True, help="要执行的用户指令")
    parser.add_argument("--config", type=str, default=None, help="配置文件路径")
    parser.add_argument("--dump-final-state", action="store_true", help="输出最终状态 JSON")
    parser.add_argument("--list-tools", action="store_true", help="输出统一入口装配的工具列表")
    return parser



def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    runtime = build_runtime_from_config(args.config) if args.config else build_runtime()

    if args.list_tools:
        print(json.dumps(sorted(runtime.mcp_client.tool_registry.keys()), ensure_ascii=False, indent=2))
        return 0

    final_state = runtime.decision.invoke(args.instruction)
    if args.dump_final_state:
        print(json.dumps(final_state, ensure_ascii=False, indent=2))
    else:
        print(final_state.get("last_node_result", {}).get("message", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
