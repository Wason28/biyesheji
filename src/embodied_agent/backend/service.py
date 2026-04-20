"""Runtime facade for the phase-3 backend layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Thread
from typing import TYPE_CHECKING
from uuid import uuid4

from ..decision.state import create_initial_state, set_last_node_result
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
from .run_registry import RunRegistry

if TYPE_CHECKING:
    from ..app import Phase1Runtime


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
        self.run_registry.publish(run_id=resolved_run_id, run=initial_snapshot, terminal=False)
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
        return {
            "run": latest_event.run,
            "version": latest_event.version,
            "terminal": latest_event.terminal,
        }

    def iter_run_events(self, *, run_id: str, after_version: int = 0) -> list[FrontendRunStatePayload]:
        return [
            {
                "run": event.run,
                "version": event.version,
                "terminal": event.terminal,
            }
            for event in self.run_registry.iter_events(run_id, after_version=after_version)
        ]

    def build_error(self, *, code: str, message: str) -> FrontendErrorPayload:
        return build_frontend_run_error(code=code, message=message)

    def _run_worker(
        self,
        *,
        instruction: str,
        run_id: str,
        initial_state: dict[str, object],
    ) -> None:
        try:
            final_state = self.runtime.decision.invoke(instruction, state=initial_state)
        except Exception as exc:
            failed_state = dict(initial_state)
            failed_state["action_result"] = "failed"
            failed_state["last_execution"] = {
                "status": "failed",
                "action_name": "",
                "message": "运行服务暂时不可用",
                "logs": [str(exc)],
            }
            failed_state = set_last_node_result(
                failed_state,
                node="runtime",
                status_code=500,
                message="运行服务暂时不可用",
                metadata={"error_type": exc.__class__.__name__},
            )
            final_snapshot = build_frontend_run_snapshot(failed_state, run_id=run_id)
        else:
            final_snapshot = build_frontend_run_snapshot(final_state, run_id=run_id)
        self.run_registry.publish(run_id=run_id, run=final_snapshot, terminal=True)


def build_frontend_facade(runtime: Phase1Runtime) -> FrontendRuntimeFacade:
    return FrontendRuntimeFacade(runtime=runtime)
