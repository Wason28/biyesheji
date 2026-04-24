from pathlib import Path

import pytest

from embodied_agent.app import (
    build_frontend_bootstrap,
    build_frontend_config_payload,
    build_frontend_facade,
    build_frontend_run_api,
    build_frontend_run_error,
    build_frontend_run_snapshot,
    build_frontend_runtime_api,
    build_runtime,
    build_runtime_from_config,
)
from embodied_agent.decision.graph import DecisionEngine
from embodied_agent.execution.server import MockMCPServer
from embodied_agent.perception.server import PerceptionMCPServer
from embodied_agent.shared.types import FrontendBootstrapPayload, FrontendRunAPI, FrontendRunSnapshot, FrontendRuntimeAPI


def test_unified_startup_builds_mock_runtime_and_runs_single_task(app_config) -> None:
    runtime = build_runtime(app_config)

    assert isinstance(runtime.decision, DecisionEngine)
    assert isinstance(runtime.perception, PerceptionMCPServer)
    assert isinstance(runtime.execution, MockMCPServer)

    final_state = runtime.decision.invoke("抓取桌面方块")

    assert final_state["action_result"] == "success"
    assert final_state["current_phase"] == "final_status"
    assert final_state["termination_reason"] == "all_tasks_completed"
    assert final_state["final_report"]["completed"] is True
    assert final_state["selected_capability"] == "pick_and_place"
    assert final_state["selected_action"] == "run_smolvla"
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert "get_image" in tool_names
    assert "get_robot_state" in tool_names
    assert "describe_scene" in tool_names
    assert tool_names.count("run_smolvla") == 1

    tool_list = {tool["name"] if isinstance(tool, dict) else tool.name for tool in runtime.execution.list_tools()}
    assert any(tool.name == "describe_scene" for tool in runtime.perception.list_tools())
    assert {"move_to", "move_home", "grasp", "release", "run_smolvla"}.issubset(tool_list)


def test_unified_startup_runs_multiple_tasks_through_single_runtime(app_config) -> None:
    runtime = build_runtime(app_config)

    final_state = runtime.decision.invoke("抓取桌面方块，然后回到安全位置")

    assert final_state["action_result"] == "success"
    assert final_state["current_phase"] == "final_status"
    assert final_state["iteration_count"] == 2
    assert final_state["task_queue"] == []
    assert final_state["current_task"] == ""
    assert final_state["termination_reason"] == "all_tasks_completed"
    assert final_state["selected_capability"] == "return_home"
    assert final_state["selected_action"] == "move_home"
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert tool_names.count("run_smolvla") == 1
    assert tool_names.count("move_home") == 1


def test_unified_startup_builds_runtime_from_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "app-config.yaml"
    config_path.write_text(
        """
decision:
  llm_provider: openai
  llm_model: gpt-4o-mini
  llm_api_key: ""
  llm_local_path: ./models/llm
  max_iterations: 3
perception:
  vlm_provider: openai_gpt4o
  vlm_model: gpt-4o
  vlm_api_key: ""
  vlm_local_path: ./models/vlm
  vlm_base_url: http://localhost:11434
  camera_backend: mock
  camera_device_id: wrist_cam
  camera_frame_id: wrist_camera
  camera_width: 800
  camera_height: 600
  robot_state_backend: mock
  robot_state_base_frame: tool0
execution:
  vla_model_path: ./models/mock
  robot_config: ./configs/mock.yaml
  robot_adapter: mock_lerobot
  smolvla_backend: mock_smolvla
  safety_policy: fail_closed
  stop_mode: estop_latched
  workspace_limits:
    x: [-0.1, 0.1]
    y: [-0.2, 0.2]
    z: [0.05, 0.4]
  home_pose:
    x: 0.1
    y: 0.0
    z: 0.3
frontend:
  port: 9000
  max_iterations: 7
  speed_scale: 0.5
""".strip(),
        encoding="utf-8",
    )

    runtime = build_runtime_from_config(config_path)

    assert runtime.config.decision.llm_provider == "openai"
    assert runtime.config.decision.llm_model == "gpt-4o-mini"
    assert runtime.config.decision.llm_local_path == "./models/llm"
    assert runtime.config.perception.vlm_provider == "openai_gpt4o"
    assert runtime.config.perception.vlm_model == "gpt-4o"
    assert runtime.config.perception.vlm_local_path == "./models/vlm"
    assert runtime.config.frontend.port == 9000
    assert runtime.config.frontend.max_iterations == 7
    assert runtime.config.frontend.speed_scale == 0.5
    assert runtime.decision.deps.max_iterations == 3
    assert runtime.execution._runtime.config.vla_model_path == "./models/mock"
    assert runtime.execution._runtime.config.robot_config == "./configs/mock.yaml"
    assert runtime.execution._runtime.config.robot_adapter == "mock_lerobot"
    assert runtime.execution._runtime.config.smolvla_backend == "mock_smolvla"
    assert runtime.execution._runtime.config.safety_policy == "fail_closed"
    assert runtime.execution._runtime.config.stop_mode == "estop_latched"
    assert runtime.execution._runtime.config.workspace_limits == {
        "x": (-0.1, 0.1),
        "y": (-0.2, 0.2),
        "z": (0.05, 0.4),
    }
    assert runtime.execution._runtime.config.home_pose == {"x": 0.1, "y": 0.0, "z": 0.3}
    assert runtime.perception.perception_config.vlm_provider == "openai_gpt4o"
    assert runtime.perception.perception_config.vlm_model == "gpt-4o"
    assert runtime.perception.perception_config.vlm_local_path == "./models/vlm"
    assert runtime.perception.perception_config.camera_device_id == "wrist_cam"
    assert runtime.perception.perception_config.camera_frame_id == "wrist_camera"
    assert runtime.perception.perception_config.robot_state_base_frame == "tool0"


