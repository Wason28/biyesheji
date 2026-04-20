"""Minimal MCP-style perception server entry for the mock-first runtime."""

from __future__ import annotations

import argparse
import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from embodied_agent.shared.config import AppConfig, PerceptionConfig, load_config

from .adapters import CameraAdapter, RobotStateAdapter, build_camera_adapter, build_robot_state_adapter
from .config import PerceptionRuntimeConfig, build_perception_runtime_config
from .contracts import (
    SceneDescriptionRequest,
    build_perception_error_envelope,
    build_perception_success_envelope,
    validate_image_payload,
    validate_robot_state_payload,
    validate_scene_description_payload,
)
from .errors import OutputValidationError, PerceptionError
from .providers import BaseVLMProvider, build_vlm_provider


@dataclass(frozen=True, slots=True)
class MCPToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class PerceptionMCPServer:
    """Mock MCP-style server that exposes the perception tool contract."""

    def __init__(
        self,
        perception_config: PerceptionConfig | PerceptionRuntimeConfig | AppConfig | None = None,
        *,
        camera: CameraAdapter | None = None,
        robot_state_client: RobotStateAdapter | None = None,
        camera_factory: Callable[[PerceptionRuntimeConfig], CameraAdapter] = build_camera_adapter,
        robot_state_factory: Callable[[PerceptionRuntimeConfig], RobotStateAdapter] = build_robot_state_adapter,
        provider_factory: Callable[[PerceptionRuntimeConfig], BaseVLMProvider] = build_vlm_provider,
    ) -> None:
        self.camera_factory = camera_factory
        self.robot_state_factory = robot_state_factory
        self.provider_factory = provider_factory
        self.perception_config = self._normalize_config(perception_config)
        self.runtime_config = self.perception_config
        self.camera = camera or self.camera_factory(self.perception_config)
        self.robot_state_client = robot_state_client or self.robot_state_factory(self.perception_config)
        self.provider = self.provider_factory(self.perception_config)
        self._tools = {tool.name: tool for tool in self.list_tools()}

    @staticmethod
    def _normalize_config(
        perception_config: PerceptionConfig | PerceptionRuntimeConfig | AppConfig | None,
    ) -> PerceptionRuntimeConfig:
        if isinstance(perception_config, AppConfig):
            return build_perception_runtime_config(perception_config.perception)
        if isinstance(perception_config, PerceptionRuntimeConfig):
            return perception_config
        return build_perception_runtime_config(perception_config)

    def reload_provider(self) -> None:
        self.provider = self.provider_factory(self.perception_config)

    def reload_runtime(
        self,
        perception_config: PerceptionConfig | PerceptionRuntimeConfig | AppConfig | None = None,
    ) -> None:
        if perception_config is not None:
            self.perception_config = self._normalize_config(perception_config)
            self.runtime_config = self.perception_config
        self.camera = self.camera_factory(self.perception_config)
        self.robot_state_client = self.robot_state_factory(self.perception_config)
        self.provider = self.provider_factory(self.perception_config)

    def runtime_summary(self) -> dict[str, Any]:
        return {
            "camera_backend": self.perception_config.camera_backend,
            "camera_device_id": self.perception_config.camera_device_id,
            "camera_frame_id": self.perception_config.camera_frame_id,
            "robot_state_backend": self.perception_config.robot_state_backend,
            "robot_state_topic": self.perception_config.robot_state_topic,
            "robot_state_base_frame": self.perception_config.robot_state_base_frame,
            "vlm_provider": self.perception_config.vlm_provider,
            "vlm_model": self.perception_config.vlm_model,
            "vlm_local_path": self.perception_config.vlm_local_path,
            "vlm_base_url": self.perception_config.vlm_base_url,
        }

    def list_tools(self) -> list[MCPToolSpec]:
        return [
            MCPToolSpec(
                name="get_image",
                description="采集当前相机图像并返回 base64 与元数据。",
                input_schema={"type": "object", "properties": {}, "additionalProperties": False},
                output_schema={
                    "type": "object",
                    "required": ["image_base64", "timestamp", "resolution", "camera_parameters"],
                },
            ),
            MCPToolSpec(
                name="get_robot_state",
                description="获取当前关节角与末端执行器位姿。",
                input_schema={"type": "object", "properties": {}, "additionalProperties": False},
                output_schema={"type": "object", "required": ["joint_positions", "ee_pose", "timestamp"]},
            ),
            MCPToolSpec(
                name="describe_scene",
                description="调用当前配置的 VLM provider 生成场景描述。",
                input_schema={
                    "type": "object",
                    "required": ["image"],
                    "properties": {
                        "image": {"type": "string"},
                        "prompt": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "required": [
                        "scene_description",
                        "provider",
                        "model",
                        "confidence",
                        "prompt_used",
                        "structured_observations",
                    ],
                },
            ),
        ]


    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if tool_name not in self._tools:
            return build_perception_error_envelope(
                tool_name=tool_name,
                code="PERCEPTION_TOOL_NOT_FOUND",
                message=f"未知工具: {tool_name}",
                retriable=False,
                details={"requested_tool_name": tool_name},
                status_code=404,
            )

        try:
            result = getattr(self, tool_name)(**arguments)
        except TypeError as exc:
            return build_perception_error_envelope(
                tool_name=tool_name,
                code="PERCEPTION_TOOL_ARGUMENT_ERROR",
                message=f"工具参数不合法: {tool_name}",
                retriable=False,
                details={"arguments": arguments, "reason": str(exc)},
                status_code=400,
            )
        except PerceptionError as exc:
            return build_perception_error_envelope(
                tool_name=tool_name,
                code=exc.code,
                message=exc.message,
                retriable=exc.retriable,
                details=exc.details,
            )

        return build_perception_success_envelope(
            tool_name,
            result,
            metadata={"runtime_config": self.runtime_summary()},
        )

    def get_image(self) -> dict[str, Any]:
        payload = self.camera.capture().to_payload()
        validate_image_payload(payload)
        return payload

    def get_robot_state(self) -> dict[str, Any]:
        payload = self.robot_state_client.read_state().to_payload()
        validate_robot_state_payload(payload)
        return payload

    def describe_scene(self, image: str, prompt: str | None = None) -> dict[str, Any]:
        if not isinstance(image, str) or not image.strip():
            raise OutputValidationError("describe_scene.image 必须是非空 base64 字符串", field="image")
        try:
            base64.b64decode(image, validate=True)
        except Exception as exc:
            raise OutputValidationError("describe_scene.image 必须是合法 base64 字符串", field="image") from exc
        request = SceneDescriptionRequest(image=image, prompt=prompt)
        payload = self.provider.describe_scene(request).to_payload()
        validate_scene_description_payload(payload)
        return payload


def build_server(
    app_config: AppConfig | PerceptionConfig | PerceptionRuntimeConfig | None = None,
    *,
    camera_factory: Callable[[PerceptionRuntimeConfig], CameraAdapter] = build_camera_adapter,
    robot_state_factory: Callable[[PerceptionRuntimeConfig], RobotStateAdapter] = build_robot_state_adapter,
    provider_factory: Callable[[PerceptionRuntimeConfig], BaseVLMProvider] = build_vlm_provider,
) -> PerceptionMCPServer:
    return PerceptionMCPServer(
        app_config,
        camera_factory=camera_factory,
        robot_state_factory=robot_state_factory,
        provider_factory=provider_factory,
    )


def create_server(config_path: str | Path | None = None) -> PerceptionMCPServer:
    if config_path is None:
        return PerceptionMCPServer()
    config = load_config(config_path)
    return PerceptionMCPServer(config)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase-1 perception MCP-style mock server")
    parser.add_argument("--config", type=str, help="配置文件路径", default=None)
    parser.add_argument("--list-tools", action="store_true", help="输出已注册工具")
    parser.add_argument("--tool", type=str, help="调用单个工具")
    parser.add_argument("--image", type=str, help="describe_scene 所需的 base64 图像")
    parser.add_argument("--prompt", type=str, help="describe_scene 可选提示词", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    server = create_server(args.config)

    if args.list_tools:
        print(
            json.dumps(
                [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                        "output_schema": tool.output_schema,
                    }
                    for tool in server.list_tools()
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.tool:
        payload = {"image": args.image, "prompt": args.prompt} if args.tool == "describe_scene" else {}
        print(json.dumps(server.call_tool(args.tool, payload), ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
