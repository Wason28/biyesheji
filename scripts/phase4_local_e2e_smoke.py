from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

BACKEND_BASE = "http://127.0.0.1:7861/api/v1/runtime"
OUTPUT_PATH = Path("docs/records/phase4_local_e2e_smoke_result_2026-04-21.json")
RUN_ID = "run-local-e2e-smoke"


def request_json(path: str, *, method: str = "GET", payload: dict[str, object] | None = None) -> dict[str, object]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(f"{BACKEND_BASE}{path}", data=data, headers=headers, method=method)
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    bootstrap = request_json("/bootstrap")
    config = request_json("/config")
    tools = request_json("/tools")
    updated_config = request_json(
        "/config",
        method="PUT",
        payload={
            "decision": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "decision-secret",
                "local_path": "/models/decision",
            },
            "perception": {
                "provider": "openai_gpt4o",
                "model": "gpt-4o",
                "api_key": "perception-secret",
                "local_path": "/models/perception",
            },
            "execution": {
                "home_pose": {"x": 0.11, "y": 0.22, "z": 0.33},
            },
            "frontend": {"max_iterations": 7, "speed_scale": 0.7, "port": 7861},
        },
    )
    refreshed_tools = request_json("/tools/refresh", method="POST")
    accepted = request_json(
        "/runs",
        method="POST",
        payload={"instruction": "抓取桌面方块", "run_id": RUN_ID},
    )
    time.sleep(0.2)
    snapshot = request_json(accepted["snapshot_url"].removeprefix("/api/v1/runtime"))
    events_request = Request(f"http://127.0.0.1:7861{accepted['events_url']}")
    with urlopen(events_request) as response:
        events_text = response.read().decode("utf-8")

    result = {
        "bootstrap_status_fields": len(bootstrap["status_fields"]),
        "config_keys": list(config.keys()),
        "tools_count": len(tools["tools"]),
        "refreshed_tools_count": len(refreshed_tools["tools"]),
        "updated_config": updated_config,
        "accepted_run_id": accepted["run_id"],
        "snapshot_status": snapshot["run"]["status"],
        "snapshot_terminal": snapshot["terminal"],
        "events_contains_snapshot": "event: snapshot" in events_text,
        "events_preview": events_text[:240],
    }
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
