"""Execution tools with phase-2 contracts, adapter factories, and safety boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from embodied_agent.shared.config import AppConfig
from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig, build_execution_safety_config
from .robot_adapter import AdapterError, BaseRobotAdapter, build_robot_adapter
from .safety import SafetyError, SafetyManager
from .smolvla import BaseSmolVLAAdapter, SmolVLAError, build_smolvla_backend
from .types import (
    ActionContract,
    CapabilityContract,
    CapabilityName,
    ExecutionToolResult,
    ModelActionTrace,
    SafetyBoundary,
    SafetyStage,
    ToolName,
)
from .validators import (
    ValidationError,
    validate_cartesian_pose,
    validate_force,
    validate_image_reference,
    validate_robot_state,
    validate_servo_rotation,
    validate_task_description,
)

_ACTION_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["status", "action_name", "message", "logs", "robot_state"],
}

_ACTION_CONTRACTS: dict[ToolName, ActionContract] = {
    "move_to": {
        "action_name": "move_to",
        "tool_name": "move_to",
        "description": "移动末端执行器到指定笛卡尔位姿。",
        "input_schema": {
            "type": "object",
            "required": ["x", "y", "z"],
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
                "orientation": {"type": ["object", "array"]},
            },
        },
        "output_schema": _ACTION_OUTPUT_SCHEMA,
        "capability_names": ["pick_and_place"],
        "safety_stages": ["input_validation", "preflight", "adapter_dispatch", "telemetry_check"],
        "estop_on_failure": True,
    },
    "move_home": {
        "action_name": "move_home",
        "tool_name": "move_home",
        "description": "按照安全路径回零。",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "output_schema": _ACTION_OUTPUT_SCHEMA,
        "capability_names": ["pick_and_place", "return_home"],
        "safety_stages": ["preflight", "adapter_dispatch", "telemetry_check"],
        "estop_on_failure": True,
    },
    "grasp": {
        "action_name": "grasp",
        "tool_name": "grasp",
        "description": "执行夹爪抓取。",
        "input_schema": {
            "type": "object",
            "properties": {
                "force": {"type": "number"},
            },
        },
        "output_schema": _ACTION_OUTPUT_SCHEMA,
        "capability_names": ["pick_and_place"],
        "safety_stages": ["input_validation", "preflight", "adapter_dispatch", "telemetry_check"],
        "estop_on_failure": True,
    },
    "servo_rotate": {
        "action_name": "servo_rotate",
        "tool_name": "servo_rotate",
        "description": "按舵机 id 旋转指定角度。",
        "input_schema": {
            "type": "object",
            "required": ["id", "degrees"],
            "properties": {
                "id": {"type": "integer", "minimum": 1},
                "degrees": {"type": "number"},
            },
            "additionalProperties": False,
        },
        "output_schema": _ACTION_OUTPUT_SCHEMA,
        "capability_names": ["servo_control"],
        "safety_stages": ["input_validation", "preflight", "adapter_dispatch", "telemetry_check"],
        "estop_on_failure": True,
    },
    "release": {
        "action_name": "release",
        "tool_name": "release",
        "description": "执行夹爪释放。",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "output_schema": _ACTION_OUTPUT_SCHEMA,
        "capability_names": ["pick_and_place", "release_object"],
        "safety_stages": ["preflight", "adapter_dispatch", "telemetry_check"],
        "estop_on_failure": True,
    },
    "clear_emergency_stop": {
        "action_name": "clear_emergency_stop",
        "tool_name": "clear_emergency_stop",
        "description": "清除急停锁存并重新同步机器人状态。",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "output_schema": _ACTION_OUTPUT_SCHEMA,
        "capability_names": [],
        "safety_stages": ["adapter_dispatch", "telemetry_check"],
        "estop_on_failure": False,
    },
    "run_smolvla": {
        "action_name": "run_smolvla",
        "tool_name": "run_smolvla",
        "description": "调用固定 SmolVLA 执行抓取能力。",
        "input_schema": {
            "type": "object",
            "required": ["task_description", "current_image", "robot_state"],
            "properties": {
                "task_description": {"type": "string"},
                "current_image": {"type": "string"},
                "robot_state": {"type": "object"},
            },
        },
        "output_schema": _ACTION_OUTPUT_SCHEMA,
        "capability_names": ["pick_and_place"],
        "safety_stages": ["input_validation", "preflight", "adapter_dispatch", "telemetry_check"],
        "estop_on_failure": True,
    },
}

_CAPABILITY_CONTRACTS: dict[CapabilityName, CapabilityContract] = {
    "pick_and_place": {
        "capability_name": "pick_and_place",
        "description": "调用固定 SmolVLA 能力完成桌面抓取与放置。",
        "default_action": "run_smolvla",
        "available_actions": ["run_smolvla", "move_to", "grasp", "release", "move_home"],
        "execution_mode": "vla",
        "required_tools": ["run_smolvla"],
        "fixed_model": True,
    },
    "return_home": {
        "capability_name": "return_home",
        "description": "沿安全路径回到 home 位姿。",
        "default_action": "move_home",
        "available_actions": ["move_home"],
        "execution_mode": "atomic",
        "required_tools": ["move_home"],
        "fixed_model": False,
    },
    "release_object": {
        "capability_name": "release_object",
        "description": "保持当前位姿并释放夹爪。",
        "default_action": "release",
        "available_actions": ["release"],
        "execution_mode": "atomic",
        "required_tools": ["release"],
        "fixed_model": False,
    },
    "servo_control": {
        "capability_name": "servo_control",
        "description": "按舵机 id 执行单关节安全旋转。",
        "default_action": "servo_rotate",
        "available_actions": ["servo_rotate"],
        "execution_mode": "atomic",
        "required_tools": ["servo_rotate"],
        "fixed_model": False,
    },
}

_DEFAULT_CAPABILITY_BY_ACTION: dict[ToolName, CapabilityName] = {
    "move_home": "return_home",
    "release": "release_object",
    "servo_rotate": "servo_control",
    "run_smolvla": "pick_and_place",
}


@dataclass(slots=True)
class ExecutionRuntime:
    """Stateful runtime hosting execution tools with stable contracts."""

    config: ExecutionSafetyConfig
    adapter: BaseRobotAdapter
    safety: SafetyManager
    smolvla: BaseSmolVLAAdapter

    @classmethod
    def create(
        cls,
        app_config: AppConfig | None = None,
        *,
        adapter_factory: Callable[[ExecutionSafetyConfig], BaseRobotAdapter] | None = None,
        smolvla_factory: Callable[[ExecutionSafetyConfig], BaseSmolVLAAdapter] | None = None,
    ) -> "ExecutionRuntime":
        shared_execution = app_config.execution if app_config is not None else None
        config = build_execution_safety_config(shared_execution)
        adapter_builder = adapter_factory or build_robot_adapter
        smolvla_builder = smolvla_factory or build_smolvla_backend
        return cls(
            config=config,
            adapter=adapter_builder(config),
            safety=SafetyManager(config),
            smolvla=smolvla_builder(config),
        )

    @property
    def is_mock(self) -> bool:
        return self.adapter.adapter_name.startswith("mock_") and self.smolvla.backend_name.startswith("mock_")

    def get_action_contract(self, action_name: ToolName) -> ActionContract:
        return dict(_ACTION_CONTRACTS[action_name])

    def list_capabilities(self) -> list[CapabilityContract]:
        return [dict(contract) for contract in _CAPABILITY_CONTRACTS.values()]

    def describe_safety_boundary(
        self,
        *,
        checked_stages: list[SafetyStage] | None = None,
    ) -> SafetyBoundary:
        return self.safety.describe_boundary(
            adapter_name=self.adapter.adapter_name,
            smolvla_backend=self.smolvla.backend_name,
            checked_stages=checked_stages,
            estop_engaged=self.adapter.estopped,
            stop_reason=self.adapter.last_stop_reason or None,
        )

    def describe_runtime_profile(self) -> dict[str, Any]:
        return {
            "adapter": {
                "name": self.adapter.adapter_name,
                "config_path": self.config.robot_config,
                "communication_retries": self.config.communication_retries,
                "connection": self.adapter.connection_summary(),
            },
            "smolvla_backend": {
                "name": self.smolvla.backend_name,
                "model_path": self.config.vla_model_path,
                "fixed_model": True,
            },
            "safety_boundary": self.describe_safety_boundary(),
        }

    def describe_execution_model(self) -> dict[str, Any]:
        return {
            "name": "SmolVLA",
            "model_path": self.config.vla_model_path,
            "backend": self.smolvla.backend_name,
            "adapter": self.adapter.adapter_name,
            "mutable": False,
            "capability_names": ["pick_and_place"],
        }

    def _resolve_capability_name(self, action_name: ToolName) -> CapabilityName | None:
        return _DEFAULT_CAPABILITY_BY_ACTION.get(action_name)

    def _build_contract_payload(self, action_name: ToolName) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "action_contract": self.get_action_contract(action_name),
        }
        capability_name = self._resolve_capability_name(action_name)
        if capability_name is not None:
            payload["capability_name"] = capability_name
            payload["capability_contract"] = dict(_CAPABILITY_CONTRACTS[capability_name])
        return payload

    def _success(
        self,
        action_name: ToolName,
        message: str,
        logs: list[str],
        *,
        robot_state: RobotState,
        validated_params: dict[str, Any] | None = None,
        safety_checks: list[str] | None = None,
        executed_plan: list[dict[str, Any]] | None = None,
        model_actions: list[ModelActionTrace] | None = None,
        checked_stages: list[SafetyStage] | None = None,
    ) -> ExecutionToolResult:
        telemetry = self.adapter.read_telemetry()
        result: ExecutionToolResult = {
            "status": "success",
            "action_name": action_name,
            "tool_name": action_name,
            "message": message,
            "logs": logs,
            "mock": self.is_mock,
            "validated_params": validated_params or {},
            "safety_checks": safety_checks or [],
            "telemetry": telemetry,
            "robot_state": robot_state,
            "executed_plan": executed_plan or [],
            "model_actions": model_actions or [],
            "safety_boundary": self.describe_safety_boundary(checked_stages=checked_stages or []),
        }
        result.update(self._build_contract_payload(action_name))
        return result

    def _read_telemetry(self) -> dict[str, Any]:
        return dict(self.adapter.read_telemetry())

    def _run_precheck(
        self,
        *,
        action_name: ToolName,
        robot_state: RobotState,
        logs: list[str],
        checked_stages: list[SafetyStage],
    ) -> tuple[list[str], dict[str, Any]]:
        checked_stages.append("preflight")
        telemetry = self._read_telemetry()
        safety_checks = self.safety.safety_precheck(
            action_name=action_name,
            robot_state=robot_state,
            telemetry=telemetry,
            estop_engaged=self.adapter.estopped,
            stop_reason=self.adapter.last_stop_reason or None,
        )
        if not self.is_mock:
            logs.append("真实链路安全前置检查通过。")
        return safety_checks, telemetry

    def _failure(
        self,
        action_name: ToolName,
        error: Exception,
        logs: list[str],
        *,
        checked_stages: list[SafetyStage] | None = None,
    ) -> ExecutionToolResult:
        self.adapter.emergency_stop(f"{action_name}: {error}")
        state = self.adapter.snapshot_state()
        boundary_stages = list(dict.fromkeys([*(checked_stages or []), "emergency_stop"]))
        result: ExecutionToolResult = {
            "status": "failed",
            "action_name": action_name,
            "tool_name": action_name,
            "message": str(error),
            "logs": logs + [f"安全链触发急停: {error}"],
            "mock": self.is_mock,
            "error_code": error.__class__.__name__,
            "robot_state": state,
            "safety_boundary": self.describe_safety_boundary(checked_stages=boundary_stages),
        }
        result.update(self._build_contract_payload(action_name))
        return result

    def _run_guarded(
        self,
        action_name: ToolName,
        operation: Callable[[list[str], list[SafetyStage]], ExecutionToolResult],
    ) -> ExecutionToolResult:
        logs = [f"{action_name}: 开始执行 {'mock' if self.is_mock else 'runtime'} 工具。"]
        checked_stages: list[SafetyStage] = []
        try:
            return operation(logs, checked_stages)
        except (ValidationError, SafetyError, AdapterError, SmolVLAError) as error:
            return self._failure(action_name, error, logs, checked_stages=checked_stages)
        except Exception as error:  # pragma: no cover - 兜底保护
            return self._failure(
                action_name,
                RuntimeError(f"未预期异常: {error}"),
                logs,
                checked_stages=checked_stages,
            )

    def move_to(self, x: Any, y: Any, z: Any, orientation: Any | None = None) -> ExecutionToolResult:
        def operation(logs: list[str], checked_stages: list[SafetyStage]) -> ExecutionToolResult:
            current_state = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            pose = validate_cartesian_pose(x, y, z, orientation, self.config)
            checked_stages.append("input_validation")
            safety_checks, _ = self._run_precheck(
                action_name="move_to",
                robot_state=current_state,
                logs=logs,
                checked_stages=checked_stages,
            )
            safety_checks += self.safety.preflight_motion(pose, current_state)
            logs.append("参数校验与运动前安全检查通过。")
            robot_state = self.adapter.move_to_pose(pose)
            checked_stages.append("adapter_dispatch")
            safety_checks += self.safety.ensure_telemetry_safe(self._read_telemetry())
            checked_stages.append("telemetry_check")
            logs.append(f"已通过 {self.adapter.adapter_name} 下发 move_to。")
            return self._success(
                "move_to",
                "末端执行器已移动到目标位姿。",
                logs,
                robot_state=robot_state,
                validated_params=pose,
                safety_checks=safety_checks,
                checked_stages=checked_stages,
            )

        return self._run_guarded("move_to", operation)

    def move_home(self) -> ExecutionToolResult:
        def operation(logs: list[str], checked_stages: list[SafetyStage]) -> ExecutionToolResult:
            current_state = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            safety_checks, _ = self._run_precheck(
                action_name="move_home",
                robot_state=current_state,
                logs=logs,
                checked_stages=checked_stages,
            )
            safety_checks += self.safety.preflight_home(current_state)
            robot_state = self.adapter.move_home()
            checked_stages.append("adapter_dispatch")
            safety_checks += self.safety.ensure_telemetry_safe(self._read_telemetry())
            checked_stages.append("telemetry_check")
            logs.append("已通过预定义安全路径回零。")
            return self._success(
                "move_home",
                "机器人已回到安全 home 位姿。",
                logs,
                robot_state=robot_state,
                validated_params={},
                safety_checks=safety_checks,
                checked_stages=checked_stages,
            )

        return self._run_guarded("move_home", operation)

    def grasp(self, force: Any | None = None) -> ExecutionToolResult:
        def operation(logs: list[str], checked_stages: list[SafetyStage]) -> ExecutionToolResult:
            current_state = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            grasp_force = validate_force(force, self.config)
            checked_stages.append("input_validation")
            safety_checks, _ = self._run_precheck(
                action_name="grasp",
                robot_state=current_state,
                logs=logs,
                checked_stages=checked_stages,
            )
            safety_checks += self.safety.preflight_grasp(grasp_force)
            robot_state = self.adapter.close_gripper(grasp_force)
            checked_stages.append("adapter_dispatch")
            safety_checks += self.safety.ensure_telemetry_safe(self._read_telemetry())
            checked_stages.append("telemetry_check")
            logs.append(f"已通过 {self.adapter.adapter_name} 闭合夹爪。")
            return self._success(
                "grasp",
                "夹爪抓取完成。",
                logs,
                robot_state=robot_state,
                validated_params={"force": grasp_force},
                safety_checks=safety_checks,
                checked_stages=checked_stages,
            )

        return self._run_guarded("grasp", operation)

    def servo_rotate(self, id: Any, degrees: Any) -> ExecutionToolResult:
        def operation(logs: list[str], checked_stages: list[SafetyStage]) -> ExecutionToolResult:
            current_state = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            validated = validate_servo_rotation(id, degrees, self.config)
            checked_stages.append("input_validation")
            safety_checks, _ = self._run_precheck(
                action_name="servo_rotate",
                robot_state=current_state,
                logs=logs,
                checked_stages=checked_stages,
            )
            safety_checks += self.safety.preflight_servo_rotation(
                int(validated["id"]),
                float(validated["degrees"]),
                current_state,
            )
            robot_state = self.adapter.rotate_servo(int(validated["id"]), float(validated["degrees"]))
            checked_stages.append("adapter_dispatch")
            safety_checks += self.safety.ensure_telemetry_safe(self._read_telemetry())
            checked_stages.append("telemetry_check")
            logs.append(f"已通过 {self.adapter.adapter_name} 下发 servo_rotate。")
            return self._success(
                "servo_rotate",
                f"舵机 {int(validated['id'])} 已旋转 {float(validated['degrees']):.2f}°。",
                logs,
                robot_state=robot_state,
                validated_params={
                    "id": int(validated["id"]),
                    "joint_index": int(validated["joint_index"]),
                    "degrees": float(validated["degrees"]),
                },
                safety_checks=safety_checks,
                checked_stages=checked_stages,
            )

        return self._run_guarded("servo_rotate", operation)

    def release(self) -> ExecutionToolResult:
        def operation(logs: list[str], checked_stages: list[SafetyStage]) -> ExecutionToolResult:
            current_state = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            safety_checks, _ = self._run_precheck(
                action_name="release",
                robot_state=current_state,
                logs=logs,
                checked_stages=checked_stages,
            )
            safety_checks += self.safety.preflight_release()
            robot_state = self.adapter.open_gripper()
            checked_stages.append("adapter_dispatch")
            safety_checks += self.safety.ensure_telemetry_safe(self._read_telemetry())
            checked_stages.append("telemetry_check")
            logs.append(f"已通过 {self.adapter.adapter_name} 打开夹爪。")
            return self._success(
                "release",
                "夹爪释放完成。",
                logs,
                robot_state=robot_state,
                validated_params={},
                safety_checks=safety_checks,
                checked_stages=checked_stages,
            )

        return self._run_guarded("release", operation)

    def clear_emergency_stop(self) -> ExecutionToolResult:
        def operation(logs: list[str], checked_stages: list[SafetyStage]) -> ExecutionToolResult:
            self.adapter.clear_emergency_stop()
            checked_stages.append("adapter_dispatch")
            logs.append("已清除急停锁存。")
            robot_state = self.adapter.sync_state()
            logs.append("已重新同步机器人状态。")
            safety_checks = self.safety.ensure_telemetry_safe(self._read_telemetry())
            checked_stages.append("telemetry_check")
            return self._success(
                "clear_emergency_stop",
                "机器人急停状态已清除。",
                logs,
                robot_state=robot_state,
                validated_params={},
                safety_checks=safety_checks,
                checked_stages=checked_stages,
            )

        return self._run_guarded("clear_emergency_stop", operation)

    def run_smolvla(
        self,
        task_description: Any,
        current_image: Any,
        robot_state: Any,
    ) -> ExecutionToolResult:
        def operation(logs: list[str], checked_stages: list[SafetyStage]) -> ExecutionToolResult:
            validated_task = validate_task_description(task_description)
            validated_image = validate_image_reference(current_image)
            validated_robot_state = validate_robot_state(robot_state)
            checked_stages.append("input_validation")
            self.adapter.load_state(validated_robot_state)
            logs.append("SmolVLA 输入校验通过，并已同步外部机器人状态。")

            if self.smolvla.supports_joint_actions:
                if not self.adapter.supports_joint_action_dispatch:
                    raise AdapterError(
                        f"{self.adapter.adapter_name} 不支持 SmolVLA 低层 joint action 执行，请改用 lerobot_local 适配器。"
                    )
                current_state = self.adapter.sync_state()
                logs.append("已同步机器人真实状态，准备执行 SmolVLA 低层动作块。")
                safety_checks, _ = self._run_precheck(
                    action_name="run_smolvla",
                    robot_state=current_state,
                    logs=logs,
                    checked_stages=checked_stages,
                )
                action_feature_names = self.adapter.get_action_feature_order()
                joint_actions = self.smolvla.infer_joint_actions(
                    validated_task,
                    validated_image,
                    current_state,
                    action_feature_names,
                )
                if not joint_actions:
                    raise SmolVLAError("SmolVLA 未生成任何可执行动作。")
                logs.append(f"SmolVLA 生成 {len(joint_actions)} 条底层 joint action。")

                final_state = current_state
                action_trace: list[ModelActionTrace] = []
                checked_stages.append("adapter_dispatch")
                for index, action in enumerate(joint_actions, start=1):
                    logs.append(f"执行 SmolVLA 动作 {index}/{len(joint_actions)}。")
                    final_state = self.adapter.dispatch_joint_action(action)
                    action_trace.append({"index": index, "targets": dict(action)})

                safety_checks += self.safety.ensure_telemetry_safe(self._read_telemetry())
                checked_stages.append("telemetry_check")
                logs.append("SmolVLA 底层动作块执行完成。")
                return self._success(
                    "run_smolvla",
                    "SmolVLA 底层动作执行成功。",
                    logs,
                    robot_state=final_state,
                    validated_params={
                        "task_description": validated_task,
                        "current_image": validated_image,
                    },
                    safety_checks=safety_checks,
                    model_actions=action_trace,
                    checked_stages=checked_stages,
                )

            plan = self.smolvla.plan(validated_task, validated_image, validated_robot_state)
            checked_stages.append("preflight")
            logs.append(f"SmolVLA mock 生成 {len(plan)} 个动作。")

            final_state = self.adapter.sync_state()
            plan_logs: list[str] = []
            checked_stages.append("adapter_dispatch")
            for index, step in enumerate(plan, start=1):
                tool_name = step["tool"]
                arguments = step["arguments"]
                logs.append(f"执行计划步骤 {index}: {tool_name}。")
                plan_logs.append(f"{index}. {tool_name}: {step['reason']}")
                if tool_name == "move_to":
                    result = self.move_to(**arguments)
                elif tool_name == "move_home":
                    result = self.move_home()
                elif tool_name == "grasp":
                    result = self.grasp(**arguments)
                elif tool_name == "release":
                    result = self.release()
                else:
                    raise SmolVLAError(f"SmolVLA 输出了未注册工具 {tool_name}。")

                logs.extend(result.get("logs", []))
                if result["status"] != "success":
                    raise SmolVLAError(
                        f"SmolVLA 执行在步骤 {index} 失败: {result.get('message', '未知错误')}"
                    )
                final_state = result["robot_state"]

            safety_checks = self.safety.ensure_telemetry_safe(self._read_telemetry())
            checked_stages.append("telemetry_check")
            logs.append("SmolVLA mock 动作序列执行完成。")
            return self._success(
                "run_smolvla",
                "SmolVLA mock 计划执行成功。",
                logs + plan_logs,
                robot_state=final_state,
                validated_params={
                    "task_description": validated_task,
                    "current_image": validated_image,
                },
                safety_checks=safety_checks,
                executed_plan=plan,
                checked_stages=checked_stages,
            )

        return self._run_guarded("run_smolvla", operation)


_DEFAULT_RUNTIME = ExecutionRuntime.create()


def get_runtime() -> ExecutionRuntime:
    return _DEFAULT_RUNTIME


def move_to(x: Any, y: Any, z: Any, orientation: Any | None = None) -> ExecutionToolResult:
    return get_runtime().move_to(x, y, z, orientation)


def move_home() -> ExecutionToolResult:
    return get_runtime().move_home()


def grasp(force: Any | None = None) -> ExecutionToolResult:
    return get_runtime().grasp(force)


def servo_rotate(id: Any, degrees: Any) -> ExecutionToolResult:
    return get_runtime().servo_rotate(id, degrees)


def release() -> ExecutionToolResult:
    return get_runtime().release()


def run_smolvla(task_description: Any, current_image: Any, robot_state: Any) -> ExecutionToolResult:
    return get_runtime().run_smolvla(task_description, current_image, robot_state)


def clear_emergency_stop() -> ExecutionToolResult:
    return get_runtime().clear_emergency_stop()
