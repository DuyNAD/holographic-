"""Procedural meshes for the built-in shapes, in scene units (same sizes as before)."""

from __future__ import annotations

import math

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
)

# Sizes match the original web scene: box 1.45, sphere r=0.82, cylinder r 0.7/0.88 h 1.65.
BOX_SIZE = 1.45
SPHERE_RADIUS = 0.82
CYLINDER_TOP = 0.7
CYLINDER_BOTTOM = 0.88
CYLINDER_HEIGHT = 1.65


class _MeshBuilder:
    def __init__(self, name: str) -> None:
        self.data = GeomVertexData(name, GeomVertexFormat.getV3n3(), Geom.UHStatic)
        self.vertex = GeomVertexWriter(self.data, "vertex")
        self.normal = GeomVertexWriter(self.data, "normal")
        self.triangles = GeomTriangles(Geom.UHStatic)
        self.count = 0
        self.name = name

    def add_vertex(self, position, normal) -> int:
        self.vertex.addData3(*position)
        self.normal.addData3(*normal)
        self.count += 1
        return self.count - 1

    def add_triangle(self, a: int, b: int, c: int) -> None:
        self.triangles.addVertices(a, b, c)

    def build(self) -> GeomNode:
        geom = Geom(self.data)
        geom.addPrimitive(self.triangles)
        node = GeomNode(self.name)
        node.addGeom(geom)
        return node


def make_box(size: float = BOX_SIZE) -> GeomNode:
    half = size / 2
    builder = _MeshBuilder("box")
    faces = [
        ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
        ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
        ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
        ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
        ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
    ]
    for normal, u, v in faces:
        corners = []
        for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            position = [half * (normal[i] + su * u[i] + sv * v[i]) for i in range(3)]
            corners.append(builder.add_vertex(position, normal))
        builder.add_triangle(corners[0], corners[1], corners[2])
        builder.add_triangle(corners[0], corners[2], corners[3])
    return builder.build()


def make_sphere(radius: float = SPHERE_RADIUS, rings: int = 24, segments: int = 40) -> GeomNode:
    builder = _MeshBuilder("sphere")
    for ring in range(rings + 1):
        phi = math.pi * ring / rings
        for segment in range(segments + 1):
            theta = 2 * math.pi * segment / segments
            normal = (
                math.sin(phi) * math.cos(theta),
                math.sin(phi) * math.sin(theta),
                math.cos(phi),
            )
            builder.add_vertex([radius * n for n in normal], normal)
    for ring in range(rings):
        for segment in range(segments):
            a = ring * (segments + 1) + segment
            b = a + segments + 1
            builder.add_triangle(a, b, a + 1)
            builder.add_triangle(a + 1, b, b + 1)
    return builder.build()


def make_cylinder(
    top: float = CYLINDER_TOP,
    bottom: float = CYLINDER_BOTTOM,
    height: float = CYLINDER_HEIGHT,
    segments: int = 36,
) -> GeomNode:
    """Built along Panda3D's up axis (Z), centred on the origin."""
    builder = _MeshBuilder("cylinder")
    half = height / 2
    slope = (bottom - top) / height
    for segment in range(segments + 1):
        theta = 2 * math.pi * segment / segments
        cos, sin = math.cos(theta), math.sin(theta)
        length = math.hypot(1, slope)
        normal = (cos / length, sin / length, slope / length)
        builder.add_vertex((bottom * cos, bottom * sin, -half), normal)
        builder.add_vertex((top * cos, top * sin, half), normal)
    for segment in range(segments):
        a = segment * 2
        builder.add_triangle(a, a + 2, a + 1)
        builder.add_triangle(a + 1, a + 2, a + 3)

    for z, radius, normal_z in ((half, top, 1), (-half, bottom, -1)):
        centre = builder.add_vertex((0, 0, z), (0, 0, normal_z))
        ring = [
            builder.add_vertex(
                (
                    radius * math.cos(2 * math.pi * s / segments),
                    radius * math.sin(2 * math.pi * s / segments),
                    z,
                ),
                (0, 0, normal_z),
            )
            for s in range(segments + 1)
        ]
        for s in range(segments):
            if normal_z > 0:
                builder.add_triangle(centre, ring[s], ring[s + 1])
            else:
                builder.add_triangle(centre, ring[s + 1], ring[s])
    return builder.build()


SHAPE_BUILDERS = {"box": make_box, "sphere": make_sphere, "cylinder": make_cylinder}
