import pytest

from holostudio.scene.history import (
    BeginInteraction,
    EndInteraction,
    Redo,
    Undo,
    create_history,
    reduce_history,
)
from holostudio.scene.state import (
    AddObject,
    RemoveObject,
    Reset,
    Select,
    SetPosition,
    Translate,
    create_model_object,
)


def run(history, *actions):
    for action in actions:
        history = reduce_history(history, action)
    return history


def selected_box():
    return run(create_history(), Select("box-1"))


def box_position(history):
    return history.present.objects[0].position


def test_undoes_and_redoes_adding_a_model():
    model = create_model_object("asset-1", "Robot")
    added = run(create_history(), AddObject(model))
    undone = run(added, Undo())
    redone = run(undone, Redo())

    assert model in added.present.objects
    assert model not in undone.present.objects
    assert model in redone.present.objects


def test_undoes_and_redoes_a_discrete_transform():
    moved = run(selected_box(), Translate(0, 1))
    undone = run(moved, Undo())

    assert box_position(moved)[0] == pytest.approx(-1.2)
    assert box_position(undone)[0] == -2.2
    assert box_position(run(undone, Redo()))[0] == pytest.approx(-1.2)


def test_groups_gesture_frames_into_one_entry():
    history = run(
        selected_box(),
        BeginInteraction(),
        SetPosition((1, 0, 0)),
        SetPosition((2, 0, 0)),
        EndInteraction(),
    )

    assert len(history.past) == 1
    assert box_position(run(history, Undo())) == (-2.2, 0, 0)


def test_selection_and_unchanged_interactions_create_no_history():
    history = run(selected_box(), BeginInteraction(), EndInteraction())
    assert history.past == ()


def test_keeps_grouping_after_an_undo_during_an_interaction():
    history = run(selected_box(), BeginInteraction(), SetPosition((1, 0, 0)), Undo())

    assert box_position(history) == (-2.2, 0, 0)
    assert len(history.past) == 0
    assert len(history.future) == 1

    for frame in range(1, 11):
        history = run(history, SetPosition((frame, 0, 0)))
    assert len(history.past) == 0

    history = run(history, EndInteraction())
    assert len(history.past) == 1
    assert history.future == ()
    assert history.interaction_baseline is None
    assert box_position(run(history, Undo())) == (-2.2, 0, 0)


def test_keeps_grouping_after_a_redo_during_an_interaction():
    history = run(selected_box(), Translate(0, 1), Undo(), BeginInteraction(), Redo())

    assert box_position(history)[0] == pytest.approx(-1.2)
    assert len(history.past) == 1

    history = run(history, SetPosition((3, 0, 0)), SetPosition((4, 0, 0)), EndInteraction())
    assert len(history.past) == 2
    assert box_position(run(history, Undo()))[0] == pytest.approx(-1.2)


def test_records_discrete_edits_separately_during_an_interaction():
    history = run(
        selected_box(),
        BeginInteraction(),
        SetPosition((1, 0, 0)),
        Translate(1, 1),
        SetPosition((2, 1, 0)),
        EndInteraction(),
    )

    assert len(history.past) == 3
    history = run(history, Undo())
    assert box_position(history) == (1, 1, 0)
    history = run(history, Undo())
    assert box_position(history) == (1, 0, 0)
    history = run(history, Undo())
    assert box_position(history) == (-2.2, 0, 0)


def test_reset_during_an_interaction_can_be_undone():
    history = run(selected_box(), Translate(0, 1), BeginInteraction(), Reset(), EndInteraction())

    assert len(history.past) == 2
    assert box_position(run(history, Undo()))[0] == pytest.approx(-1.2)


def test_undoes_and_redoes_removing_an_object():
    removed = run(selected_box(), RemoveObject())
    undone = run(removed, Undo())

    assert len(removed.present.objects) == 2
    assert len(removed.past) == 1
    assert undone.present.objects[0].id == "box-1"
    assert len(run(undone, Redo()).present.objects) == 2


def test_history_is_limited():
    history = selected_box()
    for _ in range(60):
        history = run(history, Translate(0, 0.1))
    assert len(history.past) == 50
