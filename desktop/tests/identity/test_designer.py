import numpy as np
import pytest

from holostudio.identity.bodies import Body
from holostudio.identity.designer import (
    ABSENT_SECONDS,
    CONFIRM_TIMEOUT_SECONDS,
    ENROLL_SAMPLES,
    ENROLL_TIMEOUT_SECONDS,
    DesignerLock,
    IdentityFrame,
    designer_hand_mask,
)
from holostudio.identity.faces import Face
from holostudio.tracking.types import Landmark

rng = np.random.default_rng(0)
PRINTS = {name: rng.normal(size=128) for name in ("alice", "bob", "carol")}


class Person:
    """A person in front of the camera; `size` grows as they come closer."""

    def __init__(self, name, x, size):
        self.name, self.x, self.size = name, x, size

    def face(self):
        raw = np.zeros(15, np.float32)
        raw[0] = list(PRINTS).index(self.name)  # lets the fake fingerprint find the person
        return Face(self.x - self.size / 2, 0.2, self.size, self.size * 1.3, 0.9, raw)

    def body(self):
        nose = (self.x, 0.2 + self.size * 0.65)
        return Body(nose=nose, wrists=((self.x - 0.1, 0.7), (self.x + 0.1, 0.7)))

    def hand(self):
        return tuple(Landmark(self.x + 0.1, 0.7, 0) for _ in range(21))


def fingerprint(face):
    name = list(PRINTS)[int(face.raw[0])]
    return PRINTS[name] + rng.normal(scale=0.2, size=128)  # a little noise each frame


def frame(t, people, faces_visible=True):
    return IdentityFrame(
        faces=[p.face() for p in people] if faces_visible else [],
        bodies=[p.body() for p in people],
        timestamp=t,
        fingerprint=fingerprint,
    )


def record(lock, people, start=0.0):
    """Records the nearest face; the person then waits for confirmation."""
    lock.request_enrollment(start)
    view = None
    for i in range(ENROLL_SAMPLES):
        view = lock.update(frame(start + i / 30, people))
    return view, start + ENROLL_SAMPLES / 30


def enroll(lock, people, start=0.0):
    """Records and confirms the nearest face."""
    view, t = record(lock, people, start)
    assert view.status == "pending"
    assert lock.confirm()
    t += 1 / 30
    return lock.update(frame(t, people)), t


def test_starts_unset_and_records_the_person_nearest_the_camera():
    alice, bob = Person("alice", 0.35, 0.22), Person("bob", 0.75, 0.12)
    lock = DesignerLock()
    assert lock.update(frame(0, [alice, bob])).status == "unset"

    view, _t = enroll(lock, [alice, bob])
    assert view.status == "locked"
    assert view.body == 0  # alice: the biggest face
    assert view.face.centre == pytest.approx(alice.face().centre)


def test_only_the_designers_hands_count():
    alice, bob = Person("alice", 0.35, 0.22), Person("bob", 0.75, 0.12)
    lock = DesignerLock()
    view, _t = enroll(lock, [alice, bob])
    bodies = [alice.body(), bob.body()]
    assert designer_hand_mask(bodies, view.body, (alice.hand(), bob.hand())) == (True, False)
    assert designer_hand_mask(bodies, None, (alice.hand(), bob.hand())) == (False, False)


def test_follows_the_designer_when_people_move_and_swap_places():
    alice, bob = Person("alice", 0.3, 0.22), Person("bob", 0.75, 0.15)
    lock = DesignerLock()
    _view, t = enroll(lock, [alice, bob])

    for _ in range(20):  # alice walks right slowly, bob walks left
        alice.x += 0.012
        bob.x -= 0.012
        t += 1 / 30
        view = lock.update(frame(t, [bob, alice]))  # MediaPipe order changes too
    assert view.status == "locked"
    assert view.body == 1  # still alice, now second in the list

    alice.x, bob.x = 0.2, 0.55  # a sudden jump: bob lands where alice was
    for _ in range(12):
        t += 1 / 30
        view = lock.update(frame(t, [bob, alice]))
    assert view.body == 1  # re-found by her face, not by position


