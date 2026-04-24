"""In-memory run registry for async run snapshots and stream events."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Condition, RLock, Thread
from time import monotonic
from typing import TYPE_CHECKING

from .contracts import FrontendRunSnapshot, FrontendRunStatePayload, RunPhase, RuntimeEventName

if TYPE_CHECKING:
    from collections.abc import Iterator


class RunConflictError(ValueError):
    pass


@dataclass(slots=True)
class RunEvent:
    version: int
    event: RuntimeEventName
    phase: RunPhase
    run: FrontendRunSnapshot
    terminal: bool
    timestamp: str


@dataclass(slots=True)
class RunSession:
    run_id: str
    instruction: str
    events: list[RunEvent] = field(default_factory=list)
    terminal: bool = False
    terminal_at: float | None = None
    worker: Thread | None = None
    condition: Condition = field(default_factory=lambda: Condition(RLock()))


class RunRegistry:
    def __init__(
        self,
        *,
        retention_seconds: float = 900.0,
        max_terminal_sessions: int = 100,
    ) -> None:
        self._lock = RLock()
        self._sessions: dict[str, RunSession] = {}
        self._retention_seconds = max(0.0, float(retention_seconds))
        self._max_terminal_sessions = max(1, int(max_terminal_sessions))

    def create_session(self, *, run_id: str, instruction: str) -> RunSession:
        with self._lock:
            self._sweep_locked()
            if run_id in self._sessions:
                raise RunConflictError(f"run '{run_id}' already exists")
            session = RunSession(run_id=run_id, instruction=instruction)
            self._sessions[run_id] = session
            return session

    def get_session(self, run_id: str) -> RunSession:
        with self._lock:
            self._sweep_locked()
            try:
                return self._sessions[run_id]
            except KeyError as exc:
                raise KeyError(f"run '{run_id}' not found") from exc

    def attach_worker(self, run_id: str, worker: Thread) -> None:
        session = self.get_session(run_id)
        with session.condition:
            session.worker = worker

    def publish(
        self,
        run_id: str,
        *,
        event: RuntimeEventName,
        phase: RunPhase,
        run: FrontendRunSnapshot,
        timestamp: str,
        terminal: bool,
    ) -> RunEvent:
        session = self.get_session(run_id)
        with session.condition:
            next_event = RunEvent(
                version=len(session.events) + 1,
                event=event,
                phase=phase,
                run=dict(run),
                terminal=terminal,
                timestamp=timestamp,
            )
            session.events.append(next_event)
            session.terminal = terminal
            if terminal:
                session.terminal_at = monotonic()
            session.condition.notify_all()
        with self._lock:
            self._sweep_locked()
        return next_event

    def latest(self, run_id: str) -> RunEvent:
        session = self.get_session(run_id)
        with session.condition:
            if not session.events:
                raise KeyError(f"run '{run_id}' has no events")
            return session.events[-1]

    def iter_events(
        self,
        run_id: str,
        *,
        after_version: int = 0,
        wait_timeout: float = 0.25,
    ) -> Iterator[RunEvent]:
        session = self.get_session(run_id)
        with session.condition:
            if len(session.events) <= after_version and not session.terminal:
                session.condition.wait(timeout=wait_timeout)
            events = [event for event in session.events if event.version > after_version]
        for event in events:
            yield event

    def cleanup(self) -> list[str]:
        with self._lock:
            return self._sweep_locked()

    def _sweep_locked(self) -> list[str]:
        now = monotonic()
        removed_run_ids: list[str] = []
        expired_run_ids = [
            run_id
            for run_id, session in self._sessions.items()
            if session.terminal
            and session.terminal_at is not None
            and now - session.terminal_at > self._retention_seconds
        ]
        for run_id in expired_run_ids:
            self._sessions.pop(run_id, None)
            removed_run_ids.append(run_id)

        terminal_sessions = sorted(
            (
                (run_id, session.terminal_at or now)
                for run_id, session in self._sessions.items()
                if session.terminal
            ),
            key=lambda item: item[1],
        )
        overflow = len(terminal_sessions) - self._max_terminal_sessions
        if overflow > 0:
            for run_id, _ in terminal_sessions[:overflow]:
                self._sessions.pop(run_id, None)
                removed_run_ids.append(run_id)
        return removed_run_ids


def as_state_payload(event: RunEvent) -> FrontendRunStatePayload:
    return {
        "run": event.run,
        "version": event.version,
        "terminal": event.terminal,
        "event": event.event,
        "phase": event.phase,
        "timestamp": event.timestamp,
    }
