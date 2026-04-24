from time import monotonic, sleep

from embodied_agent.app import build_runtime
from embodied_agent.backend.service import build_frontend_facade
from embodied_agent.decision.graph import DecisionEngine
from embodied_agent.execution.server import MockMCPServer
from embodied_agent.perception.server import PerceptionMCPServer


def _wait_for_terminal_events(facade, run_id: str, timeout_s: float = 5.0):
    start = monotonic()
    while monotonic() - start < timeout_s:
        events = facade.iter_run_events(run_id=run_id, after_version=0)
        if any(event["terminal"] for event in events):
            return events
        sleep(0.05)
    raise AssertionError(f"run {run_id} did not reach terminal state in time")


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
                "metadata": {"error_code": "ExecutionUnavailable", "retryable": True},
            }
        return super().call_tool(tool_name, arguments)


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
    assert accepted["run"]["current_phase"] == "trigger"
    assert snapshot["version"] >= 1
    assert snapshot["event"] in {"snapshot", "phase_started", "phase_completed", "run_completed"}


def test_backend_facade_iter_run_events_returns_blueprint_phase_events(app_config) -> None:
    runtime = build_runtime(app_config)
    facade = build_frontend_facade(runtime)

    facade.start_run(instruction="抓取桌面方块", run_id="run-events")
    events = _wait_for_terminal_events(facade, "run-events")

    assert events
    assert events[0]["event"] == "snapshot"
    assert events[-1]["event"] == "run_completed"
    assert events[-1]["terminal"] is True
    assert all(event["version"] >= 1 for event in events)
    completed_phases = [event["phase"] for event in events if event["event"] in {"phase_completed", "run_completed"}]
    assert completed_phases == [
        "trigger",
        "nlu",
        "sensory",
        "assessment",
        "task_planning",
        "pre_feedback",
        "motion_control",
        "verification",
        "success_notice",
        "goal_check",
        "final_status",
    ]


def test_backend_facade_iter_run_events_covers_failure_recovery_path(app_config) -> None:
    runtime = build_runtime(app_config)
    perception = PerceptionMCPServer(runtime.config)
    execution = _FailingExecutionServer()
    client = runtime.mcp_client.__class__(perception, execution)
    runtime = runtime.__class__(
        config=runtime.config,
        perception=perception,
        execution=execution,
        decision=DecisionEngine.from_config(runtime.config, mcp_client=client),
        mcp_client=client,
    )
    facade = build_frontend_facade(runtime)

    facade.start_run(instruction="抓取桌面方块", run_id="run-recovery")
    events = _wait_for_terminal_events(facade, "run-recovery")

    phases = [event["phase"] for event in events]
    assert "error_diagnosis" in phases
    assert "hri" in phases
    assert "compensation" in phases
    assert phases.count("motion_control") >= 2
    assert any(event["event"] == "human_intervention_required" for event in events)
    assert events[-1]["phase"] == "final_status"
    assert events[-1]["run"]["status"] == "failed"
    assert events[-1]["run"]["termination_reason"] == "compensation_exhausted"


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
    _wait_for_terminal_events(facade, "run-terminal")
    terminal_snapshot = facade.get_run(run_id="run-terminal")

    assert accepted["run_id"] == "run-terminal"
    assert terminal_snapshot["event"] == "run_completed"
    assert terminal_snapshot["run"]["run_id"] == "run-terminal"
    assert terminal_snapshot["run"]["current_phase"] == "final_status"
    assert terminal_snapshot["terminal"] is True


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
