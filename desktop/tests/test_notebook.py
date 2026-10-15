"""HolographicStudio.ipynb must run on a fresh kernel (long steps skipped here)."""

import os
from pathlib import Path

import pytest

NOTEBOOK = Path(__file__).resolve().parents[1] / "HolographicStudio.ipynb"


def test_every_notebook_cell_is_valid_python():
    import nbformat

    notebook = nbformat.read(NOTEBOOK, as_version=4)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    assert len(code_cells) == 5
    for cell in code_cells:
        compile(cell.source, "notebook cell", "exec")
    assert notebook.metadata.kernelspec.name == "holostudio"


def test_the_notebook_runs_on_a_kernel(monkeypatch):
    import nbformat
    from nbclient import NotebookClient

    monkeypatch.setenv("HOLOSTUDIO_NOTEBOOK_DRY", "1")  # skip gate, smoke run and app launch
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    # "python3" is the kernel of the interpreter running the tests (provided by ipykernel),
    # so this works before setup.ps1 has registered the "holostudio" kernel.
    client = NotebookClient(
        notebook,
        kernel_name="python3",
        timeout=120,
        resources={"metadata": {"path": str(NOTEBOOK.parent)}},
    )
    try:
        client.execute()
    except Exception as error:  # pragma: no cover - show the failing cell
        pytest.fail(str(error)[-2000:])

    printed = "".join(
        output.get("text", "")
        for cell in notebook.cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "stream"
    )
    assert "mediapipe 1.1.0" in printed
    assert "hand_landmarker.task" in printed
    assert os.environ["HOLOSTUDIO_NOTEBOOK_DRY"] == "1"
