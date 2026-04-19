from embodied_agent.decision.graph import DecisionEngine
from embodied_agent.decision.mcp_client import MinimalMCPClient


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
    assert tool_names.count("run_smolvla") == 2
