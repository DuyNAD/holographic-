"""Scene objects and the pure reducer that changes them.

Every change to the scene is an action passed to :func:`reduce_scene`, so mouse,
keyboard, menu, and hand input all share exactly the same logic.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, replace
from typing import Literal

Vector3 = tuple[float, float, float]
ObjectKind = Literal["box", "sphere", "cylinder", "model", "group"]
ShapeKind = Literal["box", "sphere", "cylinder"]
Axis = Literal[0, 1, 2]

MIN_SCALE = 0.4
MAX_SCALE = 2.5


@dataclass(frozen=True)
class SceneObject:
    id: str
    name: str
    kind: ObjectKind
    color: str
    position: Vector3
    rotation: Vector3
    scale: float
    asset_id: str | None = None
    # A group's parts, positioned relative to the group's centre (its own frame).
    children: tuple[SceneObject, ...] = ()


def iter_objects(objects: tuple[SceneObject, ...]):
    """Every object, including the parts inside groups (and groups inside groups)."""
    for obj in objects:
        yield obj
        yield from iter_objects(obj.children)


@dataclass(frozen=True)
class SceneState:
    objects: tuple[SceneObject, ...]
    selected_id: str | None = None

    def find(self, object_id: str | None) -> SceneObject | None:
        return next((obj for obj in self.objects if obj.id == object_id), None)

    @property
    def selected(self) -> SceneObject | None:
        return self.find(self.selected_id)


# --- Actions -----------------------------------------------------------------


@dataclass(frozen=True)
class AddObject:
    object: SceneObject


@dataclass(frozen=True)
class RemoveObject:
    id: str | None = None


@dataclass(frozen=True)
class Select:
    id: str | None


@dataclass(frozen=True)
class Translate:
    axis: Axis
    delta: float


@dataclass(frozen=True)
class Rotate:
    axis: Axis
    delta: float


@dataclass(frozen=True)
class Scale:
    delta: float


@dataclass(frozen=True)
class SetPosition:
    position: Vector3


@dataclass(frozen=True)
class SetRotation:
    rotation: Vector3


@dataclass(frozen=True)
class SetScale:
    scale: float


@dataclass(frozen=True)
class Reset:
    pass


@dataclass(frozen=True)
class GroupObjects:
    """Joins several objects into one group that moves, turns and scales as one."""

    ids: tuple[str, ...]
    group_id: str | None = None


@dataclass(frozen=True)
class UngroupObject:
    """Splits a group back into its parts, keeping where they are in the scene."""

    id: str | None = None


SceneAction = (
    AddObject
    | RemoveObject
    | Select
    | Translate
    | Rotate
    | Scale
    | SetPosition
    | SetRotation
    | SetScale
    | Reset
    | GroupObjects
    | UngroupObject
)

# Continuous gesture frames; everything else is a discrete edit.
GESTURE_FRAME_ACTIONS = (SetPosition, SetRotation, SetScale)


# --- Factories ---------------------------------------------------------------

SHAPE_PRESETS: dict[ShapeKind, tuple[str, str]] = {
    "box": ("Khối lập phương", "#43c7ff"),
    "sphere": ("Khối cầu", "#7d67ff"),
    "cylinder": ("Khối trụ", "#43e0aa"),
}


def create_initial_scene() -> SceneState:
    return SceneState(
        objects=(
            SceneObject(
                "box-1", "Khối lập phương", "box", "#43c7ff", (-2.2, 0, 0), (0, 0.35, 0), 1
            ),
            SceneObject("sphere-1", "Khối cầu", "sphere", "#7d67ff", (0, 0, 0), (0, 0, 0), 1),
            SceneObject(
                "cylinder-1", "Khối trụ", "cylinder", "#43e0aa", (2.2, 0, 0), (0, 0, 0.18), 1
            ),
        ),
    )


def create_shape_object(kind: ShapeKind, position: Vector3 = (0, 0, 0)) -> SceneObject:
    name, color = SHAPE_PRESETS[kind]
    return SceneObject(f"{kind}-{uuid.uuid4()}", name, kind, color, position, (0, 0, 0), 1)


def create_model_object(asset_id: str, name: str, position: Vector3 = (0, 0, 0)) -> SceneObject:
    """Every placement gets its own id, so one stored model can be placed many times."""
    return SceneObject(
        f"model-{uuid.uuid4()}", name, "model", "#ffffff", position, (0, 0, 0), 1, asset_id
    )


SPAWN_SPACING = 2.2
SPAWN_CLEARANCE = 1.5


def find_spawn_position(objects: tuple[SceneObject, ...]) -> Vector3:
    """First free slot near the centre of the view, so new objects never overlap."""
    rows = (0.0, 1.9, 3.8)
    column_groups = ((0, -1, 1), (-2, 2))

    for columns in column_groups:
        for y in rows:
            for column in columns:
                candidate = (column * SPAWN_SPACING, y, 0.0)
                if all(math.dist(obj.position, candidate) >= SPAWN_CLEARANCE for obj in objects):
                    return candidate
    return (0.0, 0.0, 0.0)


# --- Reducer -----------------------------------------------------------------


def clamp_scale(value: float) -> float:
    return min(MAX_SCALE, max(MIN_SCALE, value))


def _with_axis(vector: Vector3, axis: Axis, delta: float) -> Vector3:
    values = list(vector)
    values[axis] += delta
    return (values[0], values[1], values[2])


def _update_selected(state: SceneState, update) -> SceneState:
    if state.selected is None:
        return state
    return replace(
        state,
        objects=tuple(update(obj) if obj.id == state.selected_id else obj for obj in state.objects),
    )


def reduce_scene(state: SceneState, action: SceneAction) -> SceneState:
    """Returns the same object when nothing changes, so callers can skip history."""
    match action:
        case AddObject(object=new):
            if state.find(new.id):
                return state
            return SceneState(objects=(*state.objects, new), selected_id=new.id)
        case RemoveObject(id=object_id):
            target = object_id or state.selected_id
            if not state.find(target):
                return state
            return SceneState(
                objects=tuple(obj for obj in state.objects if obj.id != target),
                selected_id=None if state.selected_id == target else state.selected_id,
            )
        case Select(id=object_id):
            if object_id == state.selected_id:
                return state
            return replace(state, selected_id=object_id)
        case Translate(axis=axis, delta=delta):
            return _update_selected(
                state, lambda obj: replace(obj, position=_with_axis(obj.position, axis, delta))
            )
        case Rotate(axis=axis, delta=delta):
            return _update_selected(
                state, lambda obj: replace(obj, rotation=_with_axis(obj.rotation, axis, delta))
            )
        case Scale(delta=delta):
            return _update_selected(
                state, lambda obj: replace(obj, scale=clamp_scale(obj.scale + delta))
            )
        case SetPosition(position=position):
            return _update_selected(state, lambda obj: replace(obj, position=position))
        case SetRotation(rotation=rotation):
            return _update_selected(state, lambda obj: replace(obj, rotation=rotation))
        case SetScale(scale=scale):
            return _update_selected(state, lambda obj: replace(obj, scale=clamp_scale(scale)))
        case Reset():
            return create_initial_scene()
        case GroupObjects(ids=ids, group_id=group_id):
            return _group(state, ids, group_id)
        case UngroupObject(id=object_id):
            return _ungroup(state, object_id or state.selected_id)
    raise TypeError(f"Unknown scene action: {action!r}")


GROUP_NAME = "Khối ghép"


def _group(state: SceneState, ids: tuple[str, ...], group_id: str | None) -> SceneState:
    wanted = set(ids)
    members = tuple(obj for obj in state.objects if obj.id in wanted)
    if len(members) < 2:
        return state
    centre = tuple(sum(obj.position[axis] for obj in members) / len(members) for axis in range(3))
    group = SceneObject(
        id=group_id or f"group-{uuid.uuid4()}",
        name=f"{GROUP_NAME} ({len(members)})",
        kind="group",
        color="#ffffff",
        position=(centre[0], centre[1], centre[2]),
        rotation=(0.0, 0.0, 0.0),
        scale=1.0,
        children=tuple(
            replace(
                obj,
                position=(
                    obj.position[0] - centre[0],
                    obj.position[1] - centre[1],
                    obj.position[2] - centre[2],
                ),
            )
            for obj in members
        ),
    )
    first = next(i for i, obj in enumerate(state.objects) if obj.id in wanted)
    remaining = [obj for obj in state.objects if obj.id not in wanted]
    remaining.insert(min(first, len(remaining)), group)
    return SceneState(objects=tuple(remaining), selected_id=group.id)


def _ungroup(state: SceneState, group_id: str | None) -> SceneState:
    from .rotation import euler_xyz_from_matrix, euler_xyz_matrix

    group = state.find(group_id)
    if group is None or group.kind != "group":
        return state
    turn = euler_xyz_matrix(group.rotation)
    parts = []
    for child in group.children:
        offset = turn @ child.position
        parts.append(
            replace(
                child,
                position=tuple(
                    float(group.position[axis] + group.scale * offset[axis]) for axis in range(3)
                ),
                rotation=euler_xyz_from_matrix(turn @ euler_xyz_matrix(child.rotation)),
                scale=clamp_scale(group.scale * child.scale),
            )
        )
    index = state.objects.index(group)
    objects = (*state.objects[:index], *parts, *state.objects[index + 1 :])
    return SceneState(objects=objects, selected_id=None)
