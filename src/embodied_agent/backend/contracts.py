"""Frontend-facing contracts for the phase-3 backend layer."""

from __future__ import annotations

from typing import TypedDict

from ..shared.types import (
    FrontendBootstrapPayload,
    FrontendConfigPayload,
    FrontendErrorPayload,
    FrontendRunAPI,
    FrontendRunAcceptedPayload,
    FrontendRunSnapshot,
    FrontendRunStatePayload,
    FrontendToolDescriptor,
    RunPhase,
    RunStatus,
    RuntimeEventName,
)


class FrontendToolsPayload(TypedDict):
    tools: list[FrontendToolDescriptor]


class FrontendRuntimeAPI(TypedDict):
    bootstrap: FrontendBootstrapPayload
    config: FrontendConfigPayload


__all__ = [
    "FrontendBootstrapPayload",
    "FrontendConfigPayload",
    "FrontendErrorPayload",
    "FrontendRunAPI",
    "FrontendRunAcceptedPayload",
    "FrontendRunSnapshot",
    "FrontendRunStatePayload",
    "FrontendRuntimeAPI",
    "FrontendToolDescriptor",
    "FrontendToolsPayload",
    "RunPhase",
    "RunStatus",
    "RuntimeEventName",
]
