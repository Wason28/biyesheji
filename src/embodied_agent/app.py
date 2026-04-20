from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .decision.graph import DecisionEngine
from .decision.mcp_client import MCPResponse, MinimalMCPClient
from .execution.server import MockMCPServer, build_server
from .perception.server import PerceptionMCPServer, build_server as build_perception_server
from .shared.config import AppConfig, load_config
from .shared.types import (
    FrontendBootstrapPayload,
    FrontendConfigPayload,
    FrontendRunAPI,
    FrontendRunSnapshot,
    FrontendRuntimeAPI,
    FrontendToolDescriptor,
    RunStatus,
)


DECISION_LLM_PROVIDERS = ["minimax", "openai", "ollama"]
PERCEPTION_VLM_PROVIDERS = ["minimax_mcp_vision", "openai_gpt4o", "ollama_vision"]
FRONTEND_STATUS_FIELDS = [
    "run_id",
    "status",
    "current_node",
    "current_task",
    "selected_capability",
    "selected_action",
    "scene_description",
    "scene_observations",
    "action_result",
    "iteration_count",
    "max_iterations",
    "current_image",
    "robot_state",
    "last_node_result",
    "last_execution",
    "logs",
    "error",
]


@dataclass(slots=True)
class Phase1Runtime:
    config: AppConfig
    perception: PerceptionMCPServer
    execution: MockMCPServer
    decision: DecisionEngine
    mcp_client: MinimalMCPClient


@dataclass(slots=True)
class FrontendRuntimeFacade:
    runtime: Phase1Runtime

    def get_bootstrap(self) -> FrontendBootstrapPayload:
        return build_frontend_bootstrap(self.runtime)

    def get_config(self) -> FrontendConfigPayload:
        return build_frontend_config_payload(self.runtime)

    def get_runtime_api(self) -> FrontendRuntimeAPI:
        return build_frontend_runtime_api(self.runtime)

    def run_instruction(self, *, instruction: str, run_id: str) -> FrontendRunAPI:
        return build_frontend_run_api(self.runtime, instruction=instruction, run_id=run_id)

    def build_error(self, *, code: str, message: str) -> dict[str, Any]:
        return build_frontend_run_error(code=code, message=message)


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
        self.register_tool("release", self._release)

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
        if tool_name == "release":
            return self._execution_response(tool_name, self._execution_server.call_tool("release", arguments))
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

    def _release(self, arguments: dict[str, Any]) -> Any:
        return self._execution_server.call_tool("release", arguments)

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


def build_frontend_facade(runtime: Phase1Runtime) -> FrontendRuntimeFacade:
    return FrontendRuntimeFacade(runtime=runtime)


def _tool_descriptor(*, layer: str, tool: Any) -> FrontendToolDescriptor:
    if isinstance(tool, dict):
        return {
            "name": str(tool.get("name", "")),
            "layer": layer,
            "description": str(tool.get("description", "")),
            "input_schema": dict(tool.get("input_schema", {})),
            "capability_names": list(tool.get("capability_names", [])),
        }
    return {
        "name": str(getattr(tool, "name", "")),
        "layer": layer,
        "description": str(getattr(tool, "description", "")),
        "input_schema": dict(getattr(tool, "input_schema", {})),
        "capability_names": list(getattr(tool, "capability_names", [])),
    }


