"""Decision-layer LangGraph node stubs with minimal closed-loop logic."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Callable

from ..shared.config import AppConfig
from ..shared.types import ActionStatus, ExecutionResult
from .mcp_client import MCPClientProtocol, MCPResponse
from .state import (
    DEFAULT_MAX_ITERATIONS,
    DecisionAgentState,
    append_history,
    ensure_agent_state,
    record_node_duration,
    record_tool_call,
    set_last_node_result,
)


@dataclass(slots=True)
class NodeDependencies:
    """Runtime dependencies injected into the decision-layer nodes."""

    config: AppConfig
    mcp_client: MCPClientProtocol
    max_history_entries: int = 100
    now_ms: Callable[[], float] = perf_counter
    provider_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def max_iterations(self) -> int:
        if self.config.decision.max_iterations > 0:
            return self.config.decision.max_iterations
        if self.config.frontend.max_iterations > 0:
            return self.config.frontend.max_iterations
        return DEFAULT_MAX_ITERATIONS


def _split_into_tasks(user_instruction: str) -> list[str]:
    raw_parts = re.split(r"(?:\r?\n|。|；|;|然后|接着)", user_instruction)
    tasks = [part.strip(" ，,") for part in raw_parts if part and part.strip(" ，,")]
    return tasks or [user_instruction.strip()] if user_instruction.strip() else []


def _normalize_execution_result(
    response: MCPResponse,
    *,
    fallback_action_name: str,
) -> ExecutionResult:
    content = response.get("content")
    if isinstance(content, dict):
        status = content.get("status", "success")
        return {
            "status": status if status in {"success", "in_progress", "failed"} else "failed",
            "action_name": str(content.get("action_name", fallback_action_name)),
            "message": str(content.get("message", response.get("message", ""))),
            "logs": list(content.get("logs", [])),
        }
    return {
        "status": "success" if response.get("ok") else "failed",
        "action_name": fallback_action_name,
        "message": str(content or response.get("message", "")),
        "logs": [],
    }


def _record_tool_response(
    state: DecisionAgentState,
    *,
    response: MCPResponse,
) -> DecisionAgentState:
    return record_tool_call(
        state,
        tool_name=str(response.get("tool_name", "")),
        ok=bool(response.get("ok", False)),
        metadata=dict(response.get("metadata", {})),
    )


def _select_capability_and_action(
    current_task: str,
    state: DecisionAgentState,
) -> tuple[str, str, dict[str, Any]]:
    normalized_task = current_task.strip().lower()
    scene_observations = state.get("scene_observations", {})
    robot_grasp_state = str(scene_observations.get("robot_grasp_state", "")).lower()
    risk_flags = scene_observations.get("risk_flags", []) if isinstance(scene_observations, dict) else []
    objects = scene_observations.get("objects", []) if isinstance(scene_observations, dict) else []
    has_explicit_ungraspable_object = any(
        isinstance(item, dict) and item.get("graspable") is False
        for item in objects
    )
    base_arguments = {
        "task_description": current_task,
        "current_image": state.get("current_image", ""),
        "robot_state": state.get("robot_state", {}),
    }

    if any(keyword in normalized_task for keyword in ("回到安全位置", "回零", "回原点", "move home", "home")):
        return "return_home", "move_home", {}
    if any(keyword in normalized_task for keyword in ("释放", "松开", "放下", "release")):
        return "release_object", "release", {}
    if robot_grasp_state == "closed" and any(keyword in normalized_task for keyword in ("放", "置", "release", "drop")):
        return "release_object", "release", {}
    if any(keyword in normalized_task for keyword in ("抓", "取", "pick", "grasp")):
        if risk_flags or has_explicit_ungraspable_object:
            return "return_home", "move_home", {}
        return "pick_and_place", "run_smolvla", base_arguments
    if any(keyword in normalized_task for keyword in ("放", "置", "drop", "place")):
        return "release_object", "release", {}
    return "pick_and_place", "run_smolvla", base_arguments


def _run_node(
    node_name: str,
    state: DecisionAgentState,
    deps: NodeDependencies,
    logic: Callable[[DecisionAgentState, NodeDependencies], DecisionAgentState],
) -> DecisionAgentState:
    started_at = deps.now_ms()
    normalized_state = ensure_agent_state(state, max_iterations=deps.max_iterations)
    try:
        next_state = logic(normalized_state, deps)
        next_state = record_node_duration(
            next_state,
            node=node_name,
            duration_ms=(deps.now_ms() - started_at) * 1000,
        )
        return next_state
    except Exception as exc:  # pragma: no cover - defensive path
        failed_state = dict(normalized_state)
        failed_state["action_result"] = "failed"
        failed_state = set_last_node_result(
            failed_state,
            node=node_name,
            status_code=500,
            message=f"{node_name} 执行异常: {exc}",
            metadata={"error_type": type(exc).__name__},
        )
        failed_state = append_history(
            failed_state,
            node=node_name,
            message=f"{node_name} 失败: {exc}",
            status="error",
            metadata={"error_type": type(exc).__name__},
            history_limit=deps.max_history_entries,
        )
        failed_state = record_node_duration(
            failed_state,
            node=node_name,
            duration_ms=(deps.now_ms() - started_at) * 1000,
        )
        return failed_state




def task_planner_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(
        normalized_state: DecisionAgentState,
        runtime_deps: NodeDependencies,
    ) -> DecisionAgentState:
        task_queue = list(normalized_state.get("task_queue", []))
        if not task_queue:
            task_queue = _split_into_tasks(normalized_state["user_instruction"])

        status_code = 200 if task_queue else 400
        message = "任务规划完成" if task_queue else "用户指令为空，无法生成任务"
        action_result: ActionStatus = "in_progress" if task_queue else "failed"

        next_state = dict(normalized_state)
        next_state["task_queue"] = task_queue
        next_state["current_task"] = task_queue[0] if task_queue else ""
        next_state["action_result"] = action_result
        next_state = set_last_node_result(
            next_state,
            node="task_planner",
            status_code=status_code,
            message=message,
            metadata={
                "task_count": len(task_queue),
                "llm_provider": runtime_deps.config.decision.llm_provider,
                "llm_model": runtime_deps.config.decision.llm_model,
            },
        )
        return append_history(
            next_state,
            node="task_planner",
            message=message,
            status="ok" if task_queue else "error",
            metadata={
                "tasks": task_queue,
                "provider": runtime_deps.config.decision.llm_provider,
                "model": runtime_deps.config.decision.llm_model,
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("task_planner", state, deps, _logic)


def scene_analyzer_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(
        normalized_state: DecisionAgentState,
        runtime_deps: NodeDependencies,
    ) -> DecisionAgentState:
        image_response = runtime_deps.mcp_client.get_image()
        working_state = _record_tool_response(normalized_state, response=image_response)
        if not image_response.get("ok"):
            raise RuntimeError(image_response.get("message", "get_image failed"))

        robot_response = runtime_deps.mcp_client.get_robot_state()
        working_state = _record_tool_response(working_state, response=robot_response)
        if not robot_response.get("ok"):
            raise RuntimeError(robot_response.get("message", "get_robot_state failed"))

        scene_response = runtime_deps.mcp_client.describe_scene(
            str(image_response.get("content", "")),
            prompt=f"当前任务: {working_state.get('current_task', '')}",
        )
        working_state = _record_tool_response(working_state, response=scene_response)
        if not scene_response.get("ok"):
            raise RuntimeError(scene_response.get("message", "describe_scene failed"))

        next_state = dict(working_state)
        next_state["current_image"] = str(image_response.get("content", ""))
        next_state["robot_state"] = dict(robot_response.get("content", {}))
        next_state["scene_description"] = str(scene_response.get("content", ""))
        next_state["scene_observations"] = dict(scene_response.get("metadata", {})).get("structured_observations", {}) if isinstance(scene_response.get("metadata", {}), dict) else {}
        next_state = set_last_node_result(
            next_state,
            node="scene_analyzer",
            status_code=200,
            message="场景分析完成",
            metadata={
                "vlm_provider": runtime_deps.config.perception.vlm_provider,
                "vlm_model": runtime_deps.config.perception.vlm_model,
            },
        )
        return append_history(
            next_state,
            node="scene_analyzer",
            message="刷新图像、机器人状态和场景描述",
            status="ok",
            metadata={
                "scene_description": next_state["scene_description"],
                "vlm_provider": runtime_deps.config.perception.vlm_provider,
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("scene_analyzer", state, deps, _logic)


def action_decider_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(
        normalized_state: DecisionAgentState,
        runtime_deps: NodeDependencies,
    ) -> DecisionAgentState:
        current_task = normalized_state.get("current_task", "").strip()
        if not current_task and normalized_state.get("task_queue"):
            current_task = normalized_state["task_queue"][0]

        if not current_task:
            next_state = dict(normalized_state)
            next_state["action_result"] = "success"
            next_state = set_last_node_result(
                next_state,
                node="action_decider",
                status_code=204,
                message="没有待执行任务",
                metadata={},
            )
            return append_history(
                next_state,
                node="action_decider",
                message="未找到待执行任务，直接结束",
                status="ok",
                metadata={},
                history_limit=runtime_deps.max_history_entries,
            )

        next_state = dict(normalized_state)
        next_state["current_task"] = current_task
        selected_capability, selected_action, selected_action_args = _select_capability_and_action(
            current_task,
            normalized_state,
        )
        next_state["selected_capability"] = selected_capability
        next_state["selected_capability_args"] = dict(selected_action_args)
        next_state["selected_action"] = selected_action
        next_state["selected_action_args"] = dict(selected_action_args)
        next_state = set_last_node_result(
            next_state,
            node="action_decider",
            status_code=200,
            message="动作决策完成",
            metadata={
                "selected_capability": next_state["selected_capability"],
                "selected_action": next_state["selected_action"],
                "current_task": current_task,
            },
        )
        return append_history(
            next_state,
            node="action_decider",
            message=f"为任务选择能力: {next_state['selected_capability']} -> {next_state['selected_action']}",
            status="ok",
            metadata={
                "capability": next_state["selected_capability"],
                "action": next_state["selected_action"],
                "task": current_task,
                "scene_description": normalized_state.get("scene_description", ""),
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("action_decider", state, deps, _logic)


def executor_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(
        normalized_state: DecisionAgentState,
        runtime_deps: NodeDependencies,
    ) -> DecisionAgentState:
        selected_action = normalized_state.get("selected_action", "").strip()
        selected_capability = normalized_state.get("selected_capability", "").strip()
        if not selected_action:
            next_state = dict(normalized_state)
            next_state["action_result"] = "failed"
            next_state = set_last_node_result(
                next_state,
                node="executor",
                status_code=400,
                message="未提供可执行动作",
                metadata={},
            )
            return append_history(
                next_state,
                node="executor",
                message="执行阶段缺少 selected_action",
                status="error",
                metadata={"selected_capability": selected_capability},
                history_limit=runtime_deps.max_history_entries,
            )

        response = runtime_deps.mcp_client.call_tool(
            selected_action,
            dict(normalized_state.get("selected_action_args", {})),
        )
        working_state = _record_tool_response(normalized_state, response=response)
        execution_result = _normalize_execution_result(
            response,
            fallback_action_name=selected_action,
        )

        next_state = dict(working_state)
        next_state["last_execution"] = execution_result
        next_state["action_result"] = execution_result["status"]
        next_state = set_last_node_result(
            next_state,
            node="executor",
            status_code=int(response.get("status_code", 500)),
            message=str(execution_result.get("message", response.get("message", ""))),
            metadata={
                "selected_capability": selected_capability,
                "selected_action": selected_action,
                "tool_ok": bool(response.get("ok", False)),
            },
        )
        return append_history(
            next_state,
            node="executor",
            message=f"执行动作 {selected_action}",
            status="ok" if response.get("ok") else "error",
            metadata={
                "selected_capability": selected_capability,
                "execution_result": execution_result,
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("executor", state, deps, _logic)


def verifier_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(
        normalized_state: DecisionAgentState,
        runtime_deps: NodeDependencies,
    ) -> DecisionAgentState:
        next_state = dict(normalized_state)
        next_state["iteration_count"] = int(normalized_state.get("iteration_count", 0)) + 1

        verify_image_response = runtime_deps.mcp_client.get_image()
        next_state = _record_tool_response(next_state, response=verify_image_response)
        if verify_image_response.get("ok"):
            next_state["current_image"] = str(verify_image_response.get("content", ""))

        verify_scene_response = runtime_deps.mcp_client.describe_scene(
            str(next_state.get("current_image", "")),
            prompt=f"验证任务是否完成: {next_state.get('current_task', '')}",
        )
        next_state = _record_tool_response(next_state, response=verify_scene_response)
        if verify_scene_response.get("ok"):
            next_state["scene_description"] = str(verify_scene_response.get("content", ""))
            next_state["scene_observations"] = dict(verify_scene_response.get("metadata", {})).get("structured_observations", {}) if isinstance(verify_scene_response.get("metadata", {}), dict) else {}

        queue = list(next_state.get("task_queue", []))
        current_task = str(next_state.get("current_task", "")).strip()
        last_status = str(next_state.get("action_result", "failed"))

        if next_state["iteration_count"] >= int(next_state.get("max_iterations", runtime_deps.max_iterations)):
            next_state["action_result"] = "failed"
            verification_message = "达到最大闭环迭代次数，流程终止"
            status_code = 409
        elif last_status == "success":
            if queue and current_task and queue[0] == current_task:
                queue = queue[1:]
            elif current_task and current_task in queue:
                queue.remove(current_task)

            next_state["task_queue"] = queue
            if queue:
                next_state["current_task"] = queue[0]
                next_state["action_result"] = "in_progress"
                verification_message = "当前任务完成，继续处理后续任务"
            else:
                next_state["current_task"] = ""
                next_state["action_result"] = "success"
                verification_message = "全部任务完成"
            status_code = 200
        elif last_status == "in_progress":
            next_state["action_result"] = "in_progress"
            verification_message = "动作仍在进行，继续下一轮感知-决策"
            status_code = 202
        else:
            next_state["action_result"] = "failed"
            verification_message = "执行失败，闭环终止"
            status_code = 500

        next_state = set_last_node_result(
            next_state,
            node="verifier",
            status_code=status_code,
            message=verification_message,
            metadata={
                "iteration_count": next_state["iteration_count"],
                "remaining_tasks": list(next_state.get("task_queue", [])),
            },
        )
        return append_history(
            next_state,
            node="verifier",
            message=verification_message,
            status="ok" if next_state["action_result"] != "failed" else "error",
            metadata={
                "iteration_count": next_state["iteration_count"],
                "action_result": next_state["action_result"],
                "scene_description": next_state.get("scene_description", ""),
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("verifier", state, deps, _logic)
