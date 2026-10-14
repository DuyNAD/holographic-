import pytest

from holostudio.scene.state import (
    AddObject,
    RemoveObject,
    Reset,
    Rotate,
    Scale,
    Select,
    SetScale,
    Translate,
    create_initial_scene,
    create_model_object,
    create_shape_object,
    find_spawn_position,
    reduce_scene,
)


def test_adds_and_selects_an_object():
    model = create_model_object("asset-1", "Robot")
    scene = reduce_scene(create_initial_scene(), AddObject(model))

    assert scene.objects[-1] == model
    assert scene.selected_id == model.id


def test_ignores_an_object_with_a_duplicate_id():
    initial = create_initial_scene()
    assert reduce_scene(initial, AddObject(initial.objects[0])) is initial


def test_does_not_transform_before_selection():
    initial = create_initial_scene()
    assert reduce_scene(initial, Translate(0, 1)) is initial


def test_transforms_only_the_selected_object():
    scene = reduce_scene(create_initial_scene(), Select("box-1"))
    scene = reduce_scene(scene, Translate(0, 1))
    scene = reduce_scene(scene, Rotate(1, 0.5))

    assert scene.objects[0].position == pytest.approx((-1.2, 0, 0))
    assert scene.objects[0].rotation == pytest.approx((0, 0.85, 0))
    assert scene.objects[1].position == (0, 0, 0)


def test_scale_is_clamped():
    scene = reduce_scene(create_initial_scene(), Select("box-1"))

    assert reduce_scene(scene, Scale(10)).objects[0].scale == 2.5
    assert reduce_scene(scene, SetScale(0.01)).objects[0].scale == 0.4


def test_removes_the_selected_object_and_clears_selection():
    scene = reduce_scene(create_initial_scene(), Select("sphere-1"))
    scene = reduce_scene(scene, RemoveObject())

    assert [obj.id for obj in scene.objects] == ["box-1", "cylinder-1"]
    assert scene.selected_id is None


def test_removes_by_id_and_keeps_a_different_selection():
    scene = reduce_scene(create_initial_scene(), Select("box-1"))
    scene = reduce_scene(scene, RemoveObject("cylinder-1"))

    assert [obj.id for obj in scene.objects] == ["box-1", "sphere-1"]
    assert scene.selected_id == "box-1"


def test_ignores_removal_without_selection_or_with_unknown_id():
    initial = create_initial_scene()
    assert reduce_scene(initial, RemoveObject()) is initial
    assert reduce_scene(initial, RemoveObject("missing")) is initial


def test_reset_restores_the_initial_scene():
    scene = reduce_scene(create_initial_scene(), RemoveObject("box-1"))
    assert reduce_scene(scene, Reset()) == create_initial_scene()


def test_new_objects_get_unique_ids():
    assert create_shape_object("sphere").id != create_shape_object("sphere").id
    first = create_model_object("asset-1", "Robot")
    second = create_model_object("asset-1", "Robot")
    assert first.asset_id == second.asset_id == "asset-1"
    assert first.id != second.id


def test_spawns_in_a_free_slot_instead_of_on_top_of_others():
    objects = create_initial_scene().objects

    assert find_spawn_position(()) == (0, 0, 0)
    assert find_spawn_position(objects) == (0, 1.9, 0)

    crowded = (*objects, create_shape_object("box", (0, 1.9, 0)))
    assert find_spawn_position(crowded) == (-2.2, 1.9, 0)
