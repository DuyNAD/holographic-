import numpy as np
import pytest

from holostudio.avatar.mesh import JOINT_RADII, build_hand_mesh, hand_size
from holostudio.avatar.profile import bone_lengths

from .test_depth import WORLD


def joints(scale=10.0):
    return np.array([(p.x, p.y, p.z) for p in WORLD]) * scale


def test_mesh_is_well_formed_and_its_topology_never_changes():
    first = build_hand_mesh(joints(), 10.0)
    moved = build_hand_mesh(joints() * 1.3 + 2, 10.0)
    assert first.triangles is moved.triangles
    assert first.vertices.shape == first.normals.shape == moved.vertices.shape
    assert first.triangles.min() == 0 and first.triangles.max() == len(first.vertices) - 1
    assert np.allclose(np.linalg.norm(first.normals, axis=1), 1, atol=1e-5)
    assert np.isfinite(first.vertices).all()


def test_every_joint_is_wrapped_in_skin_of_the_right_thickness():
    k = 10.0
    mesh = build_hand_mesh(joints(), k)
    for joint, radius in zip(joints(), JOINT_RADII, strict=True):
        nearest = np.min(np.linalg.norm(mesh.vertices - joint, axis=1))
        assert nearest <= radius * k * 1.001


def test_thicker_for_bigger_hands_and_safe_for_collapsed_bones():
    bones = list(bone_lengths(WORLD))
    bones[8] = 0.09  # wrist to middle knuckle of an average hand
    assert hand_size(tuple(bones)) == pytest.approx(1.0)
    bones[8] = 0.01
    assert hand_size(tuple(bones)) == pytest.approx(0.6)  # clamped
    collapsed = np.zeros((21, 3))
    assert np.isfinite(build_hand_mesh(collapsed, 10.0).vertices).all()
