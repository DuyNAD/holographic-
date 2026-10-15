"""How far the hand is from the camera, compared with when it was scanned.

The same hand looks smaller the farther it is. Comparing its size in the image with
its true size in metres (MediaPipe world landmarks) gives "image units per metre",
which is proportional to 1 / distance. The fit uses every landmark, so turning the
hand in the image plane does not change it.
"""

from math import sqrt

from holostudio.tracking.types import Hand

# Below this the hand is too small or flat-on to measure.
MIN_SPREAD = 1e-6


def image_scale(hand: Hand, world: Hand, aspect: float) -> float | None:
    """Image heights per metre of hand. None if it cannot be measured."""
    if len(hand) != len(world) or len(hand) < 2:
        return None
    count = len(hand)
    ix = sum(p.x for p in hand) / count
    iy = sum(p.y for p in hand) / count
    wx = sum(p.x for p in world) / count
    wy = sum(p.y for p in world) / count
    image = sum(((p.x - ix) * aspect) ** 2 + (p.y - iy) ** 2 for p in hand)
    metres = sum((p.x - wx) ** 2 + (p.y - wy) ** 2 for p in world)
    if image < MIN_SPREAD or metres < MIN_SPREAD:
        return None
    return sqrt(image / metres)


def relative_distance(scale: float, reference_scale: float) -> float:
    """Distance now / distance at the scan (2.0 = twice as far)."""
    return reference_scale / scale
