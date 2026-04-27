"""SmolVLA backend boundary and mock implementation for execution."""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path
from typing import Callable

from embodied_agent.shared.types import RobotState

from .config import ExecutionSafetyConfig
from .types import PlannedAction


class SmolVLAError(RuntimeError):
    """Raised when SmolVLA planning fails."""


class BaseSmolVLAAdapter:
    """Minimal SmolVLA backend boundary for phase-2 execution wiring."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        self._config = config

    @property
    def backend_name(self) -> str:
        return "smolvla_backend"

    @property
    def supports_joint_actions(self) -> bool:
        return False

    def plan(
        self,
        task_description: str,
        current_image: str,
        robot_state: RobotState,
    ) -> list[PlannedAction]:
        raise NotImplementedError

    def infer_joint_actions(
        self,
        task_description: str,
        current_image: str,
        robot_state: RobotState,
        action_feature_names: list[str],
    ) -> list[dict[str, float]]:
        raise NotImplementedError


class MockSmolVLAAdapter(BaseSmolVLAAdapter):
    """Produces deterministic mock plans for local integration tests."""

    @property
    def backend_name(self) -> str:
        return "mock_smolvla"

    def plan(
        self,
        task_description: str,
        current_image: str,
        robot_state: RobotState,
    ) -> list[PlannedAction]:
        if not task_description.strip():
            raise SmolVLAError("任务描述为空，无法生成动作序列。")
        if not current_image.strip():
            raise SmolVLAError("图像引用为空，无法生成动作序列。")

        ee_pose = robot_state.get("ee_pose", {})
        position = ee_pose.get("position", {})
        current_x = float(position.get("x", 0.0))
        current_y = float(position.get("y", 0.0))
        current_z = float(position.get("z", self._config.home_pose["z"]))
        target_z = min(
            max(current_z - 0.05, self._config.workspace_limits["z"][0] + 0.05),
            self._config.workspace_limits["z"][1],
        )
        grasp_force = min(max(8.0, self._config.min_force), self._config.max_force)

        plan: list[PlannedAction] = [
            {
                "tool": "move_to",
                "arguments": {
                    "x": current_x,
                    "y": current_y,
                    "z": target_z,
                    "orientation": dict(self._config.default_orientation),
                },
                "reason": f"SmolVLA mock 对图像 {current_image} 生成接近目标的预抓取位姿。",
            }
        ]

        if "release" in task_description.lower():
            plan.append(
                {
                    "tool": "release",
                    "arguments": {},
                    "reason": "任务描述包含 release，执行释放动作。",
                }
            )
        else:
            plan.append(
                {
                    "tool": "grasp",
                    "arguments": {"force": grasp_force},
                    "reason": "默认抓取策略：闭合夹爪完成 mock 抓取。",
                }
            )

        plan.append(
            {
                "tool": "move_home",
                "arguments": {},
                "reason": "动作结束后回到安全 home 位姿。",
            }
        )
        return plan


def _ensure_lerobot_pythonpath(pythonpath: str) -> None:
    normalized = pythonpath.strip()
    if normalized and normalized not in sys.path:
        sys.path.insert(0, normalized)


def _resolve_model_dir(model_path: str) -> Path:
    candidate = Path(model_path).expanduser()
    if not candidate.exists():
        raise SmolVLAError(f"SmolVLA 模型路径不存在: {candidate}")
    if candidate.is_file():
        candidate = candidate.parent
    if (candidate / "model.safetensors").exists():
        return candidate
    pretrained_dir = candidate / "pretrained_model"
    if pretrained_dir.is_dir() and (pretrained_dir / "model.safetensors").exists():
        return pretrained_dir
    raise SmolVLAError(
        "SmolVLA 模型目录缺少 model.safetensors，"
        f"请将 execution.vla_model_path 指向 checkpoint 的 pretrained_model 目录: {candidate}"
    )


def _decode_base64_image(current_image: str):
    try:
        from PIL import Image
        import numpy as np
    except Exception as exc:  # pragma: no cover - external dependency
        raise SmolVLAError("缺少 PIL/numpy 依赖，无法解码当前图像。") from exc

    image_payload = current_image.strip()
    if "," in image_payload and image_payload.lower().startswith("data:image"):
        image_payload = image_payload.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(image_payload, validate=True)
    except Exception as exc:
        raise SmolVLAError("current_image 不是合法的 base64 图像。") from exc
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            return np.asarray(image.convert("RGB"))
    except Exception as exc:
        raise SmolVLAError("current_image 无法解码为 RGB 图像。") from exc


class LeRobotSmolVLAAdapter(BaseSmolVLAAdapter):
    """Loads a trained LeRobot SmolVLA checkpoint and produces low-level joint actions."""

    def __init__(self, config: ExecutionSafetyConfig) -> None:
        super().__init__(config)
        self._policy = None
        self._preprocessor = None
        self._postprocessor = None
        self._device = None

    @property
    def backend_name(self) -> str:
        return "lerobot_smolvla"

    @property
    def supports_joint_actions(self) -> bool:
        return True

    def _ensure_loaded(self) -> None:
        if self._policy is not None and self._preprocessor is not None and self._postprocessor is not None:
            return

        _ensure_lerobot_pythonpath(self._config.robot_pythonpath)
        model_dir = _resolve_model_dir(self._config.vla_model_path)
        try:
            import torch
            from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
            from lerobot.processor import PolicyProcessorPipeline
        except Exception as exc:  # pragma: no cover - external dependency
            raise SmolVLAError(
                "加载 LeRobot SmolVLA 依赖失败，请确认 execution.robot_pythonpath、torch、transformers 已可用。"
            ) from exc

        try:
            policy = SmolVLAPolicy.from_pretrained(str(model_dir), local_files_only=True)
            preprocessor = PolicyProcessorPipeline.from_pretrained(
                str(model_dir),
                config_filename="policy_preprocessor.json",
                local_files_only=True,
            )
            postprocessor = PolicyProcessorPipeline.from_pretrained(
                str(model_dir),
                config_filename="policy_postprocessor.json",
                local_files_only=True,
            )
        except Exception as exc:  # pragma: no cover - external dependency
            raise SmolVLAError(f"加载 SmolVLA checkpoint 失败: {exc}") from exc

        self._policy = policy
        self._preprocessor = preprocessor
        self._postprocessor = postprocessor
        self._device = torch.device(str(policy.config.device))

    def _build_observation(
        self,
        *,
        current_image: str,
        robot_state: RobotState,
    ) -> dict[str, object]:
        import numpy as np

        image_rgb = _decode_base64_image(current_image)
        joint_positions = robot_state.get("joint_positions", [])
        return {
            "observation.images.camera1": image_rgb,
            "observation.state": np.asarray(joint_positions, dtype=np.float32),
        }

    def infer_joint_actions(
        self,
        task_description: str,
        current_image: str,
        robot_state: RobotState,
        action_feature_names: list[str],
    ) -> list[dict[str, float]]:
        self._ensure_loaded()
        if self._policy is None or self._preprocessor is None or self._postprocessor is None or self._device is None:
            raise SmolVLAError("SmolVLA 推理链路未正确初始化。")

        try:
            from lerobot.policies.utils import prepare_observation_for_inference
        except Exception as exc:  # pragma: no cover - external dependency
            raise SmolVLAError("无法导入 LeRobot 观测预处理工具。") from exc

        observation = self._build_observation(
            current_image=current_image,
            robot_state=robot_state,
        )
        prepared_observation = prepare_observation_for_inference(
            observation,
            self._device,
            task=task_description,
            robot_type="",
        )
        processed_observation = self._preprocessor(prepared_observation)

        self._policy.reset()
        joint_actions: list[dict[str, float]] = []
        num_action_steps = int(getattr(self._policy.config, "n_action_steps", 1))
        for _ in range(max(num_action_steps, 1)):
            action_tensor = self._policy.select_action(processed_observation)
            action_tensor = self._postprocessor(action_tensor)
            action_values = action_tensor.squeeze(0).to("cpu").tolist()
            if len(action_values) > len(action_feature_names):
                raise SmolVLAError(
                    "SmolVLA 输出维度超过机器人 action_features，"
                    f"输出 {len(action_values)} 维，控制器仅提供 {len(action_feature_names)} 维。"
                )
            joint_actions.append(
                {
                    action_feature_names[index]: float(value)
                    for index, value in enumerate(action_values)
                }
            )

        return joint_actions


SmolVLAFactory = Callable[[ExecutionSafetyConfig], BaseSmolVLAAdapter]


_SMOLVLA_FACTORIES: dict[str, SmolVLAFactory] = {
    "mock_smolvla": MockSmolVLAAdapter,
    "lerobot_smolvla": LeRobotSmolVLAAdapter,
}


def register_smolvla_backend(backend_name: str, factory: SmolVLAFactory) -> None:
    _SMOLVLA_FACTORIES[backend_name] = factory


def build_smolvla_backend(config: ExecutionSafetyConfig) -> BaseSmolVLAAdapter:
    factory = _SMOLVLA_FACTORIES.get(config.smolvla_backend)
    if factory is None:
        raise SmolVLAError(f"不支持的 SmolVLA backend: {config.smolvla_backend}")
    return factory(config)
