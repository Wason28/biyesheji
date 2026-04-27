import json

from embodied_agent.execution.config import ExecutionSafetyConfig
from embodied_agent.execution.robot_adapter import (
    AdapterError,
    BridgeRobotAdapter,
    LeRobotLocalAdapter,
    MockLeRobotAdapter,
    build_robot_adapter,
    register_robot_adapter,
)
from embodied_agent.execution.server import MockMCPServer
from embodied_agent.execution.safety import SafetyManager
from embodied_agent.execution.smolvla import (
    BaseSmolVLAAdapter,
    MockSmolVLAAdapter,
    build_smolvla_backend,
    register_smolvla_backend,
)
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


def test_execution_server_clear_emergency_stop_recovers_from_latched_estop(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    failed = server.call_tool("servo_rotate", {"id": 0, "degrees": 15.0})
    assert failed["ok"] is False
    assert failed["metadata"]["safety_boundary"]["estop_engaged"] is True

    cleared = server.call_tool("clear_emergency_stop", {})
    assert cleared["ok"] is True
    assert cleared["tool_name"] == "clear_emergency_stop"
    assert cleared["content"]["status"] == "success"
    assert cleared["content"]["action_contract"]["tool_name"] == "clear_emergency_stop"
    assert cleared["content"]["safety_boundary"]["estop_engaged"] is False


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
    assert any(tool["name"] == "clear_emergency_stop" for tool in description["tools"])
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


class _LowLevelTrackingAdapter(MockLeRobotAdapter):
    @property
    def adapter_name(self) -> str:
        return "low_level_tracking_adapter"

    @property
    def supports_joint_action_dispatch(self) -> bool:
        return True

    def get_action_feature_order(self) -> list[str]:
        return [
            "joint_1.pos",
            "joint_2.pos",
            "joint_3.pos",
            "joint_4.pos",
            "joint_5.pos",
            "joint_6.pos",
        ]


class _LowLevelTrackingSmolVLA(BaseSmolVLAAdapter):
    @property
    def backend_name(self) -> str:
        return "low_level_tracking_smolvla"

    @property
    def supports_joint_actions(self) -> bool:
        return True

    def plan(self, task_description: str, current_image: str, robot_state):  # pragma: no cover - low-level path only
        raise AssertionError("plan should not be called for low-level backend")

    def infer_joint_actions(
        self,
        task_description: str,
        current_image: str,
        robot_state,
        action_feature_names: list[str],
    ) -> list[dict[str, float]]:
        assert task_description == "抓取红色圆环"
        assert current_image == "mock_base64_image"
        assert action_feature_names[0] == "joint_1.pos"
        return [
            {
                "joint_1.pos": 0.1,
                "joint_2.pos": -0.2,
                "joint_3.pos": 0.3,
                "joint_4.pos": 0.4,
                "joint_5.pos": 0.5,
                "joint_6.pos": 0.6,
            },
            {
                "joint_1.pos": 0.2,
                "joint_2.pos": -0.1,
                "joint_3.pos": 0.35,
                "joint_4.pos": 0.45,
                "joint_5.pos": 0.55,
                "joint_6.pos": 0.65,
            },
        ]


def test_execution_server_run_smolvla_low_level_backend_executes_joint_actions(
    app_config,
    valid_robot_state,
) -> None:
    server = MockMCPServer(
        ExecutionRuntime.create(
            app_config,
            adapter_factory=_LowLevelTrackingAdapter,
            smolvla_factory=_LowLevelTrackingSmolVLA,
        )
    )

    response = server.call_tool(
        "run_smolvla",
        {
            "task_description": "抓取红色圆环",
            "current_image": "mock_base64_image",
            "robot_state": valid_robot_state,
        },
    )

    assert response["ok"] is True
    assert response["content"]["status"] == "success"
    assert response["content"]["executed_plan"] == []
    assert len(response["content"]["model_actions"]) == 2
    assert response["content"]["model_actions"][0]["targets"]["joint_1.pos"] == 0.1
    assert response["content"]["robot_state"]["joint_positions"][:3] == [0.2, -0.1, 0.35]
    assert response["content"]["safety_boundary"]["smolvla_backend"] == "low_level_tracking_smolvla"


def test_execution_runtime_run_smolvla_low_level_backend_rejects_adapter_without_joint_dispatch(
    app_config,
    valid_robot_state,
) -> None:
    class _NoJointDispatchAdapter(MockLeRobotAdapter):
        @property
        def adapter_name(self) -> str:
            return "no_joint_dispatch_adapter"

        @property
        def supports_joint_action_dispatch(self) -> bool:
            return False

    runtime = ExecutionRuntime.create(
        app_config,
        adapter_factory=_NoJointDispatchAdapter,
        smolvla_factory=_LowLevelTrackingSmolVLA,
    )

    result = runtime.run_smolvla("抓取红色圆环", "mock_base64_image", valid_robot_state)

    assert result["status"] == "failed"
    assert result["error_code"] == "AdapterError"
    assert "不支持 SmolVLA 低层 joint action 执行" in result["message"]


def test_execution_atomic_tools_accept_phase2_optional_arguments(app_config) -> None:
    runtime = ExecutionRuntime.create(app_config)

    move_result = runtime.move_to(0.1, 0.0, 0.2)
    grasp_result = runtime.grasp()

    assert move_result["status"] == "success"
    assert move_result["validated_params"]["orientation"] == runtime.config.default_orientation
    assert grasp_result["status"] == "success"
    assert grasp_result["validated_params"]["force"] >= runtime.config.min_force


def test_execution_server_servo_rotate_success(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    response = server.call_tool("servo_rotate", {"id": 2, "degrees": 15.0})

    assert response["ok"] is True
    assert response["tool_name"] == "servo_rotate"
    assert response["content"]["status"] == "success"
    assert response["content"]["capability_name"] == "servo_control"
    assert response["content"]["validated_params"]["id"] == 2
    assert response["content"]["validated_params"]["joint_index"] == 1
    assert response["content"]["validated_params"]["degrees"] == 15.0
    assert response["content"]["action_contract"]["tool_name"] == "servo_rotate"
    assert response["content"]["action_contract"]["capability_names"] == ["servo_control"]


def test_execution_server_servo_rotate_validation_failure_triggers_estop(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    response = server.call_tool("servo_rotate", {"id": 0, "degrees": 15.0})

    assert response["ok"] is False
    assert response["tool_name"] == "servo_rotate"
    assert response["content"]["status"] == "failed"
    assert response["metadata"]["error_code"] == "ValidationError"
    assert response["metadata"]["safety_boundary"]["estop_engaged"] is True
    assert "超出舵机范围" in response["message"]


def test_execution_runtime_servo_rotate_safety_rejects_oversized_rotation(app_config) -> None:
    runtime = ExecutionRuntime.create(app_config)

    result = runtime.servo_rotate(1, 120.0)

    assert result["status"] == "failed"
    assert result["error_code"] == "SafetyError"
    assert result["safety_boundary"]["estop_engaged"] is True
    assert "超过阈值" in result["message"]


def test_execution_server_describe_includes_servo_rotate_contract(app_config) -> None:
    server = MockMCPServer(ExecutionRuntime.create(app_config))

    description = server.describe()

    servo_rotate = next(tool for tool in description["tools"] if tool["name"] == "servo_rotate")
    assert servo_rotate["capability_names"] == ["servo_control"]
    assert servo_rotate["input_schema"]["required"] == ["id", "degrees"]
    assert any(capability["capability_name"] == "servo_control" for capability in description["capabilities"])


class _HeartbeatBrokenAdapter(MockLeRobotAdapter):
    @property
    def adapter_name(self) -> str:
        return "heartbeat_broken"

    def read_telemetry(self) -> dict[str, object]:
        telemetry = dict(super().read_telemetry())
        telemetry["heartbeat_ok"] = False
        telemetry["error_code"] = ""
        return telemetry


def test_execution_runtime_precheck_rejects_broken_heartbeat(app_config) -> None:
    runtime = ExecutionRuntime.create(app_config, adapter_factory=_HeartbeatBrokenAdapter)

    result = runtime.move_home()

    assert result["status"] == "failed"
    assert result["error_code"] == "SafetyError"
    assert "心跳异常" in result["message"]
    assert "preflight" in result["safety_boundary"]["checked_stages"]


def test_bridge_robot_adapter_dispatches_actions_and_reads_telemetry() -> None:
    config = ExecutionSafetyConfig(
        robot_adapter="mcp_bridge",
        robot_base_url="http://127.0.0.1:9901",
    )

    def transport(*, method: str, url: str, headers: dict[str, str], body, timeout_s: float):
        if url.endswith("/state"):
            payload = {
                "ok": True,
                "robot_state": {
                    "joint_positions": [0.0, 0.1, 0.2],
                    "ee_pose": {
                        "position": {"x": 0.1, "y": 0.2, "z": 0.3},
                        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                        "reference_frame": "base_link",
                    },
                },
            }
        elif url.endswith("/telemetry"):
            payload = {
                "ok": True,
                "telemetry": {
                    "temperature_c": 31.0,
                    "motor_current_a": 1.1,
                    "position_error_m": 0.002,
                    "connection_ok": True,
                    "heartbeat_ok": True,
                },
            }
        else:
            payload = {
                "ok": True,
                "robot_state": {
                    "joint_positions": [0.0, 0.1, 0.2],
                    "ee_pose": {
                        "position": {"x": 0.2, "y": 0.1, "z": 0.25},
                        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                        "reference_frame": "base_link",
                    },
                },
            }
        return 200, {"Content-Type": "application/json"}, json.dumps(payload).encode("utf-8")

    adapter = BridgeRobotAdapter(config, transport=transport)

    state = adapter.move_home()
    telemetry = adapter.read_telemetry()

    assert state["ee_pose"]["position"]["x"] == 0.2
    assert telemetry["heartbeat_ok"] is True
    assert adapter.connection_summary()["mode"] == "bridge"


def test_lerobot_local_adapter_supports_joint_fallback_actions() -> None:
    class _FakeController:
        action_features = {
            "joint_1.pos": float,
            "joint_2.pos": float,
            "gripper.pos": float,
        }

        def __init__(self) -> None:
            self.observation = {
                "joint_1.pos": 0.0,
                "joint_2.pos": 0.0,
                "gripper.pos": 0.0,
            }

        def get_observation(self):
            return dict(self.observation)

        def send_action(self, action):
            self.observation.update(action)
            return action

    config = ExecutionSafetyConfig(
        robot_adapter="lerobot_local",
        home_joint_positions=[0.1, -0.1, 0.0],
    )
    adapter = LeRobotLocalAdapter(config, controller_loader=lambda config_path, pythonpath: _FakeController())

    home_state = adapter.move_home()
    rotate_state = adapter.rotate_servo(2, 10.0)
    grasp_state = adapter.close_gripper(20.0)

    assert home_state["joint_positions"][:2] == [0.1, -0.1]
    assert rotate_state["joint_positions"][1] != -0.1
    assert grasp_state["joint_positions"][2] == 20.0


def test_lerobot_local_adapter_preserves_degree_units_for_joint_fallback_actions() -> None:
    class _FakeController:
        action_features = {
            "joint_1.pos": float,
            "joint_2.pos": float,
            "gripper.pos": float,
        }

        def __init__(self) -> None:
            self.observation = {
                "joint_1.pos": 95.0,
                "joint_2.pos": -90.0,
                "gripper.pos": 0.0,
            }

        def get_observation(self):
            return dict(self.observation)

        def send_action(self, action):
            self.observation.update(action)
            return action

    config = ExecutionSafetyConfig(robot_adapter="lerobot_local")
    adapter = LeRobotLocalAdapter(config, controller_loader=lambda config_path, pythonpath: _FakeController())

    rotate_state = adapter.rotate_servo(1, 15.0)

    assert rotate_state["joint_positions"][0] == 110.0


def test_lerobot_local_adapter_preserves_controller_joint_order_for_named_servos() -> None:
    class _FakeController:
        action_features = {
            "shoulder_pan.pos": float,
            "shoulder_lift.pos": float,
            "elbow_flex.pos": float,
            "gripper.pos": float,
        }

        def __init__(self) -> None:
            self.observation = {
                "shoulder_pan.pos": 10.0,
                "shoulder_lift.pos": 20.0,
                "elbow_flex.pos": 30.0,
                "gripper.pos": 0.0,
            }

        def get_observation(self):
            return dict(self.observation)

        def send_action(self, action):
            self.observation.update(action)
            return action

    config = ExecutionSafetyConfig(robot_adapter="lerobot_local")
    adapter = LeRobotLocalAdapter(config, controller_loader=lambda config_path, pythonpath: _FakeController())

    state = adapter.sync_state()
    rotate_state = adapter.rotate_servo(1, 15.0)

    assert state["joint_positions"][:3] == [10.0, 20.0, 30.0]
    assert rotate_state["joint_positions"][:3] == [25.0, 20.0, 30.0]


def test_lerobot_local_adapter_rejects_servo_rotation_beyond_hardware_limit_before_dispatch() -> None:
    class _Motor:
        def __init__(self, motor_id: int, model: str) -> None:
            self.id = motor_id
            self.model = model

    class _FakeBus:
        def __init__(self) -> None:
            self.motors = {"elbow_flex": _Motor(3, "sts3215")}
            self.model_resolution_table = {"sts3215": 4096}
            self.sent_reads: list[tuple[str, str, bool]] = []
            self.raw_values = {
                ("Present_Position", "elbow_flex"): 3139,
                ("Min_Position_Limit", "elbow_flex"): 951,
                ("Max_Position_Limit", "elbow_flex"): 3144,
            }
            self.norm_values = {
                ("Present_Position", "elbow_flex"): 95.95604395604396,
            }

        def read(self, data_name: str, motor: str, *, normalize: bool = True, num_retry: int = 0):
            self.sent_reads.append((data_name, motor, normalize))
            if normalize:
                return self.norm_values[(data_name, motor)]
            return self.raw_values[(data_name, motor)]

    class _FakeController:
        action_features = {
            "shoulder_pan.pos": float,
            "shoulder_lift.pos": float,
            "elbow_flex.pos": float,
            "gripper.pos": float,
        }

        def __init__(self) -> None:
            self.bus = _FakeBus()
            self.observation = {
                "shoulder_pan.pos": 10.0,
                "shoulder_lift.pos": 20.0,
                "elbow_flex.pos": 95.95604395604396,
                "gripper.pos": 0.0,
            }
            self.sent_action = None

        def get_observation(self):
            return dict(self.observation)

        def send_action(self, action):
            self.sent_action = dict(action)
            self.observation.update(action)
            return action

    adapter = LeRobotLocalAdapter(
        ExecutionSafetyConfig(robot_adapter="lerobot_local"),
        controller_loader=lambda config_path, pythonpath: _FakeController(),
    )

    try:
        adapter.rotate_servo(3, 20.0)
    except AdapterError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected AdapterError")

    assert "目标超出硬件限位" in message
    controller = adapter._controller
    assert controller is not None
    assert controller.sent_action is None


def test_safety_manager_accepts_degree_based_joint_positions_for_servo_rotation() -> None:
    config = ExecutionSafetyConfig()
    safety = SafetyManager(config)

    checks = safety.preflight_servo_rotation(
        1,
        15.0,
        {
            "joint_positions": [95.0, -90.0, 0.0],
            "ee_pose": {},
        },
    )

    assert "目标舵机角度范围校验通过" in checks


def test_safety_manager_detects_degree_units_from_other_joints() -> None:
    config = ExecutionSafetyConfig()
    safety = SafetyManager(config)

    checks = safety.preflight_servo_rotation(
        3,
        20.0,
        {
            "joint_positions": [95.0, -90.0, 4.79, 65.0, -75.0, 3.6],
            "ee_pose": {},
        },
    )

    assert "目标舵机角度范围校验通过" in checks
