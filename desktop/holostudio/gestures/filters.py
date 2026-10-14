"""One Euro filter: strong smoothing when the hand is still, little lag when it moves.

Casiez, Roussel, Vogel (CHI 2012). Applied to every landmark coordinate.
"""

from __future__ import annotations

import math

from holostudio.tracking.types import Hand, Landmark

# Tuned for normalized image coordinates at webcam frame rates.
MIN_CUTOFF = 1.2  # Hz: smoothing strength for a still hand (lower = smoother)
BETA = 8.0  # how quickly smoothing relaxes as the hand speeds up
DERIVATIVE_CUTOFF = 1.0


def _alpha(cutoff: float, dt: float) -> float:
    tau = 1.0 / (2 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / dt)


class OneEuroHandFilter:
    def __init__(
        self,
        min_cutoff: float = MIN_CUTOFF,
        beta: float = BETA,
        d_cutoff: float = DERIVATIVE_CUTOFF,
    ) -> None:
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._value: list[float] | None = None
        self._derivative: list[float] | None = None
        self._timestamp: float | None = None

    def __call__(self, hand: Hand, timestamp: float) -> Hand:
        raw = [coordinate for point in hand for coordinate in point]
        if self._value is None or self._timestamp is None or len(raw) != len(self._value):
            self._value = raw
            self._derivative = [0.0] * len(raw)
            self._timestamp = timestamp
            return hand

        dt = timestamp - self._timestamp
        if dt <= 0:
            return self._as_hand()
        self._timestamp = timestamp

        d_alpha = _alpha(self._d_cutoff, dt)
        value, derivative = self._value, self._derivative
        assert derivative is not None
        for i, x in enumerate(raw):
            dx = (x - value[i]) / dt
            derivative[i] += d_alpha * (dx - derivative[i])
            cutoff = self._min_cutoff + self._beta * abs(derivative[i])
            value[i] += _alpha(cutoff, dt) * (x - value[i])
        return self._as_hand()

    def _as_hand(self) -> Hand:
        assert self._value is not None
        v = self._value
        return tuple(Landmark(v[i], v[i + 1], v[i + 2]) for i in range(0, len(v), 3))
