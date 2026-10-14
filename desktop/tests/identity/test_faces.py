"""Face tests use public OpenCV sample images (lena.jpg, messi5.jpg).

They live in data/test-assets/ (not committed); the tests are skipped if absent.
"""

import numpy as np
import pytest

from holostudio import config
from holostudio.identity.faces import (
    SAME_PERSON_SIMILARITY,
    Face,
    FaceIdentifier,
    cosine_similarity,
    nearest_face,
)

ASSETS = config.DATA_DIR / "test-assets"
needs_models = pytest.mark.skipif(
    not (
        config.FACE_DETECTOR_FILE.exists()
        and config.FACE_RECOGNIZER_FILE.exists()
        and (ASSETS / "lena.jpg").exists()
        and (ASSETS / "messi5.jpg").exists()
    ),
    reason="face models or test images not downloaded",
)


def face(x, y, w, h):
    return Face(x, y, w, h, 0.9, np.zeros(15, np.float32))


def test_the_biggest_face_is_the_nearest():
    far, near = face(0.1, 0.1, 0.1, 0.12), face(0.5, 0.3, 0.25, 0.3)
    assert nearest_face([far, near]) is near
    assert nearest_face([]) is None


def test_face_geometry():
    f = face(0.2, 0.2, 0.2, 0.2)
    assert f.centre == pytest.approx((0.3, 0.3))
    assert f.contains(0.3, 0.3)
    assert not f.contains(0.5, 0.5)
    assert f.contains(0.42, 0.3, margin=0.2)


@pytest.fixture(scope="module")
def identifier():
    return FaceIdentifier(config.FACE_DETECTOR_FILE, config.FACE_RECOGNIZER_FILE)


@pytest.fixture(scope="module")
def images():
    import cv2

    return cv2.imread(str(ASSETS / "lena.jpg")), cv2.imread(str(ASSETS / "messi5.jpg"))


@needs_models
def test_finds_one_face_in_each_sample(identifier, images):
    lena, messi = images
    found = identifier.detect(lena)
    assert len(found) == 1
    assert 0 < found[0].x < 1 and 0 < found[0].w < 1
    assert len(identifier.detect(messi)) == 1


@needs_models
def test_recognises_the_same_person_and_tells_different_people_apart(identifier, images):
    import cv2

    lena, messi = images
    reference = identifier.fingerprint(lena, identifier.detect(lena)[0])

    for variant in (
        cv2.resize(lena, None, fx=0.6, fy=0.6),  # further from the camera
        cv2.convertScaleAbs(lena, alpha=0.7, beta=-20),  # darker room
    ):
        same = identifier.fingerprint(variant, identifier.detect(variant)[0])
        assert cosine_similarity(reference, same) > SAME_PERSON_SIMILARITY + 0.3

    other = identifier.fingerprint(messi, identifier.detect(messi)[0])
    assert cosine_similarity(reference, other) < SAME_PERSON_SIMILARITY


@needs_models
def test_face_detection_is_fast_enough_for_live_video(identifier, images):
    import time

    import cv2

    frame = cv2.resize(images[1], (640, 360))
    identifier.detect(frame)
    started = time.perf_counter()
    for _ in range(10):
        identifier.detect(frame)
    assert (time.perf_counter() - started) / 10 < 0.03
