from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def default_output_path() -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d")
    return Path(f"docs/records/phase4_p0_real_smoke_result_{stamp}.json")


def request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    query: dict[str, object] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    query_string = f"?{urlencode(query)}" if query else ""
    data = None
    headers = {"Accept": "*/*"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
    request_obj = Request(f"{base_url}{path}{query_string}", data=data, headers=headers, method=method)
    try:
        with urlopen(request_obj, timeout=10) as response:
            return int(response.status), dict(response.headers.items()), response.read()
    except HTTPError as exc:
        return int(exc.code), dict(exc.headers.items()) if exc.headers else {}, exc.read()


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    query: dict[str, object] | None = None,
) -> tuple[int, dict[str, str], dict[str, object]]:
    status, headers, body = request(base_url, path, method=method, payload=payload, query=query)
    return status, headers, json.loads(body.decode("utf-8"))


def wait_for_terminal_snapshot(base_url: str, snapshot_url: str, timeout_s: float) -> dict[str, object]:
    deadline = time.monotonic() + timeout_s
    last_snapshot: dict[str, object] | None = None
    path = snapshot_url.removeprefix("/api/v1/runtime")
    while time.monotonic() < deadline:
        _, _, payload = request_json(base_url, path)
        last_snapshot = payload
        if bool(payload.get("terminal")):
            return payload
        time.sleep(0.25)
    raise TimeoutError(f"run did not reach terminal state within {timeout_s:.1f}s: {last_snapshot}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P0 real-chain smoke for embodied-agent runtime")
    parser.add_argument("--base-url", default="http://127.0.0.1:7864/api/v1/runtime", help="runtime API base URL")
    parser.add_argument("--output", default=str(default_output_path()), help="JSON result output path")
    parser.add_argument("--run-id", default="run-p0-real-smoke", help="run id for the smoke")
    parser.add_argument("--instruction", default="回到安全位置", help="instruction to execute")
    parser.add_argument("--timeout", type=float, default=20.0, help="terminal snapshot timeout")
    parser.add_argument("--expect-camera-backend", default="", help="optional expected config.perception.camera_backend")
    parser.add_argument("--expect-robot-state-backend", default="", help="optional expected perception robot_state_backend")
    parser.add_argument("--expect-robot-adapter", default="", help="optional expected config.execution.adapter")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    bootstrap_status, _, bootstrap = request_json(args.base_url, "/bootstrap")
    config_status, _, config = request_json(args.base_url, "/config")
    tools_status, _, tools = request_json(args.base_url, "/tools")

    stream_status, stream_headers, stream_body = request(
        args.base_url,
        "/video-stream",
        query={"frame_limit": 1, "fps": 2, "width": 320, "height": 240, "quality": 60},
    )

    accepted_status, _, accepted = request_json(
        args.base_url,
        "/runs",
        method="POST",
        payload={"instruction": args.instruction, "run_id": args.run_id},
    )
    terminal_snapshot = wait_for_terminal_snapshot(args.base_url, str(accepted["snapshot_url"]), args.timeout)
    events_status, _, events_payload = request(
        f"{args.base_url.removesuffix('/api/v1/runtime')}",
        str(accepted["events_url"]),
    )
    events_text = events_payload.decode("utf-8", errors="replace")

    config_perception = config.get("perception", {}) if isinstance(config.get("perception"), dict) else {}
    config_execution = config.get("execution", {}) if isinstance(config.get("execution"), dict) else {}
    bootstrap_profile = (
        bootstrap.get("execution_runtime_profile", {})
        if isinstance(bootstrap.get("execution_runtime_profile"), dict)
        else {}
    )

    checks = {
        "bootstrap_ok": bootstrap_status == 200,
        "config_ok": config_status == 200,
        "tools_ok": tools_status == 200,
        "video_stream_ok": stream_status == 200 and b"--frame" in stream_body,
        "events_ok": events_status == 200 and "event: snapshot" in events_text,
        "run_accepted": accepted_status == 202,
        "run_terminal": bool(terminal_snapshot.get("terminal")),
    }

    if args.expect_camera_backend:
        checks["camera_backend_match"] = config_perception.get("camera_backend") == args.expect_camera_backend
    if args.expect_robot_state_backend:
        checks["robot_state_backend_match"] = (
            config_perception.get("robot_state_backend") == args.expect_robot_state_backend
        )
    if args.expect_robot_adapter:
        checks["robot_adapter_match"] = config_execution.get("adapter") == args.expect_robot_adapter

    result = {
        "base_url": args.base_url,
        "run_id": args.run_id,
        "instruction": args.instruction,
        "checks": checks,
        "config_summary": {
            "camera_backend": config_perception.get("camera_backend"),
            "camera_device_id": config_perception.get("camera_device_id"),
            "robot_state_backend": config_perception.get("robot_state_backend"),
            "robot_state_base_url": config_perception.get("robot_state_base_url"),
            "robot_state_config_path": config_perception.get("robot_state_config_path"),
            "execution_adapter": config_execution.get("adapter"),
            "execution_robot_base_url": config_execution.get("robot_base_url"),
            "safety_require_precheck": config_execution.get("safety_require_precheck"),
        },
        "runtime_profile": bootstrap_profile,
        "tools_count": len(tools.get("tools", [])) if isinstance(tools.get("tools"), list) else 0,
        "video_stream": {
            "status": stream_status,
            "content_type": stream_headers.get("Content-Type", ""),
            "preview_len": len(stream_body),
        },
        "accepted": accepted,
        "terminal_snapshot": terminal_snapshot,
        "events_preview": events_text[:400],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not all(checks.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
