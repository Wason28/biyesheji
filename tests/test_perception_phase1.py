import json
import sys
import time
import types

from embodied_agent.perception.adapters import (
    BridgeRobotStateClient,
    LeRobotRobotStateClient,
    OpenCVCamera,
    build_camera_adapter,
    build_robot_state_adapter,
)
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
    VLMServiceUnavailableError,
)
from embodied_agent.perception.mocks import MockCamera, MockRobotStateClient
from embodied_agent.perception.providers import (
    MockVLMProvider,
    OllamaVisionProvider,
    OpenAICompatibleVisionProvider,
    ProviderSettings,
    build_vlm_provider,
)
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
    app_config.perception.camera_index = 2
    app_config.perception.vlm_base_url = "http://localhost:11434"
    app_config.perception.vlm_timeout_s = 7.5
    app_config.perception.robot_state_base_url = "http://127.0.0.1:9001"
    app_config.perception.robot_state_config_path = "./configs/robot.yaml"
    app_config.perception.robot_pythonpath = "/opt/lerobot/src"

    runtime_config = build_perception_runtime_config(app_config.perception)

    assert isinstance(runtime_config, PerceptionRuntimeConfig)
    assert runtime_config.camera_device_id == "camera-02"
    assert runtime_config.camera_frame_id == "wrist_camera"
    assert runtime_config.camera_width == 1280
    assert runtime_config.camera_height == 720
    assert runtime_config.camera_index == 2
    assert runtime_config.robot_state_base_frame == "tool0"
    assert runtime_config.vlm_base_url == "http://localhost:11434"
    assert runtime_config.vlm_timeout_s == 7.5
    assert runtime_config.robot_state_base_url == "http://127.0.0.1:9001"
    assert runtime_config.robot_state_config_path == "./configs/robot.yaml"
    assert runtime_config.robot_pythonpath == "/opt/lerobot/src"


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


def test_build_camera_adapter_supports_opencv_backend() -> None:
    config = PerceptionRuntimeConfig(
        camera_backend="opencv",
        camera_device_id="/dev/video0",
        camera_width=640,
        camera_height=480,
        camera_fps=30.0,
    )

    adapter = build_camera_adapter(config)

    assert isinstance(adapter, OpenCVCamera)
    assert adapter.camera_id == "/dev/video0"


