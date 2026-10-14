"""Debounces gestures: a gesture must hold for a few frames to start or stop."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .classifier import GestureName, Observation

ACTIVATION_FRAMES = 2
RELEASE_FRAMES = 2
MINIMUM_CONFIDENCE = 0.6


@dataclass(frozen=True)
class GestureMachine:
    current: GestureName = "none"
    candidate: GestureName = "none"
    candidate_frames: int = 0
    missing_frames: int = 0
    confidence: float = 0.0


def advance(machine: GestureMachine, observation: Observation) -> GestureMachine:
    qualified = observation.name != "none" and observation.confidence >= MINIMUM_CONFIDENCE

    if not qualified:
        missing = machine.missing_frames + 1
        if machine.current != "none" and missing < RELEASE_FRAMES:
            return replace(machine, missing_frames=missing)
        return GestureMachine(missing_frames=min(missing, RELEASE_FRAMES))

    if observation.name == machine.current:
        return replace(
            machine,
            candidate="none",
            candidate_frames=0,
            missing_frames=0,
            confidence=observation.confidence,
        )

    frames = machine.candidate_frames + 1 if observation.name == machine.candidate else 1
    if frames >= ACTIVATION_FRAMES:
        return GestureMachine(current=observation.name, confidence=observation.confidence)

    return replace(machine, candidate=observation.name, candidate_frames=frames, missing_frames=0)
