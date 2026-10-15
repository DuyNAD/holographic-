import math

import numpy as np
import pytest

from holostudio.assets.loader import load_glb
from holostudio.rendering.scene_view import SceneView
from holostudio.rendering.transforms import (
    euler_xyz_matrix,
    panda_to_scene,
    scene_to_panda,
)
from holostudio.scene.state import (
    AddObject,
    RemoveObject,
    Select,
    SetPosition,
    SetRotation,
    create_initial_scene,
    create_model_object,
    reduce_scene,
)


@pytest.fixture
def view(base, tmp_path, glb_file):
    paths = {"asset-ok": glb_file}
    scene_view = SceneView(base, lambda asset_id: paths.get(asset_id), load_glb)
    yield scene_view
    scene_view.root.removeNode()


def screen_point_of(base, scene_position):
    from panda3d.core import Point2, Point3

    world = Point3(*scene_to_panda(scene_position))
    camera_space = base.camera.getRelativePoint(base.render, world)
    projected = Point2()
    assert base.camLens.project(camera_space, projected)
    return ((projected.x + 1) / 2, (1 - projected.y) / 2)


def scene_point_of(node, local_scene_point):
    from panda3d.core import Point3

    world = node.getParent().getRelativePoint(node, Point3(*scene_to_panda(local_scene_point)))
    return np.array(panda_to_scene(world))


def test_axis_conversion_round_trips():
    assert panda_to_scene(scene_to_panda((1, 2, 3))) == (1, 2, 3)


@pytest.mark.parametrize("rotation", [(0, 0.35, 0), (0, 0, 0.18), (0.4, -0.7, 1.1)])
def test_node_transform_matches_the_scene_rotation(view, rotation):
    scene = reduce_scene(create_initial_scene(), Select("box-1"))
    scene = reduce_scene(scene, SetRotation(rotation))
    scene = reduce_scene(scene, SetPosition((1, 2, 3)))
    view.sync(scene)

    node = view.node_of("box-1")
    local = np.array([0.3, -0.2, 0.5])
    expected = euler_xyz_matrix(rotation) @ local + np.array([1, 2, 3])
    assert scene_point_of(node, local) == pytest.approx(expected, abs=1e-5)


def test_sync_adds_updates_and_removes_nodes(view):
    scene = create_initial_scene()
    view.sync(scene)
    assert all(view.node_of(obj.id) for obj in scene.objects)

    scene = reduce_scene(scene, RemoveObject("sphere-1"))
    view.sync(scene)
    assert view.node_of("sphere-1") is None
    assert view.root.getNumChildren() == 2


def test_selection_shows_the_outline(view):
    scene = reduce_scene(create_initial_scene(), Select("box-1"))
    view.sync(scene)
    assert not view.node_of("box-1").find("selection-outline").isHidden()
    assert view.node_of("sphere-1").find("selection-outline").isHidden()


def test_picks_the_object_under_a_screen_point(view, base):
    view.sync(create_initial_scene())
    base.graphicsEngine.renderFrame()

    assert view.pick(screen_point_of(base, (-2.2, 0, 0))) == "box-1"
    assert view.pick(screen_point_of(base, (2.2, 0, 0))) == "cylinder-1"
    assert view.pick((0.02, 0.02)) is None


def test_camera_ray_passes_through_the_projected_point(view, base):
    target = np.array([0.8, 0.4, 1.6])
    origin, direction = view.ray(screen_point_of(base, target))
    to_target = target - origin
    distance_from_ray = np.linalg.norm(to_target - (to_target @ direction) * direction)
    assert distance_from_ray == pytest.approx(0, abs=1e-4)


def test_models_load_from_the_library_and_missing_ones_show_a_placeholder(view):
    scene = reduce_scene(create_initial_scene(), AddObject(create_model_object("asset-ok", "R")))
    missing = create_model_object("asset-missing", "Gone")
    scene = reduce_scene(scene, AddObject(missing))
    view.sync(scene)

    ok_node = view.node_of(scene.objects[3].id)
    assert ok_node.find("**/normalized-model")
    missing_node = view.node_of(missing.id)
    assert not missing_node.find("**/normalized-model")
    assert missing_node.getNumChildren() == 2  # placeholder + outline


def test_vertical_field_of_view_is_fixed(view, base):
    view.update_aspect()
    assert base.camLens.getFov()[1] == pytest.approx(42)
    aspect = base.getAspectRatio()
    expected = math.degrees(2 * math.atan(math.tan(math.radians(21)) * aspect))
    assert base.camLens.getFov()[0] == pytest.approx(expected)


