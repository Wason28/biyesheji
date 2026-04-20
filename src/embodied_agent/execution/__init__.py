"""Phase-1 execution layer with mock MCP-style tools and server entrypoint."""

from .robot_adapter import BaseRobotAdapter, build_robot_adapter, register_robot_adapter
from .server import MockMCPServer, build_server
from .smolvla import BaseSmolVLAAdapter, build_smolvla_backend, register_smolvla_backend
from .tools import ExecutionRuntime, grasp, move_home, move_to, release, run_smolvla

__all__ = [
    "ExecutionRuntime",
    "MockMCPServer",
    "BaseRobotAdapter",
    "BaseSmolVLAAdapter",
    "build_server",
    "build_robot_adapter",
    "build_smolvla_backend",
    "register_robot_adapter",
    "register_smolvla_backend",
    "move_to",
    "move_home",
    "grasp",
    "release",
    "run_smolvla",
]
