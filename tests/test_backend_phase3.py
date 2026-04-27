import io
import json
from time import monotonic, sleep

from embodied_agent.app import build_runtime
from embodied_agent.backend.http import build_http_app_from_runtime
from embodied_agent.backend.service import build_frontend_facade


def _request(app, method: str, path: str, body: dict[str, object] | None = None, *, query: str = "", headers: dict[str, str] | None = None):
    payload = b""
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    status_holder: dict[str, object] = {}

    def start_response(status: str, response_headers: list[tuple[str, str]]):
        status_holder["status"] = status
        status_holder["headers"] = response_headers

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(payload)),
        "wsgi.input": io.BytesIO(payload),
    }
    for key, value in (headers or {}).items():
        environ[key] = value
    body_bytes = b"".join(app(environ, start_response))
    return status_holder["status"], dict(status_holder["headers"]), body_bytes


def _parse_sse(body: bytes) -> list[dict[str, object]]:
    raw = body.decode("utf-8")
    events: list[dict[str, object]] = []
    for chunk in [item for item in raw.split("\n\n") if item.strip()]:
        entry: dict[str, object] = {}
        for line in chunk.splitlines():
            if line.startswith("id: "):
                entry["id"] = int(line[4:])
            elif line.startswith("event: "):
                entry["event_name"] = line[7:]
            elif line.startswith("data: "):
                entry["data"] = json.loads(line[6:])
        events.append(entry)
    return events


def _wait_for_terminal_http_events(app, run_id: str, timeout_s: float = 5.0) -> list[dict[str, object]]:
    start = monotonic()
    while monotonic() - start < timeout_s:
        status, _, body = _request(app, "GET", f"/api/v1/runtime/runs/{run_id}/events")
        assert status.startswith("200")
        events = _parse_sse(body)
        if any(bool(dict(event["data"]).get("terminal", False)) for event in events if isinstance(event.get("data"), dict)):
            return events
        sleep(0.05)
    raise AssertionError(f"run {run_id} did not reach terminal state in time")


