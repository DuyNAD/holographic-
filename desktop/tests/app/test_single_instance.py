import pytest

from holostudio.app.single_instance import AlreadyRunning, SingleInstanceLock


def test_only_one_instance_can_hold_the_lock(tmp_path):
    path = tmp_path / "app.lock"
    with SingleInstanceLock(path), pytest.raises(AlreadyRunning):
        SingleInstanceLock(path).acquire()
    # Released when the first instance exits.
    with SingleInstanceLock(path):
        pass
