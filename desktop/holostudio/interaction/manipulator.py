"""Moves, rotates, and scales scene objects from stable hand gestures.

- Pinch one hand on an object: drag it.
- Fist one hand on an object (it holds it), then swipe the other hand with an open
  palm: the object turns in the direction of the swipe, around the screen's axes.
- Pinch both hands: scale the selected object.

Works purely in scene coordinates (x right, y up, z toward the viewer); the
rendering stage supplies picking, camera rays, and the camera's axes.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from holostudio.gestures.engine import StableGesture
from holostudio.scene.history import BeginInteraction, EndInteraction, HistoryAction
from holostudio.scene.rotation import turn_in_world
from holostudio.scene.state import SceneState, Select, SetPosition, SetRotation, SetScale

from .coordinates import ScreenPoint, landmark_distance, landmark_to_screen

Ray = tuple[np.ndarray, np.ndarray]  # origin, direction
Axes = tuple[np.ndarray, np.ndarray]  # camera right, camera up (scene coordinates)

# A swipe across the whole window turns the object one full turn.
TURN_PER_SCREEN = 2 * math.pi
# Palm movement (window fractions) ignored as hand jitter, so a still hand never drifts.
SWIPE_DEAD_ZONE = 0.004
# A holding fist may be lost this long (motion blur, a missed frame) without letting go.
HOLD_GRACE_SECONDS = 0.3
PALM_POINTS = (0, 5, 9, 13, 17)


@dataclass
class ViewQueries:
    """What the manipulator needs from the 3D view and the HUD."""

    pick: Callable[[ScreenPoint], str | None]
    ray: Callable[[ScreenPoint], Ray]
    over_hud: Callable[[ScreenPoint], bool]
    axes: Callable[[], Axes]


def intersect_depth_plane(ray: Ray, depth: float) -> np.ndarray | None:
    """Drags happen on a camera-facing plane at the object's depth (z stays the same)."""
    origin, direction = ray
    if abs(direction[2]) < 1e-9:
        return None
    t = (depth - origin[2]) / direction[2]
    if t < 0:
        return None
    return origin + direction * t


def palm_centre(gesture: StableGesture) -> ScreenPoint:
    points = [landmark_to_screen(gesture.landmarks[i]) for i in PALM_POINTS]
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def swipe_turn(rotation, axes: Axes, dx: float, dy: float):
    """Turns like spinning a globe: the object's near side follows the swipe.

    Swiping right turns around the camera's up axis; swiping down turns around the
    camera's right axis (screen y grows downwards).
    """
    right, up = axes
    rotation = turn_in_world(rotation, up, dx * TURN_PER_SCREEN)
    return turn_in_world(rotation, right, dy * TURN_PER_SCREEN)


