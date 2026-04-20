from embodied_agent.perception.adapters import build_camera_adapter, build_robot_state_adapter
from embodied_agent.perception.config import PerceptionRuntimeConfig, build_perception_runtime_config
from embodied_agent.perception.contracts import (
    SceneDescriptionRequest,
    SceneDescriptionResult,
    build_perception_error_envelope,
)
from embodied_agent.perception.errors import (
    AdapterConfigurationError,
    VLMAuthenticationError,
    VLMRateLimitError,
    VLMResponseFormatError,
)
from embodied_agent.perception.mocks import MockCamera, MockRobotStateClient
from embodied_agent.perception.providers import MockVLMProvider, ProviderSettings, register_vlm_provider
from embodied_agent.perception.server import PerceptionMCPServer, build_server


def test_perception_server_describe_scene_success(app_config) -> None:
    server = PerceptionMCPServer(app_config)

    response = server.call_tool("describe_scene", {"image": "ZmFrZV9pbWFnZQ=="})

    assert response["ok"] is True
    assert response["status_code"] == 200
    assert response["tool_name"] == "describe_scene"
    result = response["content"]
    assert result["provider"] == app_config.perception.vlm_provider
    assert result["scene_description"]
    assert result["structured_observations"]["objects"][0]["name"] == "cube"


def test_perception_server_get_image_failure_returns_error_payload() -> None:
    server = PerceptionMCPServer(camera=MockCamera(fail_on_capture=True))

    response = server.call_tool("get_image")

    assert response["ok"] is False
    assert response["status_code"] == 500
    assert response["tool_name"] == "get_image"
    assert response["message"] == "摄像头未连接或初始化失败"
    assert response["metadata"]["error_code"] == "PERCEPTION_CAMERA_DISCONNECTED"
    assert response["metadata"]["retriable"] is True


def test_perception_server_get_robot_state_success_returns_unified_envelope() -> None:
    server = PerceptionMCPServer()

    response = server.call_tool("get_robot_state")

    assert response["ok"] is True
    assert response["status_code"] == 200
    assert response["tool_name"] == "get_robot_state"
    assert response["content"]["joint_positions"]
    assert response["content"]["ee_pose"]["position"]["x"] == 0.42
    assert response["content"]["ee_pose"]["reference_frame"] == "base_link"


def test_perception_server_get_robot_state_failure_returns_error_envelope() -> None:
    server = PerceptionMCPServer(robot_state_client=MockRobotStateClient(fail_on_read=True))

    response = server.call_tool("get_robot_state")

    assert response["ok"] is False
    assert response["status_code"] == 500
    assert response["tool_name"] == "get_robot_state"
    assert response["metadata"]["error_code"] == "PERCEPTION_ROBOT_COMMUNICATION_FAILURE"
    assert response["metadata"]["retriable"] is True


def test_perception_server_unknown_tool_returns_unified_error_envelope() -> None:
    server = PerceptionMCPServer()

    response = server.call_tool("unknown_tool")

    assert response == build_perception_error_envelope(
        tool_name="unknown_tool",
        code="PERCEPTION_TOOL_NOT_FOUND",
        message="未知工具: unknown_tool",
        retriable=False,
        details={"requested_tool_name": "unknown_tool"},
        status_code=404,
    )


class _CustomProvider(MockVLMProvider):
    def describe_scene(self, request: SceneDescriptionRequest) -> SceneDescriptionResult:
        return SceneDescriptionResult(
            scene_description="custom provider scene",
            provider=self.provider_name,
            model=self.model_name,
            confidence=0.88,
            prompt_used=request.prompt or "custom-prompt",
            structured_observations={"objects": [], "relations": [], "robot_grasp_state": "open", "risk_flags": []},
        )




def test_perception_server_rejects_invalid_base64_image_payload() -> None:
    server = PerceptionMCPServer()

    response = server.call_tool("describe_scene", {"image": "not_base64"})

    assert response["ok"] is False
    assert response["status_code"] == 500
    assert response["metadata"]["error_code"] == "PERCEPTION_OUTPUT_VALIDATION_FAILURE"


def test_build_perception_runtime_config_maps_extended_fields(app_config) -> None:
    app_config.perception.camera_backend = "mock"
    app_config.perception.camera_device_id = "camera-02"
    app_config.perception.camera_frame_id = "wrist_camera"
    app_config.perception.camera_width = 1280
    app_config.perception.camera_height = 720
    app_config.perception.robot_state_base_frame = "tool0"
    app_config.perception.vlm_base_url = "http://localhost:11434"
    app_config.perception.vlm_timeout_s = 7.5

    runtime_config = build_perception_runtime_config(app_config.perception)

    assert isinstance(runtime_config, PerceptionRuntimeConfig)
    assert runtime_config.camera_device_id == "camera-02"
    assert runtime_config.camera_frame_id == "wrist_camera"
    assert runtime_config.camera_width == 1280
    assert runtime_config.camera_height == 720
    assert runtime_config.robot_state_base_frame == "tool0"
    assert runtime_config.vlm_base_url == "http://localhost:11434"
    assert runtime_config.vlm_timeout_s == 7.5


