"""Presentation helpers for phase-3 frontend contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping

from .contracts import (
    FrontendBootstrapPayload,
    FrontendConfigPayload,
    FrontendErrorPayload,
    FrontendRunAPI,
    FrontendRunSnapshot,
    FrontendRuntimeAPI,
    FrontendToolDescriptor,
    FrontendToolsPayload,
    RunStatus,
)

if TYPE_CHECKING:
    from ..app import Phase1Runtime


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


def build_frontend_tools_payload(runtime: Phase1Runtime) -> FrontendToolsPayload:
    perception_tools = [_tool_descriptor(layer="perception", tool=tool) for tool in runtime.perception.list_tools()]
    execution_tools = [_tool_descriptor(layer="execution", tool=tool) for tool in runtime.execution.list_tools()]
    return {"tools": perception_tools + execution_tools}


def build_frontend_config_payload(runtime: Phase1Runtime) -> FrontendConfigPayload:
    execution_description = runtime.execution.describe()
    execution_model = execution_description["execution_model"]
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
            "display_name": execution_model["name"],
            "model_path": runtime.config.execution.vla_model_path,
            "home_pose": dict(runtime.config.execution.home_pose),
            "adapter": execution_model["adapter"],
            "backend": execution_model["backend"],
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
    return {
        "config": build_frontend_config_payload(runtime),
        "execution_model": execution_description["execution_model"],
        "tools": build_frontend_tools_payload(runtime)["tools"],
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


def build_frontend_run_error(*, code: str, message: str) -> FrontendErrorPayload:
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }
