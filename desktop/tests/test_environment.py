"""Gate for the foundation: every runtime library imports and Panda3D renders."""

import importlib

import pytest

import holostudio
from holostudio import config

STAGES = [
    "app",
    "camera",
    "tracking",
    "gestures",
    "interaction",
    "scene",
    "assets",
    "rendering",
    "hud",
    "calibration",
]


@pytest.mark.parametrize("stage", STAGES)
def test_each_stage_is_its_own_package(stage):
    module = importlib.import_module(f"holostudio.{stage}")
    assert module.__doc__


def test_runtime_libraries_import():
    import cv2
    import gltf  # noqa: F401  (panda3d-gltf)
    import mediapipe
    import numpy
    from mediapipe.tasks.python import vision

    assert cv2.__version__
    assert mediapipe.__version__ == "1.1.0"
    assert numpy.__version__
    assert vision.HandLandmarker


def test_panda3d_renders_offscreen(base):
    base.graphicsEngine.renderFrame()
    assert base.win is not None


def test_data_paths_live_under_one_folder():
    assert holostudio.__doc__
    for path in (config.SCENE_FILE, config.LIBRARY_DIR, config.HAND_LANDMARKER_FILE):
        assert config.DATA_DIR in path.parents
