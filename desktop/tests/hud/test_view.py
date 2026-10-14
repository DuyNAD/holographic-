import numpy as np
import pytest

from holostudio.hud.camera_preview import crop_to_aspect, prepare_preview
from holostudio.hud.view import HudView
from holostudio.hud.widgets import HudContext, LibraryEntry, build_hud
from holostudio.interaction.pointer import PointerFrame, PointerMark
from holostudio.tracking.types import Landmark


def test_crop_keeps_the_window_aspect():
    image = np.zeros((480, 640, 3), np.uint8)  # 4:3 webcam
    cropped, (offset_x, offset_y) = crop_to_aspect(image, 16 / 9)
    assert cropped.shape[:2] == (360, 640)
    assert (offset_x, offset_y) == (0.0, 60 / 480)


def test_preview_is_mirrored_and_draws_the_hand_where_the_user_sees_it():
    image = np.zeros((360, 640, 3), np.uint8)
    image[:, :320] = (0, 0, 255)  # camera's left half is red
    hand = tuple(Landmark(0.25, 0.5, 0) for _ in range(21))

    preview = prepare_preview(image, (hand,), 16 / 9)

    assert tuple(preview[10, 600]) == (0, 0, 255)  # red now on the right (mirrored)
    assert tuple(preview[10, 40]) == (0, 0, 0)
    # a landmark at camera x=0.25 appears at 75% of the mirrored preview width
    assert preview[180, 479].any()
    assert not preview[180, 160].any()


@pytest.fixture
def hud(base):
    view = HudView(base)
    yield view
    view.root.removeNode()


def test_renders_widgets_pointer_and_camera(hud, base):
    width, height = base.win.getXSize(), base.win.getYSize()
    library = (LibraryEntry("a1", "Ghế gỗ", "12 KB"),)
    widgets = build_hud(HudContext(width, height, panel="add", library=library, camera_active=True))

    hud.render_widgets(widgets, width, height)
    builds = hud.rebuild_count
    hud.render_widgets(widgets, width, height)
    assert hud.rebuild_count == builds  # unchanged widgets are not rebuilt

    hud.update_camera(np.full((90, 160, 3), (0, 255, 0), np.uint8))
    hud.render_pointer(
        PointerFrame((PointerMark((0.5, 0.5), "point", True),), "menu.add", 0.5, None),
        width,
        height,
    )
    base.graphicsEngine.renderFrame()
    base.graphicsEngine.renderFrame()

    texture = base.win.getScreenshot()
    camera = next(w for w in widgets if w.id == "camera.video").rect
    x, y = int(camera.x + camera.w / 2), int(camera.y + camera.h / 2)
    pixels = np.frombuffer(bytes(texture.getRamImageAs("RGBA")), np.uint8)
    pixels = pixels.reshape(height, width, 4)[::-1]  # Panda3D images start at the bottom
    r, g, b, _a = pixels[y, x]
    assert g > 200 and r < 60 and b < 60


def test_every_hud_character_exists_in_the_font(hud):
    from holostudio.calibration.flow import CalibrationInputs, describe
    from holostudio.hud.widgets import SHORTCUTS  # noqa: F401  (part of the guide panel)

    rows = (("Nắm tay", "Chọn vật thể trước, nắm tay rồi nghiêng cổ tay", "Xoay vật thể"),)
    library = (LibraryEntry("a1", "Ghế gỗ", "12 KB"),) * 6
    contexts = [
        HudContext(1280, 720, panel="add", library=library, toast="Đã xóa “Khối cầu”"),
        HudContext(1280, 720, panel="guide", guide_rows=rows, collapsed=False),
        HudContext(1280, 720, collapsed=True, camera_busy=True),
        HudContext(1280, 720, designer_status="pending", designer_message="Chờ xác nhận"),
    ]
    for step in range(5):
        view = describe(step, CalibrationInputs(step % 2 == 0, False, True, step > 2))
        contexts.append(HudContext(1280, 720, calibration=view))

    characters = {c for ctx in contexts for w in build_hud(ctx) for c in w.text if c != "\n"}
    from panda3d.core import TextNode

    for bold in (False, True):
        node = TextNode("probe")
        node.setFont(hud._fonts[bold])
        missing = sorted(c for c in characters if not node.hasCharacter(c))
        assert missing == [], missing


def test_hud_changes_keep_the_camera_image_and_unchanged_widgets(hud, base):
    width, height = base.win.getXSize(), base.win.getYSize()
    hud.render_widgets(build_hud(HudContext(width, height, camera_active=True)), width, height)
    hud.update_camera(np.full((90, 160, 3), (0, 255, 0), np.uint8))
    menu_node = hud._nodes["menu.add"][1]

    # A status text change (e.g. the gesture label) must not blank the video or redraw the menu.
    changed = build_hud(HudContext(width, height, camera_active=True, gesture_label="Trỏ"))
    hud.render_widgets(changed, width, height)

    assert not hud._camera_card.isHidden()
    assert hud._nodes["menu.add"][1] is menu_node


def test_preview_draws_a_box_around_the_designers_face():
    from holostudio.tracking.types import FaceBox

    image = np.zeros((360, 640, 3), np.uint8)
    preview = prepare_preview(image, (), 16 / 9, designer_face=FaceBox(0.2, 0.2, 0.2, 0.3))
    green = (preview[:, :, 1] > 200) & (preview[:, :, 2] < 160)
    ys, xs = np.nonzero(green)
    # Mirrored: a face on the camera's left (x 0.2-0.4) shows on the right (x 0.6-0.8).
    assert 0.55 * 640 < xs.min() < 0.65 * 640
    assert 0.75 * 640 < xs.max() < 0.85 * 640
    assert 0.15 * 360 < ys.min() < 0.25 * 360


def test_a_recorded_face_waiting_for_confirmation_gets_an_amber_box():
    from holostudio.tracking.types import FaceBox

    image = np.zeros((360, 640, 3), np.uint8)
    box = FaceBox(0.2, 0.2, 0.2, 0.3)
    amber = prepare_preview(image, (), 16 / 9, designer_face=box, candidate=True)
    green = prepare_preview(image, (), 16 / 9, designer_face=box)
    assert (amber[:, :, 2] > 200).any()  # red channel lit: amber
    assert not (green[:, :, 2] > 200).any()
