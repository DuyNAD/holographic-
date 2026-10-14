"""Draws the HUD widgets, the hand pointer, and the camera preview with Panda3D."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from panda3d.core import (
    CardMaker,
    Filename,
    LineSegs,
    NodePath,
    TextNode,
    Texture,
    TransparencyAttrib,
)

from holostudio.interaction.pointer import PointerFrame

from .widgets import Rect, Widget, unit_for

FONT_REGULAR = Path("C:/Windows/Fonts/segoeui.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")

FILL = {
    "glass": (0.016, 0.055, 0.106, 0.78),
    "backdrop": (0.0, 0.02, 0.047, 0.84),
    "button": (0.04, 0.133, 0.204, 0.85),
    "danger": (0.2, 0.06, 0.1, 0.7),
    "tile": (0.04, 0.133, 0.204, 0.85),
    "camera": (0.008, 0.031, 0.063, 1),
}
BORDER = {
    "glass": (0.4, 0.87, 1, 0.24),
    "button": (0.4, 0.87, 1, 0.3),
    "danger": (1, 0.44, 0.49, 0.45),
    "tile": (0.4, 0.87, 1, 0.3),
    "camera": (0.4, 0.87, 1, 0.16),
}
TEXT = {
    "title": (0.925, 0.98, 1, 1),
    "label": (0.875, 0.973, 1, 1),
    "muted": (0.55, 0.66, 0.73, 1),
    "button": (0.79, 0.95, 1, 1),
    "danger": (1, 0.7, 0.73, 1),
    "tile": (0.79, 0.95, 1, 1),
    "camera": (0.49, 0.59, 0.67, 1),
}
DISABLED_TEXT = (0.31, 0.4, 0.46, 1)
ACCENT = (0.49, 1, 0.73, 1)
BRACKET = (0.43, 0.91, 1, 0.75)


class HudView:
    def __init__(self, base) -> None:
        self._base = base
        self.root = base.pixel2d.attachNewNode("hud")
        self.root.setTransparency(TransparencyAttrib.MAlpha)
        self.root.setDepthTest(False)
        self.root.setDepthWrite(False)
        # render2d draws in scene-graph order, so later layers are on top.
        self._static = self.root.attachNewNode("static")
        self._dynamic = self.root.attachNewNode("dynamic")
        self._widgets: tuple[Widget, ...] | None = None
        self._unit = 14.0
        self._fonts = {
            False: self._load_font(FONT_REGULAR),
            True: self._load_font(FONT_BOLD),
        }
        self._camera_texture = Texture("camera")
        self._camera_card: NodePath | None = None
        self._camera_widget_id: str | None = None
        self._camera_has_image = False
        self._nodes: dict[str, tuple[Widget, NodePath]] = {}
        self.rebuild_count = 0

    def _load_font(self, path: Path):
        if not path.exists():
            return None
        font = self._base.loader.loadFont(Filename.fromOsSpecific(str(path)).getFullpath())
        font = font.makeCopy()  # the font pool shares fonts; keep ours separate
        font.setPixelsPerUnit(48)
        return font

    # --- drawing primitives (pixel coordinates, y down) ----------------------

    def _rect(self, parent, x, y, w, h, color) -> NodePath:
        card = CardMaker("rect")
        card.setFrame(0, w, -h, 0)
        node = parent.attachNewNode(card.generate())
        node.setPos(x, 0, -y)
        node.setColor(*color)
        return node

    def _outline(self, parent, x, y, w, h, color, thickness=1.0) -> NodePath:
        lines = LineSegs("outline")
        lines.setThickness(thickness)
        lines.setColor(*color)
        lines.moveTo(x, 0, -y)
        for px, py in ((x + w, y), (x + w, y + h), (x, y + h), (x, y)):
            lines.drawTo(px, 0, -py)
        return parent.attachNewNode(lines.create())

    def _brackets(self, parent, x, y, w, h) -> None:
        size = min(0.9 * self._unit, w / 3, h / 3)
        lines = LineSegs("brackets")
        lines.setThickness(2)
        lines.setColor(*BRACKET)
        lines.moveTo(x, 0, -(y + size))
        lines.drawTo(x, 0, -y)
        lines.drawTo(x + size, 0, -y)
        lines.moveTo(x + w - size, 0, -(y + h))
        lines.drawTo(x + w, 0, -(y + h))
        lines.drawTo(x + w, 0, -(y + h - size))
        parent.attachNewNode(lines.create())

    def _text(self, parent, widget: Widget, color, align: str, bold: bool) -> None:
        if not widget.text:
            return
        node = TextNode(widget.id)
        font = self._fonts[bold] or self._fonts[False]
        if font:
            node.setFont(font)
        node.setText(widget.text)
        node.setTextColor(*color)
        size = self._unit * widget.size
        if widget.kind in ("muted", "label", "camera"):
            node.setWordwrap(max(1.0, widget.rect.w / size))
        node.setAlign({"left": TextNode.ALeft, "center": TextNode.ACenter}[align])
        text = parent.attachNewNode(node)
        text.setScale(size)

        lines = widget.text.count("\n") + 1
        if node.getWordwrap() and widget.kind != "camera":
            lines = max(lines, node.getNumRows())
        line_height = size * 1.25
        block = lines * line_height
        r = widget.rect
        top = r.y + max(0.0, (r.h - block) / 2) if widget.kind != "muted" or lines == 1 else r.y
        x = r.x + r.w / 2 if align == "center" else r.x
        text.setPos(x, 0, -(top + size * 0.95))

    # --- widgets -------------------------------------------------------------

    def render_widgets(self, widgets: tuple[Widget, ...], width: int, height: int) -> None:
        """Redraws only the widgets that changed since the last frame."""
        if widgets == self._widgets:
            return
        unit = unit_for(width, height)
        if unit != self._unit:
            self._unit = unit
            self._clear_nodes()
        self._widgets = widgets

        seen: set[str] = set()
        for index, widget in enumerate(widgets):
            seen.add(widget.id)
            cached = self._nodes.get(widget.id)
            if cached and cached[0] == widget:
                node = cached[1]
            else:
                if cached:
                    cached[1].removeNode()
                node = self._build_widget(widget)
                self._nodes[widget.id] = (widget, node)
            # render2d draws siblings in sort order, which keeps the layering stable.
            node.reparentTo(self._static, index)

        for widget_id in [key for key in self._nodes if key not in seen]:
            self._nodes.pop(widget_id)[1].removeNode()
            if widget_id == self._camera_widget_id:
                self._camera_card = None
        self.rebuild_count += 1

    def _clear_nodes(self) -> None:
        for _widget, node in self._nodes.values():
            node.removeNode()
        self._nodes.clear()
        self._camera_card = None

    def _build_widget(self, widget: Widget) -> NodePath:
        node = NodePath(widget.id)
        r = widget.rect
        kind = widget.kind
        if kind in FILL:
            fill = FILL[kind]
            if widget.pressed and kind in ("button", "tile", "glass"):
                fill = (0.12, 0.47, 0.63, 0.55)
            self._rect(node, r.x, r.y, r.w, r.h, fill)
        if kind in BORDER:
            border = BORDER[kind]
            if widget.pressed:
                border = (0.43, 0.91, 1, 0.7)
            self._outline(node, r.x, r.y, r.w, r.h, border)
        if kind == "glass" and r.w > 6 * self._unit:
            self._brackets(node, r.x, r.y, r.w, r.h)
        if kind == "meter":
            self._rect(node, r.x, r.y, r.w, r.h, (0.33, 0.52, 0.62, 0.3))
            if widget.value > 0:
                self._rect(node, r.x, r.y, r.w * widget.value, r.h, (0.19, 0.74, 0.93, 1))
        if kind == "camera":
            self._camera_card = self._rect(node, r.x, r.y, r.w, r.h, (1, 1, 1, 1))
            self._camera_card.setTexture(self._camera_texture)
            self._camera_widget_id = widget.id
            self._camera_rect = r
            # Keep showing the last camera image; never blank it just because the HUD changed.
            if not self._camera_has_image:
                self._camera_card.hide()

        color = TEXT.get(kind, TEXT["label"])
        if not widget.enabled:
            color = DISABLED_TEXT
        if widget.id == "library.message" and widget.pressed:
            color = (1, 0.7, 0.73, 1)
        align = "center" if kind in ("button", "danger", "tile", "camera") else "left"
        if widget.align != "auto":
            align = widget.align
        bold = kind == "title"
        if align == "left" and kind in ("button", "danger"):
            padded = Widget(
                widget.id,
                kind,
                Rect(r.x + self._unit, r.y, r.w, r.h),
                widget.text,
                size=widget.size,
            )
            self._text(node, padded, color, align, bold)
        else:
            self._text(node, widget, color, align, bold)
        return node

    # --- per-frame layers ----------------------------------------------------

    def update_camera(self, preview_bgr: np.ndarray | None) -> None:
        if self._camera_card is None:
            return
        if preview_bgr is None:
            self._camera_has_image = False
            self._camera_card.hide()
            return
        height, width = preview_bgr.shape[:2]
        if self._camera_texture.getXSize() != width or self._camera_texture.getYSize() != height:
            self._camera_texture.setup2dTexture(
                width, height, Texture.T_unsigned_byte, Texture.F_rgb
            )
        # Panda3D textures start at the bottom row.
        self._camera_texture.setRamImageAs(np.ascontiguousarray(preview_bgr[::-1]).tobytes(), "BGR")
        self._camera_has_image = True
        self._camera_card.show()

    def render_pointer(self, frame: PointerFrame | None, width: int, height: int) -> None:
        self._dynamic.removeNode()
        self._dynamic = self.root.attachNewNode("dynamic")
        if frame is None:
            return
        u = self._unit

        if frame.hover and self._widgets:
            widget = next((w for w in self._widgets if w.id == frame.hover), None)
            if widget:
                r = widget.rect
                self._outline(self._dynamic, r.x, r.y, r.w, r.h, ACCENT, 2)
                self._rect(self._dynamic, r.x, r.y + r.h - 3, r.w * frame.progress, 3, ACCENT)

        for mark in frame.marks:
            x, y = mark.position[0] * width, mark.position[1] * height
            color = {
                "pinch": (0.49, 1, 0.73, 1),
                "fist": (0.66, 0.6, 1, 1),
                "open-palm": (1, 0.8, 0.49, 1),
            }.get(mark.gesture, (0.42, 0.9, 1, 1))
            self._circle(self._dynamic, x, y, 0.68 * u, color, 1.0, 2)
            if mark.is_pointer and frame.progress > 0:
                self._circle(self._dynamic, x, y, 1.15 * u, ACCENT, frame.progress, 3)

    def _circle(self, parent, x, y, radius, color, fraction, thickness) -> None:
        lines = LineSegs("circle")
        lines.setThickness(thickness)
        lines.setColor(*color)
        steps = max(2, int(48 * fraction))
        for step in range(steps + 1):
            angle = -math.pi / 2 + 2 * math.pi * fraction * step / steps
            px, py = x + radius * math.cos(angle), y + radius * math.sin(angle)
            if step == 0:
                lines.moveTo(px, 0, -py)
            else:
                lines.drawTo(px, 0, -py)
        parent.attachNewNode(lines.create())

    @property
    def camera_aspect(self) -> float:
        rect = getattr(self, "_camera_rect", None)
        return rect.w / rect.h if rect else 16 / 9
