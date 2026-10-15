"""Keeps the Panda3D scene graph in sync with SceneState and answers view queries."""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
from panda3d.core import (
    AmbientLight,
    BitMask32,
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionTraverser,
    DirectionalLight,
    LColor,
    LineSegs,
    NodePath,
    Point2,
    Point3,
    PointLight,
    Vec3,
)

from holostudio.avatar.pose import ViewRig
from holostudio.interaction.coordinates import ScreenPoint, screen_to_ndc
from holostudio.scene.state import SceneObject, SceneState

from .geometry import SHAPE_BUILDERS, make_box
from .transforms import apply_transform, panda_to_scene, scene_to_panda

OBJECT_TAG = "object_id"
BOUNDS_TAG = "local_bounds"  # the body's box in the object's own space, for touching
PICK_MASK = BitMask32.bit(1)
CAMERA_POSITION = (6.5, 4.3, 7.5)  # scene coordinates, as in the original app
VERTICAL_FOV = 42.0
SELECTED_TINT = (1.15, 1.3, 1.4, 1)
SELECTED_OUTLINE = (0.47, 0.92, 1, 1)
MARKED_OUTLINE = (1.0, 0.82, 0.3, 1)  # picked for grouping


def _hex_color(value: str) -> LColor:
    value = value.lstrip("#")
    if len(value) != 6:
        return LColor(1, 1, 1, 1)
    r, g, b = (int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return LColor(r, g, b, 1)


class SceneView:
    def __init__(
        self,
        base,
        model_path: Callable[[str], Path | None],
        load_model: Callable[[Path], NodePath],
    ) -> None:
        self._base = base
        self._model_path = model_path
        self._load_model = load_model
        self.root = base.render.attachNewNode("scene-objects")
        self._nodes: dict[str, tuple[SceneObject, NodePath]] = {}
        self._selected_id: str | None = None

        self._setup_camera()
        self._setup_lights()
        self._setup_grid()
        self._setup_picker()

    # --- setup ---------------------------------------------------------------

    def _setup_camera(self) -> None:
        base = self._base
        base.disableMouse()
        base.setBackgroundColor(0.012, 0.039, 0.075, 1)
        base.camera.setPos(*scene_to_panda(CAMERA_POSITION))
        base.camera.lookAt(0, 0, 0)
        base.camLens.setNearFar(0.1, 100)
        self.update_aspect()

    def update_aspect(self) -> None:
        """Keeps a fixed vertical field of view, so the scene follows the window shape."""
        aspect = self._base.getAspectRatio()
        horizontal = math.degrees(2 * math.atan(math.tan(math.radians(VERTICAL_FOV / 2)) * aspect))
        self._base.camLens.setFov(horizontal, VERTICAL_FOV)

    def _setup_lights(self) -> None:
        render = self._base.render
        ambient = AmbientLight("ambient")
        ambient.setColor((0.38, 0.42, 0.48, 1))
        render.setLight(render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor((1.0, 1.05, 1.1, 1))
        sun_node = render.attachNewNode(sun)
        sun_node.setPos(*scene_to_panda((4, 7, 5)))
        sun_node.lookAt(0, 0, 0)
        render.setLight(sun_node)

        accents = (((-5, 2, 2), (0.1, 0.55, 1.0, 1)), ((5, 1, -2), (0.42, 0.27, 1, 1)))
        for position, color in accents:
            light = PointLight("accent")
            light.setColor(color)
            light.setAttenuation((1, 0, 0.04))
            node = render.attachNewNode(light)
            node.setPos(*scene_to_panda(position))
            render.setLight(node)

    def _setup_grid(self) -> None:
        lines = LineSegs("grid")
        lines.setThickness(1)
        size, step, floor = 9, 1, -1.15
        for i in range(-size, size + 1, step):
            lines.setColor(0.11, 0.46, 0.6, 1) if i == 0 else lines.setColor(0.07, 0.19, 0.28, 1)
            lines.moveTo(*scene_to_panda((i, floor, -size)))
            lines.drawTo(*scene_to_panda((i, floor, size)))
            lines.moveTo(*scene_to_panda((-size, floor, i)))
            lines.drawTo(*scene_to_panda((size, floor, i)))
        grid = self._base.render.attachNewNode(lines.create())
        grid.setLightOff()

    def _setup_picker(self) -> None:
        self._traverser = CollisionTraverser("picker")
        self._queue = CollisionHandlerQueue()
        node = CollisionNode("pick-ray")
        node.setFromCollideMask(PICK_MASK)
        node.setIntoCollideMask(BitMask32.allOff())
        self._ray = CollisionRay()
        node.addSolid(self._ray)
        self._traverser.addCollider(self._base.camera.attachNewNode(node), self._queue)

    # --- sync ----------------------------------------------------------------

    def sync(self, scene: SceneState, marked: frozenset[str] = frozenset()) -> None:
        """`marked` are objects picked for grouping; they get an amber outline."""
        wanted = {obj.id: obj for obj in scene.objects}

        for object_id in list(self._nodes):
            if object_id not in wanted:
                self._nodes.pop(object_id)[1].removeNode()

        for obj in scene.objects:
            current = self._nodes.get(obj.id)
            if current is None or (current[0].kind, current[0].children) != (
                obj.kind,
                obj.children,
            ):
                if current is not None:
                    current[1].removeNode()
                node = self._create_node(obj)
            elif current[0] != obj:
                node = current[1]
            else:
                continue
            self._nodes[obj.id] = (obj, node)
            apply_transform(node, obj.position, obj.rotation, obj.scale)

        self._selected_id = scene.selected_id
        for object_id, (_obj, node) in self._nodes.items():
            selected = object_id == self._selected_id
            node.setColorScale(*SELECTED_TINT) if selected else node.clearColorScale()
            outline = node.find("selection-outline")
            if not outline:
                continue
            if object_id in marked:
                outline.setColor(*MARKED_OUTLINE)
                outline.show()
            elif selected:
                outline.setColor(*SELECTED_OUTLINE)
                outline.show()
            else:
                outline.hide()

    def _create_node(self, obj: SceneObject) -> NodePath:
        holder = self.root.attachNewNode(f"object-{obj.id}")
        # Only the top-level object carries the id, so touching any part of a group
        # picks the whole group.
        holder.setPythonTag(OBJECT_TAG, obj.id)
        body = self._build_body(obj, holder)
        body.setCollideMask(PICK_MASK)

        bounds = body.getTightBounds(holder)
        if bounds:
            holder.setPythonTag(BOUNDS_TAG, (np.array(bounds[0]), np.array(bounds[1])))
        outline = holder.attachNewNode(make_box(1.0))
        outline.setName("selection-outline")
        if obj.kind == "group" and bounds:
            low, high = bounds
            outline.setPos((low + high) / 2)
            outline.setScale((high - low) * 1.08 + Vec3(0.15, 0.15, 0.15))
        else:
            outline.setScale(1.75)
        outline.setRenderModeWireframe()
        outline.setLightOff()
        outline.setColor(*SELECTED_OUTLINE)
        outline.setCollideMask(BitMask32.allOff())
        outline.hide()
        return holder

    def _build_body(self, obj: SceneObject, parent: NodePath) -> NodePath:
        if obj.kind == "model":
            return self._create_model(obj, parent)
        if obj.kind == "group":
            parts = parent.attachNewNode("group-parts")
            for child in obj.children:
                holder = parts.attachNewNode(f"part-{child.id}")
                apply_transform(holder, child.position, child.rotation, child.scale)
                self._build_body(child, holder)
            return parts
        body = parent.attachNewNode(SHAPE_BUILDERS[obj.kind]())
        body.setColor(_hex_color(obj.color))
        return body

    def _create_model(self, obj: SceneObject, holder: NodePath) -> NodePath:
        path = self._model_path(obj.asset_id) if obj.asset_id else None
        try:
            if path is None or not path.exists():
                raise FileNotFoundError(obj.asset_id)
            model = self._load_model(path)
            model.reparentTo(holder)
            return model
        except Exception:
            # Missing or broken model: show a red wireframe placeholder instead.
            placeholder = holder.attachNewNode(make_box(1.4))
            placeholder.setRenderModeWireframe()
            placeholder.setLightOff()
            placeholder.setColor(1, 0.44, 0.49, 1)
            return placeholder

    # --- view queries for interaction ----------------------------------------

    def node_of(self, object_id: str) -> NodePath | None:
        entry = self._nodes.get(object_id)
        return entry[1] if entry else None

    def pick(self, point: ScreenPoint) -> str | None:
        ndc = screen_to_ndc(point)
        self._ray.setFromLens(self._base.camNode, *ndc)
        self._traverser.traverse(self.root)
        if self._queue.getNumEntries() == 0:
            return None
        self._queue.sortEntries()
        for entry in self._queue.entries:
            tagged = entry.getIntoNodePath().findNetPythonTag(OBJECT_TAG)
            if not tagged.isEmpty():
                return tagged.getPythonTag(OBJECT_TAG)
        return None

    def touch(self, point, reach: float) -> str | None:
        """The object whose surface is within `reach` of a scene point (nearest first)."""
        best, best_gap = None, reach
        world = Point3(*scene_to_panda(point))
        for object_id, (_obj, node) in self._nodes.items():
            bounds = node.getPythonTag(BOUNDS_TAG)
            if bounds is None:
                continue
            local = np.array(node.getRelativePoint(self._base.render, world))
            low, high = bounds
            gap = (
                np.linalg.norm(local - np.clip(local, low, high))
                * node.getScale(self._base.render).x
            )
            if gap <= best_gap:
                best, best_gap = object_id, gap
        return best

    def camera_axes(self) -> tuple[np.ndarray, np.ndarray]:
        """The camera's right and up directions, in scene coordinates."""
        quat = self._base.camera.getQuat(self._base.render)
        right = np.array(panda_to_scene(quat.getRight()))
        up = np.array(panda_to_scene(quat.getUp()))
        return right / np.linalg.norm(right), up / np.linalg.norm(up)

    def view_rig(self) -> ViewRig:
        """The 3D camera for placing the virtual hand."""
        quat = self._base.camera.getQuat(self._base.render)
        right, up = self.camera_axes()
        forward = np.array(panda_to_scene(quat.getForward()))
        return ViewRig(
            origin=np.array(CAMERA_POSITION, dtype=float),
            right=right,
            up=up,
            forward=forward / np.linalg.norm(forward),
            ray=lambda point: self.ray(point)[1],
            tan_half_fov=math.tan(math.radians(VERTICAL_FOV / 2)),
            reach=math.dist(CAMERA_POSITION, (0, 0, 0)),
        )

    def ray(self, point: ScreenPoint) -> tuple[np.ndarray, np.ndarray]:
        """Camera ray through a screen point, in scene coordinates."""
        near, far = Point3(), Point3()
        self._base.camLens.extrude(Point2(*screen_to_ndc(point)), near, far)
        render = self._base.render
        near_world = render.getRelativePoint(self._base.camera, near)
        far_world = render.getRelativePoint(self._base.camera, far)
        origin = np.array(panda_to_scene(near_world))
        direction = np.array(panda_to_scene(far_world)) - origin
        return origin, direction / np.linalg.norm(direction)
