from holostudio.avatar.profile import BONES, HandProfile, bone_lengths, load_profile, save_profile
from holostudio.avatar.scan import SCAN_FRAMES, HandScan
from holostudio.gestures.engine import TrackedHand

from .test_depth import ASPECT, WORLD, project


def open_hand(centre=(0.5, 0.5), pixels_per_metre=3.0, gesture="open-palm"):
    return TrackedHand(1, project(WORLD, centre, pixels_per_metre), WORLD, gesture, ASPECT)


def run(scan, hand, frames):
    for _ in range(frames):
        status = scan.update((hand,) if hand else ())
    return status


def test_holding_an_open_palm_still_in_the_box_measures_the_hand():
    scan = HandScan()
    status = run(scan, open_hand(), SCAN_FRAMES // 2)
    assert status.phase == "scanning" and 0.4 < status.progress < 0.6
    status = run(scan, open_hand(), SCAN_FRAMES)
    assert status.phase == "done"
    assert scan.profile.bones == bone_lengths(WORLD)
    assert abs(scan.profile.reference_scale - 3.0) < 1e-6


def test_the_scan_asks_for_what_is_missing_and_starts_over():
    scan = HandScan()
    assert run(scan, None, 1).message == "Đưa bàn tay vào khung"
    assert run(scan, open_hand(centre=(0.1, 0.5)), 1).message == "Đưa cả bàn tay vào trong khung"
    assert run(scan, open_hand(gesture="fist"), 1).message.startswith("Xòe thẳng")
    run(scan, open_hand(), SCAN_FRAMES - 2)
    assert run(scan, open_hand(centre=(0.56, 0.5)), 1).message == "Giữ yên tay…"
    assert scan.status.progress == 0 and scan.profile is None


def test_a_hand_without_world_landmarks_is_not_scanned():
    scan = HandScan()
    hand = TrackedHand(1, project(WORLD, (0.5, 0.5), 3.0), (), "open-palm", ASPECT)
    assert run(scan, hand, SCAN_FRAMES + 5).phase == "waiting"


def test_profile_round_trips_and_bad_files_are_ignored(tmp_path):
    path = tmp_path / "hand_profile.json"
    profile = HandProfile(tuple(round(0.03 + 0.001 * i, 4) for i in range(len(BONES))), 2.5)
    save_profile(profile, path)
    assert load_profile(path) == profile
    assert set(path.read_text(encoding="utf-8").split('"')) >= {"bones", "reference_scale"}

    assert load_profile(tmp_path / "missing.json") is None
    path.write_text("{not json", encoding="utf-8")
    assert load_profile(path) is None
    save_profile(HandProfile((0.03,) * 3, 2.5), path)
    assert load_profile(path) is None  # wrong number of bones