def test_unified_startup_uses_frontend_max_iterations_when_decision_limit_is_non_positive(tmp_path: Path) -> None:
    config_path = tmp_path / "fallback-config.yaml"
    config_path.write_text(
        """
decision:
  llm_provider: minimax
  llm_model: MiniMax-M2.1
  llm_api_key: ""
  max_iterations: 0
perception:
  vlm_provider: minimax_mcp_vision
  vlm_model: minimax-mcp-vision-latest
  vlm_api_key: ""
execution:
  vla_model_path: ./models/mock
  robot_config: ./configs/mock.yaml
  robot_adapter: mock_lerobot
  smolvla_backend: mock_smolvla
  safety_policy: fail_closed
  stop_mode: estop_latched
frontend:
  port: 7860
  max_iterations: 6
  speed_scale: 1.0
""".strip(),
        encoding="utf-8",
    )

    runtime = build_runtime_from_config(config_path)

    assert runtime.config.decision.max_iterations == 0
    assert runtime.config.frontend.max_iterations == 6
    assert runtime.decision.deps.max_iterations == 6


def test_unified_runtime_returns_stable_unknown_tool_envelope(app_config) -> None:
    runtime = build_runtime(app_config)

    response = runtime.mcp_client.call_tool("unknown_tool", {"foo": "bar"})

    assert response == {
        "ok": False,
        "status_code": 404,
        "tool_name": "unknown_tool",
        "content": None,
        "message": "tool 'unknown_tool' is not registered",
        "metadata": {"arguments": {"foo": "bar"}},
    }


def test_unified_mcp_client_exposes_execution_atomic_tools(app_config) -> None:
    runtime = build_runtime(app_config)

    move_home_response = runtime.mcp_client.call_tool("move_home")

    assert move_home_response["ok"] is True
    assert move_home_response["tool_name"] == "move_home"
    assert move_home_response["content"]["status"] == "success"
    assert move_home_response["content"]["action_name"] == "move_home"


def test_unified_runtime_surfaces_execution_failures_with_stable_envelope(app_config) -> None:
    runtime = build_runtime(app_config)

    failed_response = runtime.mcp_client.call_tool(
        "move_to",
        {
            "x": 99.0,
            "y": 0.0,
            "z": 0.2,
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        },
    )

    assert failed_response["ok"] is False
    assert failed_response["status_code"] == 500
    assert failed_response["tool_name"] == "move_to"
    assert failed_response["content"]["status"] == "failed"
    assert failed_response["metadata"]["error_code"] == "ValidationError"


class _FailingPerceptionServer(PerceptionMCPServer):
    def call_tool(self, tool_name: str, arguments: dict[str, object] | None = None) -> dict[str, object]:
        if tool_name == "get_image":
            return {
                "ok": False,
                "status_code": 500,
                "tool_name": tool_name,
                "content": None,
                "message": "摄像头未连接或初始化失败",
                "metadata": {
                    "error_code": "PERCEPTION_CAMERA_DISCONNECTED",
                    "retriable": True,
                },
            }
        return super().call_tool(tool_name, arguments)


