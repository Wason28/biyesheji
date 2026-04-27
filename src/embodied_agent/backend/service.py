"""Runtime facade for the phase-3 backend layer."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Thread
from typing import TYPE_CHECKING, Any, Iterator
from uuid import uuid4

from ..decision.state import create_initial_state, ensure_agent_state, set_last_node_result
from ..execution.server import build_server
from ..perception.adapters import iter_mjpeg_stream
from ..perception.errors import UnsupportedProviderError
from ..shared.types import RunPhase, RuntimeEventName
from .contracts import (
    FrontendBootstrapPayload,
    FrontendConfigPayload,
    FrontendErrorPayload,
    FrontendRunAcceptedPayload,
    FrontendRunAPI,
    FrontendRunStatePayload,
    FrontendRuntimeAPI,
    FrontendToolsPayload,
)
from .presenters import (
    build_frontend_bootstrap,
    build_frontend_config_payload,
    build_frontend_run_api,
    build_frontend_run_error,
    build_frontend_run_snapshot,
    build_frontend_runtime_api,
    build_frontend_tools_payload,
)
from .run_registry import RunRegistry, as_state_payload

if TYPE_CHECKING:
    from ..app import Phase1Runtime


class RuntimeConfigError(ValueError):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(slots=True)
class FrontendRuntimeFacade:
    runtime: Phase1Runtime
    run_registry: RunRegistry = field(default_factory=RunRegistry)

    def get_bootstrap(self) -> FrontendBootstrapPayload:
        return build_frontend_bootstrap(self.runtime)

    def get_config(self) -> FrontendConfigPayload:
        return build_frontend_config_payload(self.runtime)

    def get_tools(self) -> FrontendToolsPayload:
        return build_frontend_tools_payload(self.runtime)

    def refresh_tools(self) -> FrontendToolsPayload:
        return build_frontend_tools_payload(self.runtime)

    def update_config(self, payload: dict[str, object]) -> FrontendConfigPayload:
        runtime_config = deepcopy(self.runtime.config)
        decision = payload.get("decision") if isinstance(payload.get("decision"), dict) else {}
        perception = payload.get("perception") if isinstance(payload.get("perception"), dict) else {}
        execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
        frontend = payload.get("frontend") if isinstance(payload.get("frontend"), dict) else {}
        root = payload if isinstance(payload, dict) else {}

        if "vision_model" in root:
            runtime_config.vision_model = str(root["vision_model"])

        if "provider" in decision:
            runtime_config.decision.llm_provider = str(decision["provider"])
        if "model" in decision:
            runtime_config.decision.llm_model = str(decision["model"])
        if "local_path" in decision:
            runtime_config.decision.llm_local_path = str(decision["local_path"])
        if "base_url" in decision:
            runtime_config.decision.llm_base_url = str(decision["base_url"])
        decision_api_key = decision.get("api_key")
        if isinstance(decision_api_key, str) and decision_api_key.strip():
            runtime_config.decision.llm_api_key = decision_api_key.strip()

        if "provider" in perception:
            runtime_config.perception.vlm_provider = str(perception["provider"])
        if "model" in perception:
            runtime_config.perception.vlm_model = str(perception["model"])
        if "camera_backend" in perception:
            runtime_config.perception.camera_backend = str(perception["camera_backend"])
        if "camera_device_id" in perception:
            runtime_config.perception.camera_device_id = str(perception["camera_device_id"])
        if "camera_frame_id" in perception:
            runtime_config.perception.camera_frame_id = str(perception["camera_frame_id"])
        if "camera_width" in perception:
            runtime_config.perception.camera_width = self._coerce_positive_int(perception["camera_width"], field_name="camera_width")
        if "camera_height" in perception:
            runtime_config.perception.camera_height = self._coerce_positive_int(perception["camera_height"], field_name="camera_height")
        if "camera_fps" in perception:
            runtime_config.perception.camera_fps = self._coerce_positive_float(perception["camera_fps"], field_name="camera_fps")
        if "camera_index" in perception:
            runtime_config.perception.camera_index = self._coerce_int(perception["camera_index"], field_name="camera_index")
        if "robot_state_backend" in perception:
            runtime_config.perception.robot_state_backend = str(perception["robot_state_backend"])
        if "robot_state_base_url" in perception:
            runtime_config.perception.robot_state_base_url = str(perception["robot_state_base_url"])
        if "robot_state_config_path" in perception:
            runtime_config.perception.robot_state_config_path = str(perception["robot_state_config_path"])
        if "robot_state_base_frame" in perception:
            runtime_config.perception.robot_state_base_frame = str(perception["robot_state_base_frame"])
        if "local_path" in perception:
            runtime_config.perception.vlm_local_path = str(perception["local_path"])
        if "base_url" in perception:
            runtime_config.perception.vlm_base_url = str(perception["base_url"])
        perception_api_key = perception.get("api_key")
        if isinstance(perception_api_key, str) and perception_api_key.strip():
            runtime_config.perception.vlm_api_key = perception_api_key.strip()

        if "model_path" in execution:
            runtime_config.execution.vla_model_path = str(execution["model_path"])
        if "home_joint_positions" in execution:
            home_joint_positions = execution["home_joint_positions"]
            if not isinstance(home_joint_positions, list) or not home_joint_positions:
                raise RuntimeConfigError(
                    code="InvalidHomeJointPositions",
                    message="home_joint_positions 必须是非空数值数组",
                )
            runtime_config.execution.home_joint_positions = [
                self._coerce_float(value, field_name=f"home_joint_positions[{index}]")
                for index, value in enumerate(home_joint_positions)
            ]
        if "home_pose" in execution and isinstance(execution["home_pose"], dict):
            runtime_config.execution.home_pose = dict(execution["home_pose"])
        if "adapter" in execution:
            runtime_config.execution.robot_adapter = str(execution["adapter"])
        if "robot_base_url" in execution:
            runtime_config.execution.robot_base_url = str(execution["robot_base_url"])
        if "robot_timeout_s" in execution:
            runtime_config.execution.robot_timeout_s = self._coerce_positive_float(execution["robot_timeout_s"], field_name="robot_timeout_s")
        if "telemetry_poll_timeout_s" in execution:
            runtime_config.execution.telemetry_poll_timeout_s = self._coerce_positive_float(
                execution["telemetry_poll_timeout_s"],
                field_name="telemetry_poll_timeout_s",
            )
        if "safety_require_precheck" in execution:
            runtime_config.execution.safety_require_precheck = bool(execution["safety_require_precheck"])
        if "robot_pythonpath" in execution:
            runtime_config.execution.robot_pythonpath = str(execution["robot_pythonpath"])
        if "safety_policy" in execution:
            runtime_config.execution.safety_policy = str(execution["safety_policy"])
        if "stop_mode" in execution:
            runtime_config.execution.stop_mode = str(execution["stop_mode"])

        if "port" in frontend:
            runtime_config.frontend.port = self._coerce_int(frontend["port"], field_name="port")
        if "max_iterations" in frontend:
            max_iterations = self._coerce_positive_int(frontend["max_iterations"], field_name="max_iterations")
            runtime_config.frontend.max_iterations = max_iterations
            runtime_config.decision.max_iterations = max_iterations
        if "speed_scale" in frontend:
            runtime_config.frontend.speed_scale = self._coerce_positive_float(frontend["speed_scale"], field_name="speed_scale")
        if "custom_models" in frontend and isinstance(frontend["custom_models"], list):
            runtime_config.frontend.custom_models = [
                {"id": str(m.get("id", "")), "api": str(m.get("api", "")), "url": str(m.get("url", ""))}
                for m in frontend["custom_models"]
                if isinstance(m, dict)
            ]

        try:
            new_perception = self.runtime.perception.__class__(runtime_config)
            new_execution = build_server(runtime_config)
            new_mcp_client = self.runtime.mcp_client.__class__(new_perception, new_execution)
            new_decision = type(self.runtime.decision).from_config(runtime_config, mcp_client=new_mcp_client)
        except UnsupportedProviderError as exc:
            raise RuntimeConfigError(code="InvalidPerceptionProvider", message=exc.message) from exc
        except ValueError as exc:
            raise RuntimeConfigError(code="InvalidDecisionProvider", message=str(exc)) from exc

        self.runtime.config = runtime_config
        self.runtime.perception = new_perception
        self.runtime.execution = new_execution
        self.runtime.mcp_client = new_mcp_client
        self.runtime.decision = new_decision
        return build_frontend_config_payload(self.runtime)

    def get_runtime_api(self) -> FrontendRuntimeAPI:
        return build_frontend_runtime_api(self.runtime)

    def run_instruction(self, *, instruction: str, run_id: str | None = None) -> FrontendRunAPI:
        resolved_run_id = run_id or f"run-{uuid4().hex[:8]}"
        return build_frontend_run_api(self.runtime, instruction=instruction, run_id=resolved_run_id)

    def start_run(self, *, instruction: str, run_id: str | None = None) -> FrontendRunAcceptedPayload:
        resolved_run_id = run_id or f"run-{uuid4().hex[:8]}"
        initial_state = create_initial_state(
            instruction,
            max_iterations=self.runtime.decision.deps.max_iterations,
        )
        initial_snapshot = build_frontend_run_snapshot(initial_state, run_id=resolved_run_id)
        self.run_registry.create_session(run_id=resolved_run_id, instruction=instruction)
        self.run_registry.publish(
            run_id=resolved_run_id,
            event="snapshot",
            phase="trigger",
            run=initial_snapshot,
            timestamp=str(initial_state["last_node_result"]["timestamp"]),
            terminal=False,
        )
        worker = Thread(
            target=self._run_worker,
            kwargs={
                "instruction": instruction,
                "run_id": resolved_run_id,
                "initial_state": initial_state,
            },
            daemon=True,
        )
        self.run_registry.attach_worker(resolved_run_id, worker)
        worker.start()
        return {
            "run_id": resolved_run_id,
            "status": "running",
            "snapshot_url": f"/api/v1/runtime/runs/{resolved_run_id}",
            "events_url": f"/api/v1/runtime/runs/{resolved_run_id}/events",
            "run": initial_snapshot,
        }

    def get_run(self, *, run_id: str) -> FrontendRunStatePayload:
        latest_event = self.run_registry.latest(run_id)
        return as_state_payload(latest_event)

    def stop_run(self, *, run_id: str) -> FrontendRunStatePayload:
        latest_event = self.run_registry.latest(run_id)
        if latest_event.terminal:
            return as_state_payload(latest_event)

        stop_reason = "user_requested_stop"
        stop_message = "任务已由用户手动结束。"
        self.run_registry.request_stop(run_id, reason=stop_reason)
        self._best_effort_emergency_stop(run_id=run_id, reason=stop_message)

        cancelled_run = dict(latest_event.run)
        cancelled_run["status"] = "cancelled"
        cancelled_run["current_phase"] = "final_status"
        cancelled_run["current_node"] = "final_status"
        cancelled_run["action_result"] = "failed"
        cancelled_run["assistant_response"] = stop_message
        cancelled_run["termination_reason"] = stop_reason
        cancelled_run["last_execution"] = {
            "status": "failed",
            "action_name": str(cancelled_run.get("selected_action", "")),
            "message": stop_message,
            "logs": ["stop_run: 用户在前端交互控制中心请求结束当前任务。"],
        }
        cancelled_run["final_report"] = {
            "goal": str(cancelled_run.get("user_instruction", "")),
            "status": "cancelled",
            "completed": False,
            "termination_reason": stop_reason,
            "assistant_response": stop_message,
            "remaining_tasks": [],
            "iteration_count": int(cancelled_run.get("iteration_count", 0) or 0),
            "last_execution": dict(cancelled_run.get("last_execution", {})),
            "memory_summary": dict(cancelled_run.get("memory_summary", {})),
            "observed_phases": [
                str(event.phase)
                for event in self.run_registry.iter_events(run_id, after_version=0)
            ],
        }
        timestamp = datetime.now(timezone.utc).isoformat()
        cancelled_run["last_node_result"] = {
            "node": "final_status",
            "status_code": 499,
            "message": stop_message,
            "metadata": {"stop_requested": True, "reason": stop_reason},
            "timestamp": timestamp,
        }
        published = self.run_registry.publish(
            run_id=run_id,
            event="run_completed",
            phase="final_status",
            run=cancelled_run,
            timestamp=timestamp,
            terminal=True,
        )
        return as_state_payload(published)

    def iter_run_events(self, *, run_id: str, after_version: int = 0) -> list[FrontendRunStatePayload]:
        return [
            as_state_payload(event)
            for event in self.run_registry.iter_events(run_id, after_version=after_version)
        ]

    def build_error(self, *, code: str, message: str) -> FrontendErrorPayload:
        return build_frontend_run_error(code=code, message=message)

    def iter_video_stream(
        self,
        *,
        fps: float | None = None,
        frame_limit: int | None = None,
        width: int | None = None,
        height: int | None = None,
        quality: int | None = None,
    ) -> Iterator[bytes]:
        resolved_fps = fps if fps and fps > 0 else float(self.runtime.config.perception.camera_fps or 10.0)
        return iter_mjpeg_stream(
            self.runtime.perception.camera,
            fps=resolved_fps,
            frame_limit=frame_limit,
            width=width,
            height=height,
            quality=quality or 80,
        )

    def _publish_state_event(
        self,
        *,
        run_id: str,
        state: dict[str, Any],
        phase: RunPhase,
        event: RuntimeEventName,
        timestamp: str,
        terminal: bool,
    ) -> None:
        snapshot = build_frontend_run_snapshot(state, run_id=run_id)
        self.run_registry.publish(
            run_id=run_id,
            event=event,
            phase=phase,
            run=snapshot,
            timestamp=timestamp,
            terminal=terminal,
        )

    def _build_phase_started_state(
        self,
        raw_state: dict[str, Any],
        *,
        phase: RunPhase,
        timestamp: str,
    ) -> dict[str, Any]:
        state = ensure_agent_state(raw_state, max_iterations=self.runtime.decision.deps.max_iterations)
        phase_state = dict(state)
        phase_state["current_phase"] = phase
        phase_state["last_node_result"] = {
            "node": phase,
            "status_code": 102,
            "message": f"{phase} 开始执行",
            "metadata": {"event": "phase_started"},
            "timestamp": timestamp,
        }
        return phase_state

    def _run_worker(
        self,
        *,
        instruction: str,
        run_id: str,
        initial_state: dict[str, object],
    ) -> None:
        try:
            final_state: dict[str, Any] | None = None
            for item in self.runtime.decision.graph.stream(initial_state, stream_mode="debug"):
                if self.run_registry.is_stop_requested(run_id):
                    return
                if not isinstance(item, dict):
                    continue
                event_type = str(item.get("type", ""))
                timestamp = str(item.get("timestamp", ""))
                payload = item.get("payload", {})
                if not isinstance(payload, dict):
                    continue
                phase = payload.get("name")
                if not isinstance(phase, str):
                    continue
                if event_type == "task":
                    input_state = payload.get("input", {})
                    if isinstance(input_state, dict):
                        if self.run_registry.is_stop_requested(run_id):
                            return
                        self._publish_state_event(
                            run_id=run_id,
                            state=self._build_phase_started_state(input_state, phase=phase, timestamp=timestamp),
                            phase=phase,
                            event="phase_started",
                            timestamp=timestamp,
                            terminal=False,
                        )
                    continue
                if event_type != "task_result":
                    continue

                result_state = payload.get("result", {})
                if not isinstance(result_state, dict):
                    continue
                if self.run_registry.is_stop_requested(run_id):
                    return
                final_state = result_state
                event_name: RuntimeEventName = "phase_completed"
                terminal = False
                if phase == "verification" and str(result_state.get("action_result", "")) == "failed":
                    event_name = "phase_failed"
                elif phase == "hri" and bool(dict(result_state.get("human_intervention", {})).get("required", False)):
                    event_name = "human_intervention_required"
                elif phase == "final_status":
                    event_name = "run_completed"
                    terminal = True
                self._publish_state_event(
                    run_id=run_id,
                    state=result_state,
                    phase=phase,
                    event=event_name,
                    timestamp=timestamp,
                    terminal=terminal,
                )

            if self.run_registry.is_stop_requested(run_id):
                return
            if final_state is not None and str(final_state.get("current_phase", "")) != "final_status":
                final_state = dict(final_state)
                final_state["termination_reason"] = final_state.get("termination_reason") or "stream_completed_without_terminal_phase"
                self._publish_state_event(
                    run_id=run_id,
                    state=final_state,
                    phase=str(final_state.get("current_phase", "trigger")),
                    event="run_completed",
                    timestamp=str(final_state.get("last_node_result", {}).get("timestamp", "")),
                    terminal=True,
                )
        except Exception as exc:
            if self.run_registry.is_stop_requested(run_id):
                return
            failed_state = dict(initial_state)
            failed_state["action_result"] = "failed"
            failed_state["termination_reason"] = "runtime_unavailable"
            failed_state["last_execution"] = {
                "status": "failed",
                "action_name": "",
                "message": "运行服务暂时不可用",
                "logs": [str(exc)],
            }
            failed_state = set_last_node_result(
                failed_state,
                node="final_status",
                status_code=500,
                message="运行服务暂时不可用",
                metadata={"error_type": exc.__class__.__name__},
            )
            failed_state["final_report"] = {
                "goal": instruction,
                "status": "failed",
                "completed": False,
                "termination_reason": "runtime_unavailable",
                "remaining_tasks": list(failed_state.get("task_queue", [])),
                "iteration_count": int(failed_state.get("iteration_count", 0)),
                "last_execution": dict(failed_state.get("last_execution", {})),
                "memory_summary": dict(failed_state.get("memory_summary", {})),
                "observed_phases": ["trigger", "final_status"],
            }
            self._publish_state_event(
                run_id=run_id,
                state=failed_state,
                phase="final_status",
                event="phase_failed",
                timestamp=str(failed_state["last_node_result"]["timestamp"]),
                terminal=True,
            )

    def _best_effort_emergency_stop(self, *, run_id: str, reason: str) -> None:
        del run_id
        execution_runtime = getattr(self.runtime.execution, "_runtime", None)
        adapter = getattr(execution_runtime, "adapter", None)
        if adapter is None:
            return
        try:
            adapter.emergency_stop(reason)
        except Exception:
            return

    @staticmethod
    def _coerce_int(value: object, *, field_name: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise RuntimeConfigError(code=f"Invalid{field_name.title()}", message=f"{field_name} 必须是整数") from exc

    @classmethod
    def _coerce_positive_int(cls, value: object, *, field_name: str) -> int:
        parsed = cls._coerce_int(value, field_name=field_name)
        if parsed <= 0:
            raise RuntimeConfigError(code=f"Invalid{field_name.title()}", message=f"{field_name} 必须大于 0")
        return parsed

    @staticmethod
    def _coerce_float(value: object, *, field_name: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise RuntimeConfigError(code=f"Invalid{field_name.title()}", message=f"{field_name} 必须是数字") from exc

    @staticmethod
    def _coerce_positive_float(value: object, *, field_name: str) -> float:
        parsed = FrontendRuntimeFacade._coerce_float(value, field_name=field_name)
        if parsed <= 0:
            raise RuntimeConfigError(code=f"Invalid{field_name.title()}", message=f"{field_name} 必须大于 0")
        return parsed


def build_frontend_facade(runtime: Phase1Runtime) -> FrontendRuntimeFacade:
    return FrontendRuntimeFacade(runtime=runtime)
