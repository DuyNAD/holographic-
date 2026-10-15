"""The model library: GLB files stored once on disk and placed many times."""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from holostudio.scene.history import SceneHistory
from holostudio.scene.state import iter_objects

from .loader import ModelLoadError, load_glb
from .validation import model_name_from_file, validate_glb

INDEX_FILE = "index.json"


@dataclass(frozen=True)
class LibraryItem:
    id: str
    name: str
    size: int
    created_at: float


@dataclass(frozen=True)
class ImportResult:
    item: LibraryItem | None
    message: str

    @property
    def ok(self) -> bool:
        return self.item is not None


@dataclass(frozen=True)
class RemoveResult:
    ok: bool
    message: str


def is_asset_referenced(history: SceneHistory, asset_id: str) -> bool:
    """An asset stays while the scene or its Undo/Redo history can still show it."""
    return any(
        obj.asset_id == asset_id
        for scene in history.all_states()
        for obj in iter_objects(scene.objects)  # models inside groups count too
    )


class ModelLibrary:
    def __init__(self, directory: Path, parse: Callable[[Path], object] = load_glb) -> None:
        self.directory = directory
        self._parse = parse
        self._items = self._read_index()

    @property
    def items(self) -> list[LibraryItem]:
        """Newest first."""
        return sorted(self._items.values(), key=lambda item: item.created_at, reverse=True)

    def get(self, asset_id: str) -> LibraryItem | None:
        return self._items.get(asset_id)

    def path_of(self, asset_id: str) -> Path:
        return self.directory / f"{asset_id}.glb"

    def import_file(self, source: Path) -> ImportResult:
        error = validate_glb(source)
        if error:
            return ImportResult(None, error)
        try:
            self._parse(source)
        except ModelLoadError:
            return ImportResult(None, "Không thể đọc nội dung file GLB.")

        item = LibraryItem(
            id=str(uuid.uuid4()),
            name=model_name_from_file(source),
            size=source.stat().st_size,
            created_at=time.time(),
        )
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, self.path_of(item.id))
            self._items[item.id] = item
            self._write_index()
        except OSError:
            self._items.pop(item.id, None)
            return ImportResult(None, "Không thể lưu vật thể trên thiết bị này.")
        return ImportResult(item, f"Đã lưu “{item.name}” vào kho.")

    def remove(self, asset_id: str, history: SceneHistory) -> RemoveResult:
        """Refuses while the scene or its Undo/Redo history still references the asset."""
        item = self._items.get(asset_id)
        if item is None:
            return RemoveResult(False, "Không tìm thấy vật thể trong kho.")
        if is_asset_referenced(history, asset_id):
            return RemoveResult(
                False,
                f"“{item.name}” đang có trong cảnh hoặc lịch sử Hoàn tác "
                "nên chưa thể xóa khỏi kho.",
            )
        del self._items[asset_id]
        self._write_index()
        self.path_of(asset_id).unlink(missing_ok=True)
        return RemoveResult(True, f"Đã xóa “{item.name}” khỏi kho.")

    def _read_index(self) -> dict[str, LibraryItem]:
        try:
            raw = json.loads((self.directory / INDEX_FILE).read_text(encoding="utf-8"))
            items = (LibraryItem(**entry) for entry in raw["items"])
            # Entries whose file disappeared are dropped instead of failing later.
            return {item.id: item for item in items if self.path_of(item.id).exists()}
        except (OSError, ValueError, KeyError, TypeError):
            return {}

    def _write_index(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        index = self.directory / INDEX_FILE
        temporary = index.with_suffix(".tmp")
        payload = {"items": [asdict(item) for item in self._items.values()]}
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, index)
