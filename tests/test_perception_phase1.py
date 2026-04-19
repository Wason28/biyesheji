from embodied_agent.perception.mocks import MockCamera
from embodied_agent.perception.server import PerceptionMCPServer


def test_perception_server_describe_scene_success(app_config) -> None:
    server = PerceptionMCPServer(app_config)

    response = server.call_tool("describe_scene", {"image": "ZmFrZV9pbWFnZQ=="})

    assert response["status"] == "ok"
    assert response["tool_name"] == "describe_scene"
    result = response["result"]
    assert result["provider"] == app_config.perception.vlm_provider
    assert result["scene_description"]
    assert result["structured_observations"]["objects"][0]["name"] == "cube"


def test_perception_server_get_image_failure_returns_error_payload() -> None:
    server = PerceptionMCPServer(camera=MockCamera(fail_on_capture=True))

    response = server.call_tool("get_image")

    assert response["status"] == "error"
    assert response["error"]["code"] == "PERCEPTION_CAMERA_DISCONNECTED"
    assert response["error"]["retriable"] is True
