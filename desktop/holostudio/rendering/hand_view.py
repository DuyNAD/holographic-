"""Draws the virtual hands: one skinned mesh per hand, its vertices rewritten each frame."""

from __future__ import annotations

import numpy as np
from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    Material,
    NodePath,
    OmniBoundingVolume,
)

from holostudio.avatar.mesh import build_hand_mesh
from holostudio.avatar.pose import VirtualHand

from .transforms import SCENE_TO_PANDA

# The scene lights are bright for the white blocks; skin takes less so it keeps its tone.
SKIN_DIFFUSE = (0.62, 0.42, 0.32, 1)
SKIN_AMBIENT = (0.55, 0.36, 0.28, 1)
TOUCH_TINT = (0.75, 1.0, 1.1, 1)  # cool tint while the hand touches an object
MAX_HANDS = 2


class _HandNode:
    def __init__(self, parent: NodePath, index: int, triangles: np.ndarray, count: int) -> None:
        self.data = GeomVertexData(f"hand-{index}", GeomVertexFormat.getV3n3(), Geom.UHDynamic)
        self.data.uncleanSetNumRows(count)
        primitive = GeomTriangles(Geom.UHStatic)
        primitive.setIndexType(Geom.NTUint32)
        indexes = primitive.modifyVertices()
        indexes.uncleanSetNumRows(triangles.size)
        indexes.modifyHandle().copyDataFrom(np.ascontiguousarray(triangles, np.uint32))
        geom = Geom(self.data)
        geom.addPrimitive(primitive)
        node = GeomNode(f"virtual-hand-{index}")
        node.addGeom(geom)
        # The mesh moves every frame, so never cull it on stale bounds.
        node.setBounds(OmniBoundingVolume())
        node.setFinal(True)
        self.path = parent.attachNewNode(node)
        self.path.setTwoSided(True)
        self.rows = count

    def write(self, vertices: np.ndarray, normals: np.ndarray) -> None:
        interleaved = np.hstack([vertices @ SCENE_TO_PANDA.T, normals @ SCENE_TO_PANDA.T])
        handle = self.data.modifyArray(0).modifyHandle()
        handle.copyDataFrom(np.ascontiguousarray(interleaved, np.float32))


class HandView:
    def __init__(self, base, size: float = 1.0) -> None:
        self.root = base.render.attachNewNode("virtual-hands")
        material = Material("skin")
        material.setDiffuse(SKIN_DIFFUSE)
        material.setAmbient(SKIN_AMBIENT)
        material.setSpecular((0.12, 0.1, 0.09, 1))
        material.setShininess(18)
        self.root.setMaterial(material, 1)
        self.size = size
        self._nodes: list[_HandNode] = []

    def update(
        self, hands: tuple[VirtualHand, ...], touching: frozenset[int] = frozenset()
    ) -> None:
        for index, hand in enumerate(hands[:MAX_HANDS]):
            mesh = build_hand_mesh(hand.joints, hand.units_per_metre, self.size)
            if index == len(self._nodes):
                self._nodes.append(_HandNode(self.root, index, mesh.triangles, len(mesh.vertices)))
            node = self._nodes[index]
            node.write(mesh.vertices, mesh.normals)
            node.path.show()
            if hand.track_id in touching:
                node.path.setColorScale(TOUCH_TINT)
            else:
                node.path.clearColorScale()
        for node in self._nodes[len(hands) :]:
            node.path.hide()

    def destroy(self) -> None:
        self.root.removeNode()
