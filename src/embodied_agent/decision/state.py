"""Decision-layer state helpers aligned with shared state definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, TypedDict

from ..shared.types import AgentState as SharedAgentState
from ..shared.types import ExecutionResult, RobotState

DEFAULT_MAX_ITERATIONS = 10
DEFAULT_HISTORY_LIMIT = 100


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
    selected_action: str
    selected_action_args: dict[str, Any]
    last_execution: ExecutionResult
    last_node_result: NodeOutcome
    max_iterations: int
    debug_metrics: DecisionMetrics


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_robot_state() -> RobotState:
    """Return the baseline robot state compatible with shared.types."""
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


def create_initial_state(
    user_instruction: str,
    *,
    robot_state: RobotState | None = None,
    current_image: str = "",
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> DecisionAgentState:
    """Create the minimal decision state entry compatible with shared AgentState."""
    state: DecisionAgentState = {
        "user_instruction": user_instruction.strip(),
        "task_queue": [],
        "current_task": "",
        "current_image": current_image,
        "robot_state": robot_state or empty_robot_state(),
        "scene_description": "",
        "action_result": "in_progress",
        "iteration_count": 0,
        "conversation_history": [],
        "selected_action": "",
        "selected_action_args": {},
        "last_execution": {
            "status": "in_progress",
            "action_name": "",
            "message": "decision state initialized",
            "logs": [],
        },
        "last_node_result": {
            "node": "bootstrap",
            "status_code": 200,
            "message": "state initialized",
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
        metadata={"max_iterations": max_iterations},
    )


def ensure_agent_state(
    state: Mapping[str, Any] | SharedAgentState,
    *,
    max_iterations: int | None = None,
) -> DecisionAgentState:
    """Normalize any incoming state into the decision-layer state shape."""
    normalized: DecisionAgentState = {
        "user_instruction": str(state.get("user_instruction", "")).strip(),
        "task_queue": [str(item) for item in state.get("task_queue", []) if str(item).strip()],
        "current_task": str(state.get("current_task", "")).strip(),
        "current_image": str(state.get("current_image", "")),
        "robot_state": _coerce_robot_state(state.get("robot_state")),
        "scene_description": str(state.get("scene_description", "")),
        "action_result": state.get("action_result", "in_progress"),
        "iteration_count": int(state.get("iteration_count", 0)),
        "conversation_history": _coerce_history(state.get("conversation_history")),
        "selected_action": str(state.get("selected_action", "")).strip(),
        "selected_action_args": dict(state.get("selected_action_args", {})),
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
            "action_name": normalized["selected_action"],
            "message": "",
            "logs": [],
        }

    if not normalized["last_node_result"]:
        normalized["last_node_result"] = {
            "node": "state_loader",
            "status_code": 200,
            "message": "state normalized",
            "metadata": {},
            "timestamp": _utc_now_iso(),
        }

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
    """Append a bounded history record and return a copied state."""
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
    """Set a normalized node result envelope on a copied state."""
    copied_state: DecisionAgentState = dict(state)
    copied_state["last_node_result"] = {
        "node": node,
        "status_code": status_code,
        "message": message,
        "metadata": metadata or {},
        "timestamp": _utc_now_iso(),
    }
    return copied_state


def record_node_duration(
    state: DecisionAgentState,
    *,
    node: str,
    duration_ms: float,
) -> DecisionAgentState:
    """Track node timing in debug metrics without mutating the input state."""
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
    """Track MCP tool usage for observability."""
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
