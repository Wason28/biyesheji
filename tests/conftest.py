import pytest

from embodied_agent.shared.config import AppConfig


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig()


@pytest.fixture
def valid_robot_state() -> dict[str, object]:
    return {
        "joint_positions": [0.0, -0.2, 0.4, 0.0, 1.2, 0.0],
        "ee_pose": {
            "x": 0.15,
            "y": 0.05,
            "z": 0.22,
            "roll": 0.0,
            "pitch": 1.57,
            "yaw": 0.0,
        },
    }