def test_marks_the_designer_absent_and_takes_them_back_on_return():
    alice, bob = Person("alice", 0.35, 0.22), Person("bob", 0.75, 0.12)
    lock = DesignerLock()
    _view, t = enroll(lock, [alice, bob])

    for _ in range(int(ABSENT_SECONDS * 30) + 5):
        t += 1 / 30
        view = lock.update(frame(t, [bob]))
    assert view.status == "absent"
    assert view.body is None

    alice.x = 0.4
    for _ in range(12):
        t += 1 / 30
        view = lock.update(frame(t, [bob, alice]))
    assert view.status == "locked"
    assert view.body == 1


def test_someone_else_in_the_designers_spot_is_not_the_designer():
    alice, bob = Person("alice", 0.35, 0.22), Person("bob", 0.75, 0.12)
    lock = DesignerLock()
    _view, t = enroll(lock, [alice, bob])

    bob.x = 0.36  # alice leaves; bob steps into her place
    for _ in range(12):
        t += 1 / 30
        view = lock.update(frame(t, [bob]))
    assert view.body is None


def test_enrolment_gives_up_without_a_face():
    lock = DesignerLock()
    lock.request_enrollment(0.0)
    view = lock.update(frame(ENROLL_TIMEOUT_SECONDS + 0.1, [], faces_visible=False))
    assert view.status == "unset"
    assert "Không thấy mặt" in view.message


def test_choosing_again_replaces_the_designer():
    alice, bob = Person("alice", 0.35, 0.22), Person("bob", 0.75, 0.12)
    lock = DesignerLock()
    _view, t = enroll(lock, [alice, bob])

    bob.size = 0.3  # bob comes closest to the camera and presses the button
    view, t = enroll(lock, [alice, bob], start=t)
    assert view.status == "locked"
    assert view.body == 1


def test_a_recorded_face_waits_for_confirmation_before_locking():
    alice, bob = Person("alice", 0.35, 0.22), Person("bob", 0.75, 0.12)
    lock = DesignerLock()
    view, t = record(lock, [alice, bob])

    assert view.status == "pending"
    assert not lock.locked
    assert view.face.centre == pytest.approx(alice.face().centre)  # shown for confirmation
    # The candidate is followed (so only her hand can confirm), but nothing is locked.
    for _ in range(10):
        t += 1 / 30
        view = lock.update(frame(t, [alice, bob]))
    assert view.status == "pending"
    assert view.body == 0

    assert lock.confirm()
    view = lock.update(frame(t + 1 / 30, [alice, bob]))
    assert view.status == "locked" and lock.locked


def test_cancelling_the_first_choice_leaves_no_designer():
    alice = Person("alice", 0.35, 0.22)
    lock = DesignerLock()
    _view, t = record(lock, [alice])
    lock.cancel()
    view = lock.update(frame(t, [alice]))
    assert view.status == "unset"
    assert not lock.confirm()  # nothing to confirm any more


def test_cancelling_a_new_choice_keeps_the_previous_designer():
    alice, bob = Person("alice", 0.35, 0.22), Person("bob", 0.75, 0.12)
    lock = DesignerLock()
    _view, t = enroll(lock, [alice, bob])

    bob.size = 0.3  # bob is now closest and presses the button...
    view, t = record(lock, [alice, bob], start=t)
    assert view.status == "pending" and view.body == 1
    lock.cancel()  # ...but the user cancels
    for _ in range(12):
        t += 1 / 30
        view = lock.update(frame(t, [alice, bob]))
    assert view.status == "locked"
    assert view.body == 0  # alice is the designer again, found by her face


def test_picking_again_replaces_the_candidate():
    alice, bob = Person("alice", 0.35, 0.22), Person("bob", 0.75, 0.12)
    lock = DesignerLock()
    _view, t = record(lock, [alice, bob])
    alice.size, bob.size = 0.1, 0.3  # the right person steps forward
    view, t = record(lock, [alice, bob], start=t)
    assert view.status == "pending" and view.body == 1


def test_an_unconfirmed_candidate_is_dropped_after_a_while():
    alice = Person("alice", 0.35, 0.22)
    lock = DesignerLock()
    _view, t = record(lock, [alice])
    view = lock.update(frame(t + CONFIRM_TIMEOUT_SECONDS + 1, [alice]))
    assert view.status == "unset"
    assert not lock.locked
