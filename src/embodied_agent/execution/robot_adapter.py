"""Robot adapter boundary and real/bridge implementations for execution."""

from __future__ import annotations

import json
import math
import socket
import sys
from copy import deepcopy
from time import perf_counter, sleep
from typing import Any, Callable, Mapping, TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig
from .types import CartesianPose


class AdapterError(RuntimeError):
    """Raised when the robot adapter cannot complete a request."""


T = TypeVar("T")
TransportResponse = tuple[int, dict[str, str], bytes]


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


def _joint_positions_use_degrees(joint_positions: list[float]) -> bool:
    return any(abs(_safe_float(value)) > (2 * math.pi + 0.5) for value in joint_positions)


def _servo_delta_for_joint_positions(joint_positions: list[float], degrees: float) -> float:
    if _joint_positions_use_degrees(joint_positions):
        return float(degrees)
    return math.radians(degrees)


def _degrees_to_raw_delta(max_resolution: int, degrees: float) -> int:
    return int(round(float(degrees) * float(max_resolution) / 360.0))


def _resolve_endpoint(base_url: str, *, suffix: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise AdapterError(f"缺少机器人链路地址: {suffix}")
    if normalized.endswith(suffix):
        return normalized
    return f"{normalized}{suffix}"


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
        raise AdapterError(f"机器人链路连接失败: {exc}") from exc


def _decode_json_body(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError("机器人链路返回的不是合法 JSON") from exc
    if not isinstance(payload, dict):
        raise AdapterError("机器人链路返回根对象必须为 JSON 对象")
    return payload


def _extract_joint_positions(payload: Mapping[str, Any], *, fallback: list[float]) -> list[float]:
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
    return list(fallback)


def _extract_ee_pose(
    payload: Mapping[str, Any],
    *,
    fallback: Mapping[str, Any],
) -> dict[str, Any]:
    ee_pose = payload.get("ee_pose")
    if isinstance(ee_pose, Mapping):
        position = ee_pose.get("position") if isinstance(ee_pose.get("position"), Mapping) else {}
        orientation = ee_pose.get("orientation") if isinstance(ee_pose.get("orientation"), Mapping) else {}
        return {
            "position": {
                "x": _safe_float(position.get("x"), default=_safe_float(fallback["position"].get("x"))),
                "y": _safe_float(position.get("y"), default=_safe_float(fallback["position"].get("y"))),
                "z": _safe_float(position.get("z"), default=_safe_float(fallback["position"].get("z"))),
            },
            "orientation": {
                "x": _safe_float(orientation.get("x"), default=_safe_float(fallback["orientation"].get("x"))),
                "y": _safe_float(orientation.get("y"), default=_safe_float(fallback["orientation"].get("y"))),
                "z": _safe_float(orientation.get("z"), default=_safe_float(fallback["orientation"].get("z"))),
                "w": _safe_float(orientation.get("w"), default=_safe_float(fallback["orientation"].get("w"), default=1.0)),
            },
            "reference_frame": str(ee_pose.get("reference_frame") or fallback.get("reference_frame") or "base_link"),
        }

    observation = payload.get("observation")
    if isinstance(observation, Mapping):
        return {
            "position": {
                "x": _safe_float(observation.get("ee.x"), default=_safe_float(fallback["position"].get("x"))),
                "y": _safe_float(observation.get("ee.y"), default=_safe_float(fallback["position"].get("y"))),
                "z": _safe_float(observation.get("ee.z"), default=_safe_float(fallback["position"].get("z"))),
            },
            "orientation": {
                "x": _safe_float(observation.get("ee.qx"), default=_safe_float(fallback["orientation"].get("x"))),
                "y": _safe_float(observation.get("ee.qy"), default=_safe_float(fallback["orientation"].get("y"))),
                "z": _safe_float(observation.get("ee.qz"), default=_safe_float(fallback["orientation"].get("z"))),
                "w": _safe_float(observation.get("ee.qw"), default=_safe_float(fallback["orientation"].get("w"), default=1.0)),
            },
            "reference_frame": str(fallback.get("reference_frame") or "base_link"),
        }

    return {
        "position": dict(fallback["position"]),
        "orientation": dict(fallback["orientation"]),
        "reference_frame": str(fallback.get("reference_frame") or "base_link"),
    }


def _normalize_robot_state_payload(
    payload: Mapping[str, Any],
    *,
    fallback_state: RobotState,
) -> RobotState:
    fallback_pose = fallback_state.get("ee_pose", {})
    normalized_pose = _extract_ee_pose(
        payload,
        fallback={
            "position": dict(fallback_pose.get("position", {})),
            "orientation": dict(fallback_pose.get("orientation", {})),
            "reference_frame": str(fallback_pose.get("reference_frame", "base_link")),
        },
    )
    for optional_key in ("gripper_force", "gripper_closed", "holding_object", "estop_reason"):
        if optional_key in fallback_pose and optional_key not in normalized_pose:
            normalized_pose[optional_key] = fallback_pose[optional_key]
    if isinstance(payload.get("ee_pose"), Mapping):
        for optional_key in ("gripper_force", "gripper_closed", "holding_object", "estop_reason"):
            if optional_key in payload["ee_pose"]:
                normalized_pose[optional_key] = payload["ee_pose"][optional_key]
    return {
        "joint_positions": _extract_joint_positions(payload, fallback=list(fallback_state.get("joint_positions", []))),
        "ee_pose": normalized_pose,
    }


def _normalize_telemetry_payload(payload: Mapping[str, Any], *, fallback_state: RobotState) -> dict[str, Any]:
    telemetry = payload.get("telemetry") if isinstance(payload.get("telemetry"), Mapping) else payload
    normalized: dict[str, Any] = {
        "temperature_c": _safe_float(telemetry.get("temperature_c")),
        "motor_current_a": _safe_float(telemetry.get("motor_current_a")),
        "position_error_m": _safe_float(telemetry.get("position_error_m")),
        "connection_ok": _safe_bool(telemetry.get("connection_ok"), default=True),
        "heartbeat_ok": _safe_bool(telemetry.get("heartbeat_ok"), default=True),
    }
    if telemetry.get("error_code") not in (None, "", 0, "0", False):
        normalized["error_code"] = telemetry.get("error_code")
    joint_positions = fallback_state.get("joint_positions", [])
    if len(joint_positions) >= 2:
        normalized["joint_velocities"] = [0.0 for _ in joint_positions]
    return normalized


def _import_lerobot_robot_factory(pythonpath: str):
    if pythonpath.strip() and pythonpath not in sys.path:
        sys.path.insert(0, pythonpath)

    try:
        import draccus  # type: ignore
        from lerobot.robots.config import RobotConfig  # type: ignore
        from lerobot.robots.utils import make_robot_from_config  # type: ignore
    except Exception as exc:  # pragma: no cover - external dependency
        raise AdapterError(
            "lerobot_local adapter 缺少 draccus/lerobot 依赖，请补充 robot_pythonpath 或安装依赖"
        ) from exc

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


def _build_local_lerobot_controller(config_path: str, pythonpath: str):
    if not config_path.strip():
        raise AdapterError("lerobot_local adapter 需要配置 robot_config")
    draccus, robot_config_type, make_robot_from_config = _import_lerobot_robot_factory(pythonpath)
    try:
        robot_config = draccus.parse(config_class=robot_config_type, config_path=config_path, args=[])
        robot = make_robot_from_config(robot_config)
        try:
            robot.connect(calibrate=False)
        except TypeError:
            robot.connect()
        return robot
    except Exception as exc:  # pragma: no cover - external dependency
        raise AdapterError(f"lerobot_local adapter 初始化失败: {exc}") from exc


class BaseRobotAdapter:
    """Minimal robot adapter boundary for phase-2 execution wiring."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        self._config = config
        self._estopped = False
        self._last_stop_reason = ""

    @property
    def adapter_name(self) -> str:
        return "robot_adapter"

    @property
    def estopped(self) -> bool:
        return self._estopped

    @property
    def last_stop_reason(self) -> str:
        return self._last_stop_reason

    @property
    def supports_joint_action_dispatch(self) -> bool:
        return False

    def connection_summary(self) -> dict[str, Any]:
        return {"mode": "abstract", "connected": not self._estopped}

    def sync_state(self) -> RobotState:
        raise NotImplementedError

    def load_state(self, robot_state: RobotState) -> RobotState:
        raise NotImplementedError

    def snapshot_state(self) -> RobotState:
        raise NotImplementedError

    def move_to_pose(self, pose: CartesianPose) -> RobotState:
        raise NotImplementedError

    def move_home(self) -> RobotState:
        raise NotImplementedError

    def rotate_servo(self, servo_id: int, degrees: float) -> RobotState:
        raise NotImplementedError

    def close_gripper(self, force: float) -> RobotState:
        raise NotImplementedError

    def open_gripper(self) -> RobotState:
        raise NotImplementedError

    def get_action_feature_order(self) -> list[str]:
        raise AdapterError(f"{self.adapter_name} 不支持读取关节动作特征顺序")

    def dispatch_joint_action(self, action: Mapping[str, float]) -> RobotState:
        raise AdapterError(f"{self.adapter_name} 不支持下发底层 joint action")

    def read_telemetry(self) -> dict[str, Any]:
        raise NotImplementedError

    def emergency_stop(self, reason: str) -> None:
        raise NotImplementedError

    def clear_emergency_stop(self) -> None:
        raise NotImplementedError


class MockLeRobotAdapter(BaseRobotAdapter):
    """In-memory mock of a LeRobot-compatible robot adapter."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        super().__init__(config)
        self._holding_object = False
        self._state: RobotState = {
            "joint_positions": list(config.home_joint_positions),
            "ee_pose": {
                "position": {
                    **config.home_pose,
                },
                "orientation": dict(config.default_orientation),
                "reference_frame": "base_link",
            },
        }

    @property
    def adapter_name(self) -> str:
        return "mock_lerobot"

    @property
    def supports_joint_action_dispatch(self) -> bool:
        return True

    def connection_summary(self) -> dict[str, Any]:
        return {"mode": "mock", "connected": True}

    def _ensure_ready(self) -> None:
        if self._estopped:
            raise AdapterError("机器人处于急停状态，请人工复位后再执行。")

    def _with_retry(self, action_name: str, operation: Callable[[], T]) -> T:
        attempts = self._config.communication_retries + 1
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                self._ensure_ready()
                return operation()
            except AdapterError as error:
                last_error = error
        raise AdapterError(f"{action_name} 通讯重试失败: {last_error}") from last_error

    def sync_state(self) -> RobotState:
        return deepcopy(self._state)

    def load_state(self, robot_state: RobotState) -> RobotState:
        self._state = deepcopy(robot_state)
        return deepcopy(self._state)

    def snapshot_state(self) -> RobotState:
        return deepcopy(self._state)

    def move_to_pose(self, pose: CartesianPose) -> RobotState:
        def operation() -> RobotState:
            self._state["ee_pose"] = {
                "position": {
                    "x": pose["x"],
                    "y": pose["y"],
                    "z": pose["z"],
                },
                "orientation": dict(pose["orientation"]),
                "reference_frame": str(self._state["ee_pose"].get("reference_frame", "base_link")),
            }
            return deepcopy(self._state)

        return self._with_retry("move_to", operation)

    def move_home(self) -> RobotState:
        def operation() -> RobotState:
            self._state["joint_positions"] = list(self._config.home_joint_positions)
            self._state["ee_pose"] = {
                "position": {
                    **self._config.home_pose,
                },
                "orientation": dict(self._config.default_orientation),
                "reference_frame": "base_link",
            }
            return deepcopy(self._state)

        return self._with_retry("move_home", operation)

    def rotate_servo(self, servo_id: int, degrees: float) -> RobotState:
        def operation() -> RobotState:
            joint_positions = list(self._state.get("joint_positions", []))
            joint_index = servo_id - 1
            if joint_index >= len(joint_positions):
                raise AdapterError(f"舵机 {servo_id} 不存在，无法执行旋转。")
            joint_positions[joint_index] = float(joint_positions[joint_index]) + _servo_delta_for_joint_positions(
                joint_positions,
                degrees,
            )
            self._state["joint_positions"] = joint_positions
            return deepcopy(self._state)

        return self._with_retry("servo_rotate", operation)

    def close_gripper(self, force: float) -> RobotState:
        def operation() -> RobotState:
            self._holding_object = force >= max(self._config.min_force, 5.0)
            ee_pose = dict(self._state["ee_pose"])
            ee_pose["gripper_force"] = force
            ee_pose["gripper_closed"] = True
            ee_pose["holding_object"] = self._holding_object
            self._state["ee_pose"] = ee_pose
            return deepcopy(self._state)

        return self._with_retry("grasp", operation)

    def open_gripper(self) -> RobotState:
        def operation() -> RobotState:
            self._holding_object = False
            ee_pose = dict(self._state["ee_pose"])
            ee_pose["gripper_force"] = 0.0
            ee_pose["gripper_closed"] = False
            ee_pose["holding_object"] = self._holding_object
            self._state["ee_pose"] = ee_pose
            return deepcopy(self._state)

        return self._with_retry("release", operation)

    def get_action_feature_order(self) -> list[str]:
        joint_positions = list(self._state.get("joint_positions", []))
        return [f"joint_{index + 1}.pos" for index in range(len(joint_positions))]

    def dispatch_joint_action(self, action: Mapping[str, float]) -> RobotState:
        def operation() -> RobotState:
            feature_order = self.get_action_feature_order()
            index_by_feature = {name: index for index, name in enumerate(feature_order)}
            joint_positions = list(self._state.get("joint_positions", []))
            for feature_name, target_value in action.items():
                joint_index = index_by_feature.get(str(feature_name))
                if joint_index is None or joint_index >= len(joint_positions):
                    raise AdapterError(f"mock adapter 不存在动作特征 {feature_name}")
                joint_positions[joint_index] = _safe_float(target_value, default=joint_positions[joint_index])
            self._state["joint_positions"] = joint_positions
            return deepcopy(self._state)

        return self._with_retry("joint_action", operation)

    def read_telemetry(self) -> dict[str, Any]:
        return {
            "temperature_c": 32.0,
            "motor_current_a": 1.2,
            "position_error_m": 0.001,
            "connection_ok": True,
            "heartbeat_ok": True,
        }

    def emergency_stop(self, reason: str) -> None:
        self._estopped = True
        self._last_stop_reason = reason
        ee_pose = dict(self._state["ee_pose"])
        ee_pose["estop_reason"] = reason
        self._state["ee_pose"] = ee_pose

    def clear_emergency_stop(self) -> None:
        self._estopped = False
        self._last_stop_reason = ""


class BridgeRobotAdapter(BaseRobotAdapter):
    def __init__(
        self,
        config: ExecutionSafetyConfig,
        *,
        transport=_default_transport,
    ) -> None:
        super().__init__(config)
        self._transport = transport
        self._state: RobotState = {
            "joint_positions": list(config.home_joint_positions),
            "ee_pose": {
                "position": dict(config.home_pose),
                "orientation": dict(config.default_orientation),
                "reference_frame": "base_link",
            },
        }

    @property
    def adapter_name(self) -> str:
        return "mcp_bridge"

    def connection_summary(self) -> dict[str, Any]:
        return {
            "mode": "bridge",
            "base_url": self._config.robot_base_url,
            "connected": not self._estopped,
        }

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        body: dict[str, Any] | None = None,
        timeout_s: float | None = None,
    ) -> dict[str, Any]:
        raw_body = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        status, _, response_body = self._transport(
            method=method,
            url=url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                **dict(self._config.robot_headers),
            },
            body=raw_body,
            timeout_s=timeout_s if timeout_s is not None else self._config.robot_timeout_s,
        )
        payload = _decode_json_body(response_body)
        if status >= 400 or payload.get("ok") is False:
            raise AdapterError(f"机器人桥接调用失败: {status} {payload.get('message', '')}".strip())
        return payload

    def _state_from_payload(self, payload: Mapping[str, Any]) -> RobotState:
        state_payload = payload.get("robot_state")
        if not isinstance(state_payload, Mapping):
            state_payload = payload.get("state")
        if not isinstance(state_payload, Mapping):
            state_payload = payload
        self._state = _normalize_robot_state_payload(state_payload, fallback_state=self._state)
        return deepcopy(self._state)

    def _dispatch_action(self, action_name: str, arguments: dict[str, Any]) -> RobotState:
        payload = self._request_json(
            method="POST",
            url=_resolve_endpoint(self._config.robot_base_url, suffix="/actions"),
            body={"action": action_name, "arguments": arguments},
        )
        return self._state_from_payload(payload)

    def sync_state(self) -> RobotState:
        payload = self._request_json(
            method="GET",
            url=_resolve_endpoint(self._config.robot_base_url, suffix="/state"),
        )
        return self._state_from_payload(payload)

    def load_state(self, robot_state: RobotState) -> RobotState:
        self._state = deepcopy(robot_state)
        return deepcopy(self._state)

    def snapshot_state(self) -> RobotState:
        return deepcopy(self._state)

    def move_to_pose(self, pose: CartesianPose) -> RobotState:
        return self._dispatch_action(
            "move_to",
            {
                "x": pose["x"],
                "y": pose["y"],
                "z": pose["z"],
                "orientation": dict(pose["orientation"]),
            },
        )

    def move_home(self) -> RobotState:
        return self._dispatch_action("move_home", {})

    def rotate_servo(self, servo_id: int, degrees: float) -> RobotState:
        return self._dispatch_action("servo_rotate", {"id": servo_id, "degrees": degrees})

    def close_gripper(self, force: float) -> RobotState:
        return self._dispatch_action("grasp", {"force": force})

    def open_gripper(self) -> RobotState:
        return self._dispatch_action("release", {})

    def read_telemetry(self) -> dict[str, Any]:
        payload = self._request_json(
            method="GET",
            url=_resolve_endpoint(self._config.robot_base_url, suffix="/telemetry"),
            timeout_s=self._config.telemetry_poll_timeout_s,
        )
        return _normalize_telemetry_payload(payload, fallback_state=self._state)

    def emergency_stop(self, reason: str) -> None:
        self._estopped = True
        self._last_stop_reason = reason
        try:
            self._request_json(
                method="POST",
                url=_resolve_endpoint(self._config.robot_base_url, suffix="/emergency-stop"),
                body={"reason": reason},
            )
        except AdapterError:
            pass
        self._state.setdefault("ee_pose", {})["estop_reason"] = reason

    def clear_emergency_stop(self) -> None:
        self._request_json(
            method="POST",
            url=_resolve_endpoint(self._config.robot_base_url, suffix="/clear-emergency-stop"),
            body={},
        )
        self._estopped = False
        self._last_stop_reason = ""


