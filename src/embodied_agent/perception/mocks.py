"""Mock hardware adapters for phase-1 perception development."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from .contracts import CapturedImage, RobotStateSnapshot
from .errors import CameraDisconnectedError, RobotCommunicationError

MOCK_IMAGE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAusB9Y9N8i8AAAAASUVORK5CYII="
)


@dataclass(slots=True)
class MockCamera:
    camera_id: str = "mock_camera_rgb_01"
    width: int = 640
    height: int = 480
    fail_on_capture: bool = False

    def capture(self) -> CapturedImage:
        if self.fail_on_capture:
            raise CameraDisconnectedError(camera_id=self.camera_id)

        return CapturedImage(
            image_base64=MOCK_IMAGE_BASE64,
            timestamp=datetime.now(UTC).isoformat(),
            resolution={"width": self.width, "height": self.height},
            camera_parameters={
                "camera_id": self.camera_id,
                "frame_id": "camera_color_optical_frame",
                "fx": 615.0,
                "fy": 615.0,
                "cx": self.width / 2,
                "cy": self.height / 2,
                "distortion_model": "none",
            },
        )


@dataclass(slots=True)
class MockRobotStateClient:
    fail_on_read: bool = False

    def read_state(self) -> RobotStateSnapshot:
        if self.fail_on_read:
            raise RobotCommunicationError(robot="mock_arm")

        return RobotStateSnapshot(
            joint_positions=[0.0, -0.62, 0.91, -1.12, 0.44, 0.18],
            ee_pose={
                "position": {"x": 0.42, "y": -0.08, "z": 0.21},
                "orientation": {"x": 0.0, "y": 0.707, "z": 0.0, "w": 0.707},
                "reference_frame": "base_link",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
