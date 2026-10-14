"""Converts scene coordinates to Panda3D's.

Scene (kept from the original app): x right, y up, z toward the viewer,
rotations as XYZ Euler angles in radians.
Panda3D: x right, y forward (into the screen), z up.
"""

from __future__ import annotations

import numpy as np

from holostudio.scene.rotation import euler_xyz_matrix

# p_panda = SCENE_TO_PANDA @ p_scene
SCENE_TO_PANDA = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)


def scene_to_panda(vector) -> tuple[float, float, float]:
    x, y, z = vector
    return (x, -z, y)


def panda_to_scene(vector) -> tuple[float, float, float]:
    x, y, z = vector
    return (x, z, -y)


def panda_rotation_matrix(rotation) -> np.ndarray:
    """The scene rotation expressed in Panda3D axes (column-vector convention)."""
    return SCENE_TO_PANDA @ euler_xyz_matrix(rotation) @ SCENE_TO_PANDA.T


def apply_transform(node, position, rotation, scale: float) -> None:
    """Sets a NodePath's transform from scene position, rotation, and uniform scale."""
    from panda3d.core import LMatrix4f

    rotation_matrix = panda_rotation_matrix(rotation) * scale
    px, py, pz = scene_to_panda(position)
    # Panda3D matrices are row-vector based, so the rotation is transposed.
    m = rotation_matrix.T
    node.setMat(
        LMatrix4f(
            m[0, 0], m[0, 1], m[0, 2], 0,
            m[1, 0], m[1, 1], m[1, 2], 0,
            m[2, 0], m[2, 1], m[2, 2], 0,
            px, py, pz, 1,
        )
    )  # fmt: skip