def build_frontend_config_payload(runtime: Phase1Runtime) -> FrontendConfigPayload:
    return {
        "decision": {
            "provider": runtime.config.decision.llm_provider,
            "model": runtime.config.decision.llm_model,
            "provider_options": list(DECISION_LLM_PROVIDERS),
            "api_key": "",
            "api_key_configured": bool(runtime.config.decision.llm_api_key),
            "local_path": runtime.config.decision.llm_local_path,
        },
        "perception": {
            "provider": runtime.config.perception.vlm_provider,
            "model": runtime.config.perception.vlm_model,
            "provider_options": list(PERCEPTION_VLM_PROVIDERS),
            "api_key": "",
            "api_key_configured": bool(runtime.config.perception.vlm_api_key),
            "local_path": runtime.config.perception.vlm_local_path,
        },
        "execution": {
            "display_name": "SmolVLA",
            "model_path": runtime.config.execution.vla_model_path,
            "home_pose": dict(runtime.config.execution.home_pose),
            "adapter": runtime.execution.describe()["execution_model"]["adapter"],
            "backend": runtime.execution.describe()["execution_model"]["backend"],
            "safety_policy": runtime.config.execution.safety_policy,
            "stop_mode": runtime.config.execution.stop_mode,
            "mutable": False,
        },
        "frontend": {
            "port": runtime.config.frontend.port,
            "max_iterations": runtime.decision.deps.max_iterations,
            "speed_scale": runtime.config.frontend.speed_scale,
        },
    }


def build_frontend_bootstrap(runtime: Phase1Runtime) -> FrontendBootstrapPayload:
    execution_description = runtime.execution.describe()
    perception_tools = [_tool_descriptor(layer="perception", tool=tool) for tool in runtime.perception.list_tools()]
    execution_tools = [_tool_descriptor(layer="execution", tool=tool) for tool in runtime.execution.list_tools()]
    return {
        "config": build_frontend_config_payload(runtime),
        "execution_model": execution_description["execution_model"],
        "tools": perception_tools + execution_tools,
        "status_fields": list(FRONTEND_STATUS_FIELDS),
        "execution_capabilities": list(execution_description.get("capabilities", [])),
        "execution_safety": dict(execution_description.get("safety_boundary", {})),
    }


def _frontend_run_status(state: Mapping[str, Any]) -> RunStatus:
    action_result = str(state.get("action_result", ""))
    if action_result == "failed":
        return "failed"
    if action_result == "success" and not state.get("current_task") and not state.get("task_queue"):
        return "completed"
    if action_result == "in_progress":
        return "running"
    return "idle"


def build_frontend_run_snapshot(
    state: Mapping[str, Any],
    *,
    run_id: str,
) -> FrontendRunSnapshot:
    last_node_result = state.get("last_node_result", {})
    history = state.get("conversation_history", [])
    logs = [dict(item) for item in history if isinstance(item, Mapping)]
    status = _frontend_run_status(state)
    error = ""
    if status == "failed" and isinstance(last_node_result, Mapping):
        error = str(last_node_result.get("message", ""))
    return {
        "run_id": run_id,
        "status": status,
        "current_node": str(last_node_result.get("node", "")) if isinstance(last_node_result, Mapping) else "",
        "current_task": str(state.get("current_task", "")),
        "selected_capability": str(state.get("selected_capability", "")),
        "selected_action": str(state.get("selected_action", "")),
        "scene_description": str(state.get("scene_description", "")),
        "scene_observations": dict(state.get("scene_observations", {})),
        "action_result": str(state.get("action_result", "in_progress")),
        "iteration_count": int(state.get("iteration_count", 0)),
        "max_iterations": int(state.get("max_iterations", 0)),
        "current_image": str(state.get("current_image", "")),
        "robot_state": dict(state.get("robot_state", {})),
        "last_node_result": dict(last_node_result) if isinstance(last_node_result, Mapping) else {},
        "last_execution": dict(state.get("last_execution", {})),
        "logs": logs,
        "error": error,
    }


def build_frontend_runtime_api(runtime: Phase1Runtime) -> FrontendRuntimeAPI:
    return {
        "bootstrap": build_frontend_bootstrap(runtime),
        "config": build_frontend_config_payload(runtime),
    }


def build_frontend_run_api(
    runtime: Phase1Runtime,
    *,
    instruction: str,
    run_id: str,
) -> FrontendRunAPI:
    final_state = runtime.decision.invoke(instruction)
    return {"run": build_frontend_run_snapshot(final_state, run_id=run_id)}


def build_frontend_run_error(*, code: str, message: str) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase-1 unified startup entry for the mock embodied agent")
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
