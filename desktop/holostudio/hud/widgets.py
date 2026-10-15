"""The HUD as plain data: every panel, label, and button with its rectangle.

Layout is computed from the window size, so the HUD keeps the proportions of the
open window. The same widget list drives drawing, mouse clicks, and the hand
pointer, so all three always agree on what is where.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from holostudio.calibration.flow import CalibrationView

WidgetKind = Literal[
    "glass", "backdrop", "button", "danger", "tile", "label", "title", "muted", "camera", "meter"
]

NARROW_WIDTH = 760


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    def contains(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


@dataclass(frozen=True)
class Widget:
    id: str
    kind: WidgetKind
    rect: Rect
    text: str = ""
    enabled: bool = True
    pressed: bool = False
    size: float = 1.0  # text size in units
    value: float = 0.0  # meters
    interactive: bool = False
    align: Literal["auto", "left", "center"] = "auto"

    @property
    def blocks_pointer(self) -> bool:
        return self.kind not in ("label", "title", "muted", "meter")


@dataclass(frozen=True)
class LibraryEntry:
    id: str
    name: str
    size_text: str


@dataclass(frozen=True)
class HudContext:
    width: int
    height: int
    collapsed: bool = False
    panel: Literal["add", "guide", "group"] | None = None
    selected_name: str | None = None
    selected_is_group: bool = False
    grouping: bool = False  # picking objects to join into one group
    group_count: int = 0
    gesture_label: str = "Chưa nhận diện"
    confidence: float = 0.0
    camera_badge: str = "Đang tắt"
    camera_message: str = "Camera đang tắt."
    camera_active: bool = False
    camera_running: bool = False  # open, even if it only sends black frames
    camera_busy: bool = False
    tracking_message: str = "Video chỉ xử lý trên thiết bị."
    library: tuple[LibraryEntry, ...] = ()
    library_page: int = 0
    library_message: str = "GLB tối đa 25 MB · lưu trên thiết bị."
    library_error: bool = False
    toast: str | None = None
    calibration: CalibrationView | None = None
    guide_rows: tuple[tuple[str, str, str], ...] = field(default_factory=tuple)


SHORTCUTS = (
    ("Chọn vật thể", "Bấm chuột"),
    ("Di chuyển", "Phím mũi tên"),
    ("Xoay", "Q / E"),
    ("Thu phóng", "− / ="),
    ("Xóa vật thể", "Delete"),
    ("Hoàn tác / Làm lại", "Ctrl + Z / Ctrl + Y"),
)

SHAPES = (
    ("box", "■", "Khối lập phương"),
    ("sphere", "●", "Khối cầu"),
    ("cylinder", "▬", "Khối trụ"),
)


def unit_for(width: int, height: int) -> float:
    """Base size in pixels (like the web version's root font size)."""
    return min(18.0, max(11.0, 0.0045 * width + 0.0055 * height + 3))


class _Builder:
    def __init__(self) -> None:
        self.widgets: list[Widget] = []

    def add(self, widget_id: str, kind: WidgetKind, rect: Rect, text: str = "", **kw) -> Widget:
        interactive = kind in ("button", "danger", "tile") and kw.pop("interactive", True)
        widget = Widget(widget_id, kind, rect, text, interactive=interactive, **kw)
        self.widgets.append(widget)
        return widget


def build_hud(ctx: HudContext) -> tuple[Widget, ...]:
    u = unit_for(ctx.width, ctx.height)
    narrow = ctx.width < NARROW_WIDTH
    b = _Builder()

    _status(b, ctx, u, narrow)
    _camera(b, ctx, u, narrow)
    _menu(b, ctx, u, narrow)
    if ctx.toast:
        _toast(b, ctx, u, narrow)
    if ctx.calibration:
        _calibration(b, ctx, u)
    return tuple(b.widgets)


def _status(b: _Builder, ctx: HudContext, u: float, narrow: bool) -> None:
    x, y, h = u, u, 2.6 * u
    b.add("status.brand", "glass", Rect(x, y, 11 * u, h))
    b.add("status.brand.text", "title", Rect(x + u, y, 10 * u, h), "Holographic Studio")
    x += 11.6 * u
    b.add("status.gesture", "glass", Rect(x, y, 21 * u, h))
    b.add("status.gesture.text", "label", Rect(x + u, y, 14 * u, h), f"Cử chỉ: {ctx.gesture_label}")
    b.add(
        "status.gesture.meter",
        "meter",
        Rect(x + 15 * u, y + 1.15 * u, 3.4 * u, 0.3 * u),
        value=ctx.confidence,
    )
    b.add(
        "status.gesture.value",
        "label",
        Rect(x + 18.6 * u, y, 2.4 * u, h),
        f"{round(ctx.confidence * 100)}%",
    )
    if not narrow:
        x += 21.6 * u
        name = ctx.selected_name or "Chưa chọn vật thể"
        b.add("status.selection", "glass", Rect(x, y, 15 * u, h))
        b.add("status.selection.text", "label", Rect(x + u, y, 14 * u, h), f"Đang chọn: {name}")


def _camera(b: _Builder, ctx: HudContext, u: float, narrow: bool) -> None:
    width = (12 if narrow else 19) * u
    video_h = width * 9 / 16
    header, footer = 2.6 * u, 3.2 * u
    x = ctx.width - u - width
    total = header + video_h + footer
    y = ctx.height - u - total if narrow else u

    b.add("camera.window", "glass", Rect(x, y, width, total))
    b.add("camera.title", "title", Rect(x + 0.8 * u, y, 8 * u, header), "CAMERA", size=0.85)
    b.add(
        "camera.badge",
        "muted",
        Rect(x + width - 8 * u, y, 7.2 * u, header),
        ctx.camera_badge,
        size=0.75,
    )
    video_y = y + header
    video_text = "" if ctx.camera_active else ctx.camera_message
    b.add("camera.video", "camera", Rect(x, video_y, width, video_h), video_text)
    footer_y = video_y + video_h
    if not narrow:
        b.add(
            "camera.status",
            "muted",
            Rect(x + 0.8 * u, footer_y, width - 9 * u, footer),
            ctx.tracking_message,
            size=0.72,
        )
    label = (
        "Tắt camera"
        if ctx.camera_active or ctx.camera_running
        else ("Đang kết nối…" if ctx.camera_busy else "Bật camera")
    )
    b.add(
        "camera.toggle",
        "button",
        Rect(x + width - 7.6 * u, footer_y + 0.5 * u, 6.8 * u, footer - u),
        label,
        enabled=not ctx.camera_busy,
        size=0.8,
    )


def _menu(b: _Builder, ctx: HudContext, u: float, narrow: bool) -> None:
    size = 3.6 * u if narrow else 4.6 * u
    gap = 0.45 * u
    pad = 0.5 * u
    buttons = [("menu.toggle", "≡  Menu" if ctx.collapsed else "‹  Thu gọn", "button", True, False)]
    if not ctx.collapsed:
        buttons += [
            ("menu.add", "+\nThêm", "button", True, ctx.panel == "add"),
            ("menu.delete", "×\nXóa", "danger", ctx.selected_name is not None, False),
            ("menu.group", "Ghép\nkhối", "button", True, ctx.grouping),
            ("menu.ungroup", "Tách\nkhối", "button", ctx.selected_is_group, False),
            ("menu.guide", "?\nHướng dẫn", "button", True, ctx.panel == "guide"),
        ]

    count = len(buttons)
    if narrow:
        dock = Rect(
            u, ctx.height - u - size - 2 * pad, count * (size + gap) - gap + 2 * pad, size + 2 * pad
        )
    else:
        dock = Rect(u, 5 * u, size + 2 * pad, count * (size + gap) - gap + 2 * pad)
    b.add("menu.dock", "glass", dock)

    for index, (widget_id, text, kind, enabled, pressed) in enumerate(buttons):
        offset = index * (size + gap)
        rect = (
            Rect(dock.x + pad + offset, dock.y + pad, size, size)
            if narrow
            else Rect(dock.x + pad, dock.y + pad + offset, size, size)
        )
        b.add(widget_id, kind, rect, text, enabled=enabled, pressed=pressed, size=0.78)

    if ctx.collapsed or ctx.panel is None:
        return

    width = min(21 * u, ctx.width - 2 * u)
    if narrow:
        # The panel grows upward from the dock and must stay below the status bar.
        max_h = ctx.height - dock.h - 3 * u - 4.6 * u
        panel = Rect(u, dock.y - u, width, 0)  # height fixed below; grows upward
    else:
        max_h = ctx.height - 6 * u
        panel = Rect(dock.x + dock.w + 0.75 * u, dock.y, width, 0)

    content: list[tuple] = []
    height = _panel_content(content, ctx, u, width, narrow)
    height = min(height, max_h)
    if narrow:
        panel = Rect(panel.x, panel.y - height, width, height)
    else:
        panel = Rect(panel.x, panel.y, width, height)

    b.add("panel", "glass", panel)
    for widget_id, kind, (rx, ry, rw, rh), text, extra in content:
        if ry + rh > height:
            continue  # clipped by the panel height
        b.add(widget_id, kind, Rect(panel.x + rx, panel.y + ry, rw, rh), text, **extra)


def _panel_content(
    content: list, ctx: HudContext, u: float, width: float, narrow: bool = False
) -> float:
    """Appends (id, kind, relative rect, text, extra) and returns the content height."""
    pad = 0.9 * u
    inner = width - 2 * pad
    title = {"add": "Thêm vật thể", "group": "Ghép khối"}.get(ctx.panel, "Hướng dẫn")
    content.append(("panel.title", "title", (pad, 0, inner, 3 * u), title, {}))
    content.append(
        ("panel.close", "button", (width - pad - 2.2 * u, 0.4 * u, 2.2 * u, 2.2 * u), "×", {})
    )
    y = 3.4 * u

    def section(text: str) -> None:
        nonlocal y
        content.append(
            (f"section.{text}", "muted", (pad, y, inner, 1.6 * u), text.upper(), {"size": 0.7})
        )
        y += 1.8 * u

    if ctx.panel == "add":
        section("Hình cơ bản")
        tile_w = (inner - 2 * 0.45 * u) / 3
        for index, (kind, icon, name) in enumerate(SHAPES):
            content.append(
                (
                    f"shape.{kind}",
                    "tile",
                    (pad + index * (tile_w + 0.45 * u), y, tile_w, 4.4 * u),
                    f"{icon}\n{name}",
                    {"size": 0.72},
                )
            )
        y += 5.2 * u

        section(f"Kho vật thể ({len(ctx.library)})")
        if not ctx.library:
            content.append(
                (
                    "library.empty",
                    "muted",
                    (pad, y, inner, 3.2 * u),
                    "Kho đang trống. Tải file GLB lên một lần, sau đó lấy ra\n"
                    "bằng cử chỉ tay bao nhiêu lần tùy ý.",
                    {"size": 0.7},
                )
            )
            y += 3.6 * u
        else:
            per_page = 4
            pages = max(1, -(-len(ctx.library) // per_page))
            page = min(ctx.library_page, pages - 1)
            for entry in ctx.library[page * per_page : (page + 1) * per_page]:
                content.append(
                    (
                        f"library.place:{entry.id}",
                        "button",
                        (pad, y, inner - 3.4 * u, 2.8 * u),
                        f"•  {entry.name}   ·   {entry.size_text}",
                        {"size": 0.78, "align": "left"},
                    )
                )
                content.append(
                    (
                        f"library.remove:{entry.id}",
                        "danger",
                        (pad + inner - 3 * u, y, 3 * u, 2.8 * u),
                        "×",
                        {},
                    )
                )
                y += 3.2 * u
            if pages > 1:
                half = (inner - 0.45 * u) / 2
                content.append(
                    (
                        "library.prev",
                        "button",
                        (pad, y, half, 2.4 * u),
                        "‹ Trang trước",
                        {"enabled": page > 0, "size": 0.72},
                    )
                )
                content.append(
                    (
                        "library.next",
                        "button",
                        (pad + half + 0.45 * u, y, half, 2.4 * u),
                        f"Trang sau ›  ({page + 1}/{pages})",
                        {"enabled": page < pages - 1, "size": 0.72},
                    )
                )
                y += 2.8 * u

        content.append(
            ("library.upload", "button", (pad, y, inner, 2.8 * u), "Tải file GLB vào kho", {})
        )
        y += 3.2 * u
        content.append(
            (
                "library.message",
                "label",
                (pad, y, inner, 2.4 * u),
                ctx.library_message,
                {"size": 0.72, "pressed": ctx.library_error},
            )
        )
        y += 2.8 * u
    elif ctx.panel == "group":
        content.append(
            (
                "group.help",
                "label",
                (pad, y, inner, 3.4 * u),
                "Chụm tay (hoặc bấm chuột) vào từng khối để chọn hoặc bỏ chọn.",
                {"size": 0.75},
            )
        )
        y += 3.8 * u
        content.append(
            (
                "group.count",
                "title",
                (pad, y, inner, 2.4 * u),
                f"Đã chọn {ctx.group_count} khối",
                {"size": 0.95},
            )
        )
        y += 2.8 * u
        content.append(
            (
                "group.confirm",
                "button",
                (pad, y, inner, 2.8 * u),
                f"Ghép {ctx.group_count} khối" if ctx.group_count >= 2 else "Chọn ít nhất 2 khối",
                {"enabled": ctx.group_count >= 2, "pressed": ctx.group_count >= 2},
            )
        )
        y += 3.2 * u
        content.append(("group.cancel", "tile", (pad, y, inner, 2.6 * u), "Hủy", {}))
        y += 3.0 * u
    else:
        section("Cử chỉ tay")
        for name, instruction, action in ctx.guide_rows:
            if narrow:
                # Small windows: one compact line per gesture.
                content.append(
                    (
                        f"guide.{name}.name",
                        "label",
                        (pad, y, inner, 2 * u),
                        f"{name} · {action}",
                        {"size": 0.72},
                    )
                )
                y += 2.2 * u
                continue
            content.append((f"guide.{name}", "glass", (pad, y, inner, 3.4 * u), "", {}))
            content.append(
                (
                    f"guide.{name}.name",
                    "label",
                    (pad + 0.6 * u, y + 0.2 * u, inner, 1.5 * u),
                    name,
                    {"size": 0.8},
                )
            )
            content.append(
                (
                    f"guide.{name}.text",
                    "muted",
                    (pad + 0.6 * u, y + 1.6 * u, inner - u, 1.6 * u),
                    f"{instruction}  →  {action}",
                    {"size": 0.68},
                )
            )
            y += 3.8 * u
        # Small windows keep the gestures and the button; the shortcuts are in the README.
        if not narrow:
            section("Chuột và bàn phím")
            for action, keys in SHORTCUTS:
                content.append(
                    (
                        f"shortcut.{action}",
                        "muted",
                        (pad, y, inner, 1.6 * u),
                        f"{action}:  {keys}",
                        {"size": 0.72},
                    )
                )
                y += 1.7 * u
        y += 0.4 * u
        content.append(
            ("guide.recalibrate", "button", (pad, y, inner, 2.8 * u), "Hiệu chuẩn lại", {})
        )
        y += 3.2 * u
    return y + 0.4 * u


def _toast(b: _Builder, ctx: HudContext, u: float, narrow: bool) -> None:
    width, height = 24 * u, 3.4 * u
    x = (ctx.width - width) / 2
    y = 5 * u if narrow else ctx.height - u - height
    b.add("toast", "glass", Rect(x, y, width, height))
    b.add("toast.text", "label", Rect(x + u, y, width - 9 * u, height), ctx.toast, size=0.85)
    b.add(
        "toast.undo",
        "button",
        Rect(x + width - 7.6 * u, y + 0.5 * u, 7 * u, height - u),
        "Hoàn tác",
    )


def _calibration(b: _Builder, ctx: HudContext, u: float) -> None:
    view = ctx.calibration
    assert view is not None
    b.add("calibration.backdrop", "backdrop", Rect(0, 0, ctx.width, ctx.height))
    width = min(32 * u, ctx.width - 2 * u)
    height = 24 * u
    x, y = (ctx.width - width) / 2, (ctx.height - height) / 2
    b.add("calibration.dialog", "glass", Rect(x, y, width, height))

    step_w = (width - 2 * u - 4 * 0.35 * u) / 5
    for index in range(5):
        b.add(
            f"calibration.progress.{index}",
            "meter",
            Rect(x + u + index * (step_w + 0.35 * u), y + u, step_w, 0.25 * u),
            value=1.0 if index <= view.step else 0.0,
        )

    cy = y + 2.4 * u
    b.add(
        "calibration.eyebrow",
        "muted",
        Rect(x, cy, width, 1.6 * u),
        view.eyebrow.upper(),
        size=0.72,
        align="center",
    )
    b.add(
        "calibration.title",
        "title",
        Rect(x, cy + 1.8 * u, width, 3 * u),
        view.title,
        size=1.5,
        align="center",
    )
    b.add(
        "calibration.body",
        "muted",
        Rect(x + 2 * u, cy + 5.2 * u, width - 4 * u, 4.6 * u),
        view.body,
        size=0.8,
        align="center",
    )
    if view.check:
        b.add(
            "calibration.check",
            "glass",
            Rect(x + 3 * u, cy + 10.2 * u, width - 6 * u, 2.6 * u),
            pressed=view.ready,
        )
        mark = "√ " if view.ready else "○ "
        b.add(
            "calibration.check.text",
            "label",
            Rect(x + 3 * u, cy + 10.2 * u, width - 6 * u, 2.6 * u),
            mark + view.check,
            align="center",
        )

    by = y + height - 2 * u - 2.8 * u * len(view.buttons) - 0.5 * u * (len(view.buttons) - 1)
    for button in view.buttons:
        kind = "button" if button.action != "skip" else "tile"
        b.add(
            f"calibration.{button.action}",
            kind,
            Rect(x + (width - 18 * u) / 2, by, 18 * u, 2.8 * u),
            button.label,
            enabled=button.enabled,
            size=0.8 if kind == "tile" else 0.9,
        )
        by += 3.3 * u


def widget_at(widgets: tuple[Widget, ...], point: tuple[float, float]) -> Widget | None:
    """The topmost widget under a point in pixels; a backdrop swallows everything below it."""
    for widget in reversed(widgets):
        if widget.blocks_pointer and widget.rect.contains(*point):
            return widget
    return None


def press_target(widgets: tuple[Widget, ...], point: tuple[float, float]) -> str | None:
    """The id of the enabled button under a point, if any."""
    widget = widget_at(widgets, point)
    if widget and widget.interactive and widget.enabled:
        return widget.id
    return None


def over_hud(widgets: tuple[Widget, ...], point: tuple[float, float]) -> bool:
    return widget_at(widgets, point) is not None