class GestureManipulator:
    """Edits the scene with the hand that started the action.

    One hand "owns" a drag or hold until that same hand lets go, so the other hand
    (pointing, swiping, leaving the view) never interrupts it.
    """

    def __init__(
        self,
        view: ViewQueries,
        dispatch: Callable[[HistoryAction], None],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._view = view
        self._dispatch = dispatch
        self._clock = clock
        self._mode: str | None = None  # "drag", "hold" or "scale"
        self._hand_id: int | None = None
        self._owner_seen = 0.0
        # x/y: object offset from the hand ray hit; z: depth of the drag plane.
        self._drag_offset = np.zeros(3)
        self._scale_start: tuple[float, float] | None = None
        self._scale_hands: tuple[int, int] | None = None
        self._swipe_hand: int | None = None
        self._swipe_anchor: ScreenPoint | None = None
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    @property
    def mode(self) -> str | None:
        return self._mode

    @property
    def swiping(self) -> bool:
        return self._mode == "hold" and self._swipe_anchor is not None

    def _begin(self) -> None:
        if not self._active:
            self._dispatch(BeginInteraction())
            self._active = True

    def reset(self) -> None:
        """Ends the current action; it becomes one Undo step."""
        if self._active:
            self._dispatch(EndInteraction())
            self._active = False
        self._mode = None
        self._hand_id = None
        self._scale_start = None
        self._scale_hands = None
        self._swipe_hand = None
        self._swipe_anchor = None

    def update(self, gestures: tuple[StableGesture, ...], scene: SceneState) -> None:
        now = self._clock()
        by_hand = {g.track_id: g for g in gestures}
        pinches = sorted((g for g in gestures if g.name == "pinch"), key=lambda g: g.track_id)
        selected = scene.selected

        # Two pinching hands always mean scaling, and take over from a one-hand action.
        if len(pinches) >= 2 and selected:
            hands = (pinches[0].track_id, pinches[1].track_id)
            if self._mode != "scale" or self._scale_hands != hands:
                self.reset()
                self._mode, self._scale_hands = "scale", hands
            self._two_hand_scale(pinches[:2], selected.scale)
            return
        if self._mode == "scale":
            self.reset()

        if self._mode == "drag":
            owner = by_hand.get(self._hand_id)
            if owner is not None and owner.name == "pinch":
                self._drag(owner)
                return
            self.reset()

        if self._mode == "hold":
            owner = by_hand.get(self._hand_id)
            if owner is not None and owner.name == "fist":
                self._owner_seen = now
            elif now - self._owner_seen > HOLD_GRACE_SECONDS or (
                owner is not None and owner.name in ("open-palm", "pinch")
            ):
                self.reset()  # the holding hand really let go
            if self._mode == "hold":
                if selected:
                    self._swipe(gestures, selected.rotation)
                return

        # Otherwise start a new action with a pinching or fisted hand.
        for gesture in sorted(gestures, key=lambda g: g.track_id):
            if gesture.name == "pinch" and self._start_drag(gesture, scene):
                return
            if gesture.name == "fist" and self._start_hold(gesture, scene, now):
                return

    def _start_drag(self, gesture: StableGesture, scene: SceneState) -> bool:
        point = landmark_to_screen(gesture.index_tip)
        # A pinch over a menu or panel must not grab the object behind it.
        if self._view.over_hud(point):
            return False
        target = scene.find(self._view.pick(point))
        if target is None:
            return False
        self._mode, self._hand_id = "drag", gesture.track_id
        self._dispatch(Select(target.id))
        self._begin()
        depth = target.position[2]
        hit = intersect_depth_plane(self._view.ray(point), depth)
        self._drag_offset = np.array(
            [
                target.position[0] - hit[0] if hit is not None else 0.0,
                target.position[1] - hit[1] if hit is not None else 0.0,
                depth,
            ]
        )
        return True

    def _start_hold(self, gesture: StableGesture, scene: SceneState, now: float) -> bool:
        if scene.selected is None:
            # Nothing selected yet: hold the object under the fist.
            point = palm_centre(gesture)
            if self._view.over_hud(point):
                return False
            target = scene.find(self._view.pick(point))
            if target is None:
                return False
            self._dispatch(Select(target.id))
        self._mode, self._hand_id, self._owner_seen = "hold", gesture.track_id, now
        self._begin()
        return True

    def _swipe(self, gestures: tuple[StableGesture, ...], rotation) -> None:
        swiper = next(
            (g for g in gestures if g.track_id != self._hand_id and g.name == "open-palm"), None
        )
        if swiper is None:
            self._swipe_hand, self._swipe_anchor = None, None
            return

        position = palm_centre(swiper)
        if swiper.track_id != self._swipe_hand or self._swipe_anchor is None:
            # A palm that just appeared starts from where it is: no jump.
            self._swipe_hand, self._swipe_anchor = swiper.track_id, position
            return

        dx = position[0] - self._swipe_anchor[0]
        dy = position[1] - self._swipe_anchor[1]
        if math.hypot(dx, dy) < SWIPE_DEAD_ZONE:
            return
        self._swipe_anchor = position
        self._dispatch(SetRotation(swipe_turn(rotation, self._view.axes(), dx, dy)))

    def _two_hand_scale(self, pinches: list[StableGesture], current_scale: float) -> None:
        distance = landmark_distance(pinches[0].index_tip, pinches[1].index_tip)
        if self._scale_start is None:
            self._begin()
            self._scale_start = (max(distance, 0.01), current_scale)
            return
        start_distance, start_scale = self._scale_start
        self._dispatch(SetScale(start_scale * distance / start_distance))

    def _drag(self, gesture: StableGesture) -> None:
        depth = float(self._drag_offset[2])
        hit = intersect_depth_plane(self._view.ray(landmark_to_screen(gesture.index_tip)), depth)
        if hit is not None:
            self._dispatch(
                SetPosition(
                    (
                        float(hit[0] + self._drag_offset[0]),
                        float(hit[1] + self._drag_offset[1]),
                        depth,
                    )
                )
            )
