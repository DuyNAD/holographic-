import pytest

from holostudio.assets.library import ModelLibrary, is_asset_referenced
from holostudio.assets.loader import NORMALIZED_MODEL_SIZE, ModelLoadError, load_glb
from holostudio.scene.history import create_history, reduce_history
from holostudio.scene.state import AddObject, RemoveObject, create_model_object


def test_loads_a_real_glb_normalized_to_a_common_size(glb_file):
    model = load_glb(glb_file)
    low, high = model.getTightBounds()
    size = high - low

    assert max(size.x, size.y, size.z) == pytest.approx(NORMALIZED_MODEL_SIZE, rel=1e-3)
    assert ((low + high) / 2).length() == pytest.approx(0, abs=1e-4)


def test_imports_once_and_survives_a_restart(tmp_path, glb_file):
    library = ModelLibrary(tmp_path / "library")
    result = library.import_file(glb_file)

    assert result.ok
    assert result.message == "Đã lưu “robot” vào kho."
    assert library.path_of(result.item.id).read_bytes() == glb_file.read_bytes()

    reopened = ModelLibrary(tmp_path / "library")
    assert [item.name for item in reopened.items] == ["robot"]


def test_rejects_invalid_and_unreadable_files(tmp_path, glb_file):
    library = ModelLibrary(tmp_path / "library")
    obj = tmp_path / "mesh.obj"
    obj.write_text("mesh")
    assert library.import_file(obj).message == "Chỉ hỗ trợ file GLB."

    def failing_parse(_path):
        raise ModelLoadError("broken")

    broken = ModelLibrary(tmp_path / "library", parse=failing_parse)
    assert broken.import_file(glb_file).message == "Không thể đọc nội dung file GLB."
    assert broken.items == []


def test_lists_newest_first(tmp_path, glb_file):
    library = ModelLibrary(tmp_path / "library", parse=lambda _p: None)
    first = library.import_file(glb_file).item
    second = library.import_file(glb_file).item
    assert [item.id for item in library.items][0] in {first.id, second.id}
    assert library.items[0].created_at >= library.items[1].created_at


def test_refuses_to_delete_a_model_the_history_can_restore(tmp_path, glb_file):
    library = ModelLibrary(tmp_path / "library", parse=lambda _p: None)
    item = library.import_file(glb_file).item
    history = reduce_history(create_history(), AddObject(create_model_object(item.id, item.name)))

    assert is_asset_referenced(history, item.id)
    refused = library.remove(item.id, history)
    assert not refused.ok
    assert "chưa thể xóa" in refused.message

    history = reduce_history(history, RemoveObject())
    assert is_asset_referenced(history, item.id)  # undo could bring it back

    removed = library.remove(item.id, create_history())
    assert removed.ok
    assert removed.message == "Đã xóa “robot” khỏi kho."
    assert library.items == []
    assert not library.path_of(item.id).exists()


def test_drops_index_entries_whose_file_is_gone(tmp_path, glb_file):
    library = ModelLibrary(tmp_path / "library", parse=lambda _p: None)
    item = library.import_file(glb_file).item
    library.path_of(item.id).unlink()

    assert ModelLibrary(tmp_path / "library").items == []
