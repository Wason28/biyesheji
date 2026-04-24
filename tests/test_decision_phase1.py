import json

from embodied_agent.decision.graph import DecisionEngine
from embodied_agent.decision.mcp_client import MinimalMCPClient
from embodied_agent.decision.nodes import NodeDependencies, action_decider_node
from embodied_agent.decision.providers import (
    DecisionProviderSettings,
    MockDecisionProvider,
    OpenAICompatibleDecisionProvider,
    build_decision_provider,
)
from embodied_agent.perception.server import PerceptionMCPServer


def _build_engine(app_config):
    return DecisionEngine.from_config(app_config, mcp_client=MinimalMCPClient())


def _history_messages(state: dict, node: str) -> list[str]:
    return [
        item["message"]
        for item in state["conversation_history"]
        if item.get("node") == node
    ]


def _history_nodes(state: dict) -> list[str]:
    return [
        item["node"]
        for item in state["conversation_history"]
        if item.get("node") != "bootstrap"
    ]


class _LowConfidencePerceptionServer(PerceptionMCPServer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.describe_calls = 0

    def call_tool(self, tool_name: str, arguments: dict[str, object] | None = None) -> dict[str, object]:
        payload = super().call_tool(tool_name, arguments)
        if tool_name == "describe_scene" and payload.get("ok"):
            self.describe_calls += 1
            payload = dict(payload)
            content = dict(payload.get("content", {}))
            content["confidence"] = 0.2 if self.describe_calls == 1 else 0.95
            payload["content"] = content
        return payload


def test_decision_engine_single_task_reaches_blueprint_terminal_phase(app_config) -> None:
    engine = _build_engine(app_config)

    final_state = engine.invoke("抓取桌面方块")

    assert final_state["action_result"] == "success"
    assert final_state["current_phase"] == "final_status"
    assert final_state["iteration_count"] == 1
    assert final_state["task_queue"] == []
    assert final_state["current_task"] == ""
    assert final_state["selected_capability"] == "pick_and_place"
    assert final_state["selected_action"] == "run_smolvla"
    assert final_state["last_node_result"]["node"] == "final_status"
    assert final_state["termination_reason"] == "all_tasks_completed"
    assert final_state["goal_check_result"]["terminal"] is True
    assert final_state["final_report"]["completed"] is True
    assert _history_nodes(final_state) == [
        "trigger",
        "nlu",
        "sensory",
        "assessment",
        "task_planning",
        "pre_feedback",
        "motion_control",
        "verification",
        "success_notice",
        "goal_check",
        "final_status",
    ]
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert tool_names.count("run_smolvla") == 1


def test_decision_engine_continues_loop_for_remaining_tasks(app_config) -> None:
    engine = _build_engine(app_config)

    final_state = engine.invoke("抓取桌面方块，然后回到安全位置")

    assert final_state["action_result"] == "success"
    assert final_state["current_phase"] == "final_status"
    assert final_state["iteration_count"] == 2
    assert final_state["task_queue"] == []
    assert final_state["current_task"] == ""
    assert final_state["termination_reason"] == "all_tasks_completed"
    assert "任务未完结，继续闭环" in _history_messages(final_state, "goal_check")
    motion_messages = _history_messages(final_state, "motion_control")
    assert len(motion_messages) == 2
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert tool_names.count("run_smolvla") == 1
    assert tool_names.count("move_home") == 1
    assert "state_compression" in _history_nodes(final_state)


def test_decision_engine_selects_release_action_for_release_task(app_config) -> None:
    engine = _build_engine(app_config)

    final_state = engine.invoke("释放夹爪")

    assert final_state["action_result"] == "success"
    assert final_state["selected_capability"] == "release_object"
    assert final_state["selected_action"] == "release"
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert tool_names.count("release") == 1


def test_decision_engine_routes_to_active_perception_when_confidence_is_low(app_config) -> None:
    runtime_engine = DecisionEngine.from_config(
        app_config,
        mcp_client=MinimalMCPClient(),
    )
    perception = _LowConfidencePerceptionServer(app_config)
    from embodied_agent.app import UnifiedMCPClient
    from embodied_agent.execution.server import MockMCPServer

    engine = DecisionEngine.from_config(
        app_config,
        mcp_client=UnifiedMCPClient(perception, MockMCPServer()),
    )

    final_state = engine.invoke("抓取桌面方块")

    assert final_state["action_result"] == "success"
    assert final_state["active_perception_attempts"] == 1
    history_nodes = _history_nodes(final_state)
    assert history_nodes[:8] == [
        "trigger",
        "nlu",
        "sensory",
        "assessment",
        "active_perception",
        "sensory",
        "assessment",
        "task_planning",
    ]


def test_decision_engine_selects_release_for_place_like_task(app_config) -> None:
    deps = NodeDependencies(config=app_config, mcp_client=MinimalMCPClient())

    state = {
        "user_instruction": "放下方块",
        "task_queue": ["放下方块"],
        "current_task": "放下方块",
        "current_image": "mock_base64_image",
        "robot_state": {"joint_positions": [], "ee_pose": {}},
        "scene_description": "当前夹爪已抓住目标",
        "scene_observations": {"robot_grasp_state": "closed", "risk_flags": []},
        "action_result": "in_progress",
        "iteration_count": 0,
        "conversation_history": [],
    }

    final_state = action_decider_node(state, deps)

    assert final_state["selected_capability"] == "release_object"
    assert final_state["selected_action"] == "release"


def test_decision_engine_returns_home_when_no_graspable_object_exists(app_config) -> None:
    deps = NodeDependencies(config=app_config, mcp_client=MinimalMCPClient())

    state = {
        "user_instruction": "抓取桌面方块",
        "task_queue": ["抓取桌面方块"],
        "current_task": "抓取桌面方块",
        "current_image": "mock_base64_image",
        "robot_state": {"joint_positions": [], "ee_pose": {}},
        "scene_description": "未检测到可抓取目标",
        "scene_observations": {
            "robot_grasp_state": "open",
            "risk_flags": [],
            "objects": [{"name": "cube", "category": "target_object", "graspable": False}],
        },
        "action_result": "in_progress",
        "iteration_count": 0,
        "conversation_history": [],
    }

    final_state = action_decider_node(state, deps)

    assert final_state["selected_capability"] == "return_home"
    assert final_state["selected_action"] == "move_home"




def test_build_decision_provider_uses_mock_fallback_when_unconfigured(app_config) -> None:
    provider = build_decision_provider(app_config.decision)

    assert isinstance(provider, MockDecisionProvider)
    assert provider.summary()["mode"] == "mock_fallback"



def test_openai_decision_provider_parses_planning_response() -> None:
    def transport(method: str, url: str, headers: dict[str, str], body: bytes, timeout_s: float):
        response_body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "selected_capability": "return_home",
                                    "selected_action": "move_home",
                                    "selected_action_args": {},
                                    "reason": "检测到风险标记，优先回零。",
                                },
                                ensure_ascii=False,
                            )
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 8},
            },
            ensure_ascii=False,
        ).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response_body

    provider = OpenAICompatibleDecisionProvider(
        DecisionProviderSettings(
            provider="openai",
            model="gpt-4o-mini",
            api_key="secret",
            local_path="",
        ),
        endpoint="https://api.openai.com/v1/chat/completions",
        mode="remote",
        transport=transport,
    )

    result = provider.plan(
        instruction="抓取桌面方块",
        current_task="抓取桌面方块",
        scene_description="检测到风险",
        scene_observations={"risk_flags": ["unsafe_workspace"]},
    )

    assert result["selected_capability"] == "return_home"
    assert result["selected_action"] == "move_home"
    assert result["provider_metadata"]["mode"] == "remote"



