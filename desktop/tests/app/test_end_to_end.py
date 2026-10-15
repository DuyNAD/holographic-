"""Runs the whole app headless in its own process (Panda3D allows one window per process)."""

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]


def test_scripted_hand_drives_the_whole_pipeline():
    completed = subprocess.run(
        [sys.executable, "-m", "holostudio.app.smoke"],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        # Windows pipes default to the ANSI code page; the check names are Vietnamese.
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        timeout=180,
    )
    start = completed.stdout.index("{")
    result = json.loads(completed.stdout[start:])

    failed = [name for name, ok in result["checks"].items() if not ok]
    assert failed == [], completed.stderr[-2000:]
    assert completed.returncode == 0
    # Rendering, HUD, and gestures must leave plenty of room for 30 fps.
    assert result["frame_ms_p95"] < 33, result