class LeRobotLocalAdapter(BaseRobotAdapter):
    def __init__(
        self,
        config: ExecutionSafetyConfig,
        *,
        controller_loader=_build_local_lerobot_controller,
    ) -> None:
        super().__init__(config)
        self._controller_loader = controller_loader
        self._controller = None
        self._state: RobotState = {
            "joint_positions": list(config.home_joint_positions),
            "ee_pose": {
                "position": dict(config.home_pose),
                "orientation": dict(config.default_orientation),
                "reference_frame": "base_link",
            },
        }

    @property
    def adapter_name(self) -> str:
        return "lerobot_local"

    @property
    def supports_joint_action_dispatch(self) -> bool:
        return True

    def connection_summary(self) -> dict[str, Any]:
        return {
            "mode": "local",
            "config_path": self._config.robot_config,
            "pythonpath": self._config.robot_pythonpath,
            "connected": self._controller is not None and not self._estopped,
        }

    def _ensure_ready(self) -> None:
        if self._estopped:
            raise AdapterError("机器人处于急停状态，请人工复位后再执行。")

    def _ensure_controller(self):
        self._ensure_ready()
        if self._controller is None:
            self._controller = self._controller_loader(self._config.robot_config, self._config.robot_pythonpath)
        return self._controller

    def _call_controller(self, *method_names: str, default: Any = None, **kwargs: Any) -> Any:
        controller = self._ensure_controller()
        for method_name in method_names:
            method = getattr(controller, method_name, None)
            if callable(method):
                return method(**kwargs)
        return default

    def _feature_order(self) -> list[str]:
        controller = self._ensure_controller()
        action_features = getattr(controller, "action_features", {})
        if isinstance(action_features, Mapping):
            ordered: list[str] = []
            gripper_features: list[str] = []
            for key, value in action_features.items():
                if not (isinstance(key, str) and key.endswith(".pos") and value in {float, int}):
                    continue
                if "gripper" in key.lower():
                    gripper_features.append(key)
                else:
                    ordered.append(key)
            return [*ordered, *gripper_features]
        return []

    def _gripper_feature_name(self) -> str | None:
        for name in self._feature_order():
            if "gripper" in name.lower():
                return name
        return None

    def get_action_feature_order(self) -> list[str]:
        feature_order = self._feature_order()
        if not feature_order:
            raise AdapterError("本地机器人控制器缺少 action_features，无法映射 SmolVLA 输出")
        return feature_order

    def _controller_motor_name_by_servo_id(self, servo_id: int) -> str | None:
        controller = self._ensure_controller()
        bus = getattr(controller, "bus", None)
        motors = getattr(bus, "motors", None)
        if not isinstance(motors, Mapping):
            return None
        for motor_name, motor in motors.items():
            if getattr(motor, "id", None) == servo_id:
                return str(motor_name)
        return None

    def _precheck_hardware_servo_limits(self, servo_id: int, degrees: float) -> None:
        controller = self._ensure_controller()
        bus = getattr(controller, "bus", None)
        if bus is None or not callable(getattr(bus, "read", None)):
            return

        motor_name = self._controller_motor_name_by_servo_id(servo_id)
        if not motor_name:
            return

        motor = getattr(bus, "motors", {}).get(motor_name)
        model = getattr(motor, "model", "")
        max_resolution = int(getattr(bus, "model_resolution_table", {}).get(model, 0)) - 1
        if max_resolution <= 0:
            return

        try:
            current_raw = int(bus.read("Present_Position", motor_name, normalize=False))
            current_degrees = float(bus.read("Present_Position", motor_name, normalize=True))
            min_raw = int(bus.read("Min_Position_Limit", motor_name, normalize=False))
            max_raw = int(bus.read("Max_Position_Limit", motor_name, normalize=False))
        except Exception:
            return

        target_raw = current_raw + _degrees_to_raw_delta(max_resolution, degrees)
        if min_raw <= target_raw <= max_raw:
            return

        target_degrees = current_degrees + float(degrees)
        raise AdapterError(
            "舵机 "
            f"{servo_id} 目标超出硬件限位: 当前 {current_degrees:.2f}°, "
            f"请求 {float(degrees):+.2f}°, 目标 {target_degrees:.2f}°, "
            f"原始目标 {target_raw}, 允许范围 [{min_raw}, {max_raw}]。"
        )

    def _send_joint_action(self, action: dict[str, float]) -> RobotState:
        controller = self._ensure_controller()
        send_action = getattr(controller, "send_action", None)
        if not callable(send_action):
            raise AdapterError("本地机器人控制器未实现 send_action")
        send_action(action)
        return self._wait_for_joint_targets(action)

    def dispatch_joint_action(self, action: Mapping[str, float]) -> RobotState:
        normalized_action = {str(key): float(value) for key, value in action.items()}
        if not normalized_action:
            raise AdapterError("joint action 不能为空")
        return self._send_joint_action(normalized_action)

    def _wait_for_joint_targets(self, action: Mapping[str, float]) -> RobotState:
        feature_order = self._feature_order()
        index_by_feature = {name: index for index, name in enumerate(feature_order)}
        target_indices = {
            index_by_feature[name]: float(target)
            for name, target in action.items()
            if name in index_by_feature
        }
        if not target_indices:
            return self.sync_state()

        deadline = perf_counter() + max(float(self._config.action_timeout_s), 0.1)
        last_state = self.sync_state()
        joint_positions = list(last_state.get("joint_positions", []))
        tolerance = math.radians(0.75) if not _joint_positions_use_degrees(joint_positions) else 0.75

        while True:
            joint_positions = list(last_state.get("joint_positions", []))
            if all(
                joint_index < len(joint_positions)
                and abs(_safe_float(joint_positions[joint_index]) - target_value) <= tolerance
                for joint_index, target_value in target_indices.items()
            ):
                return deepcopy(last_state)
            if perf_counter() >= deadline:
                return deepcopy(last_state)
            sleep(0.05)
            last_state = self.sync_state()

    def sync_state(self) -> RobotState:
        controller = self._ensure_controller()
        for method_name in ("get_state", "sync_state"):
            method = getattr(controller, method_name, None)
            if callable(method):
                payload = method()
                if isinstance(payload, Mapping):
                    self._state = _normalize_robot_state_payload(payload, fallback_state=self._state)
                    return deepcopy(self._state)
        observation = getattr(controller, "get_observation", None)
        if not callable(observation):
            raise AdapterError("本地机器人控制器未实现 get_state/sync_state/get_observation")
        payload = {"observation": observation()}
        self._state = _normalize_robot_state_payload(payload, fallback_state=self._state)
        return deepcopy(self._state)

    def load_state(self, robot_state: RobotState) -> RobotState:
        self._state = deepcopy(robot_state)
        return deepcopy(self._state)

    def snapshot_state(self) -> RobotState:
        return deepcopy(self._state)

    def move_to_pose(self, pose: CartesianPose) -> RobotState:
        result = self._call_controller("move_to_pose", "dispatch_cartesian_pose", default=None, pose=pose)
        if isinstance(result, Mapping):
            self._state = _normalize_robot_state_payload(result, fallback_state=self._state)
            return deepcopy(self._state)
        raise AdapterError("本地机器人控制器未实现笛卡尔 move_to_pose，请改用桥接适配器或自定义控制器")

    def move_home(self) -> RobotState:
        result = self._call_controller("move_home", default=None)
        if isinstance(result, Mapping):
            self._state = _normalize_robot_state_payload(result, fallback_state=self._state)
            return deepcopy(self._state)

        feature_order = self._feature_order()
        if feature_order and len(feature_order) >= len(self._config.home_joint_positions):
            target_action = {
                feature_name: float(self._config.home_joint_positions[index])
                for index, feature_name in enumerate(feature_order[: len(self._config.home_joint_positions)])
            }
            return self._send_joint_action(target_action)
        raise AdapterError("本地机器人控制器未实现 move_home，且无法从 action_features 推导回零动作")

    def rotate_servo(self, servo_id: int, degrees: float) -> RobotState:
        self._precheck_hardware_servo_limits(servo_id, degrees)
        result = self._call_controller("rotate_servo", default=None, servo_id=servo_id, degrees=degrees)
        if isinstance(result, Mapping):
            self._state = _normalize_robot_state_payload(result, fallback_state=self._state)
            return deepcopy(self._state)

        feature_order = self._feature_order()
        joint_index = servo_id - 1
        if joint_index >= len(feature_order):
            raise AdapterError(f"本地机器人控制器缺少舵机 {servo_id} 的 action feature")
        current_state = self.sync_state()
        joint_positions = list(current_state.get("joint_positions", []))
        if joint_index >= len(joint_positions):
            raise AdapterError(f"本地机器人状态缺少舵机 {servo_id} 的当前位置")
        target_action = {
            feature_order[joint_index]: float(joint_positions[joint_index])
            + _servo_delta_for_joint_positions(joint_positions, degrees)
        }
        return self._send_joint_action(target_action)

    def close_gripper(self, force: float) -> RobotState:
        result = self._call_controller("close_gripper", "grasp", default=None, force=force)
        if isinstance(result, Mapping):
            self._state = _normalize_robot_state_payload(result, fallback_state=self._state)
            return deepcopy(self._state)

        gripper_feature = self._gripper_feature_name()
        if not gripper_feature:
            raise AdapterError("本地机器人控制器未实现 close_gripper，且 action_features 中没有 gripper 关节")
        return self._send_joint_action({gripper_feature: max(0.0, min(100.0, force))})

    def open_gripper(self) -> RobotState:
        result = self._call_controller("open_gripper", "release", default=None)
        if isinstance(result, Mapping):
            self._state = _normalize_robot_state_payload(result, fallback_state=self._state)
            return deepcopy(self._state)

        gripper_feature = self._gripper_feature_name()
        if not gripper_feature:
            raise AdapterError("本地机器人控制器未实现 open_gripper，且 action_features 中没有 gripper 关节")
        return self._send_joint_action({gripper_feature: 0.0})

    def read_telemetry(self) -> dict[str, Any]:
        result = self._call_controller("read_telemetry", "get_telemetry", default=None)
        if isinstance(result, Mapping):
            return _normalize_telemetry_payload(result, fallback_state=self._state)
        return {
            "temperature_c": 0.0,
            "motor_current_a": 0.0,
            "position_error_m": 0.0,
            "connection_ok": True,
            "heartbeat_ok": True,
        }

    def emergency_stop(self, reason: str) -> None:
        self._estopped = True
        self._last_stop_reason = reason
        controller = self._controller
        if controller is not None:
            method = getattr(controller, "emergency_stop", None)
            if callable(method):
                try:
                    method(reason=reason)
                except Exception:
                    pass
        self._state.setdefault("ee_pose", {})["estop_reason"] = reason

    def clear_emergency_stop(self) -> None:
        controller = self._controller
        if controller is not None:
            method = getattr(controller, "clear_emergency_stop", None)
            if callable(method):
                try:
                    method()
                except Exception:
                    pass
        self._estopped = False
        self._last_stop_reason = ""


RobotAdapterFactory = Callable[[ExecutionSafetyConfig], BaseRobotAdapter]


_ADAPTER_FACTORIES: dict[str, RobotAdapterFactory] = {
    "mock_lerobot": MockLeRobotAdapter,
    "mcp_bridge": BridgeRobotAdapter,
    "lerobot_local": LeRobotLocalAdapter,
}


def register_robot_adapter(adapter_name: str, factory: RobotAdapterFactory) -> None:
    _ADAPTER_FACTORIES[adapter_name] = factory


def build_robot_adapter(config: ExecutionSafetyConfig) -> BaseRobotAdapter:
    factory = _ADAPTER_FACTORIES.get(config.robot_adapter)
    if factory is None:
        raise AdapterError(f"不支持的 robot adapter: {config.robot_adapter}")
    return factory(config)
