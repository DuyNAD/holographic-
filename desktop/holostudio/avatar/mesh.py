"""A solid hand mesh built from the 21 joints: rounded joints, tapered finger bones and
a palm slab. The triangles never change; only the vertices move each frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

import numpy as np

from .profile import BONES

# Joint radii in metres for an average adult hand (MediaPipe landmark order).
JOINT_RADII = np.array([
    0.0165,                             # wrist
    0.0125, 0.0115, 0.0100, 0.0088,     # thumb
    0.0108, 0.0092, 0.0082, 0.0072,     # index
    0.0110, 0.0095, 0.0085, 0.0074,     # middle
    0.0104, 0.0090, 0.0080, 0.0070,     # ring
    0.0095, 0.0080, 0.0072, 0.0063,     # pinky
])  # fmt: skip
TYPICAL_PALM_LENGTH = 0.09  # wrist to middle knuckle, metres
PALM_OUTLINE = (0, 1, 2, 5, 9, 13, 17)  # around the palm, thumb side first
PALM_THICKNESS = 0.032  # metres
RING = 12  # vertices around each bone
SPHERE_RINGS = 6


@dataclass(frozen=True)
class HandMesh:
    vertices: np.ndarray  # (V, 3) float32
    normals: np.ndarray  # (V, 3) float32
    triangles: np.ndarray  # (T, 3) int32, same for every frame


@cache
def _unit_sphere() -> tuple[np.ndarray, np.ndarray]:
    """Vertices and triangles of a small UV sphere of radius 1."""
    points = [(0.0, 0.0, 1.0)]
    for i in range(1, SPHERE_RINGS):
        theta = np.pi * i / SPHERE_RINGS
        for j in range(RING):
            phi = 2 * np.pi * j / RING
            points.append((np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)))
    points.append((0.0, 0.0, -1.0))
    triangles = []
    bottom = len(points) - 1
    for j in range(RING):
        nxt = (j + 1) % RING
        triangles.append((0, 1 + j, 1 + nxt))
        last = 1 + (SPHERE_RINGS - 2) * RING
        triangles.append((bottom, last + nxt, last + j))
    for i in range(SPHERE_RINGS - 2):
        row, below = 1 + i * RING, 1 + (i + 1) * RING
        for j in range(RING):
            nxt = (j + 1) % RING
            triangles.append((row + j, below + j, below + nxt))
            triangles.append((row + j, below + nxt, row + nxt))
    return np.array(points), np.array(triangles)


@cache
def _topology() -> np.ndarray:
    sphere_vertices, sphere_triangles = _unit_sphere()
    triangles = []
    offset = 0
    for _ in range(21):  # joints
        triangles.append(sphere_triangles + offset)
        offset += len(sphere_vertices)
    for _ in BONES:  # open tubes: two rings each
        for j in range(RING):
            nxt = (j + 1) % RING
            a, b, c, d = offset + j, offset + nxt, offset + RING + j, offset + RING + nxt
            triangles.append(np.array([(a, c, d), (a, d, b)]))
        offset += 2 * RING
    count = len(PALM_OUTLINE)
    front, back = offset, offset + count + 1  # each face: outline + centre
    for j in range(count):
        nxt = (j + 1) % count
        triangles.append(np.array([(front + count, front + j, front + nxt)]))
        triangles.append(np.array([(back + count, back + nxt, back + j)]))
    return np.concatenate(triangles).astype(np.int32)


def _perpendiculars(directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    helper = np.where(np.abs(directions[:, :1]) < 0.9, [[1.0, 0, 0]], [[0, 1.0, 0]])
    u = np.cross(directions, helper)
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    return u, np.cross(directions, u)


def build_hand_mesh(joints: np.ndarray, units_per_metre: float, size: float = 1.0) -> HandMesh:
    """`joints` in scene units; `size` scales thickness to the user's hand."""
    joints = np.asarray(joints, dtype=float)
    radii = JOINT_RADII * size * units_per_metre
    sphere, _ = _unit_sphere()

    vertices = [(joints[:, None, :] + sphere[None] * radii[:, None, None]).reshape(-1, 3)]
    normals = [np.tile(sphere, (21, 1))]

    parents = np.array([a for a, _ in BONES])
    children = np.array([b for _, b in BONES])
    axis = joints[children] - joints[parents]
    length = np.linalg.norm(axis, axis=1, keepdims=True)
    axis = np.where(length > 1e-9, axis / np.maximum(length, 1e-9), [[0, 0, 1.0]])
    u, v = _perpendiculars(axis)
    angles = 2 * np.pi * np.arange(RING) / RING
    around = np.cos(angles)[None, :, None] * u[:, None] + np.sin(angles)[None, :, None] * v[:, None]
    start = joints[parents][:, None] + around * radii[parents][:, None, None]
    end = joints[children][:, None] + around * radii[children][:, None, None]
    vertices.append(np.concatenate([start, end], axis=1).reshape(-1, 3))
    normals.append(np.concatenate([around, around], axis=1).reshape(-1, 3))

    outline = joints[list(PALM_OUTLINE)]
    centre = outline.mean(axis=0)
    # Palm normal from index-knuckle and pinky-knuckle directions (sign does not matter:
    # both faces are drawn).
    normal = np.cross(joints[5] - joints[0], joints[17] - joints[0])
    normal /= max(np.linalg.norm(normal), 1e-9)
    half = normal * PALM_THICKNESS * size * units_per_metre / 2
    face = np.vstack([outline, centre])
    vertices += [face + half, face - half]
    normals += [np.tile(normal, (len(face), 1)), np.tile(-normal, (len(face), 1))]

    return HandMesh(
        np.vstack(vertices).astype(np.float32),
        np.vstack(normals).astype(np.float32),
        _topology(),
    )


def hand_size(bones: tuple[float, ...]) -> float:
    """How thick the hand is compared with an average hand, from its palm length."""
    palm_length = bones[8]  # wrist to middle knuckle
    return float(np.clip(palm_length / TYPICAL_PALM_LENGTH, 0.6, 1.6))
