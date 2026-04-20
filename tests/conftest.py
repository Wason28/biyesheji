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
            "position": {
                "x": 0.15,
                "y": 0.05,
                "z": 0.22,
            },
            "orientation": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "w": 1.0,
            },
            "reference_frame": "base_link",
        },
    }