def test_camera_axes_are_the_screen_right_and_up_directions(view, base):
    right, up = view.camera_axes()
    forward = -np.array([6.5, 4.3, 7.5]) / np.linalg.norm([6.5, 4.3, 7.5])
    expected_right = np.cross(forward, [0, 1, 0])
    expected_right /= np.linalg.norm(expected_right)

    assert right == pytest.approx(expected_right, abs=1e-5)
    assert up == pytest.approx(np.cross(expected_right, forward), abs=1e-5)
    # A point one unit right of the origin appears to the right on screen.
    centre = screen_point_of(base, (0, 0, 0))
    assert screen_point_of(base, tuple(right))[0] > centre[0]
    assert screen_point_of(base, tuple(up))[1] < centre[1]


def test_a_group_is_drawn_from_its_parts_and_picked_as_one(view, base):
    from holostudio.scene.state import GroupObjects

    scene = reduce_scene(create_initial_scene(), GroupObjects(("box-1", "sphere-1"), "g1"))
    view.sync(scene)
    base.graphicsEngine.renderFrame()

    assert view.node_of("box-1") is None  # parts are inside the group's node
    group = view.node_of("g1")
    assert group.findAllMatches("**/part-*").getNumPaths() == 2
    # Touching either part picks the group.
    assert view.pick(screen_point_of(base, (-2.2, 0, 0))) == "g1"
    assert view.pick(screen_point_of(base, (0, 0, 0))) == "g1"
    assert view.pick(screen_point_of(base, (2.2, 0, 0))) == "cylinder-1"

    # The box part is drawn where it was before grouping.
    from panda3d.core import Point3

    part = group.find("**/part-box-1")
    centre = panda_to_scene(base.render.getRelativePoint(part, Point3(0, 0, 0)))
    assert centre == pytest.approx((-2.2, 0, 0), abs=1e-5)


def test_the_group_outline_wraps_all_parts(view):
    from holostudio.scene.state import GroupObjects

    scene = reduce_scene(create_initial_scene(), GroupObjects(("box-1", "sphere-1"), "g1"))
    scene = reduce_scene(scene, Select("g1"))
    view.sync(scene)
    outline = view.node_of("g1").find("selection-outline")
    low, high = outline.getTightBounds(view.node_of("g1"))
    assert not outline.isHidden()
    assert (high - low).x > 3.0  # spans both the box and the sphere


def test_objects_picked_for_grouping_get_an_amber_outline(view):
    view.sync(create_initial_scene(), marked=frozenset({"sphere-1"}))
    outline = view.node_of("sphere-1").find("selection-outline")
    assert not outline.isHidden()
    assert outline.getColor()[2] < 0.5  # amber, not the cyan selection colour
    assert view.node_of("box-1").find("selection-outline").isHidden()


def test_ungrouping_redraws_the_parts_as_separate_objects(view):
    from holostudio.scene.state import GroupObjects, UngroupObject

    scene = reduce_scene(create_initial_scene(), GroupObjects(("box-1", "sphere-1"), "g1"))
    view.sync(scene)
    scene = reduce_scene(scene, UngroupObject("g1"))
    view.sync(scene)
    assert view.node_of("g1") is None
    assert view.node_of("box-1") is not None and view.node_of("sphere-1") is not None


def test_the_virtual_hand_lands_under_the_real_hand_on_screen(view, base):
    from holostudio.avatar.pose import solve
    from holostudio.avatar.profile import HandProfile, bone_lengths
    from holostudio.gestures.engine import TrackedHand
    from holostudio.interaction.coordinates import landmark_to_screen

    from ..avatar.test_depth import ASPECT, WORLD, project

    landmarks = project(WORLD, (0.6, 0.45), 2.5)
    hand = TrackedHand(1, landmarks, WORLD, "point", ASPECT)
    virtual = solve(hand, HandProfile(bone_lengths(WORLD), 2.5), view.view_rig())
    for joint, landmark in zip(virtual.joints, landmarks, strict=True):
        assert screen_point_of(base, joint) == pytest.approx(landmark_to_screen(landmark), abs=1e-3)


def test_touch_finds_the_object_whose_surface_is_within_reach(view):
    scene = create_initial_scene()
    view.sync(scene)
    target = scene.objects[0]
    centre = np.array(target.position)
    assert view.touch(centre, 0.01) == target.id  # inside the body
    far = centre + [0, 30, 0]
    assert view.touch(far, 0.5) is None
    # Walk outward until the point leaves the body: then only a long enough reach touches it.
    step = centre.copy()
    while view.touch(step, 0.0) == target.id:
        step = step + [0, 0.02, 0]
    assert view.touch(step + [0, 0.3, 0], 0.2) is None
    assert view.touch(step + [0, 0.3, 0], 0.4) == target.id
