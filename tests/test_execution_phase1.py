from embodied_agent.execution.server import MockMCPServer
from embodied_agent.execution.tools import ExecutionRuntime


def test_execution_server_run_smolvla_success(app_config, valid_robot_state) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    response = server.call_tool(
        "run_smolvla",
        {
            "task_description": "抓取桌面方块",
            "current_image": "mock_base64_image",
            "robot_state": valid_robot_state,
        },
    )

    assert response["status"] == "success"
    assert response["action_name"] == "run_smolvla"
    assert response["executed_plan"]
    assert any(step["tool"] == "move_home" for step in response["executed_plan"])


def test_execution_server_move_to_validation_failure_triggers_estop(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    response = server.call_tool(
        "move_to",
        {
            "x": 9.0,
            "y": 0.0,
            "z": 0.2,
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        },
    )

    assert response["status"] == "failed"
    assert response["error_code"] == "ValidationError"
    assert "超出安全范围" in response["message"]
    assert "estop_reason" in response["robot_state"]["ee_pose"]
