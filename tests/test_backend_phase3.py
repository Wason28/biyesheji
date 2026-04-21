import io
import json

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
    assert snapshot["event"] == "snapshot"


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


def test_backend_http_invalid_instruction_returns_error_payload(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, _, body = _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "   "})
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("400")
    assert payload["error"]["code"] == "InvalidInstruction"


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
            },
            "perception": {
                "provider": "openai_gpt4o",
                "model": "gpt-4o",
                "api_key": "perception-secret",
                "local_path": "/models/perception",
            },
            "execution": {
                "model_path": "./models/smolvla_updated",
                "home_pose": {"x": 0.1, "y": 0.2, "z": 0.3},
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
    assert payload["perception"]["provider"] == "openai_gpt4o"
    assert payload["perception"]["model"] == "gpt-4o"
    assert payload["perception"]["api_key"] == ""
    assert payload["perception"]["api_key_configured"] is True
    assert payload["execution"]["model_path"] == "./models/smolvla_updated"
    assert payload["execution"]["home_pose"] == {"x": 0.1, "y": 0.2, "z": 0.3}
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


def test_backend_http_events_support_last_event_id_and_after_version(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "抓取桌面方块", "run_id": "run-offset"})

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

    assert status_with_header.startswith("200")
    assert status_with_query.startswith("200")
    assert isinstance(body_with_header, bytes)
    assert isinstance(body_with_query, bytes)
