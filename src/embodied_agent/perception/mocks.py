"""Mock hardware adapters for phase-1 perception development."""

from __future__ import annotations

import base64
import struct
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone

from .contracts import CapturedImage, RobotStateSnapshot
from .errors import CameraDisconnectedError, RobotCommunicationError

def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _build_mock_png_base64(*, width: int = 64, height: int = 64) -> str:
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = _png_chunk(
        b"IHDR",
        struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0),
    )

    rows: list[bytes] = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            red = min(255, 40 + x * 3)
            green = min(255, 60 + y * 2)
            blue = 180 if 16 < x < 48 and 16 < y < 48 else 90
            row.extend((red, green, blue))
        rows.append(b"\x00" + bytes(row))
    idat = _png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=9))
    iend = _png_chunk(b"IEND", b"")
    return base64.b64encode(header + ihdr + idat + iend).decode("ascii")


MOCK_IMAGE_BASE64 = _build_mock_png_base64()


@dataclass(slots=True)
class MockCamera:
    camera_id: str = "mock_camera_rgb_01"
    width: int = 640
    height: int = 480
    frame_id: str = "camera_color_optical_frame"
    fail_on_capture: bool = False

    def capture(self) -> CapturedImage:
        if self.fail_on_capture:
            raise CameraDisconnectedError(camera_id=self.camera_id)

        return CapturedImage(
            image_base64=MOCK_IMAGE_BASE64,
            timestamp=datetime.now(timezone.utc).isoformat(),
            resolution={"width": self.width, "height": self.height},
            camera_parameters={
                "camera_id": self.camera_id,
                "frame_id": self.frame_id,
                "fx": 615.0,
                "fy": 615.0,
                "cx": self.width / 2,
                "cy": self.height / 2,
                "distortion_model": "none",
            },
        )


@dataclass(slots=True)
class MockRobotStateClient:
    reference_frame: str = "base_link"
    fail_on_read: bool = False

    def read_state(self) -> RobotStateSnapshot:
        if self.fail_on_read:
            raise RobotCommunicationError(robot="mock_arm")

        return RobotStateSnapshot(
            joint_positions=[0.0, -0.62, 0.91, -1.12, 0.44, 0.18],
            ee_pose={
                "position": {"x": 0.42, "y": -0.08, "z": 0.21},
                "orientation": {"x": 0.0, "y": 0.707, "z": 0.0, "w": 0.707},
                "reference_frame": self.reference_frame,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
