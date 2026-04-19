"""LangGraph main graph for the phase-1 decision loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Any

from langgraph.graph import END, StateGraph

from ..shared.config import AppConfig
from .mcp_client import MCPClientProtocol, MinimalMCPClient
from .nodes import (
    NodeDependencies,
    action_decider_node,
    executor_node,
    scene_analyzer_node,
    task_planner_node,
    verifier_node,
)
from .state import DecisionAgentState, create_initial_state, ensure_agent_state


def _route_after_verifier(state: DecisionAgentState) -> str:
    return "continue" if state.get("action_result") == "in_progress" else "end"


def build_decision_graph(deps: NodeDependencies) -> Any:
    """Build the fixed LangGraph workflow required by the phase-1 spec."""
    graph_builder = StateGraph(DecisionAgentState)

    graph_builder.add_node("task_planner", partial(task_planner_node, deps=deps))
    graph_builder.add_node("scene_analyzer", partial(scene_analyzer_node, deps=deps))
    graph_builder.add_node("action_decider", partial(action_decider_node, deps=deps))
    graph_builder.add_node("executor", partial(executor_node, deps=deps))
    graph_builder.add_node("verifier", partial(verifier_node, deps=deps))

    graph_builder.set_entry_point("task_planner")
    graph_builder.add_edge("task_planner", "scene_analyzer")
    graph_builder.add_edge("scene_analyzer", "action_decider")
    graph_builder.add_edge("action_decider", "executor")
    graph_builder.add_edge("executor", "verifier")
    graph_builder.add_conditional_edges(
        "verifier",
        _route_after_verifier,
        {
            "continue": "scene_analyzer",
            "end": END,
        },
    )
    return graph_builder.compile()


@dataclass(slots=True)
class DecisionEngine:
    """Thin runtime wrapper around the compiled LangGraph decision graph."""

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