def test_unified_runtime_fails_closed_loop_when_perception_fails(app_config) -> None:
    failing_perception = _FailingPerceptionServer(app_config)
    execution = MockMCPServer()
    runtime = build_runtime(app_config)
    runtime = runtime.__class__(
        config=runtime.config,
        perception=failing_perception,
        execution=execution,
        decision=DecisionEngine.from_config(app_config, mcp_client=runtime.mcp_client.__class__(failing_perception, execution)),
        mcp_client=runtime.mcp_client.__class__(failing_perception, execution),
    )

    final_state = runtime.decision.invoke("抓取桌面方块")

    assert final_state["action_result"] == "failed"
    assert final_state["current_phase"] == "final_status"
    assert final_state["termination_reason"] == "compensation_exhausted"
    assert final_state["last_node_result"]["node"] == "final_status"
    assert final_state["error_diagnosis"]["reason"] == "current_image 不能为空。"
    assert final_state["last_node_result"]["message"]
    assert "active_perception" in final_state["final_report"]["observed_phases"]
    tool_names = [call["tool_name"] for call in final_state["debug_metrics"]["tool_calls"]]
    assert tool_names.count("get_image") >= 1


class _FailingExecutionServer(MockMCPServer):
    def call_tool(self, tool_name: str, arguments: dict[str, object] | None = None) -> dict[str, object]:
        if tool_name == "run_smolvla":
            return {
                "ok": False,
                "status_code": 503,
                "tool_name": tool_name,
                "content": {
                    "status": "failed",
                    "action_name": tool_name,
                    "message": "执行服务暂时不可用",
                    "logs": ["executor unavailable"],
                },
                "message": "执行服务暂时不可用",
                "metadata": {
                    "error_code": "ExecutionUnavailable",
                    "retryable": True,
                },
            }
        return super().call_tool(tool_name, arguments)


def test_unified_runtime_propagates_execution_failure_through_closed_loop(app_config) -> None:
    perception = PerceptionMCPServer(app_config)
    execution = _FailingExecutionServer()
    runtime = build_runtime(app_config)
    runtime = runtime.__class__(
        config=runtime.config,
        perception=perception,
        execution=execution,
        decision=DecisionEngine.from_config(app_config, mcp_client=runtime.mcp_client.__class__(perception, execution)),
        mcp_client=runtime.mcp_client.__class__(perception, execution),
    )

    final_state = runtime.decision.invoke("抓取桌面方块")

    assert final_state["action_result"] == "failed"
    assert final_state["current_phase"] == "final_status"
    assert final_state["termination_reason"] == "compensation_exhausted"
    assert final_state["last_execution"] == {
        "status": "success",
        "action_name": "move_home",
        "message": "机器人已回到安全 home 位姿。",
        "logs": [
            "move_home: 开始执行 mock 工具。",
            "已同步机器人状态。",
            "已通过预定义安全路径回零。",
        ],
    }
    assert final_state["error_diagnosis"]["reason"] == "执行服务暂时不可用"
    assert final_state["last_node_result"]["node"] == "final_status"
    assert final_state["last_node_result"]["status_code"] == 409
    assert final_state["last_node_result"]["message"] == "输出执行报告"
    assert final_state["final_report"]["completed"] is False
    assert any(
        call["tool_name"] == "run_smolvla" and call["ok"] is False and call["metadata"]["error_code"] == "ExecutionUnavailable"
        for call in final_state["debug_metrics"]["tool_calls"]
    )


def test_frontend_run_snapshot_normalizes_completed_state_for_ui(app_config) -> None:
    runtime = build_runtime(app_config)
    final_state = runtime.decision.invoke("抓取桌面方块")

    snapshot: FrontendRunSnapshot = build_frontend_run_snapshot(final_state, run_id="run-001")

    assert snapshot["run_id"] == "run-001"
    assert snapshot["status"] == "completed"
    assert snapshot["current_phase"] == "final_status"
    assert snapshot["current_node"] == "final_status"
    assert snapshot["current_task"] == ""
    assert snapshot["selected_capability"] == "pick_and_place"
    assert snapshot["selected_action"] == "run_smolvla"
    assert snapshot["action_result"] == "success"
    assert snapshot["iteration_count"] == 1
    assert snapshot["max_iterations"] == runtime.decision.deps.max_iterations
    assert snapshot["termination_reason"] == "all_tasks_completed"
    assert snapshot["final_report"]["completed"] is True
    assert snapshot["scene_description"]
    assert isinstance(snapshot["scene_observations"], dict)
    assert snapshot["robot_state"]["joint_positions"]
    assert snapshot["last_node_result"]["node"] == "final_status"
    assert snapshot["last_execution"]["action_name"] == "run_smolvla"
    assert snapshot["logs"]
    assert snapshot["error"] == ""



