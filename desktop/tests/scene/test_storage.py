import json

from holostudio.scene.state import (
    AddObject,
    Select,
    create_initial_scene,
    create_model_object,
    reduce_scene,
)
from holostudio.scene.storage import load_scene, save_scene


def test_round_trips_a_scene_without_selection(tmp_path):
    path = tmp_path / "scene.json"
    scene = reduce_scene(create_initial_scene(), AddObject(create_model_object("a-1", "Ghế")))
    scene = reduce_scene(scene, Select("box-1"))

    save_scene(scene, path)
    loaded = load_scene(path)

    assert loaded.objects == scene.objects
    assert loaded.selected_id is None
    assert not path.with_suffix(".tmp").exists()


def test_missing_file_gives_the_initial_scene(tmp_path):
    assert load_scene(tmp_path / "missing.json") == create_initial_scene()


def test_invalid_data_gives_the_initial_scene(tmp_path):
    path = tmp_path / "scene.json"
    for content in (
        "not json",
        json.dumps({"objects": "nope"}),
        json.dumps({"objects": [{"id": "x"}]}),
        json.dumps(
            {
                "objects": [
                    {
                        "id": "m",
                        "name": "M",
                        "kind": "model",
                        "color": "#fff",
                        "position": [0, 0, 0],
                        "rotation": [0, 0, 0],
                        "scale": 1,
                    }
                ]
            }
        ),
        json.dumps(
            {
                "objects": [
                    {
                        "id": "b",
                        "name": "B",
                        "kind": "box",
                        "color": "#fff",
                        "position": [0, 0, "x"],
                        "rotation": [0, 0, 0],
                        "scale": 1,
                    }
                ]
            }
        ),
    ):
        path.write_text(content, encoding="utf-8")
        assert load_scene(path) == create_initial_scene()


def test_clamps_scale_on_load(tmp_path):
    path = tmp_path / "scene.json"
    path.write_text(
        json.dumps(
            {
                "objects": [
                    {
                        "id": "b",
                        "name": "B",
                        "kind": "box",
                        "color": "#fff",
                        "position": [0, 0, 0],
                        "rotation": [0, 0, 0],
                        "scale": 99,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_scene(path).objects[0].scale == 2.5
