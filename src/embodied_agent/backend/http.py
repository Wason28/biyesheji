"""Minimal WSGI HTTP transport for the phase-3 backend contracts."""

from __future__ import annotations

import argparse
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIServer, make_server

from .service import FrontendRuntimeFacade, build_frontend_facade

if TYPE_CHECKING:
    from wsgiref.types import StartResponse, WSGIApplication, WSGIEnvironment

    from ..app import Phase1Runtime


JSON_HEADERS = [("Content-Type", "application/json; charset=utf-8")]
SSE_HEADERS = [
    ("Content-Type", "text/event-stream; charset=utf-8"),
    ("Cache-Control", "no-cache"),
]


class HTTPRequestError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(slots=True)
class BackendHTTPApp:
    facade: FrontendRuntimeFacade

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> list[bytes]:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", ""))
        try:
            if method == "GET" and path == "/api/v1/runtime/bootstrap":
                return self._respond(start_response, 200, self.facade.get_bootstrap())
            if method == "GET" and path == "/api/v1/runtime/config":
                return self._respond(start_response, 200, self.facade.get_config())
            if method == "GET" and path == "/api/v1/runtime/tools":
                return self._respond(start_response, 200, self.facade.get_tools())
            if method == "POST" and path == "/api/v1/runtime/tools/refresh":
                return self._respond(start_response, 200, self.facade.refresh_tools())
            if method == "PUT" and path == "/api/v1/runtime/config":
                payload = self._read_json_body(environ)
                return self._respond(start_response, 200, self.facade.update_config(payload))
            if method == "POST" and path == "/api/v1/runtime/run":
                payload = self._read_json_body(environ)
                instruction = self._extract_instruction(payload)
                run_id = self._extract_optional_run_id(payload)
                return self._respond(
                    start_response,
                    200,
                    self.facade.run_instruction(instruction=instruction, run_id=run_id),
                )
            if method == "POST" and path == "/api/v1/runtime/runs":
                payload = self._read_json_body(environ)
                instruction = self._extract_instruction(payload)
                run_id = self._extract_optional_run_id(payload)
                return self._respond(
                    start_response,
                    202,
                    self.facade.start_run(instruction=instruction, run_id=run_id),
                )
            run_id = self._match_run_snapshot_path(path)
            if method == "GET" and run_id is not None:
                return self._respond(start_response, 200, self.facade.get_run(run_id=run_id))
            run_id = self._match_run_events_path(path)
            if method == "GET" and run_id is not None:
                after_version = self._extract_after_version(environ)
                events = self.facade.iter_run_events(run_id=run_id, after_version=after_version)
                return self._respond_sse(start_response, events)
            raise HTTPRequestError(
                status_code=404,
                code="EndpointNotFound",
                message=f"unsupported route: {method} {path}",
            )
        except KeyError:
            return self._respond_error(start_response, 404, code="RunNotFound", message="run_id 不存在")
        except ValueError as exc:
            return self._respond_error(start_response, 409, code="RunAlreadyExists", message=str(exc))
        except HTTPRequestError as exc:
            return self._respond_error(start_response, exc.status_code, code=exc.code, message=exc.message)
        except Exception:
            return self._respond_error(
                start_response,
                500,
                code="RuntimeUnavailable",
                message="运行服务暂时不可用",
            )

    def _read_json_body(self, environ: WSGIEnvironment) -> dict[str, Any]:
        try:
            content_length = int(environ.get("CONTENT_LENGTH", "0") or "0")
        except ValueError as exc:
            raise HTTPRequestError(
                status_code=400,
                code="InvalidContentLength",
                message="请求体长度无效",
            ) from exc
        body_stream = environ.get("wsgi.input", io.BytesIO())
        raw_body = body_stream.read(content_length) if content_length > 0 else b""
        if not raw_body:
            raise HTTPRequestError(
                status_code=400,
                code="InvalidRequest",
                message="请求体必须包含 instruction 字段",
            )
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPRequestError(
                status_code=400,
                code="InvalidJSON",
                message="请求体不是合法 JSON",
            ) from exc
        if not isinstance(payload, dict):
            raise HTTPRequestError(
                status_code=400,
                code="InvalidRequest",
                message="请求体必须是 JSON 对象",
            )
        return payload

    @staticmethod
    def _extract_instruction(payload: dict[str, Any]) -> str:
        instruction = payload.get("instruction")
        if not isinstance(instruction, str) or not instruction.strip():
            raise HTTPRequestError(
                status_code=400,
                code="InvalidInstruction",
                message="instruction 必须是非空字符串",
            )
        return instruction.strip()

    @staticmethod
    def _extract_optional_run_id(payload: dict[str, Any]) -> str | None:
        run_id = payload.get("run_id")
        if run_id is None:
            return None
        if not isinstance(run_id, str) or not run_id.strip():
            raise HTTPRequestError(
                status_code=400,
                code="InvalidRunId",
                message="run_id 必须是非空字符串",
            )
        return run_id.strip()

    def _respond_error(
        self,
        start_response: StartResponse,
        status_code: int,
        *,
        code: str,
        message: str,
    ) -> list[bytes]:
        payload = self.facade.build_error(code=code, message=message)
        return self._respond(start_response, status_code, payload)

    @staticmethod
    def _respond(start_response: StartResponse, status_code: int, payload: Any) -> list[bytes]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = [*JSON_HEADERS, ("Content-Length", str(len(body)))]
        start_response(f"{status_code} {BackendHTTPApp._status_text(status_code)}", headers)
        return [body]

    @staticmethod
    def _respond_sse(start_response: StartResponse, events: list[dict[str, Any]]) -> list[bytes]:
        body = b"".join(BackendHTTPApp._encode_sse_event(event) for event in events)
        headers = [*SSE_HEADERS, ("Content-Length", str(len(body)))]
        start_response("200 OK", headers)
        return [body]

    @staticmethod
    def _encode_sse_event(event: dict[str, Any]) -> bytes:
        version = int(event.get("version", 0))
        event_name = str(event.get("event", "snapshot"))
        payload = json.dumps(event, ensure_ascii=False)
        return f"id: {version}\nevent: {event_name}\ndata: {payload}\n\n".encode("utf-8")

    @staticmethod
    def _match_run_snapshot_path(path: str) -> str | None:
        parts = path.strip("/").split("/")
        if len(parts) == 5 and parts[:4] == ["api", "v1", "runtime", "runs"] and parts[4]:
            return parts[4]
        return None

    @staticmethod
    def _match_run_events_path(path: str) -> str | None:
        parts = path.strip("/").split("/")
        if len(parts) == 6 and parts[:4] == ["api", "v1", "runtime", "runs"] and parts[4] and parts[5] == "events":
            return parts[4]
        return None

    @staticmethod
    def _extract_after_version(environ: WSGIEnvironment) -> int:
        last_event_id = str(environ.get("HTTP_LAST_EVENT_ID", "")).strip()
        if last_event_id:
            try:
                value = int(last_event_id)
            except ValueError as exc:
                raise HTTPRequestError(
                    status_code=400,
                    code="InvalidLastEventId",
                    message="Last-Event-ID 必须是非负整数",
                ) from exc
            if value < 0:
                raise HTTPRequestError(
                    status_code=400,
                    code="InvalidLastEventId",
                    message="Last-Event-ID 必须是非负整数",
                )
            return value
        query = parse_qs(str(environ.get("QUERY_STRING", "")))
        after_version = query.get("after_version", ["0"])[0]
        try:
            value = int(after_version or "0")
        except ValueError as exc:
            raise HTTPRequestError(
                status_code=400,
                code="InvalidAfterVersion",
                message="after_version 必须是非负整数",
            ) from exc
        if value < 0:
            raise HTTPRequestError(
                status_code=400,
                code="InvalidAfterVersion",
                message="after_version 必须是非负整数",
            )
        return value

    @staticmethod
    def _status_text(status_code: int) -> str:
        return {
            200: "OK",
            202: "Accepted",
            400: "Bad Request",
            404: "Not Found",
            409: "Conflict",
            500: "Internal Server Error",
        }.get(status_code, "OK")


def build_http_app(*, facade: FrontendRuntimeFacade) -> BackendHTTPApp:
    return BackendHTTPApp(facade=facade)


def build_http_app_from_runtime(runtime: Phase1Runtime) -> BackendHTTPApp:
    return build_http_app(facade=build_frontend_facade(runtime))


def build_http_app_from_config(config_path: str | Path) -> BackendHTTPApp:
    from ..app import build_runtime_from_config

    return build_http_app_from_runtime(build_runtime_from_config(config_path))


def serve_http_app(
    app: WSGIApplication,
    *,
    host: str = "127.0.0.1",
    port: int = 7860,
    server_factory: Callable[..., WSGIServer] = make_server,
) -> WSGIServer:
    return server_factory(host, port, app)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the phase-3 backend HTTP skeleton")
    parser.add_argument("--config", type=str, default=None, help="配置文件路径")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="HTTP 服务监听地址")
    parser.add_argument("--port", type=int, default=7860, help="HTTP 服务监听端口")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.config:
        app = build_http_app_from_config(args.config)
    else:
        from ..app import build_runtime

        app = build_http_app_from_runtime(build_runtime())
    server = serve_http_app(app, host=args.host, port=args.port)
    print(f"http server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
