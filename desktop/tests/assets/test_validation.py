from pathlib import Path

from holostudio.assets.validation import model_name_from_file, validate_glb


def test_accepts_a_valid_glb(glb_file):
    assert validate_glb(glb_file) is None


def test_rejects_other_extensions(tmp_path):
    path = tmp_path / "mesh.obj"
    path.write_text("mesh")
    assert validate_glb(path) == "Chỉ hỗ trợ file GLB."


def test_rejects_oversized_files(glb_file):
    assert validate_glb(glb_file, max_bytes=10) == "File GLB phải nhỏ hơn hoặc bằng 25 MB."


def test_rejects_short_and_corrupt_headers(tmp_path, glb_file):
    short = tmp_path / "short.glb"
    short.write_bytes(b"glTF")
    assert validate_glb(short) == "File GLB không hợp lệ."

    wrong_length = tmp_path / "wrong.glb"
    wrong_length.write_bytes(glb_file.read_bytes() + b"    ")
    assert validate_glb(wrong_length) == "File không phải GLB 2.0 hợp lệ."


def test_names_models_after_the_file():
    assert model_name_from_file(Path("Ghế gỗ.GLB")) == "Ghế gỗ"
    assert model_name_from_file(Path("   .glb")) == "Vật thể đã tải"
