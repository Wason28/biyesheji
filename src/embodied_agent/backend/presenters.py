"""Presentation helpers for phase-3 frontend contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Mapping

from .contracts import (
    FrontendBootstrapPayload,
    FrontendConfigPayload,
    FrontendErrorPayload,
    FrontendRunAPI,
    FrontendRunSnapshot,
    FrontendRunStatePayload,
    FrontendRuntimeAPI,
    FrontendToolDescriptor,
    FrontendToolsPayload,
    RunPhase,
    RunStatus,
    RuntimeEventName,
)

if TYPE_CHECKING:
    from ..app import Phase1Runtime


DECISION_LLM_PROVIDERS = ["minimax", "openai", "ollama"]
PERCEPTION_VLM_PROVIDERS = ["minimax_mcp_vision", "openai_gpt4o", "ollama_vision"]
FRONTEND_STATUS_FIELDS = [
    "run_id",
    "status",
    "user_instruction",
    "assistant_response",
    "current_phase",
    "current_node",
    "current_task",
    "selected_capability",
    "selected_action",
    "scene_description",
    "scene_observations",
    "perception_confidence",
    "action_result",
    "iteration_count",
    "max_iterations",
    "current_image",
    "robot_state",
    "plan",
    "pre_execution_feedback",
    "execution_feedback",
    "verification_result",
    "error_diagnosis",
    "retry_context",
    "memory_summary",
    "termination_reason",
    "final_report",
    "last_node_result",
    "last_execution",
    "logs",
    "error",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _build_perception_assistant(runtime: Phase1Runtime, execution_model: Mapping[str, Any]) -> dict[str, Any]:
    provider_summary = runtime.perception.provider.config_summary()
    configured = bool(provider_summary.get("configured", False))
    status = str(provider_summary.get("status", "configured" if configured else "attention"))
    fallback_reason = str(provider_summary.get("fallback_reason", "")).strip()
    endpoint = str(provider_summary.get("endpoint") or provider_summary.get("base_url") or "").strip()
    selected_provider = runtime.config.perception.vlm_provider
    selected_model = runtime.config.perception.vlm_model

    if fallback_reason:
        message = f"当前感知模型 {selected_provider} 已回退到 mock provider。{fallback_reason}"
    elif endpoint:
        message = f"当前感知模型 {selected_model} 已通过 {selected_provider} 接入：{endpoint}。"
    else:
        message = f"当前感知模型 {selected_model} 已装配到 {selected_provider}。"

    return {
        "title": "系统载入助手",
        "status": status,
        "message": message,
        "detected_models": [
            {
                "provider": selected_provider,
                "model": selected_model,
                "configured": configured,
            },
            {
                "provider": execution_model["backend"],
                "model": execution_model["name"],
                "configured": True,
            },
        ],
    }


def build_frontend_config_payload(runtime: Phase1Runtime) -> FrontendConfigPayload:
    execution_description = runtime.execution.describe()
    execution_model = execution_description["execution_model"]
    decision_provider = runtime.config.decision.llm_provider
    perception_provider = runtime.config.perception.vlm_provider
    decision_base_url = runtime.config.decision.llm_base_url
    decision_ready = bool(runtime.config.decision.llm_api_key or runtime.config.decision.llm_local_path or decision_base_url)
    return {
        "decision": {
            "provider": decision_provider,
            "model": runtime.config.decision.llm_model,
            "provider_options": list(DECISION_LLM_PROVIDERS),
            "api_key": "",
            "api_key_configured": bool(runtime.config.decision.llm_api_key),
            "local_path": runtime.config.decision.llm_local_path,
            "base_url": decision_base_url,
            "assistant": {
                "title": "模型部署助手",
                "status": "configured" if decision_ready else "attention",
                "message": (
                    f"当前决策模型使用 {decision_provider}，可继续填写 API Key、本地路径或兼容网关地址完成部署。"
                    if not decision_ready
                    else (
                        f"当前决策模型 {runtime.config.decision.llm_model} 已通过 {decision_provider} 接入：{decision_base_url}。"
                        if decision_base_url
                        else f"当前决策模型 {runtime.config.decision.llm_model} 已具备基础部署条件。"
                    )
                ),
            },
        },
        "perception": {
            "provider": perception_provider,
            "model": runtime.config.perception.vlm_model,
            "provider_options": list(PERCEPTION_VLM_PROVIDERS),
            "api_key": "",
            "api_key_configured": bool(runtime.config.perception.vlm_api_key),
            "local_path": runtime.config.perception.vlm_local_path,
            "base_url": runtime.config.perception.vlm_base_url,
            "camera_backend": runtime.config.perception.camera_backend,
            "camera_device_id": runtime.config.perception.camera_device_id,
            "camera_frame_id": runtime.config.perception.camera_frame_id,
            "camera_width": runtime.config.perception.camera_width,
            "camera_height": runtime.config.perception.camera_height,
            "camera_fps": runtime.config.perception.camera_fps,
            "camera_index": runtime.config.perception.camera_index,
            "robot_state_backend": runtime.config.perception.robot_state_backend,
            "robot_state_base_url": runtime.config.perception.robot_state_base_url,
            "robot_state_config_path": runtime.config.perception.robot_state_config_path,
            "robot_state_base_frame": runtime.config.perception.robot_state_base_frame,
            "assistant": _build_perception_assistant(runtime, execution_model),
        },
        "execution": {
            "display_name": execution_model["name"],
            "model_path": runtime.config.execution.vla_model_path,
            "home_joint_positions": list(runtime.config.execution.home_joint_positions),
            "home_pose": dict(runtime.config.execution.home_pose),
            "adapter": execution_model["adapter"],
            "backend": execution_model["backend"],
            "robot_base_url": runtime.config.execution.robot_base_url,
            "robot_timeout_s": runtime.config.execution.robot_timeout_s,
            "telemetry_poll_timeout_s": runtime.config.execution.telemetry_poll_timeout_s,
            "safety_require_precheck": runtime.config.execution.safety_require_precheck,
            "robot_pythonpath": runtime.config.execution.robot_pythonpath,
            "safety_policy": runtime.config.execution.safety_policy,
            "stop_mode": runtime.config.execution.stop_mode,
            "mutable": False,
        },
        "frontend": {
            "port": runtime.config.frontend.port,
            "max_iterations": runtime.decision.deps.max_iterations,
            "speed_scale": runtime.config.frontend.speed_scale,
            "custom_models": list(runtime.config.frontend.custom_models),
        },
        "vision_model": runtime.config.vision_model,
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
        "execution_runtime_profile": dict(execution_description.get("runtime_profile", {})),
    }


def _frontend_run_status(state: Mapping[str, Any]) -> RunStatus:
    current_phase = str(state.get("current_phase", ""))
    if current_phase != "final_status":
        return "running"

    final_report = state.get("final_report", {})
    if isinstance(final_report, Mapping):
        if final_report.get("completed"):
            return "completed"
        if final_report.get("status") == "failed":
            return "failed"

    action_result = str(state.get("action_result", ""))
    if action_result == "success":
        return "completed"
    if action_result == "failed":
        return "failed"
    return "running"


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
    if status == "failed":
        if str(state.get("current_phase", "")) == "final_status":
            diagnosis = state.get("error_diagnosis", {})
            if isinstance(diagnosis, Mapping):
                error = str(diagnosis.get("reason", ""))
            if not error:
                error = str(state.get("termination_reason", ""))
        if not error and isinstance(last_node_result, Mapping):
            error = str(last_node_result.get("message", ""))
    return {
        "run_id": run_id,
        "status": status,
        "user_instruction": str(state.get("user_instruction", "")),
        "assistant_response": str(state.get("assistant_response", "")),
        "current_phase": str(state.get("current_phase", "trigger")),
        "current_node": str(last_node_result.get("node", "")) if isinstance(last_node_result, Mapping) else "",
        "current_task": str(state.get("current_task", "")),
        "selected_capability": str(state.get("selected_capability", "")),
        "selected_action": str(state.get("selected_action", "")),
        "scene_description": str(state.get("scene_description", "")),
        "scene_observations": dict(state.get("scene_observations", {})),
        "perception_confidence": float(state.get("perception_confidence", 0.0) or 0.0),
        "action_result": str(state.get("action_result", "in_progress")),
        "iteration_count": int(state.get("iteration_count", 0)),
        "max_iterations": int(state.get("max_iterations", 0)),
        "current_image": str(state.get("current_image", "")),
        "robot_state": dict(state.get("robot_state", {})),
        "plan": [dict(item) for item in state.get("plan", []) if isinstance(item, Mapping)],
        "pre_execution_feedback": dict(state.get("pre_execution_feedback", {})),
        "execution_feedback": dict(state.get("execution_feedback", {})),
        "verification_result": dict(state.get("verification_result", {})),
        "error_diagnosis": dict(state.get("error_diagnosis", {})),
        "retry_context": dict(state.get("retry_context", {})),
        "memory_summary": dict(state.get("memory_summary", {})),
        "termination_reason": str(state.get("termination_reason", "")),
        "final_report": dict(state.get("final_report", {})),
        "last_node_result": dict(last_node_result) if isinstance(last_node_result, Mapping) else {},
        "last_execution": dict(state.get("last_execution", {})),
        "logs": logs,
        "error": error,
    }


def build_frontend_run_event(
    state: Mapping[str, Any],
    *,
    run_id: str,
    version: int,
    event: RuntimeEventName,
    terminal: bool,
    timestamp: str | None = None,
) -> FrontendRunStatePayload:
    snapshot = build_frontend_run_snapshot(state, run_id=run_id)
    phase = str(snapshot.get("current_phase", "trigger"))
    return {
        "run": snapshot,
        "version": version,
        "terminal": terminal,
        "event": event,
        "phase": phase if phase else "trigger",
        "timestamp": timestamp or _utc_now_iso(),
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
