"""Decision-layer nodes aligned with the mermaid blueprint workflow."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Callable

from ..shared.config import AppConfig
from .providers import (
    DecisionProviderError,
    build_decision_provider,
)
from ..shared.types import ActionStatus
from .mcp_client import MCPClientProtocol, MCPResponse
from .state import (
    BLUEPRINT_PHASES,
    DEFAULT_MAX_ITERATIONS,
    DecisionAgentState,
    append_history,
    ensure_agent_state,
    record_decision_cycle,
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
    confidence_threshold: float = 0.6
    max_active_perception_attempts: int = 2
    max_compensation_attempts: int = 2

    @property
    def max_iterations(self) -> int:
        if self.config.decision.max_iterations > 0:
            return self.config.decision.max_iterations
        if self.config.frontend.max_iterations > 0:
            return self.config.frontend.max_iterations
        return DEFAULT_MAX_ITERATIONS


def _split_into_tasks(user_instruction: str) -> list[str]:
    raw_parts = re.split(r"(?:\r?\n|。|；|;|，|、|然后|接着)", user_instruction)
    tasks = [part.strip(" ，,") for part in raw_parts if part and part.strip(" ，,")]
    return tasks or [user_instruction.strip()] if user_instruction.strip() else []


def _normalize_task_text(task: str) -> str:
    normalized = task.strip().lower()
    replacements = {
        "左传": "左转",
        "右传": "右转",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"(\d+)\s*后(?=(?:左|右|转|旋转|转动))", r"\1号", normalized)
    return normalized


def _extract_servo_action_args(task: str) -> dict[str, Any] | None:
    normalized_task = _normalize_task_text(task)
    if not (
        any(keyword in normalized_task for keyword in ("舵机", "关节", "servo", "joint"))
        or re.search(r"\d+\s*号\s*(?:左转|右转|转|旋转|转动)", normalized_task)
    ):
        return None
    if not any(keyword in normalized_task for keyword in ("左转", "右转", "转", "旋转", "转动", "rotate")):
        return None

    servo_id: int | None = None
    for pattern in (
        r"(\d+)\s*号?\s*(?:舵机|关节)",
        r"(?:舵机|关节)\s*(\d+)",
        r"(\d+)\s*号",
        r"servo\s*(\d+)",
        r"joint\s*(\d+)",
    ):
        match = re.search(pattern, normalized_task, re.IGNORECASE)
        if match is not None:
            servo_id = int(match.group(1))
            break

    degrees: float | None = None
    motion_match = re.search(
        r"(左转|右转|旋转|转动|转|rotate)\s*([+-]?\d+(?:\.\d+)?)\s*(?:度|°|deg|degree|degrees)?",
        normalized_task,
        re.IGNORECASE,
    )
    if motion_match is not None:
        direction = motion_match.group(1)
        degrees_text = motion_match.group(2)
        degrees = float(degrees_text)
        if not degrees_text.startswith(("+", "-")):
            if direction == "右转":
                degrees = -degrees
            elif direction == "左转":
                degrees = abs(degrees)

    for pattern in (
        r"([+-]?\d+(?:\.\d+)?)\s*(?:度|°)",
        r"([+-]?\d+(?:\.\d+)?)\s*(?:deg|degree|degrees)",
    ):
        if degrees is not None:
            break
        match = re.search(pattern, normalized_task, re.IGNORECASE)
        if match is not None:
            degrees = float(match.group(1))
            break

    if servo_id is None or degrees is None:
        return None

    return {
        "id": servo_id,
        "degrees": degrees,
    }


def _is_home_task(normalized_task: str) -> bool:
    return any(
        keyword in normalized_task
        for keyword in ("回到安全位置", "回零", "回原点", "归位", "回位", "move home", "home")
    )


def _is_servo_task(normalized_task: str) -> bool:
    return (
        (
            any(keyword in normalized_task for keyword in ("舵机", "关节", "servo", "joint"))
            or re.search(r"\d+\s*号\s*(?:左转|右转|转|旋转|转动)", normalized_task) is not None
        )
        and any(keyword in normalized_task for keyword in ("左转", "右转", "转", "旋转", "转动", "rotate"))
    )


def _is_release_task(normalized_task: str) -> bool:
    return any(keyword in normalized_task for keyword in ("释放", "松开", "放下", "release"))


def _is_scene_query_task(normalized_task: str) -> bool:
    if any(keyword in normalized_task for keyword in ("抓", "取", "pick", "grasp", "归位", "回零", "回原点", "舵机", "关节")):
        return False
    return any(
        keyword in normalized_task
        for keyword in ("看到什么", "看到了什么", "看看", "画面", "场景", "描述", "识别", "观察", "图里", "相机")
    )


def _resolve_strict_atomic_plan(
    current_task: str,
    state: DecisionAgentState,
) -> tuple[str, str, dict[str, Any]] | None:
    normalized_task = _normalize_task_text(current_task)
    if _is_home_task(normalized_task):
        return "return_home", "move_home", {}
    if _is_servo_task(normalized_task):
        servo_action_args = _extract_servo_action_args(current_task)
        if servo_action_args is None:
            raise ValueError("舵机任务缺少明确的编号或角度，无法生成安全 MCP 调用")
        return "servo_control", "servo_rotate", servo_action_args
    if _is_release_task(normalized_task):
        return "release_object", "release", {}
    if _is_scene_query_task(normalized_task):
        return (
            "scene_understanding",
            "describe_scene",
            {
                "image": state.get("current_image", ""),
                "prompt": f"请直接回答用户问题：{current_task}",
            },
        )

    scene_observations = state.get("scene_observations", {})
    robot_grasp_state = str(scene_observations.get("robot_grasp_state", "")).lower()
    if robot_grasp_state == "closed" and any(keyword in normalized_task for keyword in ("放", "置", "release", "drop")):
        return "release_object", "release", {}
    if any(keyword in normalized_task for keyword in ("放", "置", "drop", "place")):
        return "release_object", "release", {}
    return None


def _enforce_task_action_alignment(
    *,
    current_task: str,
    state: DecisionAgentState,
    selected_capability: str,
    selected_action: str,
    selected_action_args: dict[str, Any],
) -> tuple[str, str, dict[str, Any], str | None]:
    strict_plan = _resolve_strict_atomic_plan(current_task, state)
    if strict_plan is None:
        return selected_capability, selected_action, selected_action_args, None

    expected_capability, expected_action, expected_args = strict_plan
    if selected_action != expected_action or selected_capability != expected_capability:
        return (
            expected_capability,
            expected_action,
            dict(expected_args),
            f"task_requires_{expected_action}",
        )

    if expected_action == "servo_rotate":
        if selected_action_args != expected_args:
            return (
                expected_capability,
                expected_action,
                dict(expected_args),
                "task_requires_exact_servo_arguments",
            )
    elif expected_action in {"move_home", "release"} and selected_action_args:
        return (
            expected_capability,
            expected_action,
            dict(expected_args),
            f"task_requires_empty_arguments_for_{expected_action}",
        )

    return expected_capability, expected_action, dict(expected_args), None


def _supports_proprioceptive_feedback(
    current_task: str,
    state: DecisionAgentState,
) -> bool:
    normalized_task = _normalize_task_text(current_task)
    if _is_home_task(normalized_task) or _is_servo_task(normalized_task):
        return True
    _, selected_action, _ = _select_capability_and_action(current_task, state)
    return selected_action in {"servo_rotate", "move_home"}


def _resolve_proprioceptive_action_name(
    current_task: str,
    state: DecisionAgentState,
) -> str:
    normalized_task = _normalize_task_text(current_task)
    if _is_home_task(normalized_task):
        return "move_home"
    if _is_servo_task(normalized_task):
        return "servo_rotate"
    _, selected_action, _ = _select_capability_and_action(current_task, state)
    return selected_action


def _build_proprioceptive_scene_summary(
    *,
    current_task: str,
    selected_action: str,
    robot_state: dict[str, Any],
) -> tuple[str, dict[str, Any], float]:
    joint_positions = robot_state.get("joint_positions", []) if isinstance(robot_state, dict) else []
    joint_count = len(joint_positions) if isinstance(joint_positions, list) else 0
    action_label = "单关节旋转" if selected_action == "servo_rotate" else "安全归位"
    scene_description = (
        f"当前任务“{current_task}”采用机器人关节状态闭环感知。"
        f"已读取 {joint_count} 个关节位置，当前执行策略为{action_label}。"
    )
    return (
        scene_description,
        {
            "objects": [],
            "relations": [],
            "robot_grasp_state": "unknown",
            "risk_flags": [],
            "perception_mode": "proprioceptive",
            "joint_state_available": joint_count > 0,
        },
        0.92,
    )


def _normalize_execution_result(
    response: MCPResponse,
    *,
    fallback_action_name: str,
) -> dict[str, Any]:
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
    strict_plan = _resolve_strict_atomic_plan(current_task, state)
    if strict_plan is not None:
        return strict_plan

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
    if any(keyword in normalized_task for keyword in ("抓", "取", "pick", "grasp")):
        if risk_flags or has_explicit_ungraspable_object:
            return "return_home", "move_home", {}
        return "pick_and_place", "run_smolvla", base_arguments
    return "pick_and_place", "run_smolvla", base_arguments


_VALID_CAPABILITIES = {"pick_and_place", "return_home", "release_object", "servo_control", "scene_understanding"}
_VALID_ACTIONS = {"move_to", "move_home", "grasp", "release", "servo_rotate", "run_smolvla", "describe_scene"}
_ACTION_ALIASES = {
    "pick": "grasp",
    "pick_object": "grasp",
    "grasp_object": "grasp",
    "grab": "grasp",
    "release_object": "release",
    "drop_object": "release",
    "open_gripper": "release",
    "return_home": "move_home",
    "go_home": "move_home",
    "home": "move_home",
    "pick_and_place": "run_smolvla",
    "execute_pick_and_place": "run_smolvla",
    "pick_place": "run_smolvla",
    "verify_grasp": "grasp",
    "rotate_servo": "servo_rotate",
    "servo": "servo_rotate",
}
_CAPABILITY_BY_ACTION = {
    "move_home": "return_home",
    "release": "release_object",
    "servo_rotate": "servo_control",
    "describe_scene": "scene_understanding",
    "move_to": "pick_and_place",
    "grasp": "pick_and_place",
    "run_smolvla": "pick_and_place",
}
_CAPABILITY_ALIASES = {
    "grasp": "pick_and_place",
    "grasp_object": "pick_and_place",
    "pick": "pick_and_place",
    "pick_object": "pick_and_place",
    "pick_place": "pick_and_place",
    "move_home": "return_home",
    "go_home": "return_home",
    "home": "return_home",
    "release": "release_object",
    "drop": "release_object",
    "servo_control": "servo_control",
    "servo_rotate": "servo_control",
    "servo": "servo_control",
    "scene_understanding": "scene_understanding",
    "describe_scene": "scene_understanding",
}


def _normalize_provider_action_plan(
    *,
    selected_capability: str,
    selected_action: str,
    selected_action_args: dict[str, Any],
    current_task: str,
    state: DecisionAgentState,
) -> tuple[str, str, dict[str, Any]]:
    normalized_capability = _CAPABILITY_ALIASES.get(selected_capability.strip(), selected_capability.strip())
    normalized_action = _ACTION_ALIASES.get(selected_action.strip(), selected_action.strip())
    normalized_args = dict(selected_action_args)

    if not normalized_capability and normalized_action in _CAPABILITY_BY_ACTION:
        normalized_capability = _CAPABILITY_BY_ACTION[normalized_action]

    if normalized_action not in _VALID_ACTIONS:
        normalized_action = ""
    if normalized_capability not in _VALID_CAPABILITIES:
        normalized_capability = ""

    if normalized_action == "run_smolvla":
        normalized_args = {
            "task_description": current_task,
            "current_image": state.get("current_image", ""),
            "robot_state": state.get("robot_state", {}),
            **normalized_args,
        }
    elif normalized_action == "describe_scene":
        normalized_args = {
            "image": str(state.get("current_image", "")),
            "prompt": str(normalized_args.get("prompt") or f"请直接回答用户问题：{current_task}"),
        }
    elif normalized_action in {"move_home", "release"}:
        normalized_args = {}

    return normalized_capability, normalized_action, normalized_args


def _build_assistant_response(
    *,
    current_task: str,
    scene_description: str,
    selected_action: str,
    planner_reason: str,
) -> str:
    action_phrases = {
        "move_home": "先回到安全位置",
        "release": "先松开夹爪释放目标",
        "grasp": "先尝试执行抓取",
        "move_to": "先移动到目标位姿",
        "servo_rotate": "先执行单关节安全旋转",
        "run_smolvla": "我准备执行完整抓取动作",
        "describe_scene": "先直接描述当前画面",
    }
    action_phrase = action_phrases.get(selected_action, "我准备继续执行当前任务")
    scene_excerpt = scene_description.strip()
    if len(scene_excerpt) > 80:
        scene_excerpt = f"{scene_excerpt[:80].rstrip()}…"
    parts = []
    if scene_excerpt:
        parts.append(f"我观察到：{scene_excerpt}")
    parts.append(f"针对“{current_task}”，{action_phrase}。")
    if planner_reason.strip():
        parts.append(f"原因：{planner_reason.strip()}")
    return " ".join(parts)


def _build_terminal_assistant_response(
    *,
    current_task: str,
    completed: bool,
    termination_reason: str,
    selected_action: str,
    scene_description: str,
) -> str:
    if completed:
        if selected_action == "describe_scene" and scene_description.strip():
            return scene_description.strip()
        return (
            f"任务已完成。针对“{current_task or '当前任务'}”，我已经执行 `{selected_action or '当前动作'}`，"
            f"并完成本轮闭环。"
        )
    scene_excerpt = scene_description.strip()
    if len(scene_excerpt) > 60:
        scene_excerpt = f"{scene_excerpt[:60].rstrip()}…"
    detail = f" 当前观察：{scene_excerpt}" if scene_excerpt else ""
    return (
        f"这次任务没有成功完成，终止原因是 `{termination_reason or 'unknown'}`。"
        f"我最后尝试的动作是 `{selected_action or 'unknown'}`。{detail}"
    )


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
        failed_state["termination_reason"] = failed_state.get("termination_reason") or "node_exception"
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


def trigger_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        instruction = normalized_state.get("user_instruction", "").strip()
        next_state = dict(normalized_state)
        next_state["goal"] = instruction
        next_state["action_result"] = "in_progress" if instruction else "failed"
        message = "交互触发与指令采集完成" if instruction else "用户指令为空，无法启动流程"
        next_state = set_last_node_result(
            next_state,
            node="trigger",
            status_code=200 if instruction else 400,
            message=message,
            metadata={"instruction": instruction},
        )
        return append_history(
            next_state,
            node="trigger",
            message=message,
            status="ok" if instruction else "error",
            metadata={"phase": "trigger"},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("trigger", state, deps, _logic)


def nlu_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        task_queue = list(normalized_state.get("task_queue", []))
        if not task_queue:
            task_queue = _split_into_tasks(normalized_state["user_instruction"])

        next_state = dict(normalized_state)
        next_state["task_queue"] = task_queue
        next_state["current_task"] = task_queue[0] if task_queue else ""
        next_state["intent"] = {
            "instruction": normalized_state.get("user_instruction", ""),
            "task_count": len(task_queue),
            "tasks": list(task_queue),
        }
        next_state["plan"] = [
            {
                "order": index + 1,
                "task": task,
                "status": "ready" if index == 0 else "pending",
            }
            for index, task in enumerate(task_queue)
        ]
        next_state["action_result"] = "in_progress" if task_queue else "failed"
        message = "语义解析与目标提取完成" if task_queue else "用户指令为空，无法生成任务"
        next_state = set_last_node_result(
            next_state,
            node="nlu",
            status_code=200 if task_queue else 400,
            message=message,
            metadata={"task_count": len(task_queue)},
        )
        return append_history(
            next_state,
            node="nlu",
            message=message,
            status="ok" if task_queue else "error",
            metadata={"tasks": task_queue, "phase": "nlu"},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("nlu", state, deps, _logic)


def sensory_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        prompt_parts = []
        current_task = str(normalized_state.get("current_task", "")).strip()
        if current_task:
            prompt_parts.append(f"当前任务: {current_task}")
        if int(normalized_state.get("active_perception_attempts", 0)) > 0:
            prompt_parts.append("请重点确认目标物、风险标记、夹爪状态，并尽量提升输出置信度。")
        prompt = " ".join(prompt_parts)

        image_response = runtime_deps.mcp_client.get_image()
        working_state = _record_tool_response(normalized_state, response=image_response)
        if not image_response.get("ok"):
            raise RuntimeError(image_response.get("message", "get_image failed"))

        robot_response = runtime_deps.mcp_client.get_robot_state()
        working_state = _record_tool_response(working_state, response=robot_response)
        if not robot_response.get("ok"):
            raise RuntimeError(robot_response.get("message", "get_robot_state failed"))

        next_state = dict(working_state)
        next_state["current_image"] = str(image_response.get("content", ""))
        next_state["robot_state"] = dict(robot_response.get("content", {}))

        scene_response = runtime_deps.mcp_client.describe_scene(
            str(image_response.get("content", "")),
            prompt=prompt,
        )
        working_state = _record_tool_response(working_state, response=scene_response)
        if not scene_response.get("ok") and not _supports_proprioceptive_feedback(current_task, normalized_state):
            raise RuntimeError(scene_response.get("message", "describe_scene failed"))

        next_state = dict(working_state)
        next_state["current_image"] = str(image_response.get("content", ""))
        next_state["robot_state"] = dict(robot_response.get("content", {}))

        if scene_response.get("ok"):
            scene_metadata = (
                dict(scene_response.get("metadata", {}))
                if isinstance(scene_response.get("metadata"), dict)
                else {}
            )
            structured_observations = dict(scene_metadata.get("structured_observations", {}))
            confidence = float(scene_metadata.get("confidence", 0.0) or 0.0)
            perception_mode = "vision"
            provider_name = scene_metadata.get("provider", runtime_deps.config.perception.vlm_provider)
            model_name = scene_metadata.get("model", runtime_deps.config.perception.vlm_model)
            next_state["scene_description"] = str(scene_response.get("content", ""))
            next_state["scene_observations"] = structured_observations
            next_state["perception_confidence"] = confidence
        else:
            selected_capability, selected_action, _ = _select_capability_and_action(current_task, next_state)
            del selected_capability
            (
                next_state["scene_description"],
                next_state["scene_observations"],
                confidence,
            ) = _build_proprioceptive_scene_summary(
                current_task=current_task,
                selected_action=selected_action,
                robot_state=next_state["robot_state"],
            )
            next_state["perception_confidence"] = confidence
            perception_mode = "vision_fallback_to_proprioceptive"
            provider_name = "robot_state"
            model_name = "joint_state_closed_loop"

        next_state = set_last_node_result(
            next_state,
            node="sensory",
            status_code=200,
            message="多模态环境感知完成",
            metadata={
                "confidence": confidence,
                "provider": provider_name,
                "model": model_name,
                "perception_mode": perception_mode,
            },
        )
        return append_history(
            next_state,
            node="sensory",
            message="刷新图像、机器人状态和场景描述",
            status="ok",
            metadata={
                "phase": "sensory",
                "confidence": confidence,
                "perception_mode": perception_mode,
                "scene_description": next_state["scene_description"],
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("sensory", state, deps, _logic)


def assessment_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        confidence = float(normalized_state.get("perception_confidence", 0.0) or 0.0)
        attempts = int(normalized_state.get("active_perception_attempts", 0))
        degraded = attempts >= runtime_deps.max_active_perception_attempts and confidence < runtime_deps.confidence_threshold
        confidence_ok = confidence >= runtime_deps.confidence_threshold or degraded
        requires_active_perception = not confidence_ok
        assessment = {
            "confidence": confidence,
            "threshold": runtime_deps.confidence_threshold,
            "attempts": attempts,
            "confidence_ok": confidence_ok,
            "requires_active_perception": requires_active_perception,
            "degraded": degraded,
            "route": "active_perception" if requires_active_perception else "task_planning",
        }
        next_state = dict(normalized_state)
        next_state["assessment_result"] = assessment
        message = "状态置信度达标" if confidence_ok else "状态置信度不足，转入主动感知"
        next_state = set_last_node_result(
            next_state,
            node="assessment",
            status_code=200,
            message=message,
            metadata=assessment,
        )
        return append_history(
            next_state,
            node="assessment",
            message=message,
            status="ok",
            metadata={"phase": "assessment", **assessment},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("assessment", state, deps, _logic)


def active_perception_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        attempts = int(normalized_state.get("active_perception_attempts", 0)) + 1
        next_state = dict(normalized_state)
        next_state["active_perception_attempts"] = attempts
        next_state = set_last_node_result(
            next_state,
            node="active_perception",
            status_code=200,
            message="主动感知策略已调整",
            metadata={
                "attempts": attempts,
                "target_confidence": runtime_deps.confidence_threshold,
            },
        )
        return append_history(
            next_state,
            node="active_perception",
            message="提高感知关注区域并重新采集环境",
            status="ok",
            metadata={"phase": "active_perception", "attempts": attempts},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("active_perception", state, deps, _logic)


def task_planning_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        current_task = normalized_state.get("current_task", "").strip()
        if not current_task and normalized_state.get("task_queue"):
            current_task = normalized_state["task_queue"][0]

        next_state = dict(normalized_state)
        if not current_task:
            next_state["action_result"] = "success"
            next_state = set_last_node_result(
                next_state,
                node="task_planning",
                status_code=204,
                message="没有待执行任务",
                metadata={},
            )
            return append_history(
                next_state,
                node="task_planning",
                message="未找到待执行任务，直接进入终态判断",
                status="ok",
                metadata={"phase": "task_planning"},
                history_limit=runtime_deps.max_history_entries,
            )

        selected_capability = ""
        selected_action = ""
        selected_action_args: dict[str, Any] = {}
        planner_reason = "基于当前任务与感知结果生成执行路径"
        assistant_response = ""
        provider_metadata = dict(runtime_deps.provider_metadata)
        action_alignment_override: str | None = None
        planning_error = ""
        strict_atomic_plan: tuple[str, str, dict[str, Any]] | None = None

        try:
            planner = build_decision_provider(runtime_deps.config.decision)
            provider_metadata = planner.summary()
            provider_plan = planner.plan(
                instruction=str(normalized_state.get("user_instruction", "")),
                current_task=current_task,
                scene_description=str(normalized_state.get("scene_description", "")),
                scene_observations=dict(normalized_state.get("scene_observations", {})),
            )
            selected_capability = str(provider_plan.get("selected_capability", "")).strip()
            selected_action = str(provider_plan.get("selected_action", "")).strip()
            selected_action_args = dict(provider_plan.get("selected_action_args", {})) if isinstance(provider_plan.get("selected_action_args"), dict) else {}
            selected_capability, selected_action, selected_action_args = _normalize_provider_action_plan(
                selected_capability=selected_capability,
                selected_action=selected_action,
                selected_action_args=selected_action_args,
                current_task=current_task,
                state=normalized_state,
            )
            planner_reason = str(provider_plan.get("reason", planner_reason)).strip() or planner_reason
            assistant_response = str(provider_plan.get("assistant_response", "")).strip()
            provider_metadata = dict(provider_plan.get("provider_metadata", provider_metadata))
        except (DecisionProviderError, ValueError, TypeError, json.JSONDecodeError):
            selected_capability = ""
            selected_action = ""
            selected_action_args = {}

        try:
            (
                selected_capability,
                selected_action,
                selected_action_args,
                action_alignment_override,
            ) = _enforce_task_action_alignment(
                current_task=current_task,
                state=normalized_state,
                selected_capability=selected_capability,
                selected_action=selected_action,
                selected_action_args=selected_action_args,
            )
            strict_atomic_plan = _resolve_strict_atomic_plan(current_task, normalized_state)
        except ValueError as exc:
            selected_capability = ""
            selected_action = ""
            selected_action_args = {}
            planning_error = str(exc)

        if not selected_capability or not selected_action:
            if planning_error:
                provider_metadata = {
                    **provider_metadata,
                    "fallback_used": False,
                    "alignment_error": planning_error,
                }
            else:
                selected_capability, selected_action, selected_action_args = _select_capability_and_action(
                    current_task,
                    normalized_state,
                )
                provider_metadata = {
                    **provider_metadata,
                    "fallback_used": True,
                    "fallback_strategy": "heuristic_task_planning",
                }
        else:
            provider_metadata = {
                **provider_metadata,
                "fallback_used": False,
            }
        if action_alignment_override:
            provider_metadata["alignment_override"] = action_alignment_override

        if planning_error:
            assistant_response = planning_error
            next_state["action_result"] = "failed"
            next_state["termination_reason"] = "task_planning_failed"
        elif strict_atomic_plan is not None or not assistant_response:
            assistant_response = _build_assistant_response(
                current_task=current_task,
                scene_description=str(normalized_state.get("scene_description", "")),
                selected_action=selected_action,
                planner_reason=planner_reason,
            )

        next_state["current_task"] = current_task
        next_state["assistant_response"] = assistant_response
        next_state["selected_capability"] = selected_capability
        next_state["selected_capability_args"] = dict(selected_action_args)
        next_state["selected_action"] = selected_action
        next_state["selected_action_args"] = dict(selected_action_args)
        next_state["current_plan_step"] = {
            "task": current_task,
            "selected_capability": selected_capability,
            "selected_action": selected_action,
            "arguments": dict(selected_action_args),
            "reason": planner_reason,
            "provider_metadata": provider_metadata,
        }
        plan = []
        for index, task in enumerate(next_state.get("task_queue", []), start=1):
            plan.append(
                {
                    "order": index,
                    "task": task,
                    "status": "planned" if task == current_task else "pending",
                    "selected_capability": selected_capability if task == current_task else "",
                    "selected_action": selected_action if task == current_task else "",
                }
            )
        next_state["plan"] = plan
        next_state = set_last_node_result(
            next_state,
            node="task_planning",
            status_code=200,
            message="任务分解与路径规划完成",
            metadata={
                "selected_capability": selected_capability,
                "selected_action": selected_action,
                "current_task": current_task,
                "assistant_response": assistant_response,
                "provider_metadata": provider_metadata,
            },
        )
        return append_history(
            next_state,
            node="task_planning",
            message=assistant_response,
            status="ok",
            metadata={
                "phase": "task_planning",
                "task": current_task,
                "capability": selected_capability,
                "action": selected_action,
                "assistant_response": assistant_response,
                "provider_metadata": provider_metadata,
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("task_planning", state, deps, _logic)


def pre_feedback_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        feedback = {
            "task": normalized_state.get("current_task", ""),
            "selected_capability": normalized_state.get("selected_capability", ""),
            "selected_action": normalized_state.get("selected_action", ""),
            "arguments": dict(normalized_state.get("selected_action_args", {})),
            "perception_confidence": float(normalized_state.get("perception_confidence", 0.0) or 0.0),
            "risk_flags": list(normalized_state.get("scene_observations", {}).get("risk_flags", [])),
            "retry_attempts": int(normalized_state.get("retry_context", {}).get("attempts", 0)),
        }
        next_state = dict(normalized_state)
        next_state["pre_execution_feedback"] = feedback
        next_state = set_last_node_result(
            next_state,
            node="pre_feedback",
            status_code=200,
            message="执行前状态反馈已生成",
            metadata=feedback,
        )
        return append_history(
            next_state,
            node="pre_feedback",
            message="输出执行前状态反馈",
            status="ok",
            metadata={"phase": "pre_feedback", **feedback},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("pre_feedback", state, deps, _logic)


def motion_control_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        selected_action = normalized_state.get("selected_action", "").strip()
        selected_capability = normalized_state.get("selected_capability", "").strip()
        if not selected_action:
            next_state = dict(normalized_state)
            next_state["action_result"] = "failed"
            next_state["termination_reason"] = next_state.get("termination_reason") or "missing_selected_action"
            next_state = set_last_node_result(
                next_state,
                node="motion_control",
                status_code=400,
                message="未提供可执行动作",
                metadata={},
            )
            return append_history(
                next_state,
                node="motion_control",
                message="执行阶段缺少 selected_action",
                status="error",
                metadata={"phase": "motion_control", "selected_capability": selected_capability},
                history_limit=runtime_deps.max_history_entries,
            )

        if selected_action == "describe_scene":
            next_state = dict(normalized_state)
            execution_result = {
                "status": "success",
                "action_name": "describe_scene",
                "message": str(normalized_state.get("scene_description", "")).strip() or "场景感知已完成。",
                "logs": ["describe_scene: 复用本轮 sensory 阶段的视觉感知结果。"],
            }
            next_state["last_execution"] = execution_result
            next_state["execution_feedback"] = {
                "selected_capability": selected_capability,
                "selected_action": selected_action,
                "result": dict(execution_result),
                "tool_ok": True,
                "tool_status_code": 200,
                "metadata": {
                    "source": "sensory_cache",
                    "structured_observations": dict(normalized_state.get("scene_observations", {})),
                    "confidence": float(normalized_state.get("perception_confidence", 0.0) or 0.0),
                },
            }
            next_state["action_result"] = "success"
            next_state = set_last_node_result(
                next_state,
                node="motion_control",
                status_code=200,
                message=str(execution_result["message"]),
                metadata={
                    "selected_capability": selected_capability,
                    "selected_action": selected_action,
                    "tool_ok": True,
                },
            )
            return append_history(
                next_state,
                node="motion_control",
                message="执行动作 describe_scene",
                status="ok",
                metadata={
                    "phase": "motion_control",
                    "selected_capability": selected_capability,
                    "execution_result": execution_result,
                },
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
        content = response.get("content")
        if bool(response.get("ok")) and isinstance(content, dict) and isinstance(content.get("robot_state"), dict):
            next_state["robot_state"] = dict(content.get("robot_state", {}))
        if bool(response.get("ok")) and selected_action == "describe_scene":
            next_state["scene_description"] = str(content or "")
            metadata = dict(response.get("metadata", {})) if isinstance(response.get("metadata"), dict) else {}
            next_state["scene_observations"] = dict(metadata.get("structured_observations", {}))
            next_state["perception_confidence"] = float(metadata.get("confidence", next_state.get("perception_confidence", 0.0)) or 0.0)
        next_state["execution_feedback"] = {
            "selected_capability": selected_capability,
            "selected_action": selected_action,
            "result": dict(execution_result),
            "tool_ok": bool(response.get("ok", False)),
            "tool_status_code": int(response.get("status_code", 500)),
            "metadata": dict(response.get("metadata", {})),
        }
        next_state["action_result"] = execution_result["status"]
        next_state = set_last_node_result(
            next_state,
            node="motion_control",
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
            node="motion_control",
            message=f"执行动作 {selected_action}",
            status="ok" if response.get("ok") else "error",
            metadata={
                "phase": "motion_control",
                "selected_capability": selected_capability,
                "execution_result": execution_result,
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("motion_control", state, deps, _logic)


def verification_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        next_state = dict(normalized_state)
        next_state = record_decision_cycle(next_state)
        next_state["iteration_count"] = int(normalized_state.get("iteration_count", 0)) + 1

        current_task = str(next_state.get("current_task", "")).strip()
        proprioceptive_only = _supports_proprioceptive_feedback(current_task, next_state)

        if str(next_state.get("selected_action", "")).strip() == "describe_scene":
            next_state["action_result"] = "success"
        elif proprioceptive_only:
            verify_robot_state = runtime_deps.mcp_client.get_robot_state()
            next_state = _record_tool_response(next_state, response=verify_robot_state)
            if verify_robot_state.get("ok"):
                next_state["robot_state"] = dict(verify_robot_state.get("content", {}))
                (
                    next_state["scene_description"],
                    next_state["scene_observations"],
                    next_state["perception_confidence"],
                ) = _build_proprioceptive_scene_summary(
                    current_task=current_task,
                    selected_action=str(next_state.get("selected_action", "")),
                    robot_state=next_state["robot_state"],
                )
            else:
                next_state["action_result"] = "failed"
        else:
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
                verify_metadata = (
                    dict(verify_scene_response.get("metadata", {}))
                    if isinstance(verify_scene_response.get("metadata"), dict)
                    else {}
                )
                next_state["scene_description"] = str(verify_scene_response.get("content", ""))
                next_state["scene_observations"] = dict(verify_metadata.get("structured_observations", {}))
                next_state["perception_confidence"] = float(
                    verify_metadata.get("confidence", next_state.get("perception_confidence", 0.0)) or 0.0
                )

        last_status = str(next_state.get("action_result", "failed"))
        if last_status != "success" and next_state["iteration_count"] >= int(next_state.get("max_iterations", runtime_deps.max_iterations)):
            verification_status: ActionStatus = "failed"
            next_state["action_result"] = "failed"
            next_state["termination_reason"] = "max_iterations_reached"
            message = "达到最大闭环迭代次数，流程终止"
            status_code = 409
        elif last_status == "failed":
            verification_status = "failed"
            message = "执行结果验证失败"
            status_code = 500
        elif last_status == "success":
            verification_status = "success"
            message = "执行结果验证通过"
            status_code = 200
        else:
            verification_status = "in_progress"
            message = "执行仍在进行，继续进入目标判断"
            status_code = 202

        next_state["verification_result"] = {
            "status": verification_status,
            "iteration_count": next_state["iteration_count"],
            "current_task": next_state.get("current_task", ""),
            "confidence": next_state.get("perception_confidence", 0.0),
            "verification_mode": "proprioceptive" if proprioceptive_only else "vision",
            "message": message,
        }
        next_state["action_result"] = verification_status
        next_state = set_last_node_result(
            next_state,
            node="verification",
            status_code=status_code,
            message=message,
            metadata={
                "iteration_count": next_state["iteration_count"],
                "action_result": verification_status,
            },
        )
        return append_history(
            next_state,
            node="verification",
            message=message,
            status="ok" if verification_status != "failed" else "error",
            metadata={
                "phase": "verification",
                "iteration_count": next_state["iteration_count"],
                "action_result": verification_status,
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("verification", state, deps, _logic)


def error_diagnosis_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        attempts = int(normalized_state.get("retry_context", {}).get("attempts", 0)) + 1
        recoverable = attempts <= runtime_deps.max_compensation_attempts
        reason = str(
            normalized_state.get("last_execution", {}).get("message")
            or normalized_state.get("last_node_result", {}).get("message", "执行失败")
        )
        diagnosis = {
            "attempts": attempts,
            "recoverable": recoverable,
            "category": "execution_failure",
            "reason": reason,
            "recommended_strategy": "retry_last_action" if recoverable else "safe_return_home",
        }
        next_state = dict(normalized_state)
        next_state["error_diagnosis"] = diagnosis
        next_state["retry_context"] = {
            **dict(normalized_state.get("retry_context", {})),
            "attempts": attempts,
            "exhausted": not recoverable,
            "strategy": diagnosis["recommended_strategy"],
        }
        next_state["action_result"] = "failed"
        next_state = set_last_node_result(
            next_state,
            node="error_diagnosis",
            status_code=200,
            message="错误诊断完成，转入人工协同",
            metadata=diagnosis,
        )
        return append_history(
            next_state,
            node="error_diagnosis",
            message="完成错误诊断并生成恢复策略",
            status="ok",
            metadata={"phase": "error_diagnosis", **diagnosis},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("error_diagnosis", state, deps, _logic)


def hri_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        diagnosis = dict(normalized_state.get("error_diagnosis", {}))
        recoverable = bool(diagnosis.get("recoverable", False))
        intervention = {
            "required": not recoverable,
            "mode": "auto_retry" if recoverable else "safe_abort",
            "message": "自动确认补偿执行" if recoverable else "恢复预算耗尽，切换为安全终止策略",
        }
        next_state = dict(normalized_state)
        next_state["human_intervention"] = intervention
        next_state = set_last_node_result(
            next_state,
            node="hri",
            status_code=200,
            message="人工干预/协同策略已生成",
            metadata=intervention,
        )
        return append_history(
            next_state,
            node="hri",
            message="更新人工干预或协同策略",
            status="ok",
            metadata={"phase": "hri", **intervention},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("hri", state, deps, _logic)


def compensation_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        retry_context = dict(normalized_state.get("retry_context", {}))
        exhausted = bool(retry_context.get("exhausted", False))
        next_state = dict(normalized_state)
        if exhausted:
            selected_capability = "return_home"
            selected_action = "move_home"
            selected_action_args: dict[str, Any] = {}
            strategy = "safe_return_home"
            next_state["termination_reason"] = "compensation_exhausted"
            reason = "补偿预算耗尽，执行安全回零并进入终态判断"
        else:
            selected_capability = str(normalized_state.get("selected_capability", "")).strip()
            selected_action = str(normalized_state.get("selected_action", "")).strip()
            selected_action_args = dict(normalized_state.get("selected_action_args", {}))
            if not selected_action:
                selected_capability, selected_action, selected_action_args = _select_capability_and_action(
                    str(normalized_state.get("current_task", "")),
                    normalized_state,
                )
            strategy = "retry_last_action"
            reason = "补偿控制已生成，将重试上一步执行动作"

        next_state["selected_capability"] = selected_capability
        next_state["selected_action"] = selected_action
        next_state["selected_action_args"] = dict(selected_action_args)
        next_state["current_plan_step"] = {
            "task": next_state.get("current_task", ""),
            "selected_capability": selected_capability,
            "selected_action": selected_action,
            "arguments": dict(selected_action_args),
            "reason": reason,
        }
        next_state["retry_context"] = {
            **retry_context,
            "strategy": strategy,
            "exhausted": exhausted,
        }
        next_state["action_result"] = "in_progress"
        next_state = set_last_node_result(
            next_state,
            node="compensation",
            status_code=200,
            message="补偿控制与重试策略已生成",
            metadata={
                "selected_capability": selected_capability,
                "selected_action": selected_action,
                "strategy": strategy,
                "exhausted": exhausted,
            },
        )
        return append_history(
            next_state,
            node="compensation",
            message=reason,
            status="ok",
            metadata={
                "phase": "compensation",
                "selected_capability": selected_capability,
                "selected_action": selected_action,
                "strategy": strategy,
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("compensation", state, deps, _logic)


def success_notice_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        message = "完成信号反馈已生成"
        next_state = dict(normalized_state)
        next_state = set_last_node_result(
            next_state,
            node="success_notice",
            status_code=200,
            message=message,
            metadata={"action_result": next_state.get("action_result", "in_progress")},
        )
        return append_history(
            next_state,
            node="success_notice",
            message=message,
            status="ok",
            metadata={"phase": "success_notice", "action_result": next_state.get("action_result", "in_progress")},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("success_notice", state, deps, _logic)


def goal_check_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        next_state = dict(normalized_state)
        queue = list(next_state.get("task_queue", []))
        current_task = str(next_state.get("current_task", "")).strip()
        action_result = str(next_state.get("action_result", "in_progress"))
        retry_context = dict(next_state.get("retry_context", {}))

        if bool(retry_context.get("exhausted", False)) and next_state.get("termination_reason") == "compensation_exhausted":
            terminal = True
            completed = False
            reason = "compensation_exhausted"
            message = "恢复预算耗尽，任务以安全终止结束"
        elif action_result == "success":
            if queue and current_task and queue[0] == current_task:
                queue = queue[1:]
            elif current_task and current_task in queue:
                queue.remove(current_task)
            next_state["task_queue"] = queue
            if queue:
                next_state["current_task"] = queue[0]
                next_state["action_result"] = "in_progress"
                terminal = False
                completed = False
                reason = "remaining_tasks"
                message = "任务未完结，继续闭环"
            else:
                next_state["current_task"] = ""
                terminal = True
                completed = True
                reason = "all_tasks_completed"
                message = "任务完结，进入最终报告"
        else:
            terminal = False
            completed = False
            reason = "continue_loop"
            message = "任务未完结，继续闭环"

        next_state["goal_check_result"] = {
            "terminal": terminal,
            "completed": completed,
            "remaining_tasks": list(next_state.get("task_queue", [])),
            "reason": reason,
        }
        if terminal:
            next_state["termination_reason"] = reason
        next_state = set_last_node_result(
            next_state,
            node="goal_check",
            status_code=200,
            message=message,
            metadata=next_state["goal_check_result"],
        )
        return append_history(
            next_state,
            node="goal_check",
            message=message,
            status="ok",
            metadata={"phase": "goal_check", **next_state["goal_check_result"]},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("goal_check", state, deps, _logic)


def state_compression_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        next_state = dict(normalized_state)
        next_state["memory_summary"] = {
            "goal": next_state.get("goal", ""),
            "remaining_tasks": list(next_state.get("task_queue", [])),
            "iteration_count": int(next_state.get("iteration_count", 0)),
            "last_scene_description": next_state.get("scene_description", ""),
            "last_successful_action": next_state.get("selected_action", ""),
            "active_perception_attempts": int(next_state.get("active_perception_attempts", 0)),
            "retry_attempts": int(next_state.get("retry_context", {}).get("attempts", 0)),
        }
        next_state["action_result"] = "in_progress"
        next_state = set_last_node_result(
            next_state,
            node="state_compression",
            status_code=200,
            message="环境状态压缩与记忆更新完成",
            metadata=next_state["memory_summary"],
        )
        return append_history(
            next_state,
            node="state_compression",
            message="压缩当前环境状态并更新记忆摘要",
            status="ok",
            metadata={"phase": "state_compression", **next_state["memory_summary"]},
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("state_compression", state, deps, _logic)


def final_status_node(state: DecisionAgentState, deps: NodeDependencies) -> DecisionAgentState:
    def _logic(normalized_state: DecisionAgentState, runtime_deps: NodeDependencies) -> DecisionAgentState:
        goal_check_result = dict(normalized_state.get("goal_check_result", {}))
        completed = bool(goal_check_result.get("completed", False))
        termination_reason = str(
            normalized_state.get("termination_reason")
            or goal_check_result.get("reason", "all_tasks_completed" if completed else "terminated")
        )
        next_state = dict(normalized_state)
        next_state["action_result"] = "success" if completed else "failed"
        next_state["termination_reason"] = termination_reason
        preserved_failure_response = str(next_state.get("assistant_response", "")).strip()
        if not completed and termination_reason == "task_planning_failed" and preserved_failure_response:
            next_state["assistant_response"] = preserved_failure_response
        else:
            next_state["assistant_response"] = _build_terminal_assistant_response(
                current_task=str(next_state.get("current_task", "")),
                completed=completed,
                termination_reason=termination_reason,
                selected_action=str(next_state.get("selected_action", "")),
                scene_description=str(next_state.get("scene_description", "")),
            )
        next_state["final_report"] = {
            "goal": next_state.get("goal", ""),
            "status": "completed" if completed else "failed",
            "completed": completed,
            "termination_reason": termination_reason,
            "assistant_response": next_state["assistant_response"],
            "remaining_tasks": list(next_state.get("task_queue", [])),
            "iteration_count": int(next_state.get("iteration_count", 0)),
            "last_execution": dict(next_state.get("last_execution", {})),
            "memory_summary": dict(next_state.get("memory_summary", {})),
            "observed_phases": [
                item.get("node")
                for item in next_state.get("conversation_history", [])
                if item.get("node") in BLUEPRINT_PHASES
            ],
        }
        message = "输出执行报告"
        next_state = set_last_node_result(
            next_state,
            node="final_status",
            status_code=200 if completed else 409,
            message=message,
            metadata={
                "completed": completed,
                "termination_reason": termination_reason,
            },
        )
        return append_history(
            next_state,
            node="final_status",
            message=message,
            status="ok" if completed else "error",
            metadata={
                "phase": "final_status",
                "completed": completed,
                "termination_reason": termination_reason,
                "assistant_response": next_state["assistant_response"],
            },
            history_limit=runtime_deps.max_history_entries,
        )

    return _run_node("final_status", state, deps, _logic)


# Backward-compatible aliases for older imports/tests.
task_planner_node = nlu_node
scene_analyzer_node = sensory_node
action_decider_node = task_planning_node
executor_node = motion_control_node
verifier_node = verification_node