def test_opencv_camera_capture_returns_base64_png(monkeypatch) -> None:
    class _FakeEncoded:
        def tobytes(self) -> bytes:
            return b"fake_png_bytes"

    class _FakeFrame:
        shape = (480, 640, 3)

    class _FakeCapture:
        def __init__(self, device_ref, backend_flag=None) -> None:
            self.device_ref = device_ref
            self.backend_flag = backend_flag
            self.released = False
            self.settings = {}

        def isOpened(self) -> bool:
            return True

        def set(self, prop, value) -> bool:
            self.settings[prop] = value
            return True

        def read(self):
            return True, _FakeFrame()

        def release(self) -> None:
            self.released = True

    fake_cv2 = types.SimpleNamespace(
        CAP_V4L2=200,
        CAP_PROP_FRAME_WIDTH=3,
        CAP_PROP_FRAME_HEIGHT=4,
        CAP_PROP_FPS=5,
        VideoCapture=_FakeCapture,
        imencode=lambda ext, frame: (True, _FakeEncoded()),
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    camera = OpenCVCamera(
        camera_id="/dev/video0",
        width=640,
        height=480,
        fps=30.0,
        frame_id="camera_color_optical_frame",
    )

    captured = camera.capture()

    assert captured.resolution == {"width": 640, "height": 480}
    assert captured.camera_parameters["backend"] == "opencv"
    assert captured.camera_parameters["camera_id"] == "/dev/video0"
    assert captured.image_base64 == "ZmFrZV9wbmdfYnl0ZXM="
    _, reopened = camera._open_camera()
    assert reopened.backend_flag is None
    reopened.release()


def test_opencv_camera_capture_retries_after_warmup_read_failure(monkeypatch) -> None:
    class _FakeEncoded:
        def tobytes(self) -> bytes:
            return b"fake_png_bytes"

    class _FakeFrame:
        shape = (480, 640, 3)

        def copy(self):
            return self

    class _FakeCapture:
        def __init__(self, device_ref, backend_flag=None) -> None:
            del device_ref, backend_flag
            self.read_results = [
                (False, None),
                (True, _FakeFrame()),
                (True, _FakeFrame()),
            ]

        def isOpened(self) -> bool:
            return True

        def set(self, prop, value) -> bool:
            del prop, value
            return True

        def read(self):
            if self.read_results:
                return self.read_results.pop(0)
            return True, _FakeFrame()

        def release(self) -> None:
            return None

    fake_cv2 = types.SimpleNamespace(
        CAP_V4L2=200,
        CAP_PROP_FRAME_WIDTH=3,
        CAP_PROP_FRAME_HEIGHT=4,
        CAP_PROP_FPS=5,
        VideoCapture=_FakeCapture,
        imencode=lambda ext, frame: (True, _FakeEncoded()),
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    camera = OpenCVCamera(
        camera_id="/dev/video0",
        width=640,
        height=480,
        fps=30.0,
        frame_id="camera_color_optical_frame",
    )
    camera._WARMUP_FRAME_COUNT = 2
    camera._READ_RETRY_COUNT = 2
    camera._READ_RETRY_DELAY_S = 0.0

    captured = camera.capture()

    assert captured.resolution == {"width": 640, "height": 480}
    assert captured.image_base64 == "ZmFrZV9wbmdfYnl0ZXM="


def test_opencv_camera_capture_loop_reopens_after_disconnect(monkeypatch) -> None:
    class _FakeFrame:
        def __init__(self, marker: str) -> None:
            self.marker = marker
            self.shape = (480, 640, 3)

        def copy(self):
            return _FakeFrame(self.marker)

    class _FakeCapture:
        def __init__(self, reads: list[tuple[bool, _FakeFrame | None]]) -> None:
            self.reads = list(reads)
            self.released = False

        def read(self):
            if self.reads:
                return self.reads.pop(0)
            return True, _FakeFrame("steady")

        def release(self) -> None:
            self.released = True

    camera = OpenCVCamera(
        camera_id="/dev/video0",
        width=640,
        height=480,
        fps=30.0,
        frame_id="camera_color_optical_frame",
    )
    camera._WARMUP_FRAME_COUNT = 1
    camera._READ_RETRY_COUNT = 1
    camera._READ_RETRY_DELAY_S = 0.0
    camera._OPEN_RETRY_DELAY_S = 0.0

    captures = [
        _FakeCapture([(True, _FakeFrame("first")), (False, None)]),
        _FakeCapture([(True, _FakeFrame("second")), (True, _FakeFrame("second"))]),
    ]
    open_calls: list[int] = []

    def _fake_open_camera():
        open_calls.append(1)
        if captures:
            return None, captures.pop(0)
        return None, _FakeCapture([(True, _FakeFrame("steady"))])

    monkeypatch.setattr(camera, "_open_camera", _fake_open_camera)

    camera._ensure_capture_thread()

    deadline = time.time() + 1.0
    latest_marker = None
    while time.time() < deadline:
        frame = camera._get_latest_frame(wait_timeout_s=0.2, allow_direct_fallback=False)
        latest_marker = getattr(frame, "marker", None)
        if latest_marker == "second":
            break
        time.sleep(0.01)

    camera.close()

    assert latest_marker == "second"
    assert len(open_calls) >= 2




def test_build_robot_state_adapter_rejects_unsupported_backend() -> None:
    config = PerceptionRuntimeConfig(robot_state_backend="ros2")

    try:
        build_robot_state_adapter(config)
    except AdapterConfigurationError as exc:
        assert exc.code == "PERCEPTION_ADAPTER_CONFIGURATION_ERROR"
        assert exc.details["backend"] == "ros2"
    else:
        raise AssertionError("expected AdapterConfigurationError")


def test_build_robot_state_adapter_supports_bridge_backend() -> None:
    config = PerceptionRuntimeConfig(
        robot_state_backend="mcp_bridge",
        robot_state_base_url="http://127.0.0.1:8765",
        robot_state_base_frame="tool0",
    )

    adapter = build_robot_state_adapter(config)

    assert isinstance(adapter, BridgeRobotStateClient)
    assert adapter.base_url == "http://127.0.0.1:8765"


def test_bridge_robot_state_client_normalizes_gateway_payload() -> None:
    def transport(*, method: str, url: str, headers: dict[str, str], body, timeout_s: float):
        assert method == "GET"
        assert url == "http://127.0.0.1:8765/state"
        response = {
            "ok": True,
            "robot_state": {
                "joint_positions": [0.1, 0.2, 0.3],
                "ee_pose": {
                    "position": {"x": 0.4, "y": -0.1, "z": 0.2},
                    "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                    "reference_frame": "tool0",
                },
                "timestamp": "2026-04-26T00:00:00+00:00",
            },
            "telemetry": {
                "heartbeat_ok": True,
                "connection_ok": True,
                "error_code": "",
            },
        }
        return 200, {"Content-Type": "application/json"}, json.dumps(response).encode("utf-8")

    adapter = BridgeRobotStateClient(
        base_url="http://127.0.0.1:8765",
        timeout_s=1.0,
        reference_frame="tool0",
        transport=transport,
    )

    snapshot = adapter.read_state().to_payload()

    assert snapshot["joint_positions"] == [0.1, 0.2, 0.3]
    assert snapshot["ee_pose"]["reference_frame"] == "tool0"
    assert snapshot["metadata"]["backend"] == "mcp_bridge"
    assert snapshot["metadata"]["heartbeat_ok"] is True


def test_lerobot_robot_state_client_uses_loader_and_observation_fallback() -> None:
    class _FakeRobot:
        def get_observation(self):
            return {
                "joint_1.pos": 0.1,
                "joint_2.pos": -0.2,
                "gripper.pos": 30.0,
                "ee.x": 0.2,
                "ee.y": 0.0,
                "ee.z": 0.1,
            }

    adapter = LeRobotRobotStateClient(
        config_path="./robot.yaml",
        pythonpath="/opt/lerobot/src",
        reference_frame="base_link",
        loader=lambda config_path, pythonpath: _FakeRobot(),
    )

    snapshot = adapter.read_state().to_payload()

    assert snapshot["joint_positions"][:2] == [0.1, -0.2]
    assert snapshot["ee_pose"]["position"]["x"] == 0.2
    assert snapshot["metadata"]["backend"] == "lerobot_local"
    assert snapshot["metadata"]["gripper_state"] == 30.0


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

    app_config.perception.vlm_provider = "ollama_vision"
    server = PerceptionMCPServer(
        app_config,
        provider_factory=lambda config: _BrokenProvider(ProviderSettings.from_perception_config(config)),
    )

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




def test_build_vlm_provider_uses_mock_fallback_when_remote_provider_is_unconfigured() -> None:
    provider = build_vlm_provider(
        ProviderSettings(
            provider="openai_gpt4o",
            model="gpt-4o",
            api_key="",
            local_path="",
            base_url="",
            timeout_s=15.0,
            max_retries=2,
            max_tokens=512,
        )
    )

    assert isinstance(provider, MockVLMProvider)
    summary = provider.config_summary()
    assert summary["mode"] == "mock_fallback"
    assert summary["configured"] is False
    assert "fallback_reason" in summary



def test_build_vlm_provider_uses_openai_compatible_provider_when_configured() -> None:
    provider = build_vlm_provider(
        ProviderSettings(
            provider="openai_gpt4o",
            model="gpt-4o",
            api_key="secret",
            local_path="",
            base_url="",
            timeout_s=15.0,
            max_retries=2,
            max_tokens=512,
        )
    )

    assert isinstance(provider, OpenAICompatibleVisionProvider)
    assert provider.endpoint == "https://api.openai.com/v1/chat/completions"



def test_build_vlm_provider_uses_ollama_provider_when_local_endpoint_is_available() -> None:
    provider = build_vlm_provider(
        ProviderSettings(
            provider="ollama_vision",
            model="llava:7b",
            api_key="",
            local_path="./models/llava",
            base_url="",
            timeout_s=15.0,
            max_retries=2,
            max_tokens=512,
        )
    )

    assert isinstance(provider, OllamaVisionProvider)
    assert provider.endpoint == "http://127.0.0.1:11434/api/chat"



def test_openai_compatible_provider_parses_structured_json_response() -> None:
    captured: dict[str, object] = {}

    def transport(method: str, url: str, headers: dict[str, str], body: bytes, timeout_s: float):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json.loads(body.decode("utf-8"))
        captured["timeout_s"] = timeout_s
        response_body = json.dumps(
            {
                "model": "gpt-4o",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "scene_description": "桌面上有一个红色方块。",
                                    "confidence": 0.83,
                                    "structured_observations": {
                                        "objects": [
                                            {
                                                "name": "cube",
                                                "category": "target_object",
                                                "position_hint": "front_center",
                                                "graspable": True,
                                            }
                                        ],
                                        "relations": ["cube is in front of the gripper"],
                                        "robot_grasp_state": "open",
                                        "risk_flags": [],
                                    },
                                },
                                ensure_ascii=False,
                            )
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            },
            ensure_ascii=False,
        ).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response_body

    provider = OpenAICompatibleVisionProvider(
        ProviderSettings(
            provider="openai_gpt4o",
            model="gpt-4o",
            api_key="secret",
            local_path="",
            base_url="",
            timeout_s=8.0,
            max_retries=2,
            max_tokens=256,
        ),
        endpoint="https://api.openai.com/v1/chat/completions",
        transport=transport,
    )

    result = provider.describe_scene(SceneDescriptionRequest(image="ZmFrZV9pbWFnZQ==", prompt="分析场景"))

    assert captured["method"] == "POST"
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert result.scene_description == "桌面上有一个红色方块。"
    assert result.structured_observations["objects"][0]["name"] == "cube"
    assert result.provider_metadata["mode"] == "remote"
    assert result.provider_metadata["usage"]["prompt_tokens"] == 100



