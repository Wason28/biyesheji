"""Interactive collection guide for Hanoi-style single-step demonstrations."""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import queue
import select
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from embodied_agent.perception.adapters import build_camera_adapter, build_robot_state_adapter
from embodied_agent.perception.config import PerceptionRuntimeConfig, build_perception_runtime_config
from embodied_agent.shared.config import load_config


PEG_NAMES = ("A", "B", "C")
DEFAULT_LOCAL_ROBOT_CONFIG = Path("lerobot_configs/so101_follower.local.yaml")
RING_SIZES = {
    "red_large": 3,
    "yellow_medium": 2,
    "pink_small": 1,
}
RING_LABELS = {
    "red_large": "红色大圆环",
    "yellow_medium": "黄色中圆环",
    "pink_small": "粉色小圆环",
}
PEG_LABELS = {
    "A": "A柱",
    "B": "B柱",
    "C": "C柱",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_session_dir() -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d")
    return Path("docs/records") / f"hanoi_collection_session_{stamp}"


def _default_dataset_repo_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"local/hanoi_ring_atomic_{stamp}"


def _discover_lerobot_pythonpath() -> str:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "src" / "lerobot"
        if candidate.is_dir():
            return str(candidate.parent)
    return ""


@dataclass(frozen=True, slots=True)
class CollectionTask:
    ring_key: str
    target_peg: str

    @property
    def prompt(self) -> str:
        return f"把{RING_LABELS[self.ring_key]}放到{PEG_LABELS[self.target_peg]}"

    @property
    def short_name(self) -> str:
        return f"{self.ring_key}_to_{self.target_peg}"


@dataclass(frozen=True, slots=True)
class StateTemplate:
    template_id: str
    pegs: dict[str, tuple[str, ...]]

    def source_peg_for(self, ring_key: str) -> str | None:
        for peg_name, stack in self.pegs.items():
            if ring_key in stack:
                return peg_name
        return None

    def top_ring(self, peg_name: str) -> str | None:
        stack = self.pegs.get(peg_name, ())
        if not stack:
            return None
        return stack[-1]

    def is_accessible(self, ring_key: str) -> bool:
        source_peg = self.source_peg_for(ring_key)
        if source_peg is None:
            return False
        return self.top_ring(source_peg) == ring_key

    def can_place(self, ring_key: str, target_peg: str) -> bool:
        source_peg = self.source_peg_for(ring_key)
        if source_peg is None or source_peg == target_peg:
            return False
        target_top = self.top_ring(target_peg)
        if target_top is None:
            return True
        return RING_SIZES[target_top] > RING_SIZES[ring_key]

    def supports(self, task: CollectionTask) -> bool:
        return self.is_accessible(task.ring_key) and self.can_place(task.ring_key, task.target_peg)

    def render(self) -> str:
        parts: list[str] = []
        for peg_name in PEG_NAMES:
            stack = self.pegs.get(peg_name, ())
            if not stack:
                parts.append(f"{PEG_LABELS[peg_name]}: 空")
                continue
            labels = " -> ".join(RING_LABELS[item] for item in stack)
            parts.append(f"{PEG_LABELS[peg_name]}: {labels}")
        return " | ".join(parts)


@dataclass(frozen=True, slots=True)
class PlanItem:
    index: int
    group_index: int
    item_in_group: int
    task: CollectionTask
    template: StateTemplate

    @property
    def source_peg(self) -> str:
        source = self.template.source_peg_for(self.task.ring_key)
        if source is None:
            raise ValueError(f"template {self.template.template_id} missing ring {self.task.ring_key}")
        return source

    def to_payload(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "group_index": self.group_index,
            "item_in_group": self.item_in_group,
            "task_prompt": self.task.prompt,
            "task_name": self.task.short_name,
            "target_ring": RING_LABELS[self.task.ring_key],
            "target_peg": PEG_LABELS[self.task.target_peg],
            "source_peg": PEG_LABELS[self.source_peg],
            "template_id": self.template.template_id,
            "placement": self.template.render(),
        }


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    message: str
    details: dict[str, Any]


DEFAULT_TASKS = [
    CollectionTask("pink_small", "A"),
    CollectionTask("pink_small", "B"),
    CollectionTask("pink_small", "C"),
    CollectionTask("yellow_medium", "A"),
    CollectionTask("yellow_medium", "B"),
    CollectionTask("yellow_medium", "C"),
    CollectionTask("red_large", "A"),
    CollectionTask("red_large", "B"),
    CollectionTask("red_large", "C"),
]


DEFAULT_TEMPLATES = [
    StateTemplate("S01", {"A": ("red_large", "yellow_medium", "pink_small"), "B": (), "C": ()}),
    StateTemplate("S02", {"A": (), "B": ("red_large", "yellow_medium", "pink_small"), "C": ()}),
    StateTemplate("S03", {"A": (), "B": (), "C": ("red_large", "yellow_medium", "pink_small")}),
    StateTemplate("S04", {"A": ("red_large", "yellow_medium"), "B": ("pink_small",), "C": ()}),
    StateTemplate("S05", {"A": ("red_large", "yellow_medium"), "B": (), "C": ("pink_small",)}),
    StateTemplate("S06", {"A": ("red_large",), "B": ("yellow_medium",), "C": ("pink_small",)}),
    StateTemplate("S07", {"A": ("red_large",), "B": ("pink_small",), "C": ("yellow_medium",)}),
    StateTemplate("S08", {"A": ("yellow_medium",), "B": ("red_large",), "C": ("pink_small",)}),
    StateTemplate("S09", {"A": ("pink_small",), "B": ("red_large",), "C": ("yellow_medium",)}),
    StateTemplate("S10", {"A": ("pink_small",), "B": ("yellow_medium",), "C": ("red_large",)}),
    StateTemplate("S11", {"A": ("red_large",), "B": ("yellow_medium", "pink_small"), "C": ()}),
    StateTemplate("S12", {"A": ("red_large",), "B": (), "C": ("yellow_medium", "pink_small")}),
    StateTemplate("S13", {"A": ("yellow_medium", "pink_small"), "B": ("red_large",), "C": ()}),
    StateTemplate("S14", {"A": (), "B": ("red_large",), "C": ("yellow_medium", "pink_small")}),
    StateTemplate("S15", {"A": ("pink_small",), "B": ("red_large", "yellow_medium"), "C": ()}),
    StateTemplate("S16", {"A": ("pink_small",), "B": (), "C": ("red_large", "yellow_medium")}),
    StateTemplate("S17", {"A": ("yellow_medium",), "B": ("pink_small",), "C": ("red_large",)}),
    StateTemplate("S18", {"A": (), "B": ("red_large", "pink_small"), "C": ("yellow_medium",)}),
]


def build_collection_plan(
    *,
    episodes_per_group: int,
    tasks: list[CollectionTask] | None = None,
    templates: list[StateTemplate] | None = None,
) -> list[PlanItem]:
    resolved_tasks = tasks or list(DEFAULT_TASKS)
    resolved_templates = templates or list(DEFAULT_TEMPLATES)
    plan: list[PlanItem] = []
    running_index = 1
    for group_index, task in enumerate(resolved_tasks, start=1):
        candidates = [template for template in resolved_templates if template.supports(task)]
        if not candidates:
            raise ValueError(f"no placement templates available for task {task.short_name}")
        for item_in_group in range(1, episodes_per_group + 1):
            template = candidates[(item_in_group - 1) % len(candidates)]
            plan.append(
                PlanItem(
                    index=running_index,
                    group_index=group_index,
                    item_in_group=item_in_group,
                    task=task,
                    template=template,
                )
            )
            running_index += 1
    return plan


def _make_runtime_config(args: argparse.Namespace) -> PerceptionRuntimeConfig:
    if args.config:
        app_config = load_config(args.config)
        runtime_config = build_perception_runtime_config(app_config.perception)
        if not runtime_config.robot_state_config_path:
            runtime_config.robot_state_config_path = app_config.execution.robot_config
        if not runtime_config.robot_pythonpath:
            runtime_config.robot_pythonpath = app_config.execution.robot_pythonpath
    else:
        runtime_config = build_perception_runtime_config()

    runtime_config.camera_backend = "opencv"
    runtime_config.camera_device_id = args.camera_device
    runtime_config.camera_frame_id = args.camera_frame_id
    runtime_config.camera_width = args.camera_width
    runtime_config.camera_height = args.camera_height
    runtime_config.camera_fps = args.camera_fps
    runtime_config.camera_index = args.camera_index

    robot_config_path = args.robot_config or (
        str(DEFAULT_LOCAL_ROBOT_CONFIG) if DEFAULT_LOCAL_ROBOT_CONFIG.exists() else ""
    )
    robot_pythonpath = args.robot_pythonpath or _discover_lerobot_pythonpath()

    if args.robot_backend == "skip":
        runtime_config.robot_state_backend = "mock"
        runtime_config.robot_state_config_path = ""
        runtime_config.robot_state_base_url = ""
        runtime_config.robot_pythonpath = ""
        return runtime_config

    runtime_config.robot_state_backend = args.robot_backend
    if robot_config_path:
        runtime_config.robot_state_config_path = robot_config_path
    if robot_pythonpath:
        runtime_config.robot_pythonpath = robot_pythonpath
    if args.robot_base_url:
        runtime_config.robot_state_base_url = args.robot_base_url
    return runtime_config


def _run_camera_check(runtime_config: PerceptionRuntimeConfig) -> CheckResult:
    device_ref = runtime_config.camera_device_id.strip()
    if device_ref.startswith("/dev/") and not os.path.exists(device_ref):
        return CheckResult(
            name="camera",
            ok=False,
            message=f"camera device missing: {runtime_config.camera_device_id}",
            details={
                "camera_device_id": runtime_config.camera_device_id,
                "camera_index": runtime_config.camera_index,
                "error_type": "FileNotFoundError",
            },
        )
    return CheckResult(
        name="camera",
        ok=True,
        message=f"camera device ready: {runtime_config.camera_device_id}",
        details={
            "camera_device_id": runtime_config.camera_device_id,
            "camera_index": runtime_config.camera_index,
            "note": "full validation is performed when the LeRobot recording runtime connects the robot cameras",
        },
    )


def _run_robot_check(runtime_config: PerceptionRuntimeConfig) -> CheckResult:
    if runtime_config.robot_state_backend == "mock":
        return CheckResult(
            name="robot",
            ok=False,
            message="robot check skipped: missing real robot backend/config",
            details={"backend": runtime_config.robot_state_backend},
        )
    try:
        client = build_robot_state_adapter(runtime_config)
        state = client.read_state().to_payload()
        return CheckResult(
            name="robot",
            ok=True,
            message=f"robot ready: {runtime_config.robot_state_backend}",
            details={
                "backend": runtime_config.robot_state_backend,
                "joint_count": len(state.get("joint_positions", [])),
                "timestamp": state.get("timestamp", ""),
                "reference_frame": ((state.get("ee_pose") or {}).get("reference_frame", "")),
            },
        )
    except Exception as exc:
        return CheckResult(
            name="robot",
            ok=False,
            message=f"robot check failed: {exc}",
            details={
                "backend": runtime_config.robot_state_backend,
                "config_path": runtime_config.robot_state_config_path,
                "base_url": runtime_config.robot_state_base_url,
                "error_type": type(exc).__name__,
            },
        )


def _session_paths(session_dir: Path) -> dict[str, Path]:
    session_dir.mkdir(parents=True, exist_ok=True)
    return {
        "plan": session_dir / "plan.json",
        "log": session_dir / "session.jsonl",
        "summary": session_dir / "summary.json",
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _render_check(result: CheckResult) -> str:
    status = "OK" if result.ok else "FAIL"
    return f"[{status}] {result.name}: {result.message}"


def _render_plan_item(item: PlanItem) -> str:
    return (
        f"\n样本 {item.index} / 组 {item.group_index}-{item.item_in_group}\n"
        f"任务: {item.task.prompt}\n"
        f"目标环: {RING_LABELS[item.task.ring_key]}，当前位于 {PEG_LABELS[item.source_peg]} 顶部\n"
        f"目标柱: {PEG_LABELS[item.task.target_peg]}\n"
        f"当前摆放: {item.template.render()}\n"
        f"模板: {item.template.template_id}"
    )


def _resolve_dataset_dir(dataset_root: Path, dataset_repo_id: str) -> Path:
    return dataset_root / Path(dataset_repo_id)


def _normalize_recording_decision(raw: str) -> str | None:
    token = raw.strip().lower()
    if token in ("", "s"):
        return "save"
    if token == "r":
        return "rerecord"
    if token == "q":
        return "quit"
    return None


def _prompt_recording_decision() -> str:
    while True:
        decision = _normalize_recording_decision(
            input("录制结束。回车/s 保存，r 丢弃并重录当前条，q 丢弃并退出: ")
        )
        if decision is not None:
            return decision
        print("输入无效，请输入回车、s、r 或 q。")


def _poll_stop_recording() -> bool:
    ready, _, _ = select.select([sys.stdin], [], [], 0.0)
    if not ready:
        return False
    sys.stdin.readline()
    return True


def _prepare_preview_frame(frame: Any, np_module: Any) -> Any | None:
    np_frame = np_module.asarray(frame)
    if np_frame.size == 0:
        return None
    if np_frame.dtype != np_module.uint8:
        if float(np_frame.max()) <= 1.0:
            np_frame = (np_module.clip(np_frame, 0.0, 1.0) * 255.0).astype(np_module.uint8)
        else:
            np_frame = np_module.clip(np_frame, 0.0, 255.0).astype(np_module.uint8)
    return np_frame


def _tk_preview_worker(frame_queue: Any, stop_event: Any, window_name: str) -> None:
    import queue as queue_module
    import tkinter as tk
    from PIL import Image, ImageTk

    root = tk.Tk()
    root.title(window_name)
    label = tk.Label(root)
    label.pack()

    def _tick() -> None:
        latest_frame = None
        while True:
            try:
                latest_frame = frame_queue.get_nowait()
            except queue_module.Empty:
                break
        if latest_frame is not None:
            tk_image = ImageTk.PhotoImage(image=Image.fromarray(latest_frame))
            label.configure(image=tk_image)
            label.image = tk_image
        if stop_event.is_set():
            root.destroy()
            return
        root.after(15, _tick)

    root.after(15, _tick)
    root.mainloop()


def _build_preview_state(
    *,
    enabled: bool,
    camera_key: str,
    window_name: str,
    available_camera_keys: list[str],
) -> dict[str, Any]:
    if not enabled:
        return {"enabled": False}

    resolved_camera_key = camera_key if camera_key in available_camera_keys else ""
    if not resolved_camera_key and available_camera_keys:
        resolved_camera_key = available_camera_keys[0]
    if not resolved_camera_key:
        print("未找到可预览的相机，已关闭本地预览。")
        return {"enabled": False}

    try:
        import cv2
        import numpy as np

        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        return {
            "enabled": True,
            "backend": "cv2",
            "camera_key": resolved_camera_key,
            "window_name": window_name,
            "cv2": cv2,
            "np": np,
        }
    except Exception as exc:
        cv2_error = exc

    try:
        import numpy as np
        ctx = multiprocessing.get_context("spawn")
        frame_queue = ctx.Queue(maxsize=1)
        stop_event = ctx.Event()
        process = ctx.Process(
            target=_tk_preview_worker,
            args=(frame_queue, stop_event, window_name),
            daemon=True,
            name="hanoi-preview",
        )
        process.start()
        return {
            "enabled": True,
            "backend": "tk",
            "camera_key": resolved_camera_key,
            "window_name": window_name,
            "np": np,
            "frame_queue": frame_queue,
            "stop_event": stop_event,
            "process": process,
        }
    except Exception as exc:
        print(f"初始化本地相机预览失败，已关闭预览: cv2={cv2_error}; tkinter={exc}")
        return {"enabled": False}


def _update_preview_window(preview_state: dict[str, Any], observation: dict[str, Any]) -> None:
    if not preview_state.get("enabled", False):
        return

    frame = observation.get(preview_state["camera_key"])
    if frame is None:
        return

    np_frame = _prepare_preview_frame(frame, preview_state["np"])
    if np_frame is None:
        return
    if preview_state["backend"] == "cv2":
        if np_frame.ndim == 3 and np_frame.shape[2] == 3:
            np_frame = preview_state["cv2"].cvtColor(np_frame, preview_state["cv2"].COLOR_RGB2BGR)
        preview_state["cv2"].imshow(preview_state["window_name"], np_frame)
        preview_state["cv2"].waitKey(1)
        return

    try:
        while True:
            preview_state["frame_queue"].get_nowait()
    except queue.Empty:
        pass
    try:
        preview_state["frame_queue"].put_nowait(np_frame.copy())
    except queue.Full:
        pass


def _close_preview_window(preview_state: dict[str, Any]) -> None:
    if not preview_state.get("enabled", False):
        return
    try:
        if preview_state["backend"] == "cv2":
            preview_state["cv2"].destroyWindow(preview_state["window_name"])
            preview_state["cv2"].waitKey(1)
        else:
            preview_state["stop_event"].set()
            preview_state["process"].join(timeout=2.0)
            if preview_state["process"].is_alive():
                preview_state["process"].terminate()
                preview_state["process"].join(timeout=1.0)
            preview_state["frame_queue"].close()
    except Exception:
        pass


def _build_summary_payload(
    *,
    runtime_config: PerceptionRuntimeConfig,
    checks: list[CheckResult],
    session_dir: Path,
    plan: list[PlanItem],
    completed: int,
    interrupted: bool,
    dataset_repo_id: str,
    dataset_root: Path,
    dataset_dir: Path,
) -> dict[str, Any]:
    return {
        "generated_at": _now_iso(),
        "session_dir": str(session_dir),
        "dataset_repo_id": dataset_repo_id,
        "dataset_root": str(dataset_root),
        "dataset_dir": str(dataset_dir),
        "camera_device_id": runtime_config.camera_device_id,
        "robot_backend": runtime_config.robot_state_backend,
        "robot_state_config_path": runtime_config.robot_state_config_path,
        "robot_state_base_url": runtime_config.robot_state_base_url,
        "episodes_total": len(plan),
        "episodes_completed": completed,
        "interrupted": interrupted,
        "checks": [asdict(result) for result in checks],
    }


def _ensure_pythonpath(pythonpath: str) -> None:
    if pythonpath and pythonpath not in sys.path:
        sys.path.insert(0, pythonpath)


def _load_lerobot_bindings(pythonpath: str) -> dict[str, Any]:
    _ensure_pythonpath(pythonpath)
    try:
        from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
        from lerobot.datasets.pipeline_features import (
            aggregate_pipeline_dataset_features,
            create_initial_features,
        )
        from lerobot.datasets.utils import build_dataset_frame, combine_feature_dicts
        from lerobot.processor import make_default_processors
        from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
        from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
        from lerobot.utils.constants import ACTION, OBS_STR
        from lerobot.utils.robot_utils import precise_sleep
    except Exception as exc:
        raise RuntimeError(
            "需要在安装了 lerobot 依赖的环境中运行完整采集脚本，"
            "并确保 --robot-pythonpath 指向 lerobot/src"
        ) from exc

    return {
        "OpenCVCameraConfig": OpenCVCameraConfig,
        "LeRobotDataset": LeRobotDataset,
        "aggregate_pipeline_dataset_features": aggregate_pipeline_dataset_features,
        "create_initial_features": create_initial_features,
        "combine_feature_dicts": combine_feature_dicts,
        "make_default_processors": make_default_processors,
        "SO101Follower": SO101Follower,
        "SO101FollowerConfig": SO101FollowerConfig,
        "SO101Leader": SO101Leader,
        "SO101LeaderConfig": SO101LeaderConfig,
        "ACTION": ACTION,
        "OBS_STR": OBS_STR,
        "build_dataset_frame": build_dataset_frame,
        "precise_sleep": precise_sleep,
    }


def _camera_index_or_path(device: str) -> int | str:
    normalized = device.strip()
    if normalized.isdigit():
        return int(normalized)
    return normalized


def _run_lerobot_device_check(
    *,
    pythonpath: str,
    builder,
    reader_name: str,
    name: str,
    details: dict[str, Any],
) -> CheckResult:
    device = None
    try:
        _ensure_pythonpath(pythonpath)
        device = builder()
        try:
            device.connect(calibrate=False)
        except TypeError:
            device.connect()
        reader = getattr(device, reader_name)
        payload = reader()
        payload_size = len(payload) if isinstance(payload, dict) else 0
        return CheckResult(
            name=name,
            ok=True,
            message=f"{name} ready",
            details={**details, "payload_size": payload_size},
        )
    except Exception as exc:
        return CheckResult(
            name=name,
            ok=False,
            message=f"{name} check failed: {exc}",
            details={**details, "error_type": type(exc).__name__},
        )
    finally:
        if device is not None and getattr(device, "is_connected", False):
            try:
                device.disconnect()
            except Exception:
                pass


def _run_follower_check(args: argparse.Namespace) -> CheckResult:
    pythonpath = args.robot_pythonpath or _discover_lerobot_pythonpath()
    try:
        bindings = _load_lerobot_bindings(pythonpath)
    except Exception as exc:
        return CheckResult(
            name="follower",
            ok=False,
            message=str(exc),
            details={"pythonpath": pythonpath, "error_type": type(exc).__name__},
        )
    return _run_lerobot_device_check(
        pythonpath=pythonpath,
        builder=lambda: bindings["SO101Follower"](
            bindings["SO101FollowerConfig"](
                port=args.follower_port,
                id=args.follower_id,
                use_degrees=True,
            )
        ),
        reader_name="get_observation",
        name="follower",
        details={"port": args.follower_port, "id": args.follower_id},
    )


def _run_leader_check(args: argparse.Namespace) -> CheckResult:
    pythonpath = args.robot_pythonpath or _discover_lerobot_pythonpath()
    try:
        bindings = _load_lerobot_bindings(pythonpath)
    except Exception as exc:
        return CheckResult(
            name="leader",
            ok=False,
            message=str(exc),
            details={"pythonpath": pythonpath, "error_type": type(exc).__name__},
        )
    return _run_lerobot_device_check(
        pythonpath=pythonpath,
        builder=lambda: bindings["SO101Leader"](
            bindings["SO101LeaderConfig"](
                port=args.leader_port,
                id=args.leader_id,
                use_degrees=True,
            )
        ),
        reader_name="get_action",
        name="leader",
        details={"port": args.leader_port, "id": args.leader_id},
    )


def _build_dataset(
    *,
    args: argparse.Namespace,
    bindings: dict[str, Any],
):
    camera_config = {
        "front": bindings["OpenCVCameraConfig"](
            index_or_path=_camera_index_or_path(args.camera_device),
            width=args.camera_width,
            height=args.camera_height,
            fps=args.dataset_fps,
        )
    }
    robot_config = bindings["SO101FollowerConfig"](
        port=args.follower_port,
        id=args.follower_id,
        use_degrees=True,
        cameras=camera_config,
    )
    teleop_config = bindings["SO101LeaderConfig"](
        port=args.leader_port,
        id=args.leader_id,
        use_degrees=True,
    )

    robot = bindings["SO101Follower"](robot_config)
    teleop = bindings["SO101Leader"](teleop_config)

    teleop_action_processor, robot_action_processor, robot_observation_processor = bindings[
        "make_default_processors"
    ]()
    dataset_features = bindings["combine_feature_dicts"](
        bindings["aggregate_pipeline_dataset_features"](
            pipeline=teleop_action_processor,
            initial_features=bindings["create_initial_features"](action=robot.action_features),
            use_videos=True,
        ),
        bindings["aggregate_pipeline_dataset_features"](
            pipeline=robot_observation_processor,
            initial_features=bindings["create_initial_features"](observation=robot.observation_features),
            use_videos=True,
        ),
    )
    dataset = bindings["LeRobotDataset"].create(
        repo_id=args.dataset_repo_id,
        fps=args.dataset_fps,
        root=_resolve_dataset_dir(args.dataset_root, args.dataset_repo_id),
        robot_type=robot.name,
        features=dataset_features,
        use_videos=True,
        image_writer_processes=0,
        image_writer_threads=max(1, 4 * len(robot.cameras)),
        batch_encoding_size=1,
        vcodec=args.vcodec,
    )
    return {
        "dataset": dataset,
        "robot": robot,
        "teleop": teleop,
        "teleop_action_processor": teleop_action_processor,
        "robot_action_processor": robot_action_processor,
        "robot_observation_processor": robot_observation_processor,
    }


def _record_episode(
    *,
    item: PlanItem,
    args: argparse.Namespace,
    runtime: dict[str, Any],
    bindings: dict[str, Any],
    max_episode_seconds: float,
) -> tuple[str, str]:
    preview_state = _build_preview_state(
        enabled=args.camera_preview,
        camera_key=args.preview_camera_key,
        window_name=args.preview_window_name,
        available_camera_keys=list(runtime["robot"].cameras.keys()),
    )
    if preview_state.get("enabled", False):
        print(
            f"已打开相机预览窗口: {preview_state['window_name']} "
            f"(camera={preview_state['camera_key']}, backend={preview_state['backend']})"
        )

    try:
        print("录制中，完成本条后按回车结束。")
        timestamp = 0.0
        start_episode_t = time.perf_counter()
        while timestamp < max_episode_seconds:
            start_loop_t = time.perf_counter()

            if _poll_stop_recording():
                break

            observation = runtime["robot"].get_observation()
            observation_processed = runtime["robot_observation_processor"](observation)
            observation_frame = bindings["build_dataset_frame"](
                runtime["dataset"].features,
                observation_processed,
                prefix=bindings["OBS_STR"],
            )

            teleop_action = runtime["teleop"].get_action()
            processed_teleop_action = runtime["teleop_action_processor"]((teleop_action, observation))
            robot_action_to_send = runtime["robot_action_processor"]((processed_teleop_action, observation))
            runtime["robot"].send_action(robot_action_to_send)

            action_frame = bindings["build_dataset_frame"](
                runtime["dataset"].features,
                processed_teleop_action,
                prefix=bindings["ACTION"],
            )
            runtime["dataset"].add_frame({**observation_frame, **action_frame, "task": item.task.prompt})

            _update_preview_window(preview_state, observation)

            dt_s = time.perf_counter() - start_loop_t
            bindings["precise_sleep"](max(1 / runtime["dataset"].fps - dt_s, 0.0))
            timestamp = time.perf_counter() - start_episode_t
    except Exception as exc:
        runtime["dataset"].clear_episode_buffer()
        return "failed", str(exc)
    finally:
        _close_preview_window(preview_state)

    episode_buffer = runtime["dataset"].episode_buffer or {}
    if int(episode_buffer.get("size", 0)) <= 0:
        runtime["dataset"].clear_episode_buffer()
        return "failed", "本条未采到任何有效帧，已丢弃。"

    decision = _prompt_recording_decision()
    if decision == "save":
        runtime["dataset"].save_episode()
        return "saved", ""

    runtime["dataset"].clear_episode_buffer()
    if decision == "rerecord":
        return "rerecord", "当前条目录错，已丢弃并准备重录。"
    return "quit", "当前条目已丢弃，用户选择退出采集。"


def run_session(args: argparse.Namespace) -> int:
    runtime_config = _make_runtime_config(args)
    checks = [
        _run_camera_check(runtime_config),
        _run_follower_check(args),
        _run_leader_check(args),
    ]

    print("硬件检查结果")
    for check in checks:
        print(_render_check(check))

    if not checks[0].ok:
        print("相机检查失败，停止采集。")
        return 1

    if args.require_robot and any(not check.ok for check in checks[1:]):
        print("主从臂检查失败，且已启用 --require-robot，停止采集。")
        return 1

    plan = build_collection_plan(episodes_per_group=args.episodes_per_group)
    session_dir = args.session_dir
    paths = _session_paths(session_dir)
    _write_json(
        paths["plan"],
        {
            "generated_at": _now_iso(),
            "episodes_per_group": args.episodes_per_group,
            "plan": [item.to_payload() for item in plan],
        },
    )

    print(f"\n采集计划已写入 {paths['plan']}")
    dataset_dir = _resolve_dataset_dir(args.dataset_root, args.dataset_repo_id)
    print(f"目标数据集: repo_id={args.dataset_repo_id}, dir={dataset_dir}")
    print("按回车开始当前条目，采集中按回车结束本条。结束后可选择保存、重录当前条或退出。")
    if args.camera_preview:
        print(f"录制时会弹出本地相机预览窗口: {args.preview_window_name}")

    pythonpath = args.robot_pythonpath or _discover_lerobot_pythonpath()
    try:
        bindings = _load_lerobot_bindings(pythonpath)
    except Exception as exc:
        print(f"无法加载 lerobot 录制依赖: {exc}")
        return 1

    runtime = None
    try:
        runtime = _build_dataset(args=args, bindings=bindings)
        runtime["robot"].connect()
        runtime["teleop"].connect()
    except Exception as exc:
        print(f"初始化完整录制链路失败: {exc}")
        if runtime is not None:
            if getattr(runtime["robot"], "is_connected", False):
                runtime["robot"].disconnect()
            if getattr(runtime["teleop"], "is_connected", False):
                runtime["teleop"].disconnect()
            runtime["dataset"].finalize()
        return 1

    completed = 0
    interrupted = False
    attempt_counts: dict[int, int] = {}
    plan_index = 0
    try:
        while plan_index < len(plan):
            item = plan[plan_index]
            print(_render_plan_item(item))
            start_token = input("确认摆好后按回车开始，或输入 q 退出: ").strip().lower()
            if start_token == "q":
                interrupted = True
                break
            attempt_counts[item.index] = attempt_counts.get(item.index, 0) + 1
            started_at = _now_iso()
            status, message = _record_episode(
                item=item,
                args=args,
                runtime=runtime,
                bindings=bindings,
                max_episode_seconds=args.max_episode_seconds,
            )
            ended_at = _now_iso()
            event = {
                "event": f"episode_{status}",
                "recorded_at": _now_iso(),
                "episode_index": item.index,
                "attempt_index": attempt_counts[item.index],
                "group_index": item.group_index,
                "item_in_group": item.item_in_group,
                "task_prompt": item.task.prompt,
                "template_id": item.template.template_id,
                "placement": item.template.render(),
                "started_at": started_at,
                "ended_at": ended_at,
                "dataset_repo_id": args.dataset_repo_id,
                "dataset_root": str(args.dataset_root),
                "dataset_dir": str(dataset_dir),
            }
            if status == "saved":
                completed += 1
                event["saved_episode_count"] = runtime["dataset"].num_episodes
                print(f"已保存样本 {item.index}，当前累计 episodes={runtime['dataset'].num_episodes}")
                plan_index += 1
            else:
                event["message"] = message
                if status == "rerecord":
                    print(f"样本 {item.index} 已丢弃，将重新采集当前条。")
                elif status == "quit":
                    interrupted = True
                    print("已丢弃当前条并结束采集。")
                else:
                    event["error"] = message
                    print(f"样本 {item.index} 录制失败: {message}")
            _append_jsonl(paths["log"], event)
            print(f"日志已写入 {paths['log']}")
            if status == "quit":
                break
    finally:
        if runtime is not None:
            runtime["dataset"].finalize()
            if getattr(runtime["robot"], "is_connected", False):
                runtime["robot"].disconnect()
            if getattr(runtime["teleop"], "is_connected", False):
                runtime["teleop"].disconnect()

    _write_json(
        paths["summary"],
        _build_summary_payload(
            runtime_config=runtime_config,
            checks=checks,
            session_dir=session_dir,
            plan=plan,
            completed=completed,
            interrupted=interrupted,
            dataset_repo_id=args.dataset_repo_id,
            dataset_root=args.dataset_root,
            dataset_dir=dataset_dir,
        ),
    )
    print(f"\n会话摘要已写入 {paths['summary']}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guided collection script for Hanoi-ring atomic demos")
    parser.add_argument("--config", default="", help="optional embodied-agent YAML config path")
    parser.add_argument("--camera-device", default="/dev/video0", help="camera device path")
    parser.add_argument("--camera-frame-id", default="workspace_camera", help="camera frame id")
    parser.add_argument("--camera-width", type=int, default=640, help="camera capture width")
    parser.add_argument("--camera-height", type=int, default=480, help="camera capture height")
    parser.add_argument("--camera-fps", type=float, default=15.0, help="camera capture fps")
    parser.add_argument("--camera-index", type=int, default=0, help="opencv camera index fallback")
    parser.add_argument("--follower-port", default="/dev/ttyACM0", help="follower arm serial port")
    parser.add_argument("--follower-id", default="hanoi_follower_arm_v2", help="follower arm calibration id")
    parser.add_argument("--leader-port", default="/dev/ttyACM1", help="leader arm serial port")
    parser.add_argument("--leader-id", default="hanoi_leader_arm_v2", help="leader arm calibration id")
    parser.add_argument(
        "--robot-backend",
        choices=("lerobot_local", "mcp_bridge", "skip"),
        default="lerobot_local" if DEFAULT_LOCAL_ROBOT_CONFIG.exists() else "skip",
        help="robot state backend used for the fallback startup check",
    )
    parser.add_argument(
        "--robot-config",
        default=str(DEFAULT_LOCAL_ROBOT_CONFIG) if DEFAULT_LOCAL_ROBOT_CONFIG.exists() else "",
        help="path to local LeRobot robot config",
    )
    parser.add_argument(
        "--robot-pythonpath",
        default=_discover_lerobot_pythonpath(),
        help="pythonpath for local LeRobot import",
    )
    parser.add_argument("--robot-base-url", default="", help="robot bridge base url when using mcp_bridge")
    parser.add_argument("--require-robot", action="store_true", help="fail fast when robot check does not pass")
    parser.add_argument("--dataset-repo-id", default=_default_dataset_repo_id(), help="target LeRobot dataset repo id")
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("data/lerobot"),
        help="root directory for local LeRobot dataset storage",
    )
    parser.add_argument("--dataset-fps", type=int, default=15, help="recording fps written to dataset")
    parser.add_argument("--max-episode-seconds", type=float, default=120.0, help="hard limit for a single episode")
    parser.add_argument(
        "--camera-preview",
        dest="camera_preview",
        action="store_true",
        default=True,
        help="show a local OpenCV camera preview window while recording",
    )
    parser.add_argument(
        "--no-camera-preview",
        dest="camera_preview",
        action="store_false",
        help="disable the local OpenCV camera preview window",
    )
    parser.add_argument("--preview-camera-key", default="front", help="camera key used for local preview")
    parser.add_argument(
        "--preview-window-name",
        default="Hanoi Collect Preview",
        help="window title for the local camera preview",
    )
    parser.add_argument(
        "--vcodec",
        default="h264",
        choices=("h264", "hevc", "libsvtav1"),
        help="video codec used by LeRobot dataset writer",
    )
    parser.add_argument("--episodes-per-group", type=int, default=15, help="samples per ring-target group")
    parser.add_argument(
        "--session-dir",
        type=Path,
        default=_default_session_dir(),
        help="directory for plan/log/summary artifacts",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run_session(args)


if __name__ == "__main__":
    raise SystemExit(main())
