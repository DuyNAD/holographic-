"""Paths and tunable constants shared by every stage."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Everything the app writes (scene, model library, downloaded tracking model)
# stays on this machine, in one folder that can be moved with an env var.
DATA_DIR = Path(os.environ.get("HOLOSTUDIO_DATA", PROJECT_ROOT / "data"))
SCENE_FILE = DATA_DIR / "scene.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
LIBRARY_DIR = DATA_DIR / "library"
MODELS_DIR = DATA_DIR / "models"

HAND_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
HAND_LANDMARKER_FILE = MODELS_DIR / "hand_landmarker.task"

MAX_TRACKED_HANDS = 2
CAMERA_INDEX = int(os.environ.get("HOLOSTUDIO_CAMERA", "0"))
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 360
CAMERA_FPS = 30

MAX_MODEL_FILE_BYTES = 25 * 1024 * 1024
DWELL_SECONDS = 1.0
UNDO_TOAST_SECONDS = 6.0

# Body pose (who is nearest the camera), loaded once and kept on this machine.
POSE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)
POSE_LANDMARKER_FILE = MODELS_DIR / "pose_landmarker_lite.task"