def test_openai_compatible_provider_maps_auth_failure() -> None:
    def transport(method: str, url: str, headers: dict[str, str], body: bytes, timeout_s: float):
        return 401, {"Content-Type": "application/json"}, b'{"error":"unauthorized"}'

    provider = OpenAICompatibleVisionProvider(
        ProviderSettings(
            provider="openai_gpt4o",
            model="gpt-4o",
            api_key="secret",
            local_path="",
            base_url="",
            timeout_s=8.0,
            max_retries=2,
            max_tokens=256,
        ),
        endpoint="https://api.openai.com/v1/chat/completions",
        transport=transport,
    )

    try:
        provider.describe_scene(SceneDescriptionRequest(image="ZmFrZV9pbWFnZQ=="))
    except VLMAuthenticationError as exc:
        assert exc.code == "PERCEPTION_VLM_AUTHENTICATION_FAILURE"
    else:
        raise AssertionError("expected VLMAuthenticationError")
def test_openai_compatible_provider_falls_back_to_plain_text_scene_description() -> None:
    captured: dict[str, object] = {}

    def transport(method: str, url: str, headers: dict[str, str], body: bytes, timeout_s: float):
        captured["body"] = json.loads(body.decode("utf-8"))
        response_body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "画面里有一台机械臂，桌面上有一个方块，当前没有明显碰撞风险。"
                        },
                        "finish_reason": "stop",
                    }
                ],
                "model": "mimo-v2-omni",
            },
            ensure_ascii=False,
        ).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response_body

    provider = OpenAICompatibleVisionProvider(
        ProviderSettings(
            provider="openai_gpt4o",
            model="mimo-v2-omni",
            api_key="secret",
            local_path="",
            base_url="",
            timeout_s=8.0,
            max_retries=2,
            max_tokens=256,
        ),
        endpoint="https://example.com/v1/chat/completions",
        transport=transport,
    )

    result = provider.describe_scene(SceneDescriptionRequest(image="ZmFrZV9pbWFnZQ==", prompt="分析场景"))

    assert result.scene_description.startswith("画面里有一台机械臂")
    assert result.provider_metadata["parsed_mode"] == "text_fallback"
    assert result.structured_observations["objects"] == []
    assert result.confidence == 0.6
    assert "response_format" not in captured["body"]


def test_ollama_provider_maps_service_unavailable() -> None:
    def transport(method: str, url: str, headers: dict[str, str], body: bytes, timeout_s: float):
        raise ConnectionError("connection refused")

    provider = OllamaVisionProvider(
        ProviderSettings(
            provider="ollama_vision",
            model="llava:7b",
            api_key="",
            local_path="./models/llava",
            base_url="http://127.0.0.1:11434",
            timeout_s=5.0,
            max_retries=1,
            max_tokens=128,
        ),
        endpoint="http://127.0.0.1:11434/api/chat",
        transport=transport,
    )

    try:
        provider.describe_scene(SceneDescriptionRequest(image="ZmFrZV9pbWFnZQ=="))
    except VLMServiceUnavailableError as exc:
        assert exc.code == "PERCEPTION_VLM_SERVICE_UNAVAILABLE"
    else:
        raise AssertionError("expected VLMServiceUnavailableError")