def test_perception_build_server_supports_factory_injection(app_config) -> None:
    created = {}

    def camera_factory(config: PerceptionRuntimeConfig) -> MockCamera:
        created["camera"] = config.camera_device_id
        return MockCamera(camera_id=config.camera_device_id)

    def robot_state_factory(config: PerceptionRuntimeConfig) -> MockRobotStateClient:
        created["robot"] = config.robot_state_base_frame
        return MockRobotStateClient(reference_frame=config.robot_state_base_frame)

    server = build_server(
        app_config,
        camera_factory=camera_factory,
        robot_state_factory=robot_state_factory,
    )

    assert isinstance(server, PerceptionMCPServer)
    assert created["camera"] == app_config.perception.camera_device_id
    assert created["robot"] == app_config.perception.robot_state_base_frame


def test_build_camera_adapter_rejects_unsupported_backend() -> None:
    config = PerceptionRuntimeConfig(camera_backend="realsense")

    try:
        build_camera_adapter(config)
    except AdapterConfigurationError as exc:
        assert exc.code == "PERCEPTION_ADAPTER_CONFIGURATION_ERROR"
        assert exc.details["backend"] == "realsense"
    else:
        raise AssertionError("expected AdapterConfigurationError")




def test_build_robot_state_adapter_rejects_unsupported_backend() -> None:
    config = PerceptionRuntimeConfig(robot_state_backend="ros2")

    try:
        build_robot_state_adapter(config)
    except AdapterConfigurationError as exc:
        assert exc.code == "PERCEPTION_ADAPTER_CONFIGURATION_ERROR"
        assert exc.details["backend"] == "ros2"
    else:
        raise AssertionError("expected AdapterConfigurationError")


def test_perception_server_success_envelope_includes_runtime_summary(app_config) -> None:
    class _BrokenProvider(MockVLMProvider):
        def describe_scene(self, request: SceneDescriptionRequest) -> SceneDescriptionResult:
            return SceneDescriptionResult(
                scene_description="broken",
                provider=self.provider_name,
                model=self.model_name,
                confidence=0.5,
                prompt_used=request.prompt or "broken",
                structured_observations={"objects": {}, "relations": [], "robot_grasp_state": "open", "risk_flags": []},
            )

    register_vlm_provider("ollama_vision", lambda settings: _BrokenProvider(settings))
    app_config.perception.vlm_provider = "ollama_vision"
    server = PerceptionMCPServer(app_config)

    response = server.call_tool("describe_scene", {"image": "ZmFrZV9pbWFnZQ=="})

    assert response["ok"] is False
    assert response["metadata"]["error_code"] == "PERCEPTION_OUTPUT_VALIDATION_FAILURE"


def test_mock_provider_supports_auth_failure_mode() -> None:
    provider = MockVLMProvider(
        ProviderSettings(
            provider="openai_gpt4o",
            model="gpt-4o",
            api_key="",
            local_path="",
            base_url="",
            timeout_s=15.0,
            max_retries=2,
            max_tokens=512,
        ),
        fail_mode="auth",
    )

    try:
        provider.describe_scene(SceneDescriptionRequest(image="ZmFrZV9pbWFnZQ=="))
    except VLMAuthenticationError as exc:
        assert exc.code == "PERCEPTION_VLM_AUTHENTICATION_FAILURE"
    else:
        raise AssertionError("expected VLMAuthenticationError")


def test_mock_provider_supports_rate_limit_failure_mode() -> None:
    provider = MockVLMProvider(
        ProviderSettings(
            provider="openai_gpt4o",
            model="gpt-4o",
            api_key="",
            local_path="",
            base_url="",
            timeout_s=15.0,
            max_retries=2,
            max_tokens=512,
        ),
        fail_mode="rate_limit",
    )

    try:
        provider.describe_scene(SceneDescriptionRequest(image="ZmFrZV9pbWFnZQ=="))
    except VLMRateLimitError as exc:
        assert exc.code == "PERCEPTION_VLM_RATE_LIMITED"
    else:
        raise AssertionError("expected VLMRateLimitError")


def test_mock_provider_supports_invalid_response_failure_mode() -> None:
    provider = MockVLMProvider(
        ProviderSettings(
            provider="openai_gpt4o",
            model="gpt-4o",
            api_key="",
            local_path="",
            base_url="",
            timeout_s=15.0,
            max_retries=2,
            max_tokens=512,
        ),
        fail_mode="invalid_response",
    )

    try:
        provider.describe_scene(SceneDescriptionRequest(image="ZmFrZV9pbWFnZQ=="))
    except VLMResponseFormatError as exc:
        assert exc.code == "PERCEPTION_VLM_INVALID_RESPONSE"
    else:
        raise AssertionError("expected VLMResponseFormatError")