def test_frontend_run_snapshot_surfaces_failure_message(app_config) -> None:
    perception = PerceptionMCPServer(app_config)
    execution = _FailingExecutionServer()
    runtime = build_runtime(app_config)
    runtime = runtime.__class__(
        config=runtime.config,
        perception=perception,
        execution=execution,
        decision=DecisionEngine.from_config(app_config, mcp_client=runtime.mcp_client.__class__(perception, execution)),
        mcp_client=runtime.mcp_client.__class__(perception, execution),
    )

    final_state = runtime.decision.invoke("抓取桌面方块")
    snapshot: FrontendRunSnapshot = build_frontend_run_snapshot(final_state, run_id="run-failed")

    assert snapshot["status"] == "failed"
    assert snapshot["current_phase"] == "final_status"
    assert snapshot["current_node"] == "final_status"
    assert snapshot["termination_reason"] == "compensation_exhausted"
    assert snapshot["final_report"]["completed"] is False
    assert snapshot["error"] == "执行服务暂时不可用"


def test_frontend_bootstrap_and_config_payloads_expose_phase2_placeholders(app_config) -> None:
    runtime = build_runtime(app_config)

    config_payload = build_frontend_config_payload(runtime)
    bootstrap: FrontendBootstrapPayload = build_frontend_bootstrap(runtime)
    runtime_api: FrontendRuntimeAPI = build_frontend_runtime_api(runtime)

    assert config_payload["decision"]["provider"] == app_config.decision.llm_provider
    assert config_payload["decision"]["api_key"] == ""
    assert config_payload["decision"]["api_key_configured"] is False
    assert config_payload["perception"]["provider_options"] == ["minimax_mcp_vision", "openai_gpt4o", "ollama_vision"]
    assert config_payload["execution"]["display_name"] == "SmolVLA"
    assert config_payload["execution"]["adapter"] == "mock_lerobot"
    assert config_payload["execution"]["backend"] == "mock_smolvla"
    assert config_payload["execution"]["safety_policy"] == "fail_closed"
    assert config_payload["execution"]["stop_mode"] == "estop_latched"
    assert config_payload["execution"]["mutable"] is False
    assert config_payload["frontend"]["max_iterations"] == runtime.decision.deps.max_iterations

    assert bootstrap["config"] == config_payload
    assert bootstrap["execution_model"]["name"] == "SmolVLA"
    assert bootstrap["execution_model"]["adapter"] == "mock_lerobot"
    assert bootstrap["execution_model"]["backend"] == "mock_smolvla"
    assert bootstrap["execution_model"]["capability_names"] == ["pick_and_place"]
    assert len(bootstrap["tools"]) == 8
    assert {tool["layer"] for tool in bootstrap["tools"]} == {"perception", "execution"}
    assert any(tool["name"] == "run_smolvla" and tool["capability_names"] == ["pick_and_place"] for tool in bootstrap["tools"])
    assert bootstrap["execution_capabilities"]
    assert any(capability["capability_name"] == "pick_and_place" for capability in bootstrap["execution_capabilities"])
    assert bootstrap["execution_safety"]["adapter_name"] == "mock_lerobot"
    assert bootstrap["execution_safety"]["manual_reset_required"] is True
    assert "current_phase" in bootstrap["status_fields"]
    assert "current_node" in bootstrap["status_fields"]
    assert "selected_action" in bootstrap["status_fields"]
    assert "termination_reason" in bootstrap["status_fields"]
    assert "final_report" in bootstrap["status_fields"]
    assert runtime_api["bootstrap"] == bootstrap
    assert runtime_api["config"] == config_payload


def test_frontend_run_api_returns_snapshot(app_config) -> None:
    runtime = build_runtime(app_config)

    run_api: FrontendRunAPI = build_frontend_run_api(runtime, instruction="抓取桌面方块", run_id="run-api")
    snapshot = run_api["run"]

    assert snapshot["run_id"] == "run-api"
    assert snapshot["status"] == "completed"
    assert snapshot["current_phase"] == "final_status"
    assert snapshot["selected_capability"] == "pick_and_place"
    assert snapshot["selected_action"] == "run_smolvla"


def test_frontend_run_error_returns_minimal_error_payload() -> None:
    error_payload = build_frontend_run_error(code="RunUnavailable", message="运行服务暂时不可用")

    assert error_payload == {
        "error": {
            "code": "RunUnavailable",
            "message": "运行服务暂时不可用",
        }
    }



def test_frontend_runtime_facade_wraps_placeholder_endpoints(app_config) -> None:
    runtime = build_runtime(app_config)
    facade = build_frontend_facade(runtime)

    runtime_api = facade.get_runtime_api()
    run_api = facade.run_instruction(instruction="抓取桌面方块", run_id="facade-run")
    error_payload = facade.build_error(code="FacadeUnavailable", message="facade 暂不可用")

    assert runtime_api["bootstrap"]["config"] == runtime_api["config"]
    assert run_api["run"]["run_id"] == "facade-run"
    assert run_api["run"]["status"] == "completed"
    assert run_api["run"]["current_phase"] == "final_status"
    assert error_payload == {
        "error": {
            "code": "FacadeUnavailable",
            "message": "facade 暂不可用",
        }
    }
