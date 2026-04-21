from embodied_agent.app import build_runtime
from embodied_agent.backend.service import build_frontend_facade


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


def test_backend_facade_iter_run_events_returns_snapshot_events(app_config) -> None:
    runtime = build_runtime(app_config)
    facade = build_frontend_facade(runtime)

    facade.start_run(instruction="抓取桌面方块", run_id="run-events")
    events = facade.iter_run_events(run_id="run-events", after_version=0)

    assert events
    assert all(event["event"] == "snapshot" for event in events)
    assert all(event["version"] >= 1 for event in events)


def test_backend_run_registry_rejects_duplicate_run_id(app_config) -> None:
    runtime = build_runtime(app_config)
    facade = build_frontend_facade(runtime)

    facade.start_run(instruction="抓取桌面方块", run_id="run-dup")

    try:
        facade.start_run(instruction="抓取桌面方块", run_id="run-dup")
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("expected duplicate run_id to fail")


def test_backend_facade_get_run_returns_terminal_snapshot(app_config) -> None:
    runtime = build_runtime(app_config)
    facade = build_frontend_facade(runtime)

    accepted = facade.start_run(instruction="抓取桌面方块", run_id="run-terminal")
    terminal_snapshot = facade.get_run(run_id="run-terminal")

    assert accepted["run_id"] == "run-terminal"
    assert terminal_snapshot["event"] == "snapshot"
    assert terminal_snapshot["run"]["run_id"] == "run-terminal"


def test_backend_facade_build_error_returns_error_payload(app_config) -> None:
    runtime = build_runtime(app_config)
    facade = build_frontend_facade(runtime)

    payload = facade.build_error(code="RuntimeUnavailable", message="运行服务暂时不可用")

    assert payload == {
        "error": {
            "code": "RuntimeUnavailable",
            "message": "运行服务暂时不可用",
        }
    }
