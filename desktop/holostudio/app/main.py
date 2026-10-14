"""Application entry point."""

from __future__ import annotations

from panda3d.core import loadPrcFileData

from holostudio import config

from .single_instance import AlreadyRunning, SingleInstanceLock

WINDOW_CONFIG = """
window-title Holographic Studio
win-size 1280 720
win-origin -2 -2
framebuffer-multisample 1
multisamples 4
sync-video 1
audio-library-name null
"""

ALREADY_RUNNING_MESSAGE = (
    "Holographic Studio đang chạy ở một cửa sổ khác. "
    "Hãy dùng cửa sổ đó (hai cửa sổ không thể dùng chung camera)."
)


def main() -> None:
    try:
        with SingleInstanceLock(config.DATA_DIR / "app.lock"):
            loadPrcFileData("holostudio", WINDOW_CONFIG)
            from .studio import StudioApp

            StudioApp().run()
    except AlreadyRunning:
        raise SystemExit(ALREADY_RUNNING_MESSAGE) from None
