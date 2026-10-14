"""Undo/Redo history with gesture interactions grouped into single entries."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .state import (
    GESTURE_FRAME_ACTIONS,
    SceneAction,
    SceneState,
    Select,
    create_initial_scene,
    reduce_scene,
)

HISTORY_LIMIT = 50


@dataclass(frozen=True)
class Undo:
    pass


@dataclass(frozen=True)
class Redo:
    pass


@dataclass(frozen=True)
class BeginInteraction:
    pass


@dataclass(frozen=True)
class EndInteraction:
    pass


HistoryAction = SceneAction | Undo | Redo | BeginInteraction | EndInteraction


@dataclass(frozen=True)
class SceneHistory:
    present: SceneState
    past: tuple[SceneState, ...] = ()
    future: tuple[SceneState, ...] = ()
    interaction_baseline: SceneState | None = None

    @property
    def can_undo(self) -> bool:
        return bool(self.past)

    @property
    def can_redo(self) -> bool:
        return bool(self.future)

    def all_states(self) -> tuple[SceneState, ...]:
        return (self.present, *self.past, *self.future)


def create_history(present: SceneState | None = None) -> SceneHistory:
    return SceneHistory(present=present or create_initial_scene())


def _append_past(past: tuple[SceneState, ...], state: SceneState) -> tuple[SceneState, ...]:
    return (*past, state)[-HISTORY_LIMIT:]


def _commit_interaction(history: SceneHistory) -> SceneHistory:
    """Pushes changes made since the interaction began as one entry.

    The baseline itself is left for the caller to clear or rebase.
    """
    baseline = history.interaction_baseline
    if baseline is None or baseline.objects == history.present.objects:
        return history
    return replace(
        history,
        past=_append_past(history.past, replace(baseline, selected_id=history.present.selected_id)),
        future=(),
    )


def _rebase(history: SceneHistory, present: SceneState) -> SceneState | None:
    # While a gesture stays open, later frames group from the new present so the
    # interaction controller and the history never fall out of sync.
    return present if history.interaction_baseline is not None else None


def reduce_history(history: SceneHistory, action: HistoryAction) -> SceneHistory:
    match action:
        case Undo():
            committed = _commit_interaction(history)
            if not committed.past:
                return history
            previous = committed.past[-1]
            return SceneHistory(
                present=previous,
                past=committed.past[:-1],
                future=(committed.present, *committed.future)[:HISTORY_LIMIT],
                interaction_baseline=_rebase(history, previous),
            )
        case Redo():
            committed = _commit_interaction(history)
            if not committed.future:
                return history
            following = committed.future[0]
            return SceneHistory(
                present=following,
                past=_append_past(committed.past, committed.present),
                future=committed.future[1:],
                interaction_baseline=_rebase(history, following),
            )
        case BeginInteraction():
            if history.interaction_baseline is not None:
                return history
            return replace(history, interaction_baseline=history.present)
        case EndInteraction():
            if history.interaction_baseline is None:
                return history
            return replace(_commit_interaction(history), interaction_baseline=None)

    next_present = reduce_scene(history.present, action)
    if next_present is history.present:
        return history

    if isinstance(action, Select) or (
        history.interaction_baseline is not None and isinstance(action, GESTURE_FRAME_ACTIONS)
    ):
        return replace(history, present=next_present)

    # Discrete edits (keyboard, menu, delete) always get their own entry, even
    # while a gesture interaction is still open.
    committed = _commit_interaction(history)
    return SceneHistory(
        present=next_present,
        past=_append_past(committed.past, committed.present),
        future=(),
        interaction_baseline=_rebase(history, next_present),
    )
