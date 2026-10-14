import pytest

from holostudio.calibration.flow import Calibration, CalibrationInputs
from holostudio.hud.widgets import (
    HudContext,
    LibraryEntry,
    build_hud,
    over_hud,
    press_target,
    unit_for,
)

SIZES = [(1280, 720), (1920, 1080), (700, 520), (1600, 800)]


def ids(widgets):
    return {w.id for w in widgets}


def centre(widgets, widget_id):
    rect = next(w for w in widgets if w.id == widget_id).rect
    return (rect.x + rect.w / 2, rect.y + rect.h / 2)


def test_scales_with_the_window():
    assert unit_for(700, 520) < unit_for(1280, 720) < unit_for(1920, 1080)
    assert unit_for(100, 100) == 11
    assert unit_for(9000, 9000) == 18


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("panel", [None, "add", "guide"])
def test_every_widget_stays_inside_the_window(size, panel):
    library = tuple(LibraryEntry(f"a{i}", f"Model {i}", "12 KB") for i in range(9))
    ctx = HudContext(
        *size,
        panel=panel,
        library=library,
        toast="Đã xóa “Khối cầu”",
        guide_rows=(("Trỏ", "Giơ ngón trỏ", "Di chuyển con trỏ"),) * 6,
    )
    for widget in build_hud(ctx):
        r = widget.rect
        assert r.x >= 0 and r.y >= 0, widget.id
        assert r.x + r.w <= size[0] + 1e-6 and r.y + r.h <= size[1] + 1e-6, widget.id


def test_menu_has_add_delete_guide_and_collapse():
    widgets = build_hud(HudContext(1280, 720))
    assert {"menu.toggle", "menu.add", "menu.delete", "menu.guide"} <= ids(widgets)
    delete = next(w for w in widgets if w.id == "menu.delete")
    assert not delete.enabled  # nothing selected

    collapsed = build_hud(HudContext(1280, 720, collapsed=True))
    assert [w.id for w in collapsed if w.id.startswith("menu.") and w.interactive] == [
        "menu.toggle"
    ]


def test_buttons_are_found_by_point_and_disabled_ones_are_not_pressed():
    widgets = build_hud(HudContext(1280, 720, selected_name="Khối cầu"))
    assert press_target(widgets, centre(widgets, "menu.delete")) == "menu.delete"

    widgets = build_hud(HudContext(1280, 720))
    assert press_target(widgets, centre(widgets, "menu.delete")) is None
    assert over_hud(widgets, centre(widgets, "menu.delete"))
    assert not over_hud(widgets, (640, 400))  # the open 3D space


def test_add_panel_lists_shapes_library_paging_and_upload():
    library = tuple(LibraryEntry(f"a{i}", f"Model {i}", "1 KB") for i in range(6))
    first = ids(build_hud(HudContext(1280, 720, panel="add", library=library)))
    assert {"shape.box", "shape.sphere", "shape.cylinder", "library.upload"} <= first
    assert {"library.place:a0", "library.remove:a3", "library.next"} <= first
    assert "library.place:a4" not in first

    second = ids(build_hud(HudContext(1280, 720, panel="add", library=library, library_page=1)))
    assert {"library.place:a4", "library.place:a5"} <= second


def test_calibration_dialog_blocks_everything_behind_it():
    flow = Calibration(open_=True)
    view = flow.view(CalibrationInputs(False, False, False, False))
    widgets = build_hud(HudContext(1280, 720, calibration=view))

    assert press_target(widgets, centre(widgets, "calibration.start")) == "calibration.start"
    assert press_target(widgets, centre(widgets, "calibration.skip")) == "calibration.skip"
    assert press_target(widgets, centre(widgets, "menu.add")) is None
    assert over_hud(widgets, (640, 360))


def test_toast_offers_undo():
    widgets = build_hud(HudContext(1280, 720, toast="Đã xóa “Khối cầu”"))
    assert press_target(widgets, centre(widgets, "toast.undo")) == "toast.undo"


@pytest.mark.parametrize("size", SIZES + [(1024, 600)])
def test_the_guide_shows_every_gesture_and_the_recalibrate_button(size):
    from holostudio.app.controller import GUIDE_ROWS

    found = ids(build_hud(HudContext(*size, panel="guide", guide_rows=GUIDE_ROWS)))
    assert "guide.recalibrate" in found
    assert all(f"guide.{name}.name" in found for name, _i, _a in GUIDE_ROWS)


def test_the_menu_has_a_designer_button_marked_when_locked():
    widgets = build_hud(HudContext(1280, 720, designer_status="locked"))
    button = next(w for w in widgets if w.id == "menu.designer")
    assert button.interactive and button.pressed
    assert not next(w for w in build_hud(HudContext(1280, 720)) if w.id == "menu.designer").pressed


@pytest.mark.parametrize("size", SIZES + [(1024, 600), (740, 480)])
@pytest.mark.parametrize("panel", ["add", "guide"])
def test_open_panels_never_cover_the_status_bar_camera_or_dock(size, panel):
    from holostudio.app.controller import GUIDE_ROWS

    library = tuple(LibraryEntry(f"a{i}", f"Model {i}", "1 KB") for i in range(9))
    rects = {
        w.id: w.rect
        for w in build_hud(HudContext(*size, panel=panel, library=library, guide_rows=GUIDE_ROWS))
    }

    def overlap(a, b):
        return a.x < b.x + b.w and b.x < a.x + a.w and a.y < b.y + b.h and b.y < a.y + a.h

    for other in (
        "status.brand",
        "status.gesture",
        "status.selection",
        "camera.window",
        "menu.dock",
    ):
        if other in rects:
            assert not overlap(rects["panel"], rects[other]), other


@pytest.mark.parametrize("size", SIZES + [(1024, 600), (740, 480)])
def test_the_confirm_dialog_shows_only_while_waiting_and_leaves_the_camera_visible(size):
    assert not any(w.id.startswith("designer.") for w in build_hud(HudContext(*size)))

    widgets = build_hud(HudContext(*size, designer_status="pending"))
    rects = {w.id: w.rect for w in widgets}
    assert {"designer.confirm", "designer.retry", "designer.cancel"} <= set(rects)

    def overlap(a, b):
        return a.x < b.x + b.w and b.x < a.x + a.w and a.y < b.y + b.h and b.y < a.y + a.h

    for other in ("camera.window", "status.brand", "status.gesture", "menu.dock"):
        assert not overlap(rects["designer.dialog"], rects[other]), other
    assert press_target(widgets, centre(widgets, "designer.confirm")) == "designer.confirm"
