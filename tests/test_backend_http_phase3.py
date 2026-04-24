import io
import json
from time import monotonic, sleep

from embodied_agent.app import build_runtime
from embodied_agent.backend.http import build_http_app_from_runtime


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

    bootstrap = json.loads(bootstrap_body.decode("utf-8"))
    tools = json.loads(tools_body.decode("utf-8"))

    assert bootstrap_status.startswith("200")
    assert bootstrap_headers["Content-Type"].startswith("application/json")
    assert bootstrap["execution_model"]["backend"] == "mock_smolvla"
    assert bootstrap["execution_model"]["adapter"] == "mock_lerobot"
    assert any(capability["capability_name"] == "pick_and_place" for capability in bootstrap["execution_capabilities"])
    assert bootstrap["execution_safety"]["manual_reset_required"] is True

    assert tools_status.startswith("200")
    assert any(tool["name"] == "run_smolvla" and tool["capability_names"] == ["pick_and_place"] for tool in tools["tools"])


def test_backend_http_run_and_error_routes(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    run_status, _, run_body = _request(app, "POST", "/api/v1/runtime/run", {"instruction": "抓取桌面方块"})
    accepted_status, _, accepted_body = _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "抓取桌面方块", "run_id": "run-http"})
    duplicate_status, _, duplicate_body = _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "抓取桌面方块", "run_id": "run-http"})

    run_payload = json.loads(run_body.decode("utf-8"))
    accepted = json.loads(accepted_body.decode("utf-8"))
    duplicate = json.loads(duplicate_body.decode("utf-8"))

    assert run_status.startswith("200")
    assert run_payload["run"]["status"] in {"completed", "failed"}
    assert run_payload["run"]["current_phase"] == "final_status"
    assert accepted_status.startswith("202")
    assert accepted["run_id"] == "run-http"
    assert duplicate_status.startswith("409")
    assert duplicate["error"]["code"] == "RunAlreadyExists"


def test_backend_http_events_support_last_event_id_and_after_version(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "抓取桌面方块", "run_id": "run-offset"})
    _wait_for_terminal_http_events(app, "run-offset")

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


def test_backend_http_invalid_cursor_returns_error(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "抓取桌面方块", "run_id": "run-invalid"})
    status, _, body = _request(app, "GET", "/api/v1/runtime/runs/run-invalid/events", query="after_version=-1")
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("400")
    assert payload["error"]["code"] == "InvalidAfterVersion"


def test_backend_http_put_config_rejects_invalid_provider_without_mutating_runtime(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, _, body = _request(
        app,
        "PUT",
        "/api/v1/runtime/config",
        {
            "decision": {"provider": "unsupported-provider"},
            "perception": {"provider": "openai_gpt4o"},
        },
    )
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("400")
    assert payload["error"]["code"] == "InvalidDecisionProvider"

    bootstrap_status, _, bootstrap_body = _request(app, "GET", "/api/v1/runtime/bootstrap")
    bootstrap = json.loads(bootstrap_body.decode("utf-8"))
    assert bootstrap_status.startswith("200")
    assert bootstrap["config"]["decision"]["provider"] == "minimax"


def test_backend_http_invalid_last_event_id_returns_error(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    _request(app, "POST", "/api/v1/runtime/runs", {"instruction": "抓取桌面方块", "run_id": "run-last-event-id"})
    status, _, body = _request(
        app,
        "GET",
        "/api/v1/runtime/runs/run-last-event-id/events",
        headers={"HTTP_LAST_EVENT_ID": "invalid"},
    )
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("400")
    assert payload["error"]["code"] == "InvalidLastEventId"


def test_backend_http_missing_run_returns_not_found(app_config) -> None:
    runtime = build_runtime(app_config)
    app = build_http_app_from_runtime(runtime)

    status, _, body = _request(app, "GET", "/api/v1/runtime/runs/run-missing")
    payload = json.loads(body.decode("utf-8"))

    assert status.startswith("404")
    assert payload["error"]["code"] == "RunNotFound"
