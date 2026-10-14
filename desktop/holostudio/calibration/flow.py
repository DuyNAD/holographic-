"""First-run calibration: camera, hand in view, then a pinch. Can always be skipped."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CalibrationEffect = Literal["start-camera", "complete", "skip"] | None

STEP_COUNT = 5


@dataclass(frozen=True)
class CalibrationInputs:
    camera_active: bool
    camera_requesting: bool
    hand_tracked: bool
    pinch_seen: bool


@dataclass(frozen=True)
class CalibrationButton:
    action: str
    label: str
    enabled: bool = True


@dataclass(frozen=True)
class CalibrationView:
    step: int
    eyebrow: str
    title: str
    body: str
    check: str | None
    ready: bool
    buttons: tuple[CalibrationButton, ...]


SKIP = CalibrationButton("skip", "Bỏ qua, dùng chuột và bàn phím")


def describe(step: int, inputs: CalibrationInputs) -> CalibrationView:
    if step == 0:
        return CalibrationView(
            0,
            "Thiết lập lần đầu",
            "Sẵn sàng điều khiển không gian 3D?",
            "Quá trình hiệu chuẩn sẽ kiểm tra camera, vị trí bàn tay và cử chỉ chụm. "
            "Video chỉ được xử lý trên thiết bị của bạn.",
            None,
            False,
            (CalibrationButton("start", "Bắt đầu hiệu chuẩn"), SKIP),
        )
    if step == 1:
        ready = inputs.camera_active
        if ready:
            action = CalibrationButton("next", "Tiếp tục")
        elif inputs.camera_requesting:
            action = CalibrationButton("camera", "Đang kết nối…", enabled=False)
        else:
            action = CalibrationButton("camera", "Bật camera")
        return CalibrationView(
            1,
            "Bước 1 / 3",
            "Kết nối camera",
            "Đặt camera ngang tầm mắt và đảm bảo khuôn hình đủ sáng.",
            "Camera đã sẵn sàng" if ready else "Camera chưa kết nối",
            ready,
            (action, SKIP),
        )
    if step == 2:
        ready = inputs.hand_tracked
        return CalibrationView(
            2,
            "Bước 2 / 3",
            "Đưa tay vào khung hình",
            "Giữ bàn tay cách camera khoảng một cánh tay, mở lòng bàn tay và "
            "tránh để các ngón bị che khuất.",
            "Đã nhận diện bàn tay" if ready else "Đang tìm bàn tay…",
            ready,
            (
                CalibrationButton(
                    "next", "Tay đã ở đúng vị trí" if ready else "Đưa tay vào camera", ready
                ),
                SKIP,
            ),
        )
    if step == 3:
        ready = inputs.pinch_seen
        return CalibrationView(
            3,
            "Bước 3 / 3",
            "Thử cử chỉ chụm",
            "Chụm đầu ngón cái và ngón trỏ trong một giây. Đây là cử chỉ dùng để chọn "
            "và kéo vật thể.",
            "Chụm thành công" if ready else "Đang chờ cử chỉ chụm…",
            ready,
            (
                CalibrationButton(
                    "next", "Hoàn tất hiệu chuẩn" if ready else "Hãy thử chụm hai ngón", ready
                ),
                SKIP,
            ),
        )
    return CalibrationView(
        4,
        "Hiệu chuẩn hoàn tất",
        "Bạn đã sẵn sàng",
        "Trỏ ngón tay vào một nút và giữ yên 1 giây để bấm. Mở Hướng dẫn trong menu "
        "bên trái bất cứ lúc nào để xem lại các cử chỉ.",
        None,
        True,
        (CalibrationButton("finish", "Vào không gian thiết kế"),),
    )


class Calibration:
    def __init__(self, open_: bool) -> None:
        self.open = open_
        self.step = 0

    def restart(self) -> None:
        self.open = True
        self.step = 0

    def view(self, inputs: CalibrationInputs) -> CalibrationView:
        return describe(self.step, inputs)

    def press(self, action: str, inputs: CalibrationInputs) -> CalibrationEffect:
        """Applies a button press; returns the side effect the app must perform."""
        button = next((b for b in self.view(inputs).buttons if b.action == action), None)
        if not self.open or button is None or not button.enabled:
            return None
        if action == "skip":
            self.open = False
            return "skip"
        if action == "start":
            self.step = 1
        elif action == "camera":
            return "start-camera"
        elif action == "next":
            self.step = min(self.step + 1, STEP_COUNT - 1)
        elif action == "finish":
            self.open = False
            return "complete"
        return None


def load_calibrated(path: Path) -> bool:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("calibrated") is True
    except (OSError, ValueError, AttributeError):
        return False


def save_calibrated(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"calibrated": True}), encoding="utf-8")
    os.replace(temporary, path)
