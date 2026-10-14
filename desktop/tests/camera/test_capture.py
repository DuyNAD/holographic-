import time

import numpy as np

from holostudio.camera.capture import MAX_FAILED_READS, CameraStream


class FakeSource:
    def __init__(self, opened=True, frames=None, fail_after=None):
        self._opened = opened
        self._count = 0
        self._fail_after = fail_after
        self.released = False

    def isOpened(self):  # noqa: N802
        return self._opened

    def read(self):
        self._count += 1
        time.sleep(0.001)
        if self._fail_after is not None and self._count > self._fail_after:
            return False, None
        return True, np.full((36, 64, 3), self._count % 255, dtype=np.uint8)

    def release(self):
        self.released = True


def wait_for(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return False


def test_starts_delivers_newest_frames_and_stops():
    source = FakeSource()
    camera = CameraStream(opener=lambda _i: source)

    camera.start()
    assert camera.wait_until_settled() == "active"
    assert wait_for(lambda: (camera.latest_frame() or None) and camera.latest_frame().index > 3)

    camera.stop()
    assert camera.status == "idle"
    assert camera.latest_frame() is None
    assert source.released


def test_reports_a_camera_that_cannot_open():
    camera = CameraStream(opener=lambda _i: FakeSource(opened=False))
    camera.start()

    assert wait_for(lambda: camera.status == "unavailable")
    assert "Không mở được camera" in camera.message


def test_detects_an_unplugged_camera():
    camera = CameraStream(opener=lambda _i: FakeSource(fail_after=5))
    camera.start()

    assert wait_for(lambda: camera.status == "disconnected", timeout=5)
    assert camera.latest_frame() is None
    assert MAX_FAILED_READS > 1


def test_reports_an_opener_crash():
    def broken(_index):
        raise RuntimeError("driver")

    camera = CameraStream(opener=broken)
    camera.start()
    assert wait_for(lambda: camera.status == "error")


class BlackThenLiveSource(FakeSource):
    """Sends black frames (camera held by another app) until `live` is set."""

    live = False

    def read(self):
        time.sleep(0.002)
        value = 120 if self.live else 0
        return True, np.full((36, 64, 3), value, dtype=np.uint8)


def test_reports_black_frames_and_recovers_when_the_camera_is_freed(monkeypatch):
    import holostudio.camera.capture as capture

    monkeypatch.setattr(capture, "BLACK_SECONDS", 0.2)
    source = BlackThenLiveSource()
    camera = CameraStream(opener=lambda _i: source)
    camera.start()
    try:
        assert wait_for(lambda: camera.status == "blocked")
        assert "hình đen" in camera.message
        source.live = True
        assert wait_for(lambda: camera.status == "active")
    finally:
        camera.stop()
