"""Mock execution tools with validation, safety checks, and adapter integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from embodied_agent.shared.config import AppConfig
from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig, build_execution_safety_config
from .robot_adapter import AdapterError, MockLeRobotAdapter
from .safety import SafetyError, SafetyManager
from .smolvla import MockSmolVLAAdapter, SmolVLAError
from .types import CartesianPose, ExecutionToolResult, ToolName
from .validators import (
    ValidationError,
    validate_cartesian_pose,
    validate_force,
    validate_image_reference,
    validate_robot_state,
    validate_task_description,
)


@dataclass(slots=True)
class ExecutionRuntime:
    """Stateful runtime hosting the phase-1 execution tools."""

    config: ExecutionSafetyConfig
    adapter: MockLeRobotAdapter
    safety: SafetyManager
    smolvla: MockSmolVLAAdapter

    @classmethod
    def create(cls, app_config: AppConfig | None = None) -> "ExecutionRuntime":
        shared_execution = app_config.execution if app_config is not None else None
        config = build_execution_safety_config(shared_execution)
        return cls(
            config=config,
            adapter=MockLeRobotAdapter(config),
            safety=SafetyManager(config),
            smolvla=MockSmolVLAAdapter(config),
        )

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
    ) -> ExecutionToolResult:
        telemetry = self.adapter.read_telemetry()
        return {
            "status": "success",
            "action_name": action_name,
            "tool_name": action_name,
            "message": message,
            "logs": logs,
            "mock": True,
            "validated_params": validated_params or {},
            "safety_checks": safety_checks or [],
            "telemetry": telemetry,
            "robot_state": robot_state,
            "executed_plan": executed_plan or [],
        }

    def _failure(self, action_name: ToolName, error: Exception, logs: list[str]) -> ExecutionToolResult:
        self.adapter.emergency_stop(f"{action_name}: {error}")
        state = self.adapter.snapshot_state()
        return {
            "status": "failed",
            "action_name": action_name,
            "tool_name": action_name,
            "message": str(error),
            "logs": logs + [f"安全链触发急停: {error}"],
            "mock": True,
            "error_code": error.__class__.__name__,
            "robot_state": state,
        }

    def _run_guarded(
        self,
        action_name: ToolName,
        operation: Callable[[list[str]], ExecutionToolResult],
    ) -> ExecutionToolResult:
        logs = [f"{action_name}: 开始执行 mock 工具。"]
        try:
            return operation(logs)
        except (ValidationError, SafetyError, AdapterError, SmolVLAError) as error:
            return self._failure(action_name, error, logs)
        except Exception as error:  # pragma: no cover - 兜底保护
            return self._failure(action_name, RuntimeError(f"未预期异常: {error}"), logs)

    def move_to(self, x: Any, y: Any, z: Any, orientation: Any) -> ExecutionToolResult:
        def operation(logs: list[str]) -> ExecutionToolResult:
            current_state = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            pose = validate_cartesian_pose(x, y, z, orientation, self.config)
            safety_checks = self.safety.preflight_motion(pose, current_state)
            logs.append("参数校验与运动前安全检查通过。")
            robot_state = self.adapter.move_to_pose(pose)
            safety_checks += self.safety.ensure_telemetry_safe(self.adapter.read_telemetry())
            logs.append("已通过 mock LeRobot 适配器下发 move_to。")
            return self._success(
                "move_to",
                "末端执行器已移动到目标 mock 位姿。",
                logs,
                robot_state=robot_state,
                validated_params=pose,
                safety_checks=safety_checks,
            )

        return self._run_guarded("move_to", operation)

    def move_home(self) -> ExecutionToolResult:
        def operation(logs: list[str]) -> ExecutionToolResult:
            current_state = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            safety_checks = self.safety.preflight_home(current_state)
            robot_state = self.adapter.move_home()
            safety_checks += self.safety.ensure_telemetry_safe(self.adapter.read_telemetry())
            logs.append("已通过预定义安全路径回零。")
            return self._success(
                "move_home",
                "机器人已回到安全 home 位姿。",
                logs,
                robot_state=robot_state,
                validated_params={},
                safety_checks=safety_checks,
            )

        return self._run_guarded("move_home", operation)

    def grasp(self, force: Any) -> ExecutionToolResult:
        def operation(logs: list[str]) -> ExecutionToolResult:
            _ = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            grasp_force = validate_force(force, self.config)
            safety_checks = self.safety.preflight_grasp(grasp_force)
            robot_state = self.adapter.close_gripper(grasp_force)
            safety_checks += self.safety.ensure_telemetry_safe(self.adapter.read_telemetry())
            logs.append("已通过 mock LeRobot 适配器闭合夹爪。")
            return self._success(
                "grasp",
                "夹爪 mock 抓取完成。",
                logs,
                robot_state=robot_state,
                validated_params={"force": grasp_force},
                safety_checks=safety_checks,
            )

        return self._run_guarded("grasp", operation)

    def release(self) -> ExecutionToolResult:
        def operation(logs: list[str]) -> ExecutionToolResult:
            _ = self.adapter.sync_state()
            logs.append("已同步机器人状态。")
            safety_checks = self.safety.preflight_release()
            robot_state = self.adapter.open_gripper()
            safety_checks += self.safety.ensure_telemetry_safe(self.adapter.read_telemetry())
            logs.append("已通过 mock LeRobot 适配器打开夹爪。")
            return self._success(
                "release",
                "夹爪 mock 释放完成。",
                logs,
                robot_state=robot_state,
                validated_params={},
                safety_checks=safety_checks,
            )

        return self._run_guarded("release", operation)

    def run_smolvla(
        self,
        task_description: Any,
        current_image: Any,
        robot_state: Any,
    ) -> ExecutionToolResult:
        def operation(logs: list[str]) -> ExecutionToolResult:
            validated_task = validate_task_description(task_description)
            validated_image = validate_image_reference(current_image)
            validated_robot_state = validate_robot_state(robot_state)
            logs.append("SmolVLA 输入校验通过。")

            plan = self.smolvla.plan(validated_task, validated_image, validated_robot_state)
            logs.append(f"SmolVLA mock 生成 {len(plan)} 个动作。")

            final_state = self.adapter.sync_state()
            plan_logs: list[str] = []
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

            safety_checks = self.safety.ensure_telemetry_safe(self.adapter.read_telemetry())
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
            )

        return self._run_guarded("run_smolvla", operation)


_DEFAULT_RUNTIME = ExecutionRuntime.create()


def get_runtime() -> ExecutionRuntime:
    return _DEFAULT_RUNTIME


def move_to(x: Any, y: Any, z: Any, orientation: Any) -> ExecutionToolResult:
    return get_runtime().move_to(x, y, z, orientation)


def move_home() -> ExecutionToolResult:
    return get_runtime().move_home()


def grasp(force: Any) -> ExecutionToolResult:
    return get_runtime().grasp(force)


def release() -> ExecutionToolResult:
    return get_runtime().release()


def run_smolvla(task_description: Any, current_image: Any, robot_state: Any) -> ExecutionToolResult:
    return get_runtime().run_smolvla(task_description, current_image, robot_state)
