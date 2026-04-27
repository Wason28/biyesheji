"""Decision-layer state helpers aligned with the blueprint workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, TypedDict

from ..shared.types import AgentState as SharedAgentState
from ..shared.types import ExecutionResult, RobotState, RunPhase

DEFAULT_MAX_ITERATIONS = 10
DEFAULT_HISTORY_LIMIT = 100
BLUEPRINT_PHASES: tuple[RunPhase, ...] = (
    "trigger",
    "nlu",
    "sensory",
    "assessment",
    "active_perception",
    "task_planning",
    "pre_feedback",
    "motion_control",
    "verification",
    "error_diagnosis",
    "hri",
    "compensation",
    "success_notice",
    "goal_check",
    "state_compression",
    "final_status",
)
TERMINAL_PHASE: RunPhase = "final_status"


class NodeOutcome(TypedDict, total=False):
    node: str
    status_code: int
    message: str
    metadata: dict[str, Any]
    timestamp: str


class DecisionMetrics(TypedDict, total=False):
    decision_cycles: int
    node_durations_ms: dict[str, float]
    tool_calls: list[dict[str, Any]]


class DecisionAgentState(SharedAgentState, total=False):
    current_phase: RunPhase
    goal: str
    intent: dict[str, Any]
    scene_observations: dict[str, Any]
    perception_confidence: float
    assessment_result: dict[str, Any]
    active_perception_attempts: int
    selected_capability: str
    selected_capability_args: dict[str, Any]
    selected_action: str
    selected_action_args: dict[str, Any]
    plan: list[dict[str, Any]]
    current_plan_step: dict[str, Any]
    pre_execution_feedback: dict[str, Any]
    execution_feedback: dict[str, Any]
    verification_result: dict[str, Any]
    error_diagnosis: dict[str, Any]
    human_intervention: dict[str, Any]
    retry_context: dict[str, Any]
    memory_summary: dict[str, Any]
    goal_check_result: dict[str, Any]
    final_report: dict[str, Any]
    termination_reason: str
    last_execution: ExecutionResult
    last_node_result: NodeOutcome
    max_iterations: int
    debug_metrics: DecisionMetrics


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_robot_state() -> RobotState:
    return {
        "joint_positions": [],
        "ee_pose": {},
    }


def _coerce_robot_state(value: Any) -> RobotState:
    if not isinstance(value, Mapping):
        return empty_robot_state()
    joint_positions = value.get("joint_positions")
    ee_pose = value.get("ee_pose")
    return {
        "joint_positions": list(joint_positions) if isinstance(joint_positions, list) else [],
        "ee_pose": dict(ee_pose) if isinstance(ee_pose, Mapping) else {},
    }


def _coerce_history(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized_history: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            normalized_history.append(dict(item))
        else:
            normalized_history.append(
                {
                    "timestamp": _utc_now_iso(),
                    "node": "state_loader",
                    "status": "normalized",
                    "message": str(item),
                    "metadata": {},
                }
            )
    return normalized_history


def _coerce_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _coerce_plan(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            normalized.append(dict(item))
    return normalized


def _coerce_metrics(value: Any) -> DecisionMetrics:
    if not isinstance(value, Mapping):
        return {
            "decision_cycles": 0,
            "node_durations_ms": {},
            "tool_calls": [],
        }
    tool_calls = value.get("tool_calls")
    return {
        "decision_cycles": int(value.get("decision_cycles", 0)),
        "node_durations_ms": dict(value.get("node_durations_ms", {})),
        "tool_calls": list(tool_calls) if isinstance(tool_calls, list) else [],
    }


def _coerce_phase(value: Any) -> RunPhase:
    if isinstance(value, str) and value in BLUEPRINT_PHASES:
        return value  # type: ignore[return-value]
    return "trigger"


def create_initial_state(
    user_instruction: str,
    *,
    robot_state: RobotState | None = None,
    current_image: str = "",
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> DecisionAgentState:
    state: DecisionAgentState = {
        "user_instruction": user_instruction.strip(),
        "task_queue": [],
        "current_task": "",
        "assistant_response": "",
        "current_image": current_image,
        "robot_state": robot_state or empty_robot_state(),
        "scene_description": "",
        "scene_observations": {},
        "current_phase": "trigger",
        "goal": user_instruction.strip(),
        "intent": {},
        "perception_confidence": 0.0,
        "assessment_result": {},
        "active_perception_attempts": 0,
        "action_result": "in_progress",
        "iteration_count": 0,
        "conversation_history": [],
        "selected_capability": "",
        "selected_capability_args": {},
        "selected_action": "",
        "selected_action_args": {},
        "plan": [],
        "current_plan_step": {},
        "pre_execution_feedback": {},
        "execution_feedback": {},
        "verification_result": {},
        "error_diagnosis": {},
        "human_intervention": {},
        "retry_context": {"attempts": 0},
        "memory_summary": {},
        "goal_check_result": {},
        "final_report": {},
        "termination_reason": "",
        "last_execution": {
            "status": "in_progress",
            "action_name": "",
            "message": "decision state initialized",
            "logs": [],
        },
        "last_node_result": {
            "node": "trigger",
            "status_code": 200,
            "message": "交互触发已就绪",
            "metadata": {},
            "timestamp": _utc_now_iso(),
        },
        "max_iterations": max_iterations,
        "debug_metrics": _coerce_metrics(None),
    }
    return append_history(
        state,
        node="bootstrap",
        message="初始化决策状态",
        status="ready",
        metadata={"max_iterations": max_iterations, "phase": "trigger"},
    )


def ensure_agent_state(
    state: Mapping[str, Any] | SharedAgentState,
    *,
    max_iterations: int | None = None,
) -> DecisionAgentState:
    normalized: DecisionAgentState = {
        "user_instruction": str(state.get("user_instruction", "")).strip(),
        "task_queue": [str(item) for item in state.get("task_queue", []) if str(item).strip()],
        "current_task": str(state.get("current_task", "")).strip(),
        "assistant_response": str(state.get("assistant_response", "")).strip(),
        "current_image": str(state.get("current_image", "")),
        "robot_state": _coerce_robot_state(state.get("robot_state")),
        "scene_description": str(state.get("scene_description", "")),
        "scene_observations": _coerce_mapping(state.get("scene_observations")),
        "current_phase": _coerce_phase(state.get("current_phase")),
        "goal": str(state.get("goal", state.get("user_instruction", ""))).strip(),
        "intent": _coerce_mapping(state.get("intent")),
        "perception_confidence": float(state.get("perception_confidence", 0.0) or 0.0),
        "assessment_result": _coerce_mapping(state.get("assessment_result")),
        "active_perception_attempts": int(state.get("active_perception_attempts", 0)),
        "action_result": state.get("action_result", "in_progress"),
        "iteration_count": int(state.get("iteration_count", 0)),
        "conversation_history": _coerce_history(state.get("conversation_history")),
        "selected_capability": str(state.get("selected_capability", "")).strip(),
        "selected_capability_args": _coerce_mapping(state.get("selected_capability_args")),
        "selected_action": str(state.get("selected_action", "")).strip(),
        "selected_action_args": _coerce_mapping(state.get("selected_action_args")),
        "plan": _coerce_plan(state.get("plan")),
        "current_plan_step": _coerce_mapping(state.get("current_plan_step")),
        "pre_execution_feedback": _coerce_mapping(state.get("pre_execution_feedback")),
        "execution_feedback": _coerce_mapping(state.get("execution_feedback")),
        "verification_result": _coerce_mapping(state.get("verification_result")),
        "error_diagnosis": _coerce_mapping(state.get("error_diagnosis")),
        "human_intervention": _coerce_mapping(state.get("human_intervention")),
        "retry_context": _coerce_mapping(state.get("retry_context")),
        "memory_summary": _coerce_mapping(state.get("memory_summary")),
        "goal_check_result": _coerce_mapping(state.get("goal_check_result")),
        "final_report": _coerce_mapping(state.get("final_report")),
        "termination_reason": str(state.get("termination_reason", "")),
        "last_execution": dict(state.get("last_execution", {})),
        "last_node_result": dict(state.get("last_node_result", {})),
        "max_iterations": int(
            state.get(
                "max_iterations",
                max_iterations if max_iterations is not None else DEFAULT_MAX_ITERATIONS,
            )
        ),
        "debug_metrics": _coerce_metrics(state.get("debug_metrics")),
    }

    if not normalized["current_task"] and normalized["task_queue"]:
        normalized["current_task"] = normalized["task_queue"][0]

    if not normalized["last_execution"]:
        normalized["last_execution"] = {
            "status": normalized["action_result"],
            "action_name": normalized["selected_action"] or normalized["selected_capability"],
            "message": "",
            "logs": [],
        }

    if not normalized["last_node_result"]:
        normalized["last_node_result"] = {
            "node": normalized["current_phase"],
            "status_code": 200,
            "message": "state normalized",
            "metadata": {},
            "timestamp": _utc_now_iso(),
        }

    if not normalized["retry_context"]:
        normalized["retry_context"] = {"attempts": 0}

    return normalized


def append_history(
    state: DecisionAgentState,
    *,
    node: str,
    message: str,
    status: str,
    metadata: dict[str, Any] | None = None,
    history_limit: int = DEFAULT_HISTORY_LIMIT,
) -> DecisionAgentState:
    copied_state: DecisionAgentState = dict(state)
    history = list(copied_state.get("conversation_history", []))
    history.append(
        {
            "timestamp": _utc_now_iso(),
            "node": node,
            "status": status,
            "message": message,
            "metadata": metadata or {},
        }
    )
    copied_state["conversation_history"] = history[-history_limit:]
    return copied_state


def set_last_node_result(
    state: DecisionAgentState,
    *,
    node: str,
    status_code: int,
    message: str,
    metadata: dict[str, Any] | None = None,
) -> DecisionAgentState:
    copied_state: DecisionAgentState = dict(state)
    copied_state["last_node_result"] = {
        "node": node,
        "status_code": status_code,
        "message": message,
        "metadata": metadata or {},
        "timestamp": _utc_now_iso(),
    }
    copied_state["current_phase"] = _coerce_phase(node)
    return copied_state


def record_node_duration(
    state: DecisionAgentState,
    *,
    node: str,
    duration_ms: float,
) -> DecisionAgentState:
    copied_state: DecisionAgentState = dict(state)
    metrics = _coerce_metrics(copied_state.get("debug_metrics"))
    node_durations = dict(metrics.get("node_durations_ms", {}))
    node_durations[node] = round(duration_ms, 3)
    metrics["node_durations_ms"] = node_durations
    copied_state["debug_metrics"] = metrics
    return copied_state


def record_tool_call(
    state: DecisionAgentState,
    *,
    tool_name: str,
    ok: bool,
    metadata: dict[str, Any] | None = None,
) -> DecisionAgentState:
    copied_state: DecisionAgentState = dict(state)
    metrics = _coerce_metrics(copied_state.get("debug_metrics"))
    tool_calls = list(metrics.get("tool_calls", []))
    tool_calls.append(
        {
            "timestamp": _utc_now_iso(),
            "tool_name": tool_name,
            "ok": ok,
            "metadata": metadata or {},
        }
    )
    metrics["tool_calls"] = tool_calls[-DEFAULT_HISTORY_LIMIT:]
    copied_state["debug_metrics"] = metrics
    return copied_state


def record_decision_cycle(state: DecisionAgentState) -> DecisionAgentState:
    copied_state: DecisionAgentState = dict(state)
    metrics = _coerce_metrics(copied_state.get("debug_metrics"))
    metrics["decision_cycles"] = int(metrics.get("decision_cycles", 0)) + 1
    copied_state["debug_metrics"] = metrics
    return copied_state
