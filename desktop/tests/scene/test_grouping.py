import math

import numpy as np
import pytest

from holostudio.assets.library import is_asset_referenced
from holostudio.scene.history import Redo, Undo, create_history, reduce_history
from holostudio.scene.rotation import euler_xyz_matrix
from holostudio.scene.state import (
    AddObject,
    GroupObjects,
    RemoveObject,
    Select,
    SetPosition,
    SetRotation,
    SetScale,
    UngroupObject,
    create_initial_scene,
    create_model_object,
    iter_objects,
    reduce_scene,
)
from holostudio.scene.storage import load_scene, save_scene


def grouped(ids=("box-1", "sphere-1"), group_id="g1"):
    return reduce_scene(create_initial_scene(), GroupObjects(ids, group_id))


def world_point(obj, parent=None, local=(0.3, -0.2, 0.5)):
    """Where a point fixed on `obj` ends up in the scene."""
    point = euler_xyz_matrix(obj.rotation) @ np.array(local) * obj.scale + np.array(obj.position)
    if parent is not None:
        point = euler_xyz_matrix(parent.rotation) @ point * parent.scale + np.array(parent.position)
    return point


def test_grouping_joins_objects_into_one_selected_group_centred_on_them():
    scene = grouped()
    group = scene.find("g1")

    assert [obj.id for obj in scene.objects] == ["g1", "cylinder-1"]
    assert scene.selected_id == "g1"
    assert group.kind == "group"
    assert group.position == pytest.approx((-1.1, 0, 0))
    assert [child.id for child in group.children] == ["box-1", "sphere-1"]
    assert group.children[0].position == pytest.approx((-1.1, 0, 0))  # relative to the centre


def test_grouping_needs_at_least_two_objects():
    scene = create_initial_scene()
    assert reduce_scene(scene, GroupObjects(("box-1",))) is scene
    assert reduce_scene(scene, GroupObjects(("box-1", "missing"))) is scene


def test_a_group_moves_turns_and_scales_as_one_and_ungroups_in_place():
    scene = grouped()
    before = {child.id: world_point(child, scene.find("g1")) for child in scene.find("g1").children}

    scene = reduce_scene(scene, SetPosition((1.0, 2.0, -0.5)))
    scene = reduce_scene(scene, SetRotation((0.3, -0.8, 1.1)))
    scene = reduce_scene(scene, SetScale(1.5))
    group = scene.find("g1")
    moved = {child.id: world_point(child, group) for child in group.children}
    assert not np.allclose(moved["box-1"], before["box-1"])

    split = reduce_scene(scene, UngroupObject())
    assert [obj.id for obj in split.objects] == ["box-1", "sphere-1", "cylinder-1"]
    assert split.selected_id is None
    for obj_id, point in moved.items():
        # Every part stays exactly where it was shown inside the group.
        assert world_point(split.find(obj_id)) == pytest.approx(point, abs=1e-9)


def test_only_groups_can_be_split():
    scene = reduce_scene(create_initial_scene(), Select("box-1"))
    assert reduce_scene(scene, UngroupObject()) is scene


def test_groups_can_contain_groups():
    scene = grouped()
    scene = reduce_scene(scene, GroupObjects(("g1", "cylinder-1"), "g2"))
    assert len(scene.objects) == 1
    assert {obj.id for obj in iter_objects(scene.objects)} == {
        "g2",
        "g1",
        "cylinder-1",
        "box-1",
        "sphere-1",
    }
    scene = reduce_scene(scene, UngroupObject("g2"))
    assert [obj.id for obj in scene.objects] == ["g1", "cylinder-1"]


def test_group_and_ungroup_are_single_undo_steps():
    history = create_history()
    history = reduce_history(history, GroupObjects(("box-1", "sphere-1"), "g1"))
    history = reduce_history(history, UngroupObject())
    assert len(history.past) == 2

    history = reduce_history(history, Undo())
    assert [obj.id for obj in history.present.objects] == ["g1", "cylinder-1"]
    history = reduce_history(history, Undo())
    assert history.present.objects == create_initial_scene().objects
    history = reduce_history(history, Redo())
    assert history.present.find("g1") is not None


def test_deleting_a_group_deletes_its_parts_and_undo_brings_them_back():
    history = reduce_history(create_history(), GroupObjects(("box-1", "sphere-1"), "g1"))
    history = reduce_history(history, RemoveObject())
    assert [obj.id for obj in history.present.objects] == ["cylinder-1"]
    history = reduce_history(history, Undo())
    assert history.present.find("g1") is not None


def test_groups_are_saved_and_loaded_with_their_parts(tmp_path):
    path = tmp_path / "scene.json"
    scene = grouped()
    scene = reduce_scene(scene, SetRotation((0, math.pi / 4, 0)))
    save_scene(scene, path)
    assert load_scene(path).objects == scene.objects


def test_a_model_inside_a_group_still_counts_as_used():
    history = create_history()
    model = create_model_object("asset-1", "Robot", (3, 0, 0))
    history = reduce_history(history, AddObject(model))
    history = reduce_history(history, GroupObjects((model.id, "box-1"), "g1"))
    trimmed = type(history)(present=history.present)  # no undo history left
    assert is_asset_referenced(trimmed, "asset-1")
