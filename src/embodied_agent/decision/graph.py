"""LangGraph main graph aligned with the mermaid blueprint workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Any

from langgraph.graph import END, StateGraph

from ..shared.config import AppConfig
from .mcp_client import MCPClientProtocol, MinimalMCPClient
from .providers import build_decision_provider
from .nodes import (
    NodeDependencies,
    active_perception_node,
    assessment_node,
    compensation_node,
    error_diagnosis_node,
    final_status_node,
    goal_check_node,
    hri_node,
    motion_control_node,
    nlu_node,
    pre_feedback_node,
    sensory_node,
    state_compression_node,
    success_notice_node,
    task_planning_node,
    trigger_node,
    verification_node,
)
from .state import DecisionAgentState, create_initial_state, ensure_agent_state


def _route_after_assessment(state: DecisionAgentState) -> str:
    assessment = state.get("assessment_result", {})
    if isinstance(assessment, dict) and assessment.get("requires_active_perception"):
        return "active_perception"
    return "task_planning"


def _route_after_verification(state: DecisionAgentState) -> str:
    retry_context = state.get("retry_context", {})
    if isinstance(retry_context, dict) and retry_context.get("exhausted"):
        return "success"
    if state.get("termination_reason") == "compensation_exhausted":
        return "success"
    if state.get("action_result") == "failed":
        return "error"
    return "success"


def _route_after_hri(state: DecisionAgentState) -> str:
    intervention = state.get("human_intervention", {})
    if isinstance(intervention, dict) and intervention.get("required"):
        return "compensation"
    return "compensation"


def _route_after_goal_check(state: DecisionAgentState) -> str:
    goal_check = state.get("goal_check_result", {})
    if isinstance(goal_check, dict) and goal_check.get("terminal"):
        return "final_status"
    return "state_compression"


def build_decision_graph(deps: NodeDependencies) -> Any:
    graph_builder = StateGraph(DecisionAgentState)

    graph_builder.add_node("trigger", partial(trigger_node, deps=deps))
    graph_builder.add_node("nlu", partial(nlu_node, deps=deps))
    graph_builder.add_node("sensory", partial(sensory_node, deps=deps))
    graph_builder.add_node("assessment", partial(assessment_node, deps=deps))
    graph_builder.add_node("active_perception", partial(active_perception_node, deps=deps))
    graph_builder.add_node("task_planning", partial(task_planning_node, deps=deps))
    graph_builder.add_node("pre_feedback", partial(pre_feedback_node, deps=deps))
    graph_builder.add_node("motion_control", partial(motion_control_node, deps=deps))
    graph_builder.add_node("verification", partial(verification_node, deps=deps))
    graph_builder.add_node("error_diagnosis", partial(error_diagnosis_node, deps=deps))
    graph_builder.add_node("hri", partial(hri_node, deps=deps))
    graph_builder.add_node("compensation", partial(compensation_node, deps=deps))
    graph_builder.add_node("success_notice", partial(success_notice_node, deps=deps))
    graph_builder.add_node("goal_check", partial(goal_check_node, deps=deps))
    graph_builder.add_node("state_compression", partial(state_compression_node, deps=deps))
    graph_builder.add_node("final_status", partial(final_status_node, deps=deps))

    graph_builder.set_entry_point("trigger")
    graph_builder.add_edge("trigger", "nlu")
    graph_builder.add_edge("nlu", "sensory")
    graph_builder.add_edge("sensory", "assessment")
    graph_builder.add_conditional_edges(
        "assessment",
        _route_after_assessment,
        {
            "active_perception": "active_perception",
            "task_planning": "task_planning",
        },
    )
    graph_builder.add_edge("active_perception", "sensory")
    graph_builder.add_edge("task_planning", "pre_feedback")
    graph_builder.add_edge("pre_feedback", "motion_control")
    graph_builder.add_edge("motion_control", "verification")
    graph_builder.add_conditional_edges(
        "verification",
        _route_after_verification,
        {
            "error": "error_diagnosis",
            "success": "success_notice",
        },
    )
    graph_builder.add_edge("error_diagnosis", "hri")
    graph_builder.add_conditional_edges(
        "hri",
        _route_after_hri,
        {
            "compensation": "compensation",
        },
    )
    graph_builder.add_edge("compensation", "motion_control")
    graph_builder.add_edge("success_notice", "goal_check")
    graph_builder.add_conditional_edges(
        "goal_check",
        _route_after_goal_check,
        {
            "state_compression": "state_compression",
            "final_status": "final_status",
        },
    )
    graph_builder.add_edge("state_compression", "sensory")
    graph_builder.add_edge("final_status", END)
    return graph_builder.compile()


@dataclass(slots=True)
class DecisionEngine:
    """Runtime wrapper around the compiled LangGraph decision graph."""

    deps: NodeDependencies
    graph: Any = field(init=False)

    def __post_init__(self) -> None:
        self.graph = build_decision_graph(self.deps)

    @classmethod
    def from_config(
        cls,
        config: AppConfig,
        *,
        mcp_client: MCPClientProtocol | None = None,
    ) -> "DecisionEngine":
        deps = NodeDependencies(
            config=config,
            mcp_client=mcp_client or MinimalMCPClient(),
            provider_metadata=build_decision_provider(config.decision).summary(),
        )
        return cls(deps=deps)

    def invoke(
        self,
        user_instruction: str,
        *,
        state: DecisionAgentState | None = None,
    ) -> DecisionAgentState:
        if state is None:
            runtime_state = create_initial_state(
                user_instruction,
                max_iterations=self.deps.max_iterations,
            )
        else:
            runtime_state = ensure_agent_state(
                state,
                max_iterations=self.deps.max_iterations,
            )
            runtime_state["user_instruction"] = runtime_state.get("user_instruction") or user_instruction
        runtime_state["max_iterations"] = self.deps.max_iterations
        return self.graph.invoke(runtime_state)