def test_action_decider_falls_back_to_heuristic_when_decision_provider_is_unconfigured(app_config) -> None:
    deps = NodeDependencies(config=app_config, mcp_client=MinimalMCPClient())

    state = {
        "user_instruction": "抓取桌面方块",
        "task_queue": ["抓取桌面方块"],
        "current_task": "抓取桌面方块",
        "current_image": "mock_base64_image",
        "robot_state": {"joint_positions": [], "ee_pose": {}},
        "scene_description": "桌面中央有一个方块",
        "scene_observations": {"robot_grasp_state": "open", "risk_flags": []},
        "action_result": "in_progress",
        "iteration_count": 0,
        "conversation_history": [],
    }

    final_state = action_decider_node(state, deps)

    assert final_state["selected_capability"] == "pick_and_place"
    assert final_state["selected_action"] == "run_smolvla"
    assert final_state["current_plan_step"]["provider_metadata"]["fallback_used"] is True



def test_action_decider_uses_decision_provider_when_configured(app_config) -> None:
    app_config.decision.llm_provider = "openai"
    app_config.decision.llm_api_key = "decision-secret"

    class _StubProvider(OpenAICompatibleDecisionProvider):
        def __init__(self) -> None:
            pass

        def summary(self) -> dict[str, object]:
            return {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "mode": "remote",
                "configured": True,
                "status": "configured",
            }

        def plan(self, *, instruction: str, current_task: str, scene_description: str, scene_observations: dict[str, object]) -> dict[str, object]:
            return {
                "selected_capability": "return_home",
                "selected_action": "move_home",
                "selected_action_args": {},
                "reason": "LLM 判断当前风险较高。",
                "provider_metadata": self.summary(),
            }

    import embodied_agent.decision.graph as decision_graph_module
    import embodied_agent.decision.nodes as decision_nodes_module

    original_graph_builder = decision_graph_module.build_decision_provider
    original_node_builder = decision_nodes_module.build_decision_provider
    decision_graph_module.build_decision_provider = lambda config: _StubProvider()
    decision_nodes_module.build_decision_provider = lambda config: _StubProvider()
    try:
        deps = NodeDependencies(config=app_config, mcp_client=MinimalMCPClient())
        state = {
            "user_instruction": "抓取桌面方块",
            "task_queue": ["抓取桌面方块"],
            "current_task": "抓取桌面方块",
            "current_image": "mock_base64_image",
            "robot_state": {"joint_positions": [], "ee_pose": {}},
            "scene_description": "检测到风险",
            "scene_observations": {"robot_grasp_state": "open", "risk_flags": ["unsafe_workspace"]},
            "action_result": "in_progress",
            "iteration_count": 0,
            "conversation_history": [],
        }

        final_state = action_decider_node(state, deps)
    finally:
        decision_graph_module.build_decision_provider = original_graph_builder
        decision_nodes_module.build_decision_provider = original_node_builder

    assert final_state["selected_capability"] == "return_home"
    assert final_state["selected_action"] == "move_home"
    assert final_state["current_plan_step"]["provider_metadata"]["fallback_used"] is False
