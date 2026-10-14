from holostudio.tracking.types import Landmark

FINGERS = ((5, 6, 8, 0.38), (9, 10, 12, 0.47), (13, 14, 16, 0.56), (17, 18, 20, 0.65))


def make_hand(extended=(), offset_x=0.0, pinch=False):
    """A synthetic hand; `extended` lists finger indexes 0=index .. 3=pinky."""
    hand = [Landmark(0.5 + offset_x, 0.7, 0)] * 21
    hand[0] = Landmark(0.5 + offset_x, 0.9, 0)
    hand[4] = Landmark(0.2 + offset_x, 0.5, 0)
    for index, (mcp, pip, tip, x) in enumerate(FINGERS):
        hand[mcp] = Landmark(x + offset_x, 0.64, 0)
        hand[pip] = Landmark(x + offset_x, 0.5, 0)
        hand[tip] = Landmark(x + offset_x, 0.18 if index in extended else 0.72, 0)
    if pinch:
        hand[4] = Landmark(hand[8].x - 0.01, hand[8].y, 0)
    return tuple(hand)


def make_real_fist(offset_x=0.0, loose_pinky=False):
    """A fist as MediaPipe sees it: fingertips curled back to the knuckles, and the
    thumb lying across the index finger (so thumb tip and index tip are close)."""
    hand = [Landmark(0.5 + offset_x, 0.7, 0)] * 21
    hand[0] = Landmark(0.5 + offset_x, 0.9, 0)
    for index, (mcp, pip, tip, x) in enumerate(FINGERS):
        hand[mcp] = Landmark(x + offset_x, 0.64, 0)
        hand[pip] = Landmark(x + offset_x, 0.55, 0)
        hand[pip + 1] = Landmark(x + offset_x, 0.6, 0)
        curled = 0.66 if not (loose_pinky and index == 3) else 0.4
        hand[tip] = Landmark(x + offset_x, curled, 0)
    hand[2] = Landmark(0.3 + offset_x, 0.75, 0)
    hand[3] = Landmark(0.36 + offset_x, 0.66, 0)
    hand[4] = Landmark(0.41 + offset_x, 0.62, 0)  # thumb tip over the index finger
    return tuple(hand)


def make_curved_pinch(offset_x=0.0):
    """An 'OK' pinch: index curls down to meet the thumb, other fingers relaxed up."""
    hand = list(make_hand((1, 2, 3), offset_x=offset_x))
    hand[6] = Landmark(0.38 + offset_x, 0.48, 0)
    hand[7] = Landmark(0.35 + offset_x, 0.42, 0)
    hand[8] = Landmark(0.31 + offset_x, 0.45, 0)
    hand[4] = Landmark(0.30 + offset_x, 0.47, 0)
    return tuple(hand)
