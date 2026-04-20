from embodied_agent.decision.graph import DecisionEngine
from embodied_agent.decision.mcp_client import MinimalMCPClient
from embodied_agent.decision.nodes import NodeDependencies, action_decider_node


def _build_engine(app_config):
    return DecisionEngine.from_config(app_config, mcp_client=MinimalMCPClient())


def _history_messages(state: dict, node: str) -> list[str]:
    return [
        item["message"]
        for item in state["conversation_history"]
        if item.get("node") == node
    ]


def test_decision_engine_single_task_reaches_normal_end(app_config) -> None:
    engine = _build_engine(app_config)

    final_state = engine.invoke("抓取桌面方块")

    assert final_state["action_result"] == "success"
    assert final_state["iteration_count"] == 1
    assert final_state["task_queue"] == []
    assert final_state["current_task"] == ""
    assert final_state["selected_capability"] == "pick_and_place"
    assert final_state["selected_action"] == "run_smolvla"
    assert final_state["last_node_result"]["node"] == "verifier"
    assert final_state["last_node_result"]["message"] == "全部任务完成"
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert tool_names.count("run_smolvla") == 1


def test_decision_engine_continues_loop_for_remaining_tasks(app_config) -> None:
    engine = _build_engine(app_config)

    final_state = engine.invoke("抓取桌面方块，然后回到安全位置")

    assert final_state["action_result"] == "success"
    assert final_state["iteration_count"] == 2
    assert final_state["task_queue"] == []
    assert final_state["current_task"] == ""
    assert "当前任务完成，继续处理后续任务" in _history_messages(final_state, "verifier")
    executor_messages = _history_messages(final_state, "executor")
    assert len(executor_messages) == 2
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert tool_names.count("run_smolvla") == 1
    assert tool_names.count("move_home") == 1


def test_decision_engine_selects_release_action_for_release_task(app_config) -> None:
    engine = _build_engine(app_config)

    final_state = engine.invoke("释放夹爪")

    assert final_state["action_result"] == "success"
    assert final_state["selected_capability"] == "release_object"
    assert final_state["selected_action"] == "release"
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert tool_names.count("release") == 1


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


def test_decision_engine_selects_return_home_when_scene_has_risk_flags(app_config) -> None:
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

    assert final_state["selected_capability"] == "return_home"
    assert final_state["selected_action"] == "move_home"
