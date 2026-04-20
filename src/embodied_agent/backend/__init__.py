"""Backend-facing contracts and facade helpers."""

from .contracts import (
    FrontendBootstrapPayload,
    FrontendConfigPayload,
    FrontendErrorPayload,
    FrontendRunAcceptedPayload,
    FrontendRunAPI,
    FrontendRunSnapshot,
    FrontendRunStatePayload,
    FrontendRuntimeAPI,
    FrontendToolDescriptor,
    FrontendToolsPayload,
    RunStatus,
)
from .presenters import (
    FRONTEND_STATUS_FIELDS,
    build_frontend_bootstrap,
    build_frontend_config_payload,
    build_frontend_run_api,
    build_frontend_run_error,
    build_frontend_run_snapshot,
    build_frontend_runtime_api,
    build_frontend_tools_payload,
)
from .http import BackendHTTPApp, build_http_app, build_http_app_from_config, build_http_app_from_runtime, serve_http_app
from .run_registry import RunEvent, RunRegistry
from .service import FrontendRuntimeFacade, build_frontend_facade

__all__ = [
    "FRONTEND_STATUS_FIELDS",
    "BackendHTTPApp",
    "FrontendBootstrapPayload",
    "FrontendConfigPayload",
    "FrontendErrorPayload",
    "FrontendRunAcceptedPayload",
    "FrontendRunAPI",
    "FrontendRunSnapshot",
    "FrontendRunStatePayload",
    "FrontendRuntimeAPI",
    "FrontendRuntimeFacade",
    "FrontendToolDescriptor",
    "FrontendToolsPayload",
    "RunEvent",
    "RunRegistry",
    "RunStatus",
    "build_frontend_bootstrap",
    "build_frontend_config_payload",
    "build_frontend_facade",
    "build_http_app",
    "build_http_app_from_config",
    "build_http_app_from_runtime",
    "build_frontend_run_api",
    "build_frontend_run_error",
    "build_frontend_run_snapshot",
    "build_frontend_runtime_api",
    "build_frontend_tools_payload",
    "serve_http_app",
]
