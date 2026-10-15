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
from holostudio.tracking.types import HandFrame, Landmark, TrackingState

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


# Image heights per metre of the scripted hands at the scanned distance.
SCRIPTED_SCALE = 3.0
ASPECT = 16 / 9


def world_of(hand: tuple[Landmark, ...]) -> tuple[Landmark, ...]:
    """A flat 3D shape in metres that matches the scripted image hand."""
    wrist = hand[0]
    return tuple(
        Landmark((p.x - wrist.x) * ASPECT / SCRIPTED_SCALE, (p.y - wrist.y) / SCRIPTED_SCALE, 0.0)
        for p in hand
    )


def at_distance(hand: tuple[Landmark, ...], distance: float) -> tuple[Landmark, ...]:
    """The same hand `distance` times as far from the webcam: smaller around the fingertip."""
    tip = hand[8]
    return tuple(
        Landmark(tip.x + (p.x - tip.x) / distance, tip.y + (p.y - tip.y) / distance, p.z)
        for p in hand
    )


class ScriptedTracking:
    """Stands in for TrackingWorker; the script sets the current hands."""

    def __init__(self) -> None:
        self.hands: tuple = ()
        self.world_hands: tuple = ()  # 3D shapes (metres), only when the script sets them
        self.other_hands: tuple = ()  # someone farther away (set aside by the filter)
        self.timestamp = 0.0
        self.started = False

    @property
    def state(self) -> TrackingState:
        if not self.hands:
            return TrackingState(
                "no-hand",
                "Đưa bàn tay vào giữa khung hình.",
                HandFrame(other_hands=self.other_hands, timestamp=self.timestamp),
            )
        frame = HandFrame(
            self.hands,
            ("Right",) * len(self.hands),
            self.timestamp,
            self.other_hands,
            self.world_hands,
            ASPECT,
        )
        return TrackingState("tracking", f"Đã nhận diện {len(self.hands)}/2 bàn tay.", frame)

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
    # First start: no scanned hand yet, so the scan panel asks for one.
    checks["the first start asks to scan the hand"] = controller.scanning
    scan_hand = make_hand("open-palm", 0.55, 0.25)
    tracking.world_hands = (world_of(scan_hand),)
    frames(40, (at_distance(scan_hand, 1.3),))  # open palm held still in the box
    tracking.world_hands = ()
    frames(3)
    scanned = controller.profile
    checks["an open palm held in the box is scanned and saved"] = (
        scanned is not None
        and abs(scanned.reference_scale - SCRIPTED_SCALE / 1.3) < 0.05
        and (data_dir / "hand_profile.json").exists()
    )
    dwell_on("scan.done")

    # Someone farther away points at a button: their hand is set aside, nothing happens.
    x, y = centre_of("menu.add")
    tracking.other_hands = (make_hand("point", x, y),)
    frames(40)
    tracking.other_hands = ()
    checks["a farther person's hand does nothing"] = controller.panel is None

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
    checks["without 3D landmarks, drag keeps depth"] = abs(box_after[2] - box_before[2]) < 1e-6

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

    # Join the sphere and the cylinder by hand, then split them again.
    def pinch_tap(position) -> None:
        x, y = screen_of(position)
        frames(4, (make_hand("pinch", x, y),))
        frames(3, (make_hand("point", x, y),))

    dwell_on("menu.group")
    pinch_tap(controller.scene.find("sphere-1").position)
    pinch_tap(controller.scene.find("cylinder-1").position)
    picked = list(controller.group_picks)
    dwell_on("group.confirm")
    group = controller.scene.selected
    checks["pinch taps pick objects and Ghép joins them"] = (
        "sphere-1" in picked
        and "cylinder-1" in picked
        and group is not None
        and group.kind == "group"
        and controller.scene.find("sphere-1") is None
    )
    dwell_on("menu.ungroup")
    checks["Tách splits the group back"] = (
        controller.scene.find("sphere-1") is not None
        and controller.scene.find("cylinder-1") is not None
        and all(obj.kind != "group" for obj in controller.scene.objects)
    )

    # The scanned virtual hand: a pinch must really touch the box, then drags it in depth.
    from holostudio.avatar.profile import HandProfile, bone_lengths

    shape = world_of(make_hand("pinch", 0.5, 0.5))
    controller.profile = HandProfile(bone_lengths(shape), SCRIPTED_SCALE)
    rig = app.scene_view.view_rig()

    def depth_of(position) -> float:
        return float((np.asarray(position) - rig.origin) @ rig.forward)

    def hand3d(gesture: str, position, distance: float):
        x, y = screen_of(position)
        image = at_distance(make_hand(gesture, x, y), distance)
        return image, world_of(make_hand(gesture, x, y))

    def frames3d(count: int, *hands) -> None:
        tracking.world_hands = tuple(world for _image, world in hands)
        frames(count, tuple(image for image, _world in hands))

    box = controller.scene.find("box-1").position
    box_distance = depth_of(box) / rig.reach
    frames3d(4, hand3d("open-palm", box, box_distance))
    checks["a scanned hand is drawn as a 3D hand"] = bool(app.virtual_hands) and any(
        not node.path.isHidden() for node in app.hand_view._nodes
    )
    frames3d(8, hand3d("pinch", box, box_distance * 0.55))  # in the air, in front of it
    frames3d(3, hand3d("open-palm", box, box_distance * 0.55))
    checks["a pinch in front of the box grabs nothing"] = (
        controller.scene.find("box-1").position == box
    )

    frames3d(8, hand3d("pinch", box, box_distance))  # fingertips on the box
    for step in range(1, 16):
        frames3d(1, hand3d("pinch", box, box_distance * (1 - 0.02 * step)))
    frames3d(3, hand3d("open-palm", box, box_distance * 0.7))
    tracking.world_hands = ()
    frames(3)
    moved = controller.scene.find("box-1").position
    checks["a touching pinch pulls the box toward the viewer"] = depth_of(moved) < depth_of(
        box
    ) - 1.0 and np.allclose(screen_of(moved), screen_of(box), atol=0.03)
    controller.key("control-z")
    checks["the whole 3D drag is one undo step"] = controller.scene.find("box-1").position == box

    controller.profile = scanned
    dwell_on("menu.scan")
    dwell_on("scan.off")
    checks["Tắt tay 3D goes back to the cursor"] = (
        controller.profile is None and not (data_dir / "hand_profile.json").exists()
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
