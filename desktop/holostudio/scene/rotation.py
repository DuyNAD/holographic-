"""Rotation math for scene objects.

Objects store XYZ Euler angles in radians (matrix = Rx @ Ry @ Rz). Turning an
object by hand happens around world axes (the camera's right and up), so the
turn is applied as a matrix and converted back to Euler angles.
"""

from __future__ import annotations

import math

import numpy as np

Vector3 = tuple[float, float, float]


def euler_xyz_matrix(rotation: Vector3) -> np.ndarray:
    a, b, c = rotation
    rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return rx @ ry @ rz


def euler_xyz_from_matrix(matrix: np.ndarray) -> Vector3:
    """Inverse of euler_xyz_matrix (same convention as three.js 'XYZ')."""
    m = matrix
    y = math.asin(max(-1.0, min(1.0, m[0, 2])))
    if abs(m[0, 2]) < 0.9999999:
        x = math.atan2(-m[1, 2], m[2, 2])
        z = math.atan2(-m[0, 1], m[0, 0])
    else:  # gimbal lock: fold the remaining turn into x
        x = math.atan2(m[2, 1], m[1, 1])
        z = 0.0
    return (x, y, z)


def axis_angle_matrix(axis, angle: float) -> np.ndarray:
    """Rodrigues' rotation around a unit axis (right-hand rule)."""
    x, y, z = np.asarray(axis, dtype=float) / np.linalg.norm(axis)
    c, s, t = math.cos(angle), math.sin(angle), 1 - math.cos(angle)
    return np.array(
        [
            [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
        ]
    )


def turn_in_world(rotation: Vector3, axis, angle: float) -> Vector3:
    """The object's rotation after turning it by `angle` around a world axis."""
    return euler_xyz_from_matrix(axis_angle_matrix(axis, angle) @ euler_xyz_matrix(rotation))
