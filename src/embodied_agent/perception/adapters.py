"""Perception adapter protocols and hardware-backed factories."""

from __future__ import annotations

import base64
import json
import socket
import sys
from datetime import datetime, timezone
from threading import Event, Lock, Thread
from time import monotonic, sleep
from typing import Any, Iterator, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import PerceptionRuntimeConfig
from .contracts import CapturedImage, RobotStateSnapshot
from .errors import AdapterConfigurationError, CameraDisconnectedError, RobotCommunicationError
from .mocks import MOCK_IMAGE_BASE64, MockCamera, MockRobotStateClient


class CameraAdapter(Protocol):
    def capture(self) -> CapturedImage:
        ...


class RobotStateAdapter(Protocol):
    def read_state(self) -> RobotStateSnapshot:
        ...


class OpenCVCamera:
    _OPEN_RETRY_DELAY_S = 0.2
    _READ_RETRY_DELAY_S = 0.05
    _WARMUP_FRAME_COUNT = 3
    _READ_RETRY_COUNT = 5

    def __init__(
        self,
        *,
        camera_id: str,
        width: int,
        height: int,
        fps: float,
        frame_id: str,
        camera_index: int = 0,
    ) -> None:
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_id = frame_id
        self.camera_index = camera_index
        self._frame_lock = Lock()
        self._capture_thread: Thread | None = None
        self._stop_event = Event()
        self._latest_frame = None
        self._latest_frame_timestamp = 0.0

    @staticmethod
    def _resolve_device_ref(camera_id: str, *, camera_index: int) -> str | int:
        normalized = camera_id.strip()
        if normalized.isdigit():
            return int(normalized)
        if normalized.startswith("/dev/") or normalized:
            return normalized
        return int(camera_index)

    @staticmethod
    def _import_cv2():
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise AdapterConfigurationError(
                message="opencv camera backend 需要安装 opencv-python-headless",
                backend="opencv",
            ) from exc
        return cv2

    def _open_camera(self):
        cv2 = self._import_cv2()
        device_ref = self._resolve_device_ref(self.camera_id, camera_index=self.camera_index)
        backend_flag = getattr(cv2, "CAP_V4L2", 0)

        capture_attempts: list[tuple[Any, int | None]]
        if isinstance(device_ref, str):
            # `/dev/videoN` style device paths often fail when forced through CAP_V4L2 by name.
            capture_attempts = [(device_ref, None)]
            if backend_flag:
                capture_attempts.append((device_ref, backend_flag))
        else:
            capture_attempts = [(device_ref, backend_flag if backend_flag else None), (device_ref, None)]

        camera = None
        for ref, backend in capture_attempts:
            candidate = cv2.VideoCapture(ref) if backend is None else cv2.VideoCapture(ref, backend)
            if candidate.isOpened():
                camera = candidate
                break
            candidate.release()

        if camera is None:
            raise CameraDisconnectedError(camera_id=self.camera_id)

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.width))
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.height))
        if hasattr(cv2, "VideoWriter_fourcc") and hasattr(cv2, "CAP_PROP_FOURCC"):
            camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        camera.set(cv2.CAP_PROP_FPS, float(self.fps))
        if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cv2, camera

    @staticmethod
    def _read_frame(camera, *, camera_id: str):
        ok, frame = camera.read()
        if not ok or frame is None:
            raise CameraDisconnectedError(message="摄像头读取失败", camera_id=camera_id)
        return frame

    def _prime_camera(self, camera) -> None:
        last_error: CameraDisconnectedError | None = None
        for _ in range(self._WARMUP_FRAME_COUNT):
            try:
                self._read_frame(camera, camera_id=self.camera_id)
                last_error = None
            except CameraDisconnectedError as exc:
                last_error = exc
                sleep(self._READ_RETRY_DELAY_S)
        if last_error is not None:
            raise last_error

    def _read_frame_with_retries(self, camera, *, attempts: int | None = None):
        remaining_attempts = attempts or self._READ_RETRY_COUNT
        last_error: CameraDisconnectedError | None = None
        for _ in range(max(1, remaining_attempts)):
            try:
                return self._read_frame(camera, camera_id=self.camera_id)
            except CameraDisconnectedError as exc:
                last_error = exc
                sleep(self._READ_RETRY_DELAY_S)
        raise last_error or CameraDisconnectedError(camera_id=self.camera_id)

    def _capture_loop(self) -> None:
        target_interval_s = 1.0 / self.fps if self.fps > 0 else 0.03
        camera = None
        try:
            while not self._stop_event.is_set():
                try:
                    if camera is None:
                        _, camera = self._open_camera()
                        self._prime_camera(camera)
                    started_at = monotonic()
                    frame = self._read_frame_with_retries(camera)
                    with self._frame_lock:
                        self._latest_frame = frame.copy() if hasattr(frame, "copy") else frame
                        self._latest_frame_timestamp = monotonic()
                    remaining = target_interval_s - (monotonic() - started_at)
                    if remaining > 0:
                        sleep(remaining)
                except CameraDisconnectedError:
                    if camera is not None:
                        camera.release()
                        camera = None
                    sleep(max(self._OPEN_RETRY_DELAY_S, target_interval_s))
        finally:
            if camera is not None:
                camera.release()

    def _ensure_capture_thread(self) -> None:
        if self._capture_thread and self._capture_thread.is_alive():
            return
        self._stop_event = Event()
        self._capture_thread = Thread(
            target=self._capture_loop,
            name=f"opencv-camera-{self.camera_id}",
            daemon=True,
        )
        self._capture_thread.start()

    def close(self) -> None:
        self._stop_event.set()
        thread = self._capture_thread
        if thread and thread.is_alive():
            thread.join(timeout=1.0)
        self._capture_thread = None

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def _get_latest_frame(
        self,
        *,
        wait_timeout_s: float = 2.5,
        allow_direct_fallback: bool = True,
    ):
        self._ensure_capture_thread()
        deadline = monotonic() + wait_timeout_s
        while monotonic() < deadline:
            with self._frame_lock:
                if self._latest_frame is None:
                    frame = None
                else:
                    frame_age_s = monotonic() - self._latest_frame_timestamp
                    is_fresh = frame_age_s <= max(wait_timeout_s, 1.0)
                    frame = (
                        self._latest_frame.copy() if is_fresh and hasattr(self._latest_frame, "copy") else self._latest_frame
                    ) if is_fresh else None
            if frame is not None:
                return frame
            sleep(0.01)
        if not allow_direct_fallback:
            raise CameraDisconnectedError(message="摄像头读取超时", camera_id=self.camera_id)
        return self._capture_frame_once()

    def _capture_frame_once(self):
        _, camera = self._open_camera()
        try:
            self._prime_camera(camera)
            return self._read_frame_with_retries(camera)
        finally:
            camera.release()

    def _capture_encoded_bytes(self, *, image_extension: str) -> tuple[bytes, int, int, str]:
        cv2 = self._import_cv2()
        # Reuse the same long-lived capture thread for both snapshots and MJPEG streaming.
        # Some UVC devices are stable only when the process keeps a persistent handle open.
        frame = self._get_latest_frame(wait_timeout_s=5.0, allow_direct_fallback=True)
        ok, encoded = cv2.imencode(image_extension, frame)
        if not ok:
            raise CameraDisconnectedError(message="摄像头图像编码失败", camera_id=self.camera_id)

        captured_height, captured_width = frame.shape[:2]
        return encoded.tobytes(), int(captured_width), int(captured_height), "opencv"

    def capture(self) -> CapturedImage:
        image_bytes, captured_width, captured_height, backend = self._capture_encoded_bytes(
            image_extension=".png",
        )
        return CapturedImage(
            image_base64=base64.b64encode(image_bytes).decode("ascii"),
            timestamp=datetime.now(timezone.utc).isoformat(),
            resolution={"width": int(captured_width), "height": int(captured_height)},
            camera_parameters={
                "camera_id": self.camera_id,
                "frame_id": self.frame_id,
                "fx": float(captured_width),
                "fy": float(captured_height),
                "cx": captured_width / 2,
                "cy": captured_height / 2,
                "distortion_model": "unknown",
                "backend": backend,
                "fps": self.fps,
                "camera_index": self.camera_index,
            },
        )

    def capture_jpeg_bytes(self) -> bytes:
        image_bytes, _, _, _ = self._capture_encoded_bytes(image_extension=".jpg")
        return image_bytes

    def iter_jpeg_frames(
        self,
        *,
        fps: float,
        frame_limit: int | None = None,
        width: int | None = None,
        height: int | None = None,
        quality: int = 80,
    ) -> Iterator[bytes]:
        cv2 = self._import_cv2()
        self._ensure_capture_thread()
        produced_frames = 0
        frame_interval_s = 1.0 / fps if fps > 0 else 0.0
        resize_width = width if width and width > 0 else None
        resize_height = height if height and height > 0 else None
        jpeg_quality = min(95, max(40, quality))

        while frame_limit is None or produced_frames < frame_limit:
            started_at = monotonic()
            frame = self._get_latest_frame(wait_timeout_s=5.0, allow_direct_fallback=False)
            if resize_width or resize_height:
                source_height, source_width = frame.shape[:2]
                target_width = resize_width or int(source_width * ((resize_height or source_height) / source_height))
                target_height = resize_height or int(source_height * ((resize_width or source_width) / source_width))
                frame = cv2.resize(frame, (target_width, target_height))
            ok, encoded = cv2.imencode(
                ".jpg",
                frame,
                [int(getattr(cv2, "IMWRITE_JPEG_QUALITY", 1)), jpeg_quality],
            )
            if not ok:
                raise CameraDisconnectedError(message="摄像头图像编码失败", camera_id=self.camera_id)
            yield encoded.tobytes()
            produced_frames += 1
            remaining = frame_interval_s - (monotonic() - started_at)
            if remaining > 0:
                sleep(remaining)