def test_backend_http_bootstrap_and_tools_expose_execution_contracts(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    bootstrap_status, bootstrap_headers, bootstrap_body = _request(app, "GET", "/api/v1/runtime/bootstrap")
    tools_status, _, tools_body = _request(app, "GET", "/api/v1/runtime/tools")
    refresh_status, _, refresh_body = _request(app, "POST", "/api/v1/runtime/tools/refresh")

    bootstrap = json.loads(bootstrap_body.decode("utf-8"))
    tools = json.loads(tools_body.decode("utf-8"))
    refreshed_tools = json.loads(refresh_body.decode("utf-8"))

    assert bootstrap_status.startswith("200")
    assert bootstrap_headers["Content-Type"].startswith("application/json")
    assert bootstrap["execution_model"]["backend"] == "mock_smolvla"
    assert bootstrap["execution_model"]["adapter"] == "mock_lerobot"
    assert any(capability["capability_name"] == "pick_and_place" for capability in bootstrap["execution_capabilities"])
    assert bootstrap["execution_safety"]["manual_reset_required"] is True

    assert tools_status.startswith("200")
    assert any(tool["name"] == "run_smolvla" and tool["capability_names"] == ["pick_and_place"] for tool in tools["tools"])
    assert refresh_status.startswith("200")
    assert refreshed_tools["tools"] == tools["tools"]


def test_backend_facade_start_run_exposes_snapshot_and_events_urls(app_config) -> None:
    runtime = build_runtime(app_config)
    facade = build_frontend_facade(runtime)

    accepted = facade.start_run(instruction="抓取桌面方块", run_id="run-backend")
    snapshot = facade.get_run(run_id="run-backend")

    assert accepted["run_id"] == "run-backend"
    assert accepted["status"] == "running"
    assert accepted["snapshot_url"] == "/api/v1/runtime/runs/run-backend"
    assert accepted["events_url"] == "/api/v1/runtime/runs/run-backend/events"
    assert accepted["run"]["status"] == "running"
    assert snapshot["version"] >= 1
    assert snapshot["event"] in {"snapshot", "phase_started", "phase_completed", "run_completed"}


def test_backend_http_run_route_returns_direct_snapshot(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, headers, body = _request(
        app,
        "POST",
        "/api/v1/runtime/run",
        {"instruction": "抓取桌面方块", "run_id": "run-direct"},
    )
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("200")
    assert headers["Content-Type"].startswith("application/json")
    assert payload["run"]["run_id"] == "run-direct"
    assert payload["run"]["status"] in {"completed", "failed"}
    assert payload["run"]["current_phase"] == "final_status"


def test_backend_http_invalid_instruction_returns_error_payload(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, _, body = _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "   "})
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("400")
    assert payload["error"]["code"] == "InvalidInstruction"


def test_backend_http_video_stream_route_returns_mjpeg_frame(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, headers, body = _request(
        app,
        "GET",
        "/api/v1/runtime/video-stream",
        query="frame_limit=1&fps=30",
    )

    assert status.startswith("200")
    assert headers["Content-Type"].startswith("multipart/x-mixed-replace")
    assert b"Content-Type: image/" in body
    assert b"--frame" in body


def test_backend_http_put_config_updates_runtime_view(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, _, body = _request(
        app,
        "PUT",
        "/api/v1/runtime/config",
        {
            "decision": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "decision-secret",
                "local_path": "/models/decision",
                "base_url": "https://llm.example.com/v1",
            },
            "perception": {
                "provider": "openai_gpt4o",
                "model": "gpt-4o",
                "api_key": "perception-secret",
                "local_path": "/models/perception",
                "base_url": "https://vlm.example.com/v1",
                "camera_backend": "opencv",
                "camera_device_id": "/dev/video2",
                "camera_frame_id": "wrist_camera",
                "camera_width": 1280,
                "camera_height": 720,
                "camera_fps": 15.0,
                "camera_index": 2,
                "robot_state_backend": "mcp_bridge",
                "robot_state_base_url": "http://127.0.0.1:8765",
                "robot_state_config_path": "./configs/robot.yaml",
                "robot_state_base_frame": "tool0",
            },
            "execution": {
                "model_path": "./models/smolvla_updated",
                "home_pose": {"x": 0.1, "y": 0.2, "z": 0.3},
                "adapter": "mcp_bridge",
                "robot_base_url": "http://127.0.0.1:9901",
                "robot_timeout_s": 3.0,
                "telemetry_poll_timeout_s": 1.5,
                "safety_require_precheck": True,
                "robot_pythonpath": "/opt/lerobot/src",
            },
            "frontend": {"max_iterations": 6, "speed_scale": 0.6, "port": 9000},
        },
    )
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("200")
    assert payload["decision"]["provider"] == "openai"
    assert payload["decision"]["model"] == "gpt-4o-mini"
    assert payload["decision"]["api_key"] == ""
    assert payload["decision"]["api_key_configured"] is True
    assert payload["decision"]["local_path"] == "/models/decision"
    assert payload["decision"]["base_url"] == "https://llm.example.com/v1"
    assert payload["perception"]["provider"] == "openai_gpt4o"
    assert payload["perception"]["model"] == "gpt-4o"
    assert payload["perception"]["api_key"] == ""
    assert payload["perception"]["api_key_configured"] is True
    assert payload["perception"]["base_url"] == "https://vlm.example.com/v1"
    assert payload["perception"]["camera_backend"] == "opencv"
    assert payload["perception"]["camera_device_id"] == "/dev/video2"
    assert payload["perception"]["camera_index"] == 2
    assert payload["perception"]["robot_state_backend"] == "mcp_bridge"
    assert payload["perception"]["robot_state_base_url"] == "http://127.0.0.1:8765"
    assert payload["execution"]["model_path"] == "./models/smolvla_updated"
    assert payload["execution"]["home_pose"] == {"x": 0.1, "y": 0.2, "z": 0.3}
    assert payload["execution"]["adapter"] == "mcp_bridge"
    assert payload["execution"]["robot_base_url"] == "http://127.0.0.1:9901"
    assert payload["execution"]["robot_timeout_s"] == 3.0
    assert payload["execution"]["telemetry_poll_timeout_s"] == 1.5
    assert payload["execution"]["safety_require_precheck"] is True
    assert payload["frontend"]["max_iterations"] == 6
    assert payload["frontend"]["speed_scale"] == 0.6
    assert payload["frontend"]["port"] == 9000


def test_backend_bootstrap_config_exposes_assistant_metadata(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, _, body = _request(app, "GET", "/api/v1/runtime/bootstrap")
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("200")
    assert payload["config"]["decision"]["assistant"]["title"] == "模型部署助手"
    assert payload["config"]["perception"]["assistant"]["title"] == "系统载入助手"
    assert payload["config"]["perception"]["assistant"]["detected_models"]
    assert payload["config"]["perception"]["assistant"]["status"] == "attention"
    assert "mock provider" in payload["config"]["perception"]["assistant"]["message"]



def test_backend_bootstrap_config_marks_perception_provider_configured_when_remote_ready(app_config) -> None:
    app_config.perception.vlm_provider = "openai_gpt4o"
    app_config.perception.vlm_api_key = "perception-secret"
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, _, body = _request(app, "GET", "/api/v1/runtime/bootstrap")
    payload = json.loads(body.decode("utf-8"))
    perception_assistant = payload["config"]["perception"]["assistant"]

    assert status.startswith("200")
    assert perception_assistant["status"] == "configured"
    assert perception_assistant["detected_models"][0]["configured"] is True
    assert perception_assistant["detected_models"][0]["provider"] == "openai_gpt4o"


def test_backend_bootstrap_config_marks_decision_provider_configured_when_base_url_ready(app_config) -> None:
    app_config.decision.llm_provider = "openai"
    app_config.decision.llm_base_url = "https://llm.example.com/v1"
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, _, body = _request(app, "GET", "/api/v1/runtime/bootstrap")
    payload = json.loads(body.decode("utf-8"))
    decision_assistant = payload["config"]["decision"]["assistant"]

    assert status.startswith("200")
    assert payload["config"]["decision"]["base_url"] == "https://llm.example.com/v1"
    assert decision_assistant["status"] == "configured"
    assert "https://llm.example.com/v1" in decision_assistant["message"]


def test_backend_http_events_support_last_event_id_and_after_version(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "抓取桌面方块", "run_id": "run-offset"})
    events = _wait_for_terminal_http_events(app, "run-offset")
    assert events

    status_with_header, _, body_with_header = _request(
        app,
        "GET",
        "/api/v1/runtime/runs/run-offset/events",
        headers={"HTTP_LAST_EVENT_ID": "1"},
    )
    status_with_query, _, body_with_query = _request(
        app,
        "GET",
        "/api/v1/runtime/runs/run-offset/events",
        query="after_version=1",
    )

    parsed_header = _parse_sse(body_with_header)
    parsed_query = _parse_sse(body_with_query)

    assert status_with_header.startswith("200")
    assert status_with_query.startswith("200")
    assert parsed_header
    assert parsed_query
    assert all(int(event["id"]) > 1 for event in parsed_header)
    assert all(int(event["id"]) > 1 for event in parsed_query)
    assert parsed_header[-1]["event_name"] == dict(parsed_header[-1]["data"])["event"]
    assert parsed_query[-1]["event_name"] == dict(parsed_query[-1]["data"])["event"]


def test_backend_facade_update_config_is_atomic_when_provider_is_invalid(app_config) -> None:
    runtime = build_runtime(app_config)
    facade = build_frontend_facade(runtime)
    original_provider = runtime.config.decision.llm_provider
    original_model = runtime.config.decision.llm_model

    try:
        facade.update_config({"decision": {"provider": "unsupported-provider", "model": "broken-model"}})
    except ValueError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("expected invalid provider update to fail")

    payload = facade.get_config()
    assert runtime.config.decision.llm_provider == original_provider
    assert runtime.config.decision.llm_model == original_model
    assert payload["decision"]["provider"] == original_provider
    assert payload["decision"]["model"] == original_model
