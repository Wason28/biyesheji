from embodied_agent.execution.config import ExecutionSafetyConfig
from embodied_agent.execution.robot_adapter import MockLeRobotAdapter, build_robot_adapter, register_robot_adapter
from embodied_agent.execution.server import MockMCPServer
from embodied_agent.execution.smolvla import MockSmolVLAAdapter, build_smolvla_backend, register_smolvla_backend
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

    assert response["ok"] is True
    assert response["tool_name"] == "run_smolvla"
    assert response["content"]["status"] == "success"
    assert response["content"]["action_name"] == "run_smolvla"
    assert response["content"]["capability_name"] == "pick_and_place"
    assert response["content"]["action_contract"]["tool_name"] == "run_smolvla"
    assert response["content"]["action_contract"]["estop_on_failure"] is True
    assert response["content"]["action_contract"]["safety_stages"] == [
        "input_validation",
        "preflight",
        "adapter_dispatch",
        "telemetry_check",
    ]
    assert response["content"]["capability_contract"]["default_action"] == "run_smolvla"
    assert response["content"]["capability_contract"]["execution_mode"] == "vla"
    assert response["content"]["capability_contract"]["fixed_model"] is True
    assert response["content"]["safety_boundary"]["adapter_name"] == "mock_lerobot"
    assert response["content"]["safety_boundary"]["smolvla_backend"] == "mock_smolvla"
    assert "input_validation" in response["content"]["safety_boundary"]["checked_stages"]
    assert response["content"]["executed_plan"]
    assert any(step["tool"] == "move_home" for step in response["content"]["executed_plan"])


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

    assert response["ok"] is False
    assert response["tool_name"] == "move_to"
    assert response["content"]["status"] == "failed"
    assert response["metadata"]["error_code"] == "ValidationError"
    assert response["metadata"]["safety_boundary"]["estop_engaged"] is True
    assert response["metadata"]["safety_boundary"]["manual_reset_required"] is True
    assert response["metadata"]["safety_boundary"]["action_timeout_s"] == server.describe()["safety_boundary"]["action_timeout_s"]
    assert "emergency_stop" in response["metadata"]["safety_boundary"]["checked_stages"]
    assert "超出安全范围" in response["message"]
    assert "estop_reason" in response["content"]["robot_state"]["ee_pose"]


def test_execution_server_unknown_tool_returns_unified_error_envelope(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    response = server.call_tool("unknown_tool")

    assert response["ok"] is False
    assert response["status_code"] == 404
    assert response["tool_name"] == "unknown_tool"
    assert response["content"] is None
    assert response["metadata"]["error_code"] == "UnknownTool"


def test_execution_server_invalid_request_returns_unified_error_envelope(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    response = server.handle_request({})

    assert response["ok"] is False
    assert response["status_code"] == 400
    assert response["tool_name"] == "server"
    assert response["content"] is None
    assert response["metadata"]["error_code"] == "InvalidRequest"


def test_execution_server_describe_exposes_capabilities_and_safety_boundary(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    description = server.describe()

    assert any(capability["capability_name"] == "pick_and_place" for capability in description["capabilities"])
    assert description["execution_model"]["name"] == "SmolVLA"
    assert description["execution_model"]["backend"] == "mock_smolvla"
    assert description["runtime_profile"]["adapter"]["name"] == "mock_lerobot"
    assert description["runtime_profile"]["smolvla_backend"]["fixed_model"] is True
    assert description["safety_boundary"]["adapter_name"] == "mock_lerobot"
    assert description["safety_boundary"]["smolvla_backend"] == "mock_smolvla"
    move_to = next(tool for tool in description["tools"] if tool["name"] == "move_to")
    assert move_to["capability_names"] == ["pick_and_place"]
    assert move_to["input_schema"]["required"] == ["x", "y", "z"]


def test_execution_server_invalid_arguments_return_unified_error_envelope(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    response = server.call_tool("move_to", {"x": 0.1, "y": 0.0, "z": 0.2, "foo": "bar"})

    assert response["ok"] is False
    assert response["status_code"] == 400
    assert response["metadata"]["error_code"] == "ToolArgumentError"
    assert response["metadata"]["arguments"]["foo"] == "bar"


class _TrackingAdapter(MockLeRobotAdapter):
    @property
    def adapter_name(self) -> str:
        return "tracking_adapter"


class _TrackingSmolVLA(MockSmolVLAAdapter):
    @property
    def backend_name(self) -> str:
        return "tracking_smolvla"


def test_execution_runtime_create_supports_factory_injection(app_config) -> None:
    runtime = ExecutionRuntime.create(
        app_config,
        adapter_factory=_TrackingAdapter,
        smolvla_factory=_TrackingSmolVLA,
    )

    assert isinstance(runtime.adapter, _TrackingAdapter)
    assert isinstance(runtime.smolvla, _TrackingSmolVLA)
    assert isinstance(runtime.config, ExecutionSafetyConfig)
    assert runtime.describe_safety_boundary()["adapter_name"] == "tracking_adapter"
    assert runtime.describe_safety_boundary()["smolvla_backend"] == "tracking_smolvla"


def test_execution_runtime_supports_registered_adapter_and_backend_factories(app_config) -> None:
    register_robot_adapter("tracking_adapter", _TrackingAdapter)
    register_smolvla_backend("tracking_smolvla", _TrackingSmolVLA)
    app_config.execution.robot_adapter = "tracking_adapter"
    app_config.execution.smolvla_backend = "tracking_smolvla"

    runtime = ExecutionRuntime.create(app_config)

    assert isinstance(runtime.adapter, _TrackingAdapter)
    assert isinstance(runtime.smolvla, _TrackingSmolVLA)
    assert isinstance(build_robot_adapter(runtime.config), _TrackingAdapter)
    assert isinstance(build_smolvla_backend(runtime.config), _TrackingSmolVLA)


def test_execution_atomic_tools_accept_phase2_optional_arguments(app_config) -> None:
    runtime = ExecutionRuntime.create(app_config)

    move_result = runtime.move_to(0.1, 0.0, 0.2)
    grasp_result = runtime.grasp()

    assert move_result["status"] == "success"
    assert move_result["validated_params"]["orientation"] == runtime.config.default_orientation
    assert grasp_result["status"] == "success"
    assert grasp_result["validated_params"]["force"] >= runtime.config.min_force