TransportResponse = tuple[int, dict[str, str], bytes]


def _resolve_endpoint(base_url: str, *, suffix: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise AdapterConfigurationError(message=f"缺少真实链路地址: {suffix}", backend="http")
    if normalized.endswith(suffix):
        return normalized
    return f"{normalized}{suffix}"


def _decode_json_body(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RobotCommunicationError(message="机器人网关返回的不是合法 JSON") from exc
    if not isinstance(payload, dict):
        raise RobotCommunicationError(message="机器人网关返回根对象必须为 JSON 对象")
    return payload


def _default_transport(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
    timeout_s: float,
) -> TransportResponse:
    request = Request(url=url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout_s) as response:
            return int(response.status), dict(response.headers.items()), response.read()
    except HTTPError as exc:
        response_headers = dict(exc.headers.items()) if exc.headers is not None else {}
        return int(exc.code), response_headers, exc.read()
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise RobotCommunicationError(message=f"机器人链路连接失败: {exc}") from exc


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _safe_bool(value: Any, *, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "ok"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return default


def _extract_joint_positions(payload: Mapping[str, Any]) -> list[float]:
    joints = payload.get("joint_positions")
    if isinstance(joints, list) and joints:
        return [_safe_float(value) for value in joints]

    observation = payload.get("observation")
    if isinstance(observation, Mapping):
        positions: list[float] = []
        gripper_positions: list[float] = []
        for key, value in observation.items():
            if not (isinstance(key, str) and key.endswith(".pos") and isinstance(value, (int, float))):
                continue
            if "gripper" in key.lower():
                gripper_positions.append(_safe_float(value))
            else:
                positions.append(_safe_float(value))
        if positions or gripper_positions:
            return [*positions, *gripper_positions]
    return [0.0] * 6


def _extract_ee_pose(payload: Mapping[str, Any], *, reference_frame: str) -> dict[str, Any]:
    ee_pose = payload.get("ee_pose")
    if isinstance(ee_pose, Mapping):
        position = ee_pose.get("position") if isinstance(ee_pose.get("position"), Mapping) else {}
        orientation = ee_pose.get("orientation") if isinstance(ee_pose.get("orientation"), Mapping) else {}
        return {
            "position": {
                "x": _safe_float(position.get("x")),
                "y": _safe_float(position.get("y")),
                "z": _safe_float(position.get("z")),
            },
            "orientation": {
                "x": _safe_float(orientation.get("x")),
                "y": _safe_float(orientation.get("y")),
                "z": _safe_float(orientation.get("z")),
                "w": _safe_float(orientation.get("w"), default=1.0),
            },
            "reference_frame": str(ee_pose.get("reference_frame") or reference_frame),
        }

    observation = payload.get("observation")
    if isinstance(observation, Mapping):
        return {
            "position": {
                "x": _safe_float(observation.get("ee.x")),
                "y": _safe_float(observation.get("ee.y")),
                "z": _safe_float(observation.get("ee.z")),
            },
            "orientation": {
                "x": _safe_float(observation.get("ee.qx")),
                "y": _safe_float(observation.get("ee.qy")),
                "z": _safe_float(observation.get("ee.qz")),
                "w": _safe_float(observation.get("ee.qw"), default=1.0),
            },
            "reference_frame": reference_frame,
        }

    return {
        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "reference_frame": reference_frame,
    }


def _build_metadata(
    *,
    payload: Mapping[str, Any],
    telemetry: Mapping[str, Any] | None = None,
    backend: str,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "backend": backend,
        "connection_ok": True,
        "heartbeat_ok": True,
    }
    if telemetry:
        if "connection_ok" in telemetry:
            metadata["connection_ok"] = _safe_bool(telemetry.get("connection_ok"), default=True)
        if "heartbeat_ok" in telemetry:
            metadata["heartbeat_ok"] = _safe_bool(telemetry.get("heartbeat_ok"), default=True)
        if telemetry.get("error_code") not in (None, "", 0, "0", False):
            metadata["error_code"] = telemetry.get("error_code")
        for field_name in ("temperature_c", "motor_current_a", "position_error_m"):
            if field_name in telemetry:
                metadata[field_name] = _safe_float(telemetry.get(field_name))

    if "gripper_state" in payload:
        metadata["gripper_state"] = payload.get("gripper_state")
    observation = payload.get("observation")
    if isinstance(observation, Mapping) and "gripper.pos" in observation:
        metadata["gripper_state"] = observation.get("gripper.pos")
    return metadata


def _build_robot_state_snapshot(
    *,
    payload: Mapping[str, Any],
    reference_frame: str,
    backend: str,
    telemetry: Mapping[str, Any] | None = None,
) -> RobotStateSnapshot:
    timestamp = str(payload.get("timestamp") or datetime.now(timezone.utc).isoformat())
    return RobotStateSnapshot(
        joint_positions=_extract_joint_positions(payload),
        ee_pose=_extract_ee_pose(payload, reference_frame=reference_frame),
        timestamp=timestamp,
        metadata=_build_metadata(payload=payload, telemetry=telemetry, backend=backend),
    )


def _import_lerobot_robot_factory(pythonpath: str):
    if pythonpath.strip() and pythonpath not in sys.path:
        sys.path.insert(0, pythonpath)

    try:
        import draccus  # type: ignore
        from lerobot.robots.config import RobotConfig  # type: ignore
        from lerobot.robots.utils import make_robot_from_config  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on external env
        raise AdapterConfigurationError(
            message="lerobot_local backend 缺少 draccus/lerobot 依赖，请补充 robot_pythonpath 或安装依赖",
            backend="lerobot_local",
            pythonpath=pythonpath,
        ) from exc

    # Import common config registries so draccus can resolve robot types.
    for module_name in (
        "lerobot.robots.so_follower.config_so_follower",
        "lerobot.robots.openarm_follower.config_openarm_follower",
        "lerobot.robots.bi_openarm_follower.config_bi_openarm_follower",
        "lerobot.robots.bi_so_follower.config_bi_so_follower",
        "lerobot.robots.omx_follower.config_omx_follower",
        "lerobot.robots.koch_follower.config_koch_follower",
        "lerobot.robots.reachy2.configuration_reachy2",
        "lerobot.robots.unitree_g1.config_unitree_g1",
    ):
        try:
            __import__(module_name)
        except Exception:
            continue

    return draccus, RobotConfig, make_robot_from_config


def _build_local_lerobot(config_path: str, pythonpath: str):
    if not config_path.strip():
        raise AdapterConfigurationError(
            message="lerobot_local backend 需要配置 robot_state_config_path",
            backend="lerobot_local",
        )
    draccus, robot_config_type, make_robot_from_config = _import_lerobot_robot_factory(pythonpath)
    try:
        robot_config = draccus.parse(config_class=robot_config_type, config_path=config_path, args=[])
        robot = make_robot_from_config(robot_config)
        try:
            robot.connect(calibrate=False)
        except TypeError:
            robot.connect()
        return robot
    except Exception as exc:  # pragma: no cover - depends on external env
        raise RobotCommunicationError(
            message=f"lerobot_local backend 初始化失败: {exc}",
            config_path=config_path,
        ) from exc


class BridgeRobotStateClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_s: float,
        reference_frame: str,
        headers: dict[str, str] | None = None,
        transport=_default_transport,
    ) -> None:
        self.base_url = base_url
        self.timeout_s = timeout_s
        self.reference_frame = reference_frame
        self.headers = headers or {}
        self._transport = transport

    def read_state(self) -> RobotStateSnapshot:
        url = _resolve_endpoint(self.base_url, suffix="/state")
        status, _, body = self._transport(
            method="GET",
            url=url,
            headers={"Accept": "application/json", **self.headers},
            body=None,
            timeout_s=self.timeout_s,
        )
        payload = _decode_json_body(body)
        if status >= 400 or payload.get("ok") is False:
            raise RobotCommunicationError(
                message=f"机器人状态网关返回失败状态: {status}",
                status_code=status,
                payload=payload,
            )

        state_payload = payload.get("robot_state")
        if not isinstance(state_payload, Mapping):
            state_payload = payload.get("state")
        if not isinstance(state_payload, Mapping):
            state_payload = payload
        telemetry = payload.get("telemetry") if isinstance(payload.get("telemetry"), Mapping) else None
        return _build_robot_state_snapshot(
            payload=state_payload,
            reference_frame=self.reference_frame,
            backend="mcp_bridge",
            telemetry=telemetry,
        )


class LeRobotRobotStateClient:
    def __init__(
        self,
        *,
        config_path: str,
        pythonpath: str,
        reference_frame: str,
        loader=_build_local_lerobot,
    ) -> None:
        self.config_path = config_path
        self.pythonpath = pythonpath
        self.reference_frame = reference_frame
        self._loader = loader
        self._robot = None

    def _ensure_robot(self):
        if self._robot is None:
            self._robot = self._loader(self.config_path, self.pythonpath)
        return self._robot

    def read_state(self) -> RobotStateSnapshot:
        robot = self._ensure_robot()
        try:
            observation = robot.get_observation()
        except Exception as exc:  # pragma: no cover - depends on external env
            raise RobotCommunicationError(message=f"真实机器人状态读取失败: {exc}") from exc
        payload = {
            "observation": observation if isinstance(observation, Mapping) else {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return _build_robot_state_snapshot(
            payload=payload,
            reference_frame=self.reference_frame,
            backend="lerobot_local",
        )


def build_camera_adapter(config: PerceptionRuntimeConfig) -> CameraAdapter:
    if config.camera_backend == "mock":
        return MockCamera(
            camera_id=config.camera_device_id,
            width=config.camera_width,
            height=config.camera_height,
            frame_id=config.camera_frame_id,
        )
    if config.camera_backend == "opencv":
        return OpenCVCamera(
            camera_id=config.camera_device_id,
            width=config.camera_width,
            height=config.camera_height,
            fps=config.camera_fps,
            frame_id=config.camera_frame_id,
            camera_index=config.camera_index,
        )
    raise AdapterConfigurationError(
        message=f"不支持的 camera backend: {config.camera_backend}",
        backend=config.camera_backend,
    )


def build_robot_state_adapter(config: PerceptionRuntimeConfig) -> RobotStateAdapter:
    if config.robot_state_backend == "mock":
        return MockRobotStateClient(reference_frame=config.robot_state_base_frame)
    if config.robot_state_backend == "mcp_bridge":
        return BridgeRobotStateClient(
            base_url=config.robot_state_base_url,
            timeout_s=config.robot_state_timeout_s,
            reference_frame=config.robot_state_base_frame,
            headers=dict(config.robot_state_headers),
        )
    if config.robot_state_backend == "lerobot_local":
        return LeRobotRobotStateClient(
            config_path=config.robot_state_config_path,
            pythonpath=config.robot_pythonpath,
            reference_frame=config.robot_state_base_frame,
        )
    raise AdapterConfigurationError(
        message=f"不支持的 robot_state backend: {config.robot_state_backend}",
        backend=config.robot_state_backend,
    )


def iter_mjpeg_stream(
    camera: CameraAdapter,
    *,
    fps: float,
    frame_limit: int | None = None,
    width: int | None = None,
    height: int | None = None,
    quality: int = 80,
) -> Iterator[bytes]:
    if isinstance(camera, OpenCVCamera):
        for image_bytes in camera.iter_jpeg_frames(
            fps=fps,
            frame_limit=frame_limit,
            width=width,
            height=height,
            quality=quality,
        ):
            yield (
                b"--frame\r\n"
                + b"Content-Type: image/jpeg\r\n"
                + f"Content-Length: {len(image_bytes)}\r\n\r\n".encode("utf-8")
                + image_bytes
                + b"\r\n"
            )
        return

    produced_frames = 0
    frame_interval_s = 1.0 / fps if fps > 0 else 0.1
    while frame_limit is None or produced_frames < frame_limit:
        payload = camera.capture()
        image_bytes = base64.b64decode(payload.image_base64 or MOCK_IMAGE_BASE64)
        yield (
            b"--frame\r\n"
            + b"Content-Type: image/png\r\n"
            + f"Content-Length: {len(image_bytes)}\r\n\r\n".encode("utf-8")
            + image_bytes
            + b"\r\n"
        )
        produced_frames += 1
        sleep(frame_interval_s)
