"""Headless end-to-end run with a scripted virtual hand.

    python -m holostudio.app.smoke [screenshot.png]

Drives the real pipeline (gestures -> pointer/manipulator -> controller ->
3D view and HUD) offscreen, checks the outcome, and prints frame timings as JSON.
Only the webcam and MediaPipe are replaced by scripted landmarks.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from panda3d.core import Filename, loadPrcFileData

from holostudio.calibration.flow import save_calibrated
from holostudio.camera.capture import Frame
from holostudio.tracking.types import DesignerInfo, HandFrame, Landmark, TrackingState

FINGERS = ((5, 6, 8, 0.38), (9, 10, 12, 0.47), (13, 14, 16, 0.56), (17, 18, 20, 0.65))


def make_hand(gesture: str, screen_x: float, screen_y: float) -> tuple[Landmark, ...]:
    """A hand doing `gesture` with the index fingertip at a screen point."""
    extended = {"point": (0,), "pinch": (0,), "open-palm": (0, 1, 2, 3), "fist": ()}[gesture]
    hand = [Landmark(0.5, 0.7, 0)] * 21
    hand[0] = Landmark(0.5, 0.9, 0)
    hand[4] = Landmark(0.2, 0.5, 0)
    for index, (mcp, pip, tip, x) in enumerate(FINGERS):
        hand[mcp] = Landmark(x, 0.64, 0)
        hand[pip] = Landmark(x, 0.5, 0)
        hand[tip] = Landmark(x, 0.18 if index in extended else 0.72, 0)
    if gesture == "pinch":
        hand[4] = Landmark(hand[8].x - 0.01, hand[8].y, 0)
    # Shift so the fingertip lands on the target (camera x is mirrored on screen).
    dx, dy = (1 - screen_x) - hand[8].x, screen_y - hand[8].y
    return tuple(Landmark(p.x + dx, p.y + dy, p.z) for p in hand)


class ScriptedTracking:
    """Stands in for TrackingWorker; the script sets the current hands.

    Choosing a designer records them as a candidate who must be confirmed; hands
    listed in `stranger_hands` belong to someone else in front of the camera.
    """

    def __init__(self) -> None:
        self.hands: tuple = ()
        self.timestamp = 0.0
        self.started = False
        self.designer_status = "unset"
        self.stranger_hands: set[int] = set()

    @property
    def state(self) -> TrackingState:
        designer = DesignerInfo(self.designer_status, self.designer_status)
        if not self.hands:
            return TrackingState("no-hand", "Đưa bàn tay vào giữa khung hình.", designer=designer)
        frame = HandFrame(
            self.hands,
            ("Right",) * len(self.hands),
            self.timestamp,
            tuple(i not in self.stranger_hands for i in range(len(self.hands))),
        )
        message = f"Đã nhận diện {len(self.hands)}/2 bàn tay."
        return TrackingState("tracking", message, frame, designer)

    def request_designer(self) -> None:
        self.designer_status = "pending"

    def confirm_designer(self) -> None:
        if self.designer_status == "pending":
            self.designer_status = "locked"

    def cancel_designer(self) -> None:
        self.designer_status = "unset"

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.started = False


class ScriptedCamera:
    status = "active"
    message = "Camera đang hoạt động trên thiết bị."
    active = True

    def __init__(self) -> None:
        self.index = 0

    def latest_frame(self) -> Frame:
        self.index += 1
        image = np.zeros((360, 640, 3), np.uint8)
        image[:, :, 1] = 60
        return Frame(image, time.monotonic(), self.index)

    def start(self) -> None: ...
    def stop(self) -> None: ...


@dataclass
class Clock:
    now: float = 0.0

    def __call__(self) -> float:
        return self.now


def run(screenshot: Path | None = None) -> dict:
    loadPrcFileData("", "window-type offscreen\nwin-size 1280 720\naudio-library-name null")
    from holostudio.app.studio import StudioApp

    data_dir = Path(tempfile.mkdtemp(prefix="holostudio-smoke-"))
    save_calibrated(data_dir / "settings.json")
    clock = Clock()
    tracking = ScriptedTracking()
    app = StudioApp(
        camera=ScriptedCamera(),
        tracking=tracking,
        data_dir=data_dir,
        pick_file=lambda: None,
        clock=clock,
    )
    frame_times: list[float] = []

    def frames(count: int, hands=()) -> None:
        tracking.hands = hands
        for _ in range(count):
            clock.now += 1 / 30
            tracking.timestamp = clock.now
            started = time.perf_counter()
            app.step()
            app.graphicsEngine.renderFrame()
            frame_times.append(time.perf_counter() - started)

    def centre_of(widget_id: str) -> tuple[float, float]:
        widget = next(w for w in app.widgets if w.id == widget_id)
        width, height = app.win.getXSize(), app.win.getYSize()
        return (
            (widget.rect.x + widget.rect.w / 2) / width,
            (widget.rect.y + widget.rect.h / 2) / height,
        )

    def dwell_on(widget_id: str) -> None:
        x, y = centre_of(widget_id)
        frames(40, (make_hand("point", x, y),))  # 40 frames at 30 fps > 1 s dwell
        frames(3)  # hand leaves

    controller = app.controller
    checks: dict[str, bool] = {}

    frames(3)
    dwell_on("menu.add")
    checks["hands are locked until a designer is chosen"] = controller.panel is None

    dwell_on("menu.designer")
    checks["a recorded designer waits for confirmation"] = (
        tracking.designer_status == "pending"
        and any(w.id == "designer.confirm" for w in app.widgets)
    )

    tracking.stranger_hands = {0}
    dwell_on("designer.confirm")
    checks["a stranger cannot confirm"] = tracking.designer_status == "pending"
    tracking.stranger_hands = set()

    dwell_on("designer.confirm")
    checks["the recorded person confirms and is locked"] = (
        tracking.designer_status == "locked"
        and not any(w.id == "designer.confirm" for w in app.widgets)
    )

    tracking.stranger_hands = {0}
    dwell_on("menu.add")
    checks["a stranger's hand is ignored"] = controller.panel is None
    tracking.stranger_hands = set()

    dwell_on("menu.add")
    checks["dwell opens the add panel"] = controller.panel == "add"

    dwell_on("shape.sphere")
    checks["dwell adds a shape"] = len(controller.scene.objects) == 4
    added = controller.scene.selected

    dwell_on("menu.delete")
    checks["dwell deletes the selected object"] = (
        len(controller.scene.objects) == 3 and controller.toast is not None
    )

    dwell_on("toast.undo")
    checks["undo toast restores it"] = (
        added is not None and controller.scene.find(added.id) is not None
    )

    from panda3d.core import Point2, Point3

    from holostudio.rendering.transforms import scene_to_panda

    def screen_of(position) -> tuple[float, float]:
        camera_space = app.camera.getRelativePoint(app.render, Point3(*scene_to_panda(position)))
        projected = Point2()
        app.camLens.project(camera_space, projected)
        return ((projected.x + 1) / 2, (1 - projected.y) / 2)

    dwell_on("panel.close")
    box_before = controller.scene.find("box-1").position
    bx, by = screen_of(box_before)
    for step in range(20):
        frames(1, (make_hand("pinch", bx + 0.01 * step, by),))
    frames(3, (make_hand("open-palm", bx + 0.2, by),))
    frames(3)
    box_after = controller.scene.find("box-1").position
    checks["pinch drags the box sideways"] = box_after[0] > box_before[0] + 0.5
    checks["drag keeps depth"] = abs(box_after[2] - box_before[2]) < 1e-6

    undo_depth = len(controller.history.past)
    controller.key("control-z")
    checks["the whole drag is one undo step"] = (
        controller.scene.find("box-1").position == box_before
        and len(controller.history.past) == undo_depth - 1
    )

    # Fist holds the selected box; the other hand swipes an open palm to the right.
    rotation_before = controller.scene.find("box-1").rotation
    position_before = controller.scene.find("box-1").position
    holder = make_hand("fist", bx, by)
    for step in range(30):
        frames(1, (holder, make_hand("open-palm", 0.45 + 0.008 * step, 0.55)))
    frames(3, (make_hand("open-palm", bx, by),))  # the holding hand opens: let go
    frames(3)
    rotation_after = controller.scene.find("box-1").rotation
    turned = max(abs(a - b) for a, b in zip(rotation_after, rotation_before, strict=True))
    checks["fist + swipe turns the box"] = turned > 0.5
    checks["turning does not move the box"] = (
        controller.scene.find("box-1").position == position_before
    )
    controller.key("control-z")
    checks["the whole turn is one undo step"] = (
        controller.scene.find("box-1").rotation == rotation_before
    )

    dwell_on("menu.toggle")
    checks["menu collapses to one button"] = controller.collapsed and not any(
        w.id == "menu.add" for w in app.widgets
    )
    dwell_on("menu.toggle")

    frames(5)
    if screenshot:
        app.win.saveScreenshot(Filename.fromOsSpecific(str(screenshot)))

    controller.save()
    checks["scene saved to disk"] = (data_dir / "scene.json").exists()
    app.close_studio()

    ms = sorted(t * 1000 for t in frame_times[5:])
    return {
        "checks": checks,
        "frames": len(frame_times),
        "frame_ms_median": round(ms[len(ms) // 2], 2),
        "frame_ms_p95": round(ms[int(len(ms) * 0.95)], 2),
    }


if __name__ == "__main__":
    result = run(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if all(result["checks"].values()) else 1)
